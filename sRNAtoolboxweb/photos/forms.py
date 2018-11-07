from django import forms

from .models import Photo2
from django.db import models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, ButtonHolder, Submit
import os
class PhotoForm(forms.ModelForm):
    # def __init__(self, *args, **kwargs):
    #     if kwargs.get("request_path"):
    #         self.request_path = kwargs.pop("request_path", None)
    #     super(PhotoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Photo2
        fields = ('file', )


class MultiURLForm(forms.Form):
    SRRtext = forms.CharField(label="Paste SRA IDs (starting with SRR or ERR, one per line) ", widget=forms.Textarea, required=False)
    URLtext = forms.CharField(label="Paste URL/links with the files (one per line) ", widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(MultiURLForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
                'Choose miRNA input',
                Field('SRRtext', css_class='form-control'),
                Field('URLtext', css_class='form-control'),
                ButtonHolder(
                Submit('submit', 'PROCEED', css_class='btn btn-primary')
            )
        )

    def clean(self,dest_folder):

        cleaned_data = super(MultiURLForm, self).clean()

        with open(os.path.join(dest_folder,"SRR_files.txt"),"w") as SRR_file:
            SRR_file.write(cleaned_data.get('SRRtext'))

        with open(os.path.join(dest_folder,"URL_files.txt"),"w") as URL_file:
            URL_file.write(cleaned_data.get('URLtext'))



# class PhotoForm(forms.ModelForm):
#     # def __init__(self, *args, **kwargs):
#     #     self.request_path = kwargs.pop("request_path", None)
#     #     super(PhotoForm, self).__init__(*args, **kwargs)
#
#     #title = models.CharField(max_length=255, blank=True)
#     file = models.FileField(upload_to= '%Y%m%d%H%M')
#     #uploaded_at = models.DateTimeField(auto_now_add=True)
