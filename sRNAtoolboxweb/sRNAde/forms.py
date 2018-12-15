import datetime
import json

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, ButtonHolder, Submit
from crispy_forms.bootstrap import InlineRadios, TabHolder, Tab, Accordion,AccordionGroup
from django import forms
from django.core.files.storage import FileSystemStorage
from django.http import Http404

from progress.models import JobStatus
from sRNAtoolboxweb.settings import BASE_DIR, QSUB
from sRNAtoolboxweb.settings import MEDIA_ROOT
from sRNAtoolboxweb.utils import render_modal
from utils.pipeline_utils import generate_uniq_id
from utils.sysUtils import *
from django.utils.safestring import mark_safe
import os

def check_mat_file(mat):
    if istext(mat) and istabfile(mat):
        return True
    else:
        return False


class DEForm(forms.Form):
    listofIDs = forms.CharField(
        label='List of sRNAbench IDs (colon separated, separate groups by hashes):' + render_modal('becnhids'),
        required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: id1:id2#id3:id4#id5:id6:id7"}),
        )
    sampleGroups = forms.CharField(label='Sample groups (hash separated):',
                                   required=False,
                                   widget=forms.TextInput(attrs={'placeholder': "e.g: Normal#TumorI#TumorII"}))
    sampleDescription = forms.CharField(label='Sample description (colon separated):' + render_modal('SampleDesc'),
                                     required=False, widget=forms.TextInput(
            attrs={'placeholder': "e.g: Normal_1:Normal_2:TumorI_1:TumorI_2:TumorII_1:TumorII_2:TumorII_3"}))

    ifile = forms.FileField(label='Or upload a matrix of expression values:', required=False)
    matDescription = forms.CharField(label='Sample description (colon separated):' + render_modal('SampleDesc'),
                                     required=False, widget=forms.TextInput(
            attrs={'placeholder': "e.g: Normal,Normal,TumorI,TumorI,TumorII,TumorII,TumorII"}))
    pvalue = forms.CharField(label='Differential expression cutoff used by DESeq and EdgeR (p-value):',
                             required=False, widget=forms.TextInput(attrs={'placeholder': "Default 0.05"}))
    probability = forms.CharField(label='Differential expression cutoff used by NOISeq(probability):',
                                  required=False, widget=forms.TextInput(attrs={'placeholder': "Default 0.8"}))
    isomiRs = forms.BooleanField(label='isoMir Analysis', required=False)

    def __init__(self, *args, **kwargs):
        super(DEForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Using job IDs',
                Field('listofIDs', css_class='form-control'),
                Field('sampleGroups', css_class='form-control'),
                Field('sampleDescription', css_class='form-control')),
            Fieldset("Uploading an expression matrix",
                'ifile',
                Field('matDescription', css_class='form-control')),
                Fieldset('Parameters',
                         Field('pvalue', css_class='form-control'),
                         Field('probability', css_class='form-control'),
                         'isomiRs'
                         ),
            ButtonHolder(
                Submit('submit', 'RUN', css_class='btn btn-primary')
            )
        )

    def clean(self):
        cleaned_data = super(DEForm, self).clean()
        if not cleaned_data.get('ifile') and not cleaned_data.get('listofIDs'):
            self.add_error('ifile', 'One of these two fields is required')
            self.add_error('listofIDs', 'One of these two fields is required')
        if cleaned_data.get('ifile') and cleaned_data.get('listofIDs'):
            self.add_error('ifile', 'Choose either List of IDs or matrix expression file')
            self.add_error('listofIDs', 'Choose either List of IDs or matrix expression file')
        #TODO: check this
        # if cleaned_data.get('ifile') and not cleaned_data.get('matDescription'):
        #     self.add_error('matDescription', 'This field is mandatory if a matrix of Expression Values is provided ')
        if cleaned_data.get('listofIDs') and not cleaned_data.get('sampleGroups'):
            self.add_error('matDescription', 'This field is mandatory if a list of sRNAbench IDs is provided')
        probability = cleaned_data.get('probability') or "0.8"
        pvalue = cleaned_data.get('pvalue') or "0.05"
        if (1.0 < float(pvalue)) or (0.0 > float(pvalue)):
            self.add_error('pvalue', 'Must be a number between 1 and 0, you entered: ' + pvalue)
        if (1.0 < float(probability)) or (0.0 > float(probability)):
            self.add_error('probability', 'Must be a number between 1 and 0,  you entered: ' + probability)

        if cleaned_data.get('listofIDs'):
            samples = len(cleaned_data.get('listofIDs').split("#"))
            groups = len(cleaned_data.get('sampleGroups').split("#"))
            if not (groups == samples):
                self.add_error('listofIDs', 'Number of groups must be the same, separate with #')
                self.add_error('sampleGroups', 'Number of groups must be the same, separate with #')
            if cleaned_data.get('matDescription'):
                desc = len(cleaned_data.get('matDescription').split("#"))
                if not (groups == samples == desc):
                    self.add_error('listofIDs', 'Number of groups must be the same, separate with #')
                    self.add_error('sampleGroups', 'Number of groups must be the same, separate with #')
                    self.add_error('matDescription', 'Number of groups must be the same, separate with #')
        return cleaned_data

    def generate_id(self):
        is_new = True
        while is_new:
            pipeline_id = generate_uniq_id()
            if not JobStatus.objects.filter(pipeline_key=pipeline_id):
                return pipeline_id

    @staticmethod
    def create_conf_file(cleaned_data, pipeline_id):
        conf = {}
        if cleaned_data.get("isomiRs"):
            conf['isom'] = "true"
        else:
            conf['isom'] = "false"
        conf['pipeline_id'] = pipeline_id
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        conf['out_dir'] = out_dir
        ifile = cleaned_data.get("ifile")
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = os.path.join(out_dir, FS.save(uploaded_file, file_to_update))
            if not check_mat_file(ifile):
                # TODO: Antonio control this error
                raise Http404
            conf['input'] = ifile

        elif cleaned_data.get("listofIDs"):
            conf['input'] = cleaned_data.get("listofIDs")
            ifile = " "
        else:
            return Http404

        name = pipeline_id + '_de'
        conf['name'] = name
        conf['probab'] = cleaned_data.get("probability") or "0.8"
        conf['pval'] = cleaned_data.get("pvalue") or "0.05"
        conf['top'] = "20"
        conf['perc'] = "1"
        conf['groups'] = cleaned_data.get("sampleGroups")
        conf['matdesc'] = cleaned_data.get("matDescription")
        conf['type'] = 'sRNAde'
        conf['sampleDescription']= cleaned_data.get("sampleDescription")

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="sRNAde",
                                 )
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(conf, conf_file, indent=True)
        return name, configuration_file_path

    def create_call(self):
        pipeline_id = self.generate_id()
        name, configuration_file_path = self.create_conf_file(self.cleaned_data, pipeline_id)
        if QSUB:
            return 'qsub -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id
        else:
            return '{sh} {configuration_file_path}'.format(
                configuration_file_path=configuration_file_path,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run.sh')), pipeline_id

class DEinputForm(forms.Form):

    #Input
    jobIDs = forms.CharField(
        label='Use a list of sRNAbench IDs (comma separated):' + render_modal('idlist'),
        required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: id1,id2,id3..."}))
    ifile = forms.FileField(label='Upload an expression matrix (tab delimited or comma separated):', required=False)
    listofIDs = forms.CharField(
        label='List of sRNAbench IDs (colon separated, separate groups by hashes):' + render_modal('becnhids'),
        required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: id1:id2#id3:id4#id5:id6:id7"}),
    )
    sampleDescription = forms.CharField(label='Sample description (optional)' + render_modal('SampleDesc'),
                                        required=False, widget=forms.TextInput(
            attrs={'placeholder': "e.g: Normal_1:Normal_2:TumorI_1:TumorI_2:TumorII_1:TumorII_2:TumorII_3"}))
    matDescription = forms.CharField(label=mark_safe('Sample description <strong class="text-danger">(required)</strong>:') + render_modal('SampleDesc'),
                                     required=False, widget=forms.TextInput(
            attrs={'placeholder': "e.g: Normal,Normal,TumorI,TumorI,TumorII,TumorII,TumorII"}))
    #Groups
    sampleGroups = forms.CharField(label='Sample groups (hash separated):',
                                   required=False,
                                   widget=forms.TextInput(attrs={'placeholder': "e.g: Normal#TumorI#TumorII"}))

    def __init__(self, *args, **kwargs):
        super(DEinputForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(

            TabHolder(
                Tab("Use Job IDs (recommended)",
                    Field("jobIDs", css_class="form-control"),
                    Field('sampleDescription', css_class='form-control')
                    ),
                Tab("Upload Expression Matrix",
                    "ifile",
                    Field("matDescription", css_class="form-control") ),
                Tab("Use Group String",
                    Field("listofIDs", css_class="form-control"),
                    Field('sampleDescription', css_class='form-control')
                    ),

            ),
            Field("sampleGroups", css_class="form-control"),
            ButtonHolder(
                Submit('submit', 'SUBMIT', css_class='btn btn-primary')
            )

        )

    def clean(self):
        cleaned_data = super(DEinputForm, self).clean()
        if not cleaned_data.get('ifile') and not cleaned_data.get('listofIDs') and not cleaned_data.get("jobIDs"):
            self.add_error('ifile', 'One input field is required')
            self.add_error('listofIDs', 'One input field is required')
            self.add_error('jobIDs', 'One input field is required')
        if sum([bool(cleaned_data.get('ifile')), bool(cleaned_data.get('listofIDs')),bool(cleaned_data.get("jobIDs"))]):
            self.add_error('ifile', 'Choose either List of IDs or matrix expression file')
            self.add_error('listofIDs', 'Choose either List of IDs or matrix expression file')
            self.add_error('listofIDs', 'Choose either List of IDs or matrix expression file')



        return cleaned_data

    def generate_id(self):
        is_new = True
        while is_new:
            pipeline_id = generate_uniq_id()
            if not JobStatus.objects.filter(pipeline_key=pipeline_id):
                return pipeline_id

    def create_config_file(self):
        pipeline_id = self.generate_id()
        cleaned_data = self.cleaned_data
        os.mkdir(os.path.join(MEDIA_ROOT,pipeline_id))
        name = pipeline_id + '_de'
        ifile = self.cleaned_data.get("ifile")
        if not ifile:
            ifile = " "

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="sRNAde",
                                 )

        return pipeline_id
