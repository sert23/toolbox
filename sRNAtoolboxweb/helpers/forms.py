import os
import urllib

from django import forms
from django.core.files.storage import FileSystemStorage
from django.http import Http404

from pipelines.pipeline_utils import generate_uniq_id
from progress.models import JobStatus
from sRNAtoolboxweb.settings import MEDIA_ROOT


class RemovedupForm(forms.Form):
    ifile = forms.FileField(label='Upload input file(Fasta file)', required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)
    string = forms.CharField(label='Provide a string of characters to be dropped out from the sequence names',
                             required=True)
    duplicates = forms.BooleanField(label='Remove also duplicate  SEQUENCES', required=False)

    def clean(self):
        cleaned_data = super(RemovedupForm, self).clean()
        if not cleaned_data.get('ifile') and not cleaned_data.get('url'):
            self.add_error('ifile', 'One of these two fields is required')
            self.add_error('url', 'One of these two fields is required')
        if cleaned_data.get('ifile') and cleaned_data.get('url'):
            self.add_error('ifile', 'Choose either file or URL')
            self.add_error('url', 'Choose either file or URL')
        return cleaned_data

    def generate_id(self):
        is_new = True
        while is_new:
            pipeline_id = generate_uniq_id()
            if not JobStatus.objects.filter(pipeline_key=pipeline_id):
                return pipeline_id

    def create_call(self):

        pipeline_id=self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        ifile = self.cleaned_data.get("ifile")
        if ifile:
            file_to_update = ifile
            uploaded_file=str(file_to_update)
            ifile=FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url_input = self.cleaned_data.get("url")
            dest = os.path.join(FS.location, os.path.basename(url_input))
            handler = urllib.URLopener()
            handler.retrieve(url_input, dest)
            ifile = dest

        else:
            raise Http404
        name= pipeline_id+'_h_rd'
        JobStatus.objects.create()

        return 'qsub -v pipeline="helper",mode="rd",key="{pipeline_id}",outdir="{out_dir}",inputfile="{input_file}",string="{string}",remove="true",name="{name}" -N {job_name} {sh}'.format(
            pipeline_id=pipeline_id,
            out_dir=out_dir,
            input_file=os.path.join(FS.location,ifile),
            string=self.cleaned_data.get("string"),
            name=name,
            job_name=name,
            sh='/shared/sRNAtoolbox/core/bash_scripts/run_helper_remove_duplicates.sh'
        )

