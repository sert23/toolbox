from django import forms

from .models import Photo2


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo2
        fields = ('file', )
