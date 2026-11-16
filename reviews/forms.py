from django import forms
from PIL import Image
from .models import Review


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class PhotoField(forms.FileField):
    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else ([data] if data else [])
        if len(files) > 3:
            raise forms.ValidationError('Можно прикрепить не больше трёх фотографий.')
        result = []
        for item in files:
            item = super().clean(item, initial)
            if item.size > 5*1024*1024:
                raise forms.ValidationError('Каждая фотография должна быть не больше 5 МБ.')
            try:
                image = Image.open(item)
                if image.format not in ['JPEG', 'PNG', 'WEBP']:
                    raise ValueError
                image.verify(); item.seek(0)
            except Exception as exc:
                raise forms.ValidationError('Выберите исправные фотографии JPEG, PNG или WebP.') from exc
            result.append(item)
        return result


class ReviewForm(forms.ModelForm):
    photos = PhotoField(label='Фотографии результата уборки', required=False, widget=MultipleFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}), help_text='До трёх фотографий JPEG, PNG или WebP, не более 5 МБ каждая.')

    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {'rating': forms.Select(choices=[('', 'Выберите оценку'), *[(i, f'{i} из 5') for i in range(1, 6)]]), 'text': forms.Textarea(attrs={'rows': 4, 'maxlength': 2000})}
