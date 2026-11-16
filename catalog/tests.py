import io, tempfile
from datetime import timedelta
from decimal import Decimal
from PIL import Image
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from accounts.forms import RegisterForm
from accounts.models import Customer
from catalog.models import RoomType, Service
from crews.models import Crew, Employee, ScheduleSlot
from orders.forms import OrderForm
from orders.models import Order, RecurrenceRule
from orders.services import assign_crew, assign_series, create_orders
from reviews.forms import ReviewForm

@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='cleaning-tests-'))
class InterfaceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.customer = Customer.objects.get(user__username='client1')
        cls.other = Customer.objects.get(user__username='client2')
        cls.service = Service.objects.get(slug='general')
        cls.room = RoomType.objects.get(slug='flat')

    def payload(self):
        start = (timezone.localtime() + timedelta(days=40)).replace(hour=9, minute=0, second=0, microsecond=0)
        return {'room_type': self.room.pk, 'service': self.service.pk, 'area': '54', 'address': self.customer.addresses.first().pk, 'start': start.strftime('%Y-%m-%dT%H:%M'), 'comment': 'Не звонить в домофон', 'period': ''}

    def login(self, name='client1'):
        self.client.force_login(User.objects.get(username=name))

    def test_public_and_customer_pages(self):
        for name in ['home', 'services', 'search', 'guarantee', 'contacts', 'privacy']:
            response = self.client.get(reverse('catalog:' + name))
            self.assertEqual(response.status_code, 200, name)
            self.assertContains(response, '<h1>', count=1)
        self.assertEqual(self.client.get(reverse('catalog:service', args=['general'])).status_code, 200)
        self.assertEqual(self.client.get(reverse('catalog:not_found')).status_code, 404)
        for name in ['login', 'register']:
            self.assertEqual(self.client.get(reverse('accounts:' + name)).status_code, 200)
        self.login()
        for name in ['mine', 'addresses', 'series', 'create']:
            self.assertEqual(self.client.get(reverse('orders:' + name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse('orders:detail', args=[self.customer.orders.first().pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('accounts:password')).status_code, 200)

    def test_staff_and_ownership(self):
        self.assertEqual(self.client.get(reverse('orders:mine')).status_code, 302)
        self.login()
        self.assertEqual(self.client.get(reverse('crews:dispatch')).status_code, 403)
        self.assertEqual(self.client.get(reverse('orders:detail', args=[self.other.orders.first().pk])).status_code, 404)
        self.login('dispatcher')
        for name in ['dispatch', 'schedule']:
            self.assertEqual(self.client.get(reverse('crews:' + name)).status_code, 200)
        self.assertEqual(self.client.get(reverse('crews:assign', args=[Order.objects.filter(status='new').first().pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('crews:series_assign', args=[RecurrenceRule.objects.first().pk])).status_code, 200)
        self.login('admin')
        for name in ['dashboard', 'manage']:
            self.assertEqual(self.client.get(reverse('crews:' + name)).status_code, 200)
        self.login('crew1')
        employee = Employee.objects.get(user__username='crew1')
        order = Order.objects.filter(crew=employee.crew).first()
        self.assertEqual(self.client.get(reverse('crews:day')).status_code, 200)
        self.assertEqual(self.client.get(reverse('crews:print', args=[order.pk])).status_code, 200)
        other = Order.objects.exclude(crew=employee.crew).filter(crew__isnull=False).first()
        self.assertEqual(self.client.get(reverse('crews:print', args=[other.pk])).status_code, 404)

    def test_pagination_search_and_json(self):
        Service.objects.bulk_create([Service(name=f'Проверочная услуга {i}', slug=f'pagination-{i}', kind='extra', unit='pcs', price=1, minutes_per_unit=1, description='Тест пагинации') for i in range(25)])
        page = self.client.get(reverse('catalog:services')).context['page_obj']
        self.assertEqual(len(page), 20)
        self.assertTrue(page.has_next())
        response = self.client.get(reverse('catalog:search'), {'q': 'Генеральная'})
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        response = self.client.get(reverse('catalog:service_api'), {'q': '<script>alert(1)</script>'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('<script>', response.json()['html'])
        self.assertEqual(response.json()['count'], 0)

    def test_quote_uses_tariffs_and_validates(self):
        data = {'room_type': self.room.pk, 'service': self.service.pk, 'area': '54', f"extra_{Service.objects.get(slug='window').pk}": 2, f"extra_{Service.objects.get(slug='fridge').pk}": 1, 'price': '1'}
        response = self.client.get(reverse('orders:estimate'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.json()['price']), Decimal('12200'))
        self.assertEqual(response.json()['duration_min'], 240)
        data['area'] = '9'
        self.assertEqual(self.client.get(reverse('orders:estimate'), data).status_code, 400)
        data.update(service=Service.objects.get(slug='office-daily').pk, area='54')
        self.assertEqual(self.client.get(reverse('orders:estimate'), data).status_code, 400)

    def test_order_save_validation_and_redirect(self):
        self.login()
        data = self.payload()
        data['area'] = '9'
        response = self.client.post(reverse('orders:create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Не звонить в домофон')
        self.assertIn('area', response.context['form'].errors)
        data['area'] = '54'
        before = Order.objects.count()
        response = self.client.post(reverse('orders:create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), before + 1)
        order = Order.objects.latest('pk')
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.price, Decimal('10800'))
        self.assertEqual(order.items.count(), 1)
        data = self.payload()
        data['address'] = self.other.addresses.first().pk
        form = OrderForm(data, customer=self.customer)
        self.assertFalse(form.is_valid())
        self.assertIn('address', form.errors)
        data = self.payload()
        data['start'] = '2020-01-01T09:00'
        form = OrderForm(data, customer=self.customer)
        self.assertFalse(form.is_valid())
        self.assertIn('start', form.errors)

    def test_registration_and_csrf(self):
        data = {'username': 'newclient', 'first_name': 'Иван', 'last_name': 'Тестов', 'email': 'wrong', 'phone': '123', 'password1': 'Valid-Example-937!', 'password2': 'Valid-Example-937!'}
        form = RegisterForm(data)
        self.assertFalse(form.is_valid())
        self.assertTrue({'email', 'phone', 'consent'}.issubset(form.errors))
        data.update(email='new@example.test', phone='+79990000099', consent='on')
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(user__username='newclient').exists())
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('accounts:register'), data).status_code, 403)

    def test_series_discount_and_atomic_assignment(self):
        data = self.payload()
        start = timezone.make_aware(timezone.datetime.strptime(data['start'], '%Y-%m-%dT%H:%M'))
        data.update(service=Service.objects.get(slug='support').pk, period='week', end_date=(start + timedelta(days=14)).date().isoformat())
        form = OrderForm(data, customer=self.customer)
        self.assertTrue(form.is_valid(), form.errors)
        orders = create_orders(self.customer, form.cleaned_data)
        self.assertEqual(len(orders), 3)
        self.assertEqual(orders[0].discount_percent, 10)
        self.assertEqual(orders[0].price, Decimal('4860'))
        crew = Crew.objects.filter(is_active=True).first()
        ScheduleSlot.objects.create(crew=crew, start=orders[1].start, end=orders[1].end, kind='day_off')
        with self.assertRaises(ValidationError):
            assign_series(orders[0].rule, crew)
        self.assertFalse(ScheduleSlot.objects.filter(order__in=orders).exists())
        orders[0].refresh_from_db()
        self.assertEqual(orders[0].status, 'new')

    def test_assignment_conflict_and_cancel(self):
        order = Order.objects.filter(status='new').first()
        crew = Crew.objects.filter(is_active=True).first()
        ScheduleSlot.objects.create(crew=crew, start=order.start, end=order.end, kind='day_off')
        with self.assertRaises(ValidationError):
            assign_crew(order.pk, crew)
        order.status = 'cancelled'
        order.save()
        with self.assertRaises(ValidationError):
            assign_crew(order.pk, crew)

    def test_review_access_and_photo_validation(self):
        self.login()
        order = self.customer.orders.exclude(status='done').first()
        self.assertEqual(self.client.get(reverse('reviews:create', args=[order.pk])).status_code, 404)
        invalid = SimpleUploadedFile('bad.png', b'not an image', content_type='image/png')
        form = ReviewForm({'rating': '5', 'text': 'Хорошо'}, {'photos': [invalid]})
        self.assertFalse(form.is_valid())
        self.assertIn('photos', form.errors)
        buf = io.BytesIO()
        Image.new('RGB', (16, 16), 'white').save(buf, 'PNG')
        valid = SimpleUploadedFile('clean.png', buf.getvalue(), content_type='image/png')
        form = ReviewForm({'rating': '5', 'text': 'Хорошо'}, {'photos': [valid]})
        self.assertTrue(form.is_valid(), form.errors)

    def test_login_redirects_by_role(self):
        for user, target in [('client1', 'orders:mine'), ('dispatcher', 'crews:dispatch'), ('crew1', 'crews:day'), ('admin', 'crews:dashboard')]:
            self.client.logout()
            response = self.client.post(reverse('accounts:login'), {'username': user, 'password': 'demo-pass-24'})
            self.assertRedirects(response, reverse(target))

    def test_address_duplicate_is_reported_without_server_error(self):
        self.login()
        address = self.customer.addresses.first()
        data = {field: getattr(address, field) or '' for field in ['city', 'street', 'house', 'flat', 'floor', 'comment']}
        before = self.customer.addresses.count()
        response = self.client.post(reverse('orders:addresses'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Этот адрес уже сохранён')
        self.assertEqual(self.customer.addresses.count(), before)

    def test_review_post_saves_photo_and_redirects(self):
        from reviews.models import ReviewPhoto
        order = self.customer.orders.filter(status='done', review__isnull=True).first()
        self.assertIsNotNone(order)
        self.login()
        output = io.BytesIO()
        Image.new('RGB', (16, 16), 'white').save(output, 'PNG')
        photo = SimpleUploadedFile('result.png', output.getvalue(), content_type='image/png')
        response = self.client.post(reverse('reviews:create', args=[order.pk]), {'rating': '5', 'text': 'Уборка выполнена хорошо', 'photos': photo})
        self.assertRedirects(response, reverse('orders:detail', args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.review.rating, 5)
        self.assertEqual(ReviewPhoto.objects.filter(review=order.review).count(), 1)


    def test_login_accepts_email(self):
        user = self.customer.user
        response = self.client.post(reverse('accounts:login'), {'username': user.email.upper(), 'password': 'demo-pass-24'})
        self.assertRedirects(response, reverse('orders:mine'))
