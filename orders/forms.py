from datetime import timedelta
from decimal import Decimal

from django import forms
from django.utils import timezone

from accounts.models import Address
from catalog.models import RoomType, Service
from .models import RecurrenceRule
from .services import quote


class QuoteForm(forms.Form):
    room_type = forms.ModelChoiceField(RoomType.objects.all(), label='Тип помещения', empty_label=None)
    service = forms.ModelChoiceField(Service.objects.filter(is_active=True, kind='main'), label='Вид уборки', empty_label=None)
    area = forms.DecimalField(label='Площадь, м²', min_value=10, max_value=1000, max_digits=6, decimal_places=1, initial=54)
    period = forms.ChoiceField(label='Регулярность', choices=[('', 'Разовая уборка'), *RecurrenceRule.Period.choices], required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extras = list(Service.objects.filter(is_active=True, kind='extra'))
        for extra in self.extras:
            self.fields[f'extra_{extra.pk}'] = forms.IntegerField(label=extra.name+' (количество)', min_value=0, max_value=20, initial=0, required=False)

    def clean(self):
        data = super().clean()
        if data.get('service') and data.get('room_type') and not data['service'].room_types.filter(pk=data['room_type'].pk).exists():
            self.add_error('service', 'Эта уборка не подходит для выбранного типа помещения.')
        data['extras'] = self.extras
        return data


class OrderForm(QuoteForm):
    address = forms.ModelChoiceField(Address.objects.none(), label='Адрес уборки', empty_label='Выберите сохранённый адрес')
    start = forms.DateTimeField(label='Дата и время начала', input_formats=['%Y-%m-%dT%H:%M'], widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))
    end_date = forms.DateField(label='Последняя дата серии', required=False, widget=forms.DateInput(attrs={'type': 'date'}), help_text='Заполните для регулярной уборки. Серия не дольше шести месяцев.')
    comment = forms.CharField(label='Комментарий для бригады', required=False, max_length=2000, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, customer, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].queryset = Address.objects.filter(customer=customer)

    def clean(self):
        data = super().clean()
        start = data.get('start')
        if start:
            if start < timezone.now() + timedelta(hours=1):
                self.add_error('start', 'Выберите время минимум через час от текущего.')
            elif not self.errors:
                local = timezone.localtime(start); end = local + timedelta(minutes=quote(data)['duration_min'])
                if local.hour < 8 or end.date() != local.date() or end.hour > 21 or (end.hour == 21 and end.minute):
                    self.add_error('start', 'Уборка должна целиком помещаться в интервал 08:00–21:00. Измените время или параметры.')
        if data.get('period'):
            if not data.get('end_date'):
                self.add_error('end_date', 'Укажите последнюю дату серии.')
            elif start and not 0 <= (data['end_date']-timezone.localtime(start).date()).days <= 183:
                self.add_error('end_date', 'Дата должна быть не раньше первой уборки и не позже чем через шесть месяцев.')
        return data
