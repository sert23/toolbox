import json
from datetime import datetime
import os
import urllib.request

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Field
from django import forms
from django.core.files.storage import FileSystemStorage
from django.utils.safestring import mark_safe

from DataModels.sRNABenchConfig import SRNABenchConfig
from FileModels.speciesAnnotationParser import SpeciesAnnotationParser
from progress.models import JobStatus
from sRNABench.models import Species
from sRNAtoolboxweb.settings import MEDIA_ROOT, CONF, QSUB, BASE_DIR
from sRNAtoolboxweb.utils import create_collapsable_div, render_modal
from utils.pipeline_utils import generate_uniq_id


class CategoriesField(forms.ModelMultipleChoiceField):
    def __init__(self, queryset, **kwargs):
        try:
            queryset = queryset()
            super(CategoriesField, self).__init__(queryset, **kwargs)
            self.queryset = queryset.select_related()
            self.to_field_name=None

            group = None
            list = []
            self.choices = []

            for category in queryset:
                if not group:
                    group = category.sp_class

                if group != category.sp_class:
                    self.choices.append((group, list))
                    group = category.sp_class
                    list = [(category.id, str(category))]
                else:
                    #list.append((category.id, str(category)))
                    list.append((str(category.id)+":"+category.scientific, str(category)))
                    #list.append((str(category.id)+""+category.scientific, str(category)))
            try:
                self.choices.append((group, list))
            except:
                pass

        except:
            pass

    def clean(self, value):
        if value:
            if isinstance(value[0], list):
                value = value[0]
        value = [v for v in value if v != '']
        return super(CategoriesField, self).clean(value)

def m():
    return Species.objects.all().order_by('sp_class')

