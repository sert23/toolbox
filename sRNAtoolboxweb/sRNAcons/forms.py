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


class sRNAconsForm(forms.Form):
    KINGDOMS = (
        ("plant","Plant"),
        ("animal","Animal")
    )
    ifile = forms.FileField(label='Upload input file(Fasta file)', required=True)
    mistmatches = forms.IntegerField(label="Number of mistmatches", required=True, initial=1)
    kingdom=forms.ChoiceField(label= 'Kingdom', choices=KINGDOMS, required=True)


    def __init__(self, *args, **kwargs):
        self.folder = kwargs.pop('dest_folder', None)
        super(sRNAconsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(

            "ifile",
            HTML("""<br>"""),
            "mistmatches",
            HTML("""<br>"""),
            "kingdom",
            HTML("""<br>"""),
            ButtonHolder(
                # Submit('submit', 'SUBMIT', css_class='btn btn-primary')
                # Submit('submit', 'SUBMIT', css_class='btn btn-primary', onclick="return add_hidden(); return alert('he')")
                Submit('submit', 'SUBMIT', css_class='btn btn-primary', onclick='return add_hidden();')
            )

        )

    def clean(self):
        cleaned_data = super(sRNAconsForm, self).clean()

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
        mistmatches = self.cleaned_data.get("mistmatches")
        kingdom = self.cleaned_data.get("kingdom")

        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        else:
            raise Http404
        name = pipeline_id + '_srnacons'
        config_location = os.path.join(out_dir, "conf.txt")

        conf_params = dict()
        conf_params["web"] = "true"
        conf_params["input"] = MEDIA_ROOT
        conf_params['pipeline_id'] = pipeline_id
        conf_params['out_dir'] = os.path.join(MEDIA_ROOT,pipeline_id)
        conf_params['output'] = os.path.join(MEDIA_ROOT,pipeline_id)
        conf_params['name'] = pipeline_id + "_sRNAcons"
        conf_params['type'] = "sRNAcons"
        conf_params['conf_input'] = os.path.join(MEDIA_ROOT,pipeline_id,"conf.txt")

        with open(config_location, "w+") as file:
            file.write("input=" + os.path.join(out_dir, ifile) + "\n")
            file.write("output=" + out_dir + "\n")
            file.write("mm=" + str(mistmatches) + "\n")
            file.write("kingdom=" + kingdom + "\n")
            file.write("dbPath=/opt/sRNAtoolboxDB\n")
            file.write("alignType=v\n")
        import json
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(conf_params, conf_file, indent=True)

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="sRNAcons",
                                 outdir=FS.location,
                                 )
        if QSUB:
            return 'qsub -q fast -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id