from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from accounts.access import roles
from orders.models import Order
from .forms import ReviewForm
from .models import Review, ReviewPhoto


@roles('Заказчик')
def create(request, pk):
    order = get_object_or_404(Order, pk=pk, customer__user=request.user, status='done')
    if Review.objects.filter(order=order).exists():
        messages.info(request, 'Отзыв об этом заказе уже сохранён.')
        return redirect('orders:detail', pk=pk)
    form = ReviewForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            review = form.save(commit=False); review.order = order; review.save()
            for image in form.cleaned_data['photos']:
                ReviewPhoto.objects.create(review=review, image=image)
        messages.success(request, 'Отзыв опубликован. Спасибо за оценку.')
        return redirect('orders:detail', pk=pk)
    return render(request, 'reviews/create.html', {'title': f'Отзыв о заказе №{pk}', 'form': form, 'order': order})
