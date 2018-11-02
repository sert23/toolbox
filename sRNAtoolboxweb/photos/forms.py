from django import forms

from .models import Photo2
from django.db import models


class PhotoForm_old(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if kwargs.get("request_path"):
            self.request_path = kwargs.pop("request_path", None)
        super(PhotoForm_old, self).__init__(*args, **kwargs)

    class Meta:
        model = Photo2
        fields = ('file', )


class PhotoForm(forms.ModelForm):
    # def __init__(self, *args, **kwargs):
    #     self.request_path = kwargs.pop("request_path", None)
    #     super(PhotoForm, self).__init__(*args, **kwargs)

    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to= '%Y%m%d%H%M')
    uploaded_at = models.DateTimeField(auto_now_add=True)
