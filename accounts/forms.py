from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Address, Customer, phone_validator


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label='Имя', max_length=150, widget=forms.TextInput(attrs={'autocomplete': 'given-name'}))
    last_name = forms.CharField(label='Фамилия', max_length=150, widget=forms.TextInput(attrs={'autocomplete': 'family-name'}))
    email = forms.EmailField(label='Электронная почта', widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    phone = forms.CharField(label='Телефон', validators=[phone_validator], max_length=12, help_text='Формат: +7XXXXXXXXXX', widget=forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel', 'pattern': r'\+7[0-9]{10}'}))
    consent = forms.BooleanField(label='Согласен на обработку персональных данных')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2', 'consent']

    def clean_email(self):
        value = self.cleaned_data['email']
        if User.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError('Эта почта уже зарегистрирована. Войдите в существующий аккаунт.')
        return value

    def clean_phone(self):
        value = self.cleaned_data['phone']
        if Customer.objects.filter(phone=value).exists():
            raise forms.ValidationError('Этот телефон уже зарегистрирован.')
        return value


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['city', 'street', 'house', 'flat', 'floor', 'comment']
        widgets = {'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}), 'street': forms.TextInput(attrs={'autocomplete': 'street-address'})}
