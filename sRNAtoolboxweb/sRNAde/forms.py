import datetime
import json

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, ButtonHolder, Submit, HTML
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

import json

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
        label='Use a list of sRNAbench IDs (comma separated):' + render_modal('listids'),
        required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: id1,id2,id3..."}))
    ifile = forms.FileField(label='Upload an expression matrix (tab delimited or comma separated):', required=False)
    listofIDs = forms.CharField(
        label='List of sRNAbench IDs (colon separated, separate groups by hashes):' + render_modal('becnhids'),
        required=False, widget=forms.TextInput(attrs={'placeholder': "e.g: id1:id2#id3:id4#id5:id6:id7"}),
    )
    sampleDescription = forms.CharField(label='Sample description (provided names will replace jobIDs in analysis, optional)' + render_modal('SampleDesc'),
                                        required=False, widget=forms.TextInput(
            attrs={'placeholder': "e.g: Normal_1:Normal_2:TumorI_1:TumorI_2:TumorII_1:TumorII_2:TumorII_3"}))
    sampleDescription2 = forms.CharField(
        label='Sample description (provided names will replace jobIDs in analysis, optional)' + render_modal(
            'SampleDesc'),
        required=False, widget=forms.TextInput(
            attrs={'placeholder': "e.g: Normal_1:Normal_2:TumorI_1:TumorI_2:TumorII_1:TumorII_2:TumorII_3"}))
    matDescription = forms.CharField(label=mark_safe('Sample description <strong class="text-danger">(required)</strong>:') + render_modal('SampleDesc'),
                                     required=False, widget=forms.TextInput(
            attrs={'placeholder': "e.g: Normal,Normal,TumorI,TumorI,TumorII,TumorII,TumorII"}))
    #Groups

    sampleGroups = forms.CharField(label=mark_safe('Sample groups (hash separated, <strong class="text-danger">required</strong>):'),
                                   required=False,
                                   widget=forms.TextInput(attrs={'placeholder': "e.g: Normal#TumorI#TumorII"}))
    sampleGroupsMat = forms.CharField(
        label=mark_safe('Sample groups (hash separated):'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': "e.g: Normal#TumorI#TumorII"}))
    sampleGroupsNot = forms.CharField(
        label=mark_safe('Sample groups (hash separated):'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': "e.g: Normal#TumorI#TumorII"}))


    def __init__(self, *args, **kwargs):
        super(DEinputForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(

            TabHolder(
                Tab("Use Job IDs",
                    Field("jobIDs", css_class="form-control"),
                    Field('sampleDescription', css_class='form-control'),
                    Field("sampleGroups", css_class="form-control")
                    ),
                # Tab("Upload Expression Matrix",
                #     "ifile",
                #     Field("matDescription", css_class="form-control"),
                #     Field("sampleGroupsMat", css_class="form-control")
                #     ),
                Tab("Use Group String (advanced)",
                    Field("listofIDs", css_class="form-control"),
                    Field('sampleDescription2', css_class='form-control'),
                    Field("sampleGroupsNot", css_class="form-control")
                    ),
            ),
            # Field("sampleGroups", css_class="form-control"),
            ButtonHolder(
                Submit('submit', 'SUBMIT', css_class='btn btn-primary')
            )

        )

    def clean(self):

        #TODO check input format

        cleaned_data = super(DEinputForm, self).clean()
        if not cleaned_data.get('ifile') and not cleaned_data.get('listofIDs') and not cleaned_data.get("jobIDs"):
            self.add_error('ifile', 'One input field is required')
            self.add_error('listofIDs', 'One input field is required')
            self.add_error('jobIDs', 'One input field is required')
        if sum([bool(cleaned_data.get('ifile')), bool(cleaned_data.get('listofIDs')),bool(cleaned_data.get("jobIDs"))]) >1:
            self.add_error('ifile', 'Choose one input method')
            self.add_error('listofIDs', 'Choose one input method')
            self.add_error('jobIDs', 'Choose one input method')

        if cleaned_data.get('ifile'):
            if cleaned_data.get("matDescription"):
                cleaned_data["skip"] = True
            elif not cleaned_data.get("sampleGroupsMat"):
                self.add_error("matDescription", 'At least Sample D')
                self.add_error("sampleGroupsNot", 'At least Sample D')
        elif cleaned_data.get('jobIDs'):
            if cleaned_data.get("sampleGroups"):
                cleaned_data["skip"] = False
            else:
                self.add_error("sampleGroups", 'Groups must be provided')
        elif cleaned_data.get("listofIDs"):
            cleaned_data["skip"] = True

        if cleaned_data.get("sampleGroupsNot") and not cleaned_data.get("sampleGroups"):
            cleaned_data["sampleGroups"] = cleaned_data.get("sampleGroupsNot")

        # if cleaned_data.get("ifile") and not cleaned_data.get("matDescription"):
        #     self.add_error('ifile', 'Sample description is required when you upload a matrix')
        #     self.add_error('listofIDs', 'Sample description is required when you upload a matrix')
        #     self.add_error('jobIDs', 'Sample description is required when you upload a matrix')

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
        out_dir = os.path.join(MEDIA_ROOT,pipeline_id)
        json_path = os.path.join(MEDIA_ROOT,pipeline_id,"init_par.json")
        ifile = self.cleaned_data.get("ifile")
        if not ifile:
            ifile = " "
        elif ifile:
            FS = FileSystemStorage()
            FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = os.path.join(out_dir, FS.save(uploaded_file, file_to_update))

        parameters = {}
        for k in cleaned_data.keys():
            if cleaned_data.get(k):
                parameters[k] = cleaned_data[k]
        parameters["ifile"] = ifile

        with open(json_path, 'w') as jf:
            json.dump(parameters, jf)


        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="sRNAde",
                                 )

        return pipeline_id

class DElaunchForm(forms.Form):
    fdr = forms.CharField(label='Differential expression cutoff used by DESeq and EdgeR (p-value):',
                             required=False, widget=forms.TextInput(attrs={'placeholder': "Default 0.05"}))
    noiseq = forms.CharField(label='Differential expression cutoff used by NOISeq (probability):',
                                  required=False, widget=forms.TextInput(attrs={'placeholder': "Default 0.8"}))
    isomiRs = forms.BooleanField(label='isoMir Analysis', required=False)

    minRCexpr = forms.IntegerField(label="Minimum Read Count", required=False, initial=1)

    samples_hidden = forms.CharField(label='', required=False, widget=forms.HiddenInput, max_length=2500)
    groups_hidden = forms.CharField(label='', required=False, widget=forms.HiddenInput, max_length=2500)


    def __init__(self, *args, **kwargs):
        self.folder = kwargs.pop('dest_folder', None)
        super(DElaunchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(

            "samples_hidden",
            "groups_hidden",
            "fdr",
            HTML("""<br>"""),
            "noiseq",
            HTML("""<br>"""),
            "minRCexpr",
            HTML("""<br>"""),
            ButtonHolder(
                # Submit('submit', 'SUBMIT', css_class='btn btn-primary')
                # Submit('submit', 'SUBMIT', css_class='btn btn-primary', onclick="return add_hidden(); return alert('he')")
                Submit('submit', 'SUBMIT', css_class='btn btn-primary', onclick='return add_hidden();')
            )

        )

    def clean(self):
        cleaned_data = super(DElaunchForm, self).clean()

        return cleaned_data



    def create_call(self):
        pipeline = self.folder
        initial_path = os.path.join(MEDIA_ROOT,pipeline,"init_par.json")
        with open(initial_path,"r") as param_file:
            initial_params = json.load(param_file)
        cleaned_data = self.cleaned_data

        conf_params = dict()
        conf_params["web"] = "true"
        conf_params["input"] = MEDIA_ROOT
        conf_params['pipeline_id'] = pipeline
        conf_params['out_dir'] = os.path.join(MEDIA_ROOT,pipeline)
        conf_params['output'] = os.path.join(MEDIA_ROOT,pipeline)
        conf_params['name'] = pipeline + "_de"
        conf_params['type'] = "sRNAde"
        conf_params['conf_input'] = os.path.join(MEDIA_ROOT,pipeline,"conf.txt")

        for p in cleaned_data:
            if cleaned_data.get(p):
                conf_params[p] = cleaned_data.get(p)
        if initial_params.get("listofIDs"):
            conf_params["grpString"] = initial_params.get("listofIDs")
            if initial_params.get("sampleGroups"):
                conf_params["grpDesc"] = initial_params.get("sampleGroups")
            if initial_params.get("sampleDescription2"):
                conf_params["sampleDesc"] = initial_params.get("sampleDescription2")
            conf_params["input"] = MEDIA_ROOT
        elif initial_params.get("ifile") != " ":
            conf_params["input"] = initial_params.get("ifile")
            if initial_params.get("matDescription"):
                conf_params["matrixDesc"] = initial_params.get("matDescription")
            else:
                conf_params["matrixDesc"] = cleaned_data.get("groups_hidden")
            if conf_params.get("sampleGroupsMat"):
                conf_params["grpDesc"] = initial_params.get("sampleGroupsMat")
        elif initial_params.get("jobIDs"):
            conf_params["grpString"] = initial_params.get("jobIDs")
            if initial_params.get("sampleDescription"):
                conf_params["sampleDesc"] = initial_params.get("sampleDescription")
            conf_params["grpDesc"] = initial_params.get("sampleGroups")
            conf_params["matrixDesc"] = cleaned_data.get("groups_hidden")

        configuration_file_path = os.path.join(conf_params["out_dir"], 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(conf_params, conf_file, indent=True)
        with open(conf_params['conf_input'],"w") as conf_txt:
            for k in sorted(conf_params.keys()):
                conf_txt.write(k + "=" + str(conf_params.get(k))+"\n")

        if QSUB:
            call= 'qsub -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name= conf_params["name"],
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh'))
        else:
            call = '{sh} {configuration_file_path}'.format(
                configuration_file_path=configuration_file_path,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run.sh'))

        return pipeline,call


class DEmultiForm(forms.Form):
    sampleGroups = forms.CharField(
        label=mark_safe('Sample groups (hash separated, <strong class="text-danger">required</strong>):'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': "e.g: Normal#TumorI#TumorII"}))

    def __init__(self, *args, **kwargs):
        self.folder = kwargs.pop('orig_folder', None)
        super(DEmultiForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("sampleGroups", css_class="form-control"),
            ButtonHolder(
                Submit('submit', 'SUBMIT', css_class='btn btn-primary')
            )
        )
    def clean(self):

        #TODO check input format

        cleaned_data = super(DEmultiForm, self).clean()
        if not cleaned_data.get("sampleGroups"):
            self.add_error("sampleGroups", 'You need to provide Sample Groups')
        else:
            sampleGroups = cleaned_data.get("sampleGroups").replace("#",",")
            if len(sampleGroups.split(",")) <2:
                self.add_error("sampleGroups", 'You need to provide at least 2 groups')

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
        out_dir = os.path.join(MEDIA_ROOT,pipeline_id)
        json_path = os.path.join(MEDIA_ROOT,pipeline_id,"init_par.json")

        #Get jobIDs
        jobs_folder = os.path.join(MEDIA_ROOT,self.folder , "launched")
        launched_ids = [f for f in os.listdir(jobs_folder) if os.path.isfile(os.path.join(jobs_folder, f))]

        parameters = {}
        parameters["jobIDs"] = ",".join(launched_ids)

        for k in cleaned_data.keys():
            if cleaned_data.get(k):
                parameters[k] = cleaned_data[k]
        # parameters["input"] = MEDIA_ROOT
        parameters["ifile"] = " "
        with open(json_path, 'w') as jf:
            json.dump(parameters, jf, sort_keys=True)

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files=" ",
                                 modules_files="",
                                 pipeline_type="sRNAde",
                                 )

        return pipeline_id