class sRNAblastForm(forms.Form):
    ADAPTERS = (
        ("EMPTY", "Input reads are already trimmed"),
        (None, "Select Adapter to trim off"),
        ("TGGAATTCTCGGGTGCCAAGG", "Illumina RA3 - TGGAATTCTCGGGTGCCAAGG"),
        ("UCGUAUGCCGUCUUCUGCUUGU", "Illumina(alternative) - UCGUAUGCCGUCUUCUGCUUGU", ),
        ("330201030313112312", "SOLiD(SREK) - 330201030313112312"),
    )
    NUMBERS = (
        ("1","1"),
        ("5","5"),
        ("10","10"),
        ("50","50"),
        ("100","100"),
        ("500","500"),
        ("1000","1000"),
        ("2000","2000"),
    )

    DATABASES = (
        ("nr","nr"),
        ("refseq_rna","refseq_rna"),
        ("est","est"),
        ("env_nt","env_nt")
    )

    ALIGMENT_TYPES = (
        ('n', 'bowtie seed alignment(only mismatches in seed region count)'),
        ('v', 'full read alignment(all mismatches count)'),
    )

    ifile = forms.FileField(label='Upload the reads (fastq.gz, fa.gz or rc.gz)' + render_modal('SRNAinput'),
                            required=False)
    url = forms.URLField(label=mark_safe('<strong >Or provide a URL for big files <strong class="text-success"> (recommended!)</strong>'), required=False)
    job_ID = forms.CharField(label='Or provide a sRNAbench jobID: (unmapped reads from the job will be used)',
                             required=False)
    maxReads=forms.ChoiceField(label='Number of unique unmapped reads to blast',choices= NUMBERS, required=False )
    dataBase=forms.ChoiceField(label= 'Database', choices=DATABASES, required=False)
    maxEval=forms.DecimalField(label= 'Evalue Maximum threshold', required= False)

    adapter_chosen = forms.ChoiceField(choices=ADAPTERS, required=False, initial=("EMPTY", "Input reads are already trimmed"))
    adapter_manual = forms.CharField(label='Or Provide adapter sequence', required=False)
    adapter_length = forms.IntegerField(label='Minimum Adapter Length', max_value=12, min_value=6, initial=10, required=False)
    adapter_mismatch = forms.IntegerField(label='Max. mismatches in adapter detection', max_value=2, min_value=0, initial=1, required=False)



    def __init__(self, *args, **kwargs):
        super(sRNAblastForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                '',
                'ifile',
                Field('url',css_class='form-control'),
                Field('job_ID', css_class='form-control'),
                Field('maxReads', css_class='form-control'),
                Field('dataBase', css_class='form-control'),
                Field('maxEval', css_class='form-control'),

            ),
            create_collapsable_div(
                Fieldset(
                'Adapter Selection',
                Field('adapter_chosen', css_class='form-control'),
                Field('adapter_manual', css_class='form-control')
                ),Fieldset(
                    'Trimming Options',
                Field('adapter_length', css_class='form-control'),
                Field('adapter_mismatch', css_class='form-control'),
                ),
                title='Adapter Trimming', c_id='3',
                open=True
            ),
            ButtonHolder(
                #Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                Submit('submit', 'RUN', css_class='btn btn-primary')
                       #onsubmit="alert('Neat!'); return false")

            )
        )

    def clean(self):

        cleaned_data = super(sRNAblastForm, self).clean()

        if sum([0,bool(cleaned_data.get('ifile')),bool(cleaned_data.get('url')),bool(cleaned_data.get('job_ID'))]) != 1:
            self.add_error('ifile', 'Choose either file or URL as input')
            self.add_error('url', 'Choose either file or URL as input')
            self.add_error('job_ID', 'Choose either file or URL as input')
            #print(cleaned_data.get('ifile'))
        if sum([bool(cleaned_data.get('guess_adapter')), bool(cleaned_data.get('adapter_chosen')==''), bool(cleaned_data.get('adapter_manual')=='')]) != 1:
            self.add_error('adapter_chosen', 'Choose either an adapter from the list or enter it manually ')
            self.add_error('adapter_manual','Choose either an adapter from the list or enter it manually ')
        return cleaned_data

    @staticmethod
    def upload_files(cleaned_data, FS):
        libs_files = []
        name_modifier = ""
        url = cleaned_data.get('url')
        ifile = cleaned_data.get("ifile") or ''
        if ifile:
            file_to_update = ifile
            extension = file_to_update.name.split('.')[-1]
            if name_modifier is not None and name_modifier != '':
                uploaded_file = str(name_modifier) + "." + extension
            else:
                uploaded_file = str(file_to_update).replace(" ", "")

            FS.save(uploaded_file, file_to_update)
            ifile = os.path.join(FS.location, uploaded_file)

        elif url:

            # extension = os.path.basename(url).split('.')[-1]
            # if name_modifier is not None:
            #     dest = os.path.join(FS.location, str(name_modifier) + "." + extension).replace(" ", "")
            # else:
            #     dest = os.path.join(FS.location, os.path.basename(url))
            #
            # ifile, headers = urllib.request.urlretrieve(url, filename=dest)
            ifile = url

        for i in range(1, 6):
            profile = cleaned_data.get('profile' + str(i))
            if profile:
                uploaded_file = str(profile).replace(' ', '')
                FS.save(uploaded_file, profile)
                libs_files.append(os.path.join(FS.location, uploaded_file))

        user_urls = cleaned_data.get('profile_url1')
        if user_urls:
            for line in user_urls.split('\n'):
                url_line = str(line).replace(' ', '')
                dest = os.path.join(FS.location, os.path.basename(url_line))
                url_lib, headers = urllib.request.urlretrieve(url, filename=dest)
                libs_files.append(url_lib)

        return ifile, libs_files

    def create_conf_file(self, cleaned_data, pipeline_id):
        conf = {}
        conf['pipeline_id'] = pipeline_id
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        conf['out_dir'] = out_dir
        ifile, libs_files = self.upload_files(cleaned_data, FS)
        if not ifile and cleaned_data.get("job_ID"):
            new_record = JobStatus.objects.get(pipeline_key=cleaned_data.get("job_ID"))
            path = new_record.outdir
            ifile=os.path.join(path,"reads.fa")


        #recursive_adapter_trimming = str(cleaned_data.get('recursive_adapter_trimming')).lower()
        adapter = cleaned_data['adapter_chosen'] or cleaned_data['adapter_manual']
        adapter_length = str(cleaned_data['adapter_length'])
        adapter_mismatch = str(cleaned_data['adapter_mismatch'])
        conf_dict={}
        conf_dict["input"] = ifile
        conf_dict["output"] = out_dir
        conf_dict["maxReads"] = cleaned_data.get("maxReads")
        conf_dict["blastDB"]= cleaned_data.get("dataBase")
        #conf_dict["minIdent"]= cleaned_data.get("minIdent")
        conf_dict["maxEvalue"]= cleaned_data.get("maxEval")
        conf_dict["adapter"] = adapter
        if conf_dict["adapter"] =="EMPTY":
            conf_dict["adapter"] = None
        conf_dict["adapterMinLength"] = adapter_length
        conf_dict["adapterMM"] = adapter_mismatch
        conf_file_location = os.path.join(FS.location, "conf.txt")
        with open(conf_file_location, "a") as cfile:
            for k in conf_dict.keys():
                if conf_dict.get(k):
                    line= str(k)+"="+conf_dict.get(k)+"\n"
                    cfile.write(line)

        name = pipeline_id + '_blast'
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': conf_file_location,
            'type': 'sRNAblast'
        }

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.now(),
                                 all_files=ifile,
                                 modules_files="",
                                 outdir=out_dir,
                                 #parameters="".join(open(conf_file_location).readlines()),
                                 pipeline_type="sRNAblast",
                                 zip_file=pipeline_id+"/"+"sRNAblast_full_Result.zip",
                                 )
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)
        return name, configuration_file_path

    def generate_id(self):
        is_new = True
        while is_new:
            pipeline_id = generate_uniq_id()
            if not JobStatus.objects.filter(pipeline_key=pipeline_id):
                return pipeline_id

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