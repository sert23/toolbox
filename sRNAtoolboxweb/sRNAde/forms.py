import datetime
import os
import urllib

from django import forms
from django.core.files.storage import FileSystemStorage
from django.http import Http404

from progress.models import JobStatus
from sRNAtoolboxweb.settings import BASE_DIR
from sRNAtoolboxweb.settings import MEDIA_ROOT
from utils.pipeline_utils import generate_uniq_id


class DEForm(forms.Form):
    lisfofIDs = forms.CharField(label='List of sRNAbench IDs (colon separated, separate groups by hashes):',
                             required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: id1:id2#id3:id4#id5:id6:id7"}),
                                help_text="sRNAde can use completed jobs of sRNAbench if jobsID of these jobs are provided.\n"+
                                          "In order to assign the groups of analysis, ids of different groups must be separated using hashes and samples inside the same group using colons. Additionally the groups name must be provided in the same order separated by hashes using the Sample groups form. For example:\n"+
                                            "Given the samples: ID1(cancer), ID2(cancer) and ID3(normal)\n:"+
                                            "The user should fill \"List of sRNAbench IDs\" with: ID1:ID2#ID3 abd \"Sample groups\" with: cancer#normal")
    ifile = forms.FileField(label='Or upload a matrix of expression values:', required=False)
    sampleGroups = forms.CharField(label='Sample groups (hash separated):',
                             required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: Normal#TumorI#TumorII"}))
    sampleDescription = forms.CharField(label='Sample description (colon separated):',
                             required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: Normal:Normal:TumorI:TumorI:TumorII:TumorII:TumorII"}))
    pvalue= forms.CharField(label='Differential expression cutoff used by DESeq and EdgeR (p-value):', default= "0.05",
                             required=False, widget=forms.TextInput(attrs={'placeholder': "Default 0.05"}))
    probability = forms.CharField(label='Differential expression cutoff used by NOISeq(probability):', default= "0.8",
                             required=False, widget=forms.TextInput(attrs={'placeholder': "Default 0.05"}))
    isomiRs = forms.BooleanField(label='isoMir Analysis', required=False )

    def clean(self):
        cleaned_data = super(DEForm, self).clean()
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

        pipeline_id = self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        ifile = self.cleaned_data.get("ifile")
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url_input = self.cleaned_data.get("url")
            dest = os.path.join(FS.location, os.path.basename(url_input))
            handler = urllib.URLopener()
            handler.retrieve(url_input, dest)
            ifile = dest

        else:
            raise Http404

        name = pipeline_id + '_h_extract'
        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 #finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                )

        return 'qsub -v pipeline="helper",mode="extract",key="{pipeline_id}",outdir="{out_dir}",inputfile="{input_file}",string="{string}",name="{name}" -N {job_name} {sh}'.format(
                pipeline_id=pipeline_id,
                out_dir=out_dir,
                input_file=os.path.join(FS.location, ifile),
                string=self.cleaned_data.get("string"),
                name=name,
                job_name=name,
                sh=os.path.join(BASE_DIR + '/core/bash_scripts/run_helper_extract.sh')
            )