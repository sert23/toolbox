import datetime
import json

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, ButtonHolder, Submit, HTML
from crispy_forms.bootstrap import InlineRadios, TabHolder, Tab, Accordion, AccordionGroup
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
from sRNAtoolboxweb.utils import create_collapsable_div, render_modal


class sRNAconsForm(forms.Form):
    KINGDOMS = (
        ("animal", "Animal"),
        ("plant", "Plant")

    )
    ifile = forms.FileField(label='Upload input file(Fasta file)', required=False)
    url = forms.URLField(label='URL/link', required=False)
    mistmatches = forms.IntegerField(label="Number of mistmatches", required=True, initial=1, min_value=0, max_value=2)
    kingdom = forms.ChoiceField(label='Kingdom', choices=KINGDOMS, required=False)

    def __init__(self, *args, **kwargs):
        self.folder = kwargs.pop('dest_folder', None)
        super(sRNAconsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            create_collapsable_div(
                TabHolder(
                    Tab('Upload',
                        HTML("""<br>"""),
                        Field('ifile', css_class='form-control'),
                        ),
                    Tab('URL/link',
                        HTML("""<br>"""),
                        Field('url', css_class='form-control'),
                        )
                ),
                title='Choose your input',
                c_id='100',
                extra_title=render_modal('Choose_Input'),
                open=True
            ),
            create_collapsable_div(
                Field("mistmatches", css_class='form-control'),
                Field("kingdom", css_class="form-control"),
                title='Parameters',
                c_id='101',
                open=True
            ),
            ButtonHolder(
                Submit('submit', 'SUBMIT', css_class='btn btn-primary', onclick='return add_hidden();')
            )

        )

    def clean(self):
        cleaned_data = super(sRNAconsForm, self).clean()
        if not cleaned_data.get('ifile') and not cleaned_data.get('url'):
            self.add_error('ifile', 'One of these two fields is required (file or url)')
            self.add_error('url', 'One of these two fields is required (file or url)')
        if not cleaned_data.get('mistmatches') and cleaned_data.get('mistmatches') != 0:
            self.add_error('mistmatches', 'This field is required and should be equal to 0 or more')
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
        mistmatches = self.cleaned_data.get("mistmatches")
        kingdom = self.cleaned_data.get("kingdom")

        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url = self.cleaned_data.get("url")
            extension = os.path.basename(url).split('.')[-1]
            dest = os.path.join(FS.location, os.path.basename(url))
            try:
                ifile, headers = urllib.request.urlretrieve(url, filename=dest)
            except:
                os.system("wget --no-check-certificate " + url + " -O " + dest)
                ifile = dest
        else:
            raise Http404
        name = pipeline_id + '_srnacons'
        config_location = os.path.join(out_dir, "conf.txt")

        conf_params = dict()
        conf_params["web"] = "true"
        conf_params["input"] = MEDIA_ROOT
        conf_params['pipeline_id'] = pipeline_id
        conf_params['out_dir'] = os.path.join(MEDIA_ROOT, pipeline_id)
        conf_params['output'] = os.path.join(MEDIA_ROOT, pipeline_id)
        conf_params['name'] = pipeline_id + "_sRNAcons"
        conf_params['type'] = "sRNAcons"
        conf_params['conf_input'] = os.path.join(MEDIA_ROOT, pipeline_id, "conf.txt")

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