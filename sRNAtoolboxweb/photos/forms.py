import json
from datetime import datetime
import urllib.request
from django.db import models
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Field, Div, Row
from crispy_forms.bootstrap import InlineRadios, TabHolder, Tab, Accordion, AccordionGroup
from django import forms
from django.core.files.storage import FileSystemStorage
from django.utils.safestring import mark_safe
from DataModels.sRNABenchConfig import SRNABenchConfig
from FileModels.speciesAnnotationParser import SpeciesAnnotationParser

from .models import Photo2

from crispy_forms.helper import FormHelper

import os
from progress.models import JobStatus
from sRNABench.models import Species
from sRNAtoolboxweb.settings import MEDIA_ROOT, CONF, QSUB, BASE_DIR
from sRNAtoolboxweb.utils import create_collapsable_div, render_modal
from utils.pipeline_utils import generate_uniq_id
import shutil



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
        self.folder = kwargs.pop('dest_folder', None)
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

    def clean(self):

        cleaned_data = super(MultiURLForm, self).clean()
        dest_folder = self.folder

        with open(os.path.join(dest_folder,"SRR_files.txt"),"w") as SRR_file:
            SRR_file.write(cleaned_data.get('SRRtext'))

        with open(os.path.join(dest_folder,"URL_files.txt"),"w") as URL_file:
            URL_file.write(cleaned_data.get('URLtext'))

class sRNABenchForm(forms.Form):
    ADAPTERS = (
        (None, "Select Adapter to trim off"),
        ("EMPTY", "Input reads are already trimmed"),
        ("TGGAATTCTCGGGTGCCAAGG", "Illumina RA3 - TGGAATTCTCGGGTGCCAAGG"),
        ("UCGUAUGCCGUCUUCUGCUUGU", "Illumina(alternative) - UCGUAUGCCGUCUUCUGCUUGU",),
        ("330201030313112312", "SOLiD(SREK) - 330201030313112312"),
    )

    ALIGMENT_TYPES = (
        ('n', 'bowtie seed alignment(only mismatches in seed region count)'),
        ('v', 'full read alignment(all mismatches count)'),
    )

    # mirdb_list = [(None, "Do not use MirGeneDB")]
    mirdb_list = []
    fh = open(CONF["mirDbPath"])
    for line in fh:
        mirdb_list.append((line.rstrip(), line.rstrip()))

    ifile = forms.FileField(label='Upload the reads (fastq.gz, fa.gz or rc.gz)' + render_modal('SRNAinput'),
                            required=False)
    sra_input = forms.CharField(label='Or provide a SRA ID (starting with SRR or ERR)', required=False)
    url = forms.URLField(
        label=mark_safe('Or provide a URL for big files <strong class="text-success"> (recommended!)</strong>'),
        required=False)
    job_name = forms.CharField(label='Reuse input from previous job using jobID',
                               required=False)
    # species
    library_mode = forms.BooleanField(label='Do not map to genome (Library mode)', required=False)
    no_libs = forms.BooleanField(
        label='Do not profile other ncRNAs  (you are interested in known microRNAs only!)', required=False)
    species = CategoriesField(queryset=m, required=False)

    # Adapter Trimming<div class="alert alert-danger">
    # guess_adapter = forms.BooleanField(label=mark_safe('<strong >Guess the adapter sequence<strong style="color:Red;"> (not recommended!)</strong>'), required=False)
    guess_adapter = forms.BooleanField(label=mark_safe(
        '<strong >Guess the adapter sequence <strong class="text-danger"> (not recommended!)</strong>'),
                                       required=False)
    # guess_adapter = forms.BooleanField(label='Guess the adapter sequence  (not recommended!)', required=False) <strong>My Condition is</strong>
    adapter_chosen = forms.ChoiceField(choices=ADAPTERS, required=False)
    adapter_manual = forms.CharField(label='Or Provide adapter sequence', required=False)
    adapter_length = forms.IntegerField(label='Minimum Adapter Length', max_value=12, min_value=6, initial=10)
    adapter_mismatch = forms.IntegerField(label='Max. mismatches in adapter detection', max_value=2,
                                          min_value=0, initial=1)
    adapter_recursive_trimming = forms.BooleanField(label='Recursive Adapter trimming', required=False,
                                                    initial=False)

    # MicroRNA Analysis

    referenceDB = forms.ChoiceField(label="", choices=[("miRBase", "Use miRBase (default)"), (
    "highconf", "Use high-confidence miRNAs only (miRBase)"), ("MirGeneDB", "Use a MirGeneDBv2.0 tag")],
                                    required=False, widget=forms.RadioSelect())
    genome_mir = forms.BooleanField(label='Use the miRNAs for the species from the selected genomes',
                                    required=False)
    highconf = forms.BooleanField(label='Use high confidence microRNAs from miRBase', required=False,
                                  initial=False)
    mirDB = forms.ChoiceField(label="", choices=mirdb_list, required=False)
    mirna_profiled = forms.CharField(
        label='Use miRBase tag(s) to define your miRNA reference annotation (microRNAs from selected species used by default)',
        required=False, initial="", widget=forms.TextInput(
            attrs={'placeholder': "e.g: hsa (human),mmu (mouse) or hsa:hsv1(human and herpes simplex virus)"}))

    homologous = forms.CharField(label='Analyse homologous microRNAs (can be set to "all"):', required=False)

    # Parameters
    is_solid = forms.BooleanField(label='The input is SOLiD', required=False)
    predict_mirna = forms.BooleanField(label='Predict New miRNAs', required=False)
    aligment_type = forms.ChoiceField(choices=ALIGMENT_TYPES, initial='n')
    seed_length = forms.IntegerField(label='Select the seed length for alignment', max_value=21, min_value=17,
                                     initial=20)
    min_read_count = forms.IntegerField(label='Minimum Read Count: ', max_value=10, min_value=1, initial=2)
    min_read_length = forms.IntegerField(label='Min. Read Length ', max_value=17, min_value=15, initial=15)
    mismatches = forms.IntegerField(label='Allowed number of mismatches (either to the genome or libraries)',
                                    max_value=2, min_value=0, initial=2)
    nucleotides_5_removed = forms.IntegerField(label='Remove 5\' barcode', max_value=6, min_value=0, initial=0)
    max_multiple_mapping = forms.IntegerField(label='Maximum Number of Multiple Mappings', max_value=40,
                                              min_value=1, initial=10)

    # Profile
    profile1 = forms.FileField(label='', required=False)
    profile2 = forms.FileField(label='', required=False)
    profile3 = forms.FileField(label='', required=False)
    profile4 = forms.FileField(label='', required=False)
    profile5 = forms.FileField(label='', required=False)
    profile_url1 = forms.CharField(label='Provide a URLs (one per line)', required=False, widget=forms.Textarea)
    species_hidden = forms.CharField(label='', required=False, widget=forms.HiddenInput, max_length=2500)
    input_hidden = forms.CharField(label='', required=False, widget=forms.HiddenInput, max_length=2500)

    def __init__(self, *args, **kwargs):
        self.folder = kwargs.pop('dest_folder', None)
        super(sRNABenchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(

            # Fieldset(
            #     '',
            #     'ifile',
            #     Field('sra_input', css_class='form-control'),
            #     Field('url',css_class='form-control'),
            #     Field('job_name', css_class='form-control'),
            #     Field('species_hidden', name='species_hidden')
            # ),

            create_collapsable_div(
                'library_mode',
                'no_libs',
                Field('species'),
                Field('species_hidden', name='species_hidden'),
                Field('input_hidden', name='input_hidden'),
                title='Select species', c_id='2',
                extra_title=render_modal('Species'),
                open=True
            ),

            create_collapsable_div(
                Fieldset(
                    'Adapter Selection',
                    'guess_adapter',
                    Field('adapter_chosen', css_class='form-control'),
                    Field('adapter_manual', css_class='form-control')
                ), Fieldset(
                    'Trimming Options',
                    Field('adapter_length', css_class='form-control'),
                    Field('adapter_mismatch', css_class='form-control'),
                    'adapter_recursive_trimming'),
                title='Adapter Trimming', c_id='3',
                open=True
            ),

            create_collapsable_div(
                Fieldset(
                    'Choose miRNA reference sequences',

                    # 'genome_mir',
                    # 'highconf',
                    # InlineRadios('referenceDB'),
                    Div(InlineRadios('referenceDB'), css_class="col-md-12"),
                    Field('mirDB', css_class='form-control', style="visibility: hidden;")
                ),
                Fieldset(
                    'Species Selection',
                    Field('mirna_profiled', css_class='form-control'),
                    # Field('homologous',css_class='form-control'),
                ),
                title='MicroRNA analysis', c_id='4'
            ),

            create_collapsable_div(
                # 'is_solid',
                'predict_mirna',
                Field('aligment_type', css_class='form-control'),
                Field('seed_length', css_class='form-control'),
                Field('min_read_count', css_class='form-control'),
                Field('min_read_length', css_class='form-control'),
                Field('mismatches', css_class='form-control'),
                Field('nucleotides_5_removed', css_class='form-control'),
                Field('max_multiple_mapping', css_class='form-control'),
                title='Parameters', c_id='5'
            ),

            create_collapsable_div(
                'profile1',
                'profile2',
                'profile3',
                'profile4',
                'profile5',
                Field('profile_url1', css_class='form-control'),
                title='Upload user annotations for profiling', c_id='6'
            ),

            ButtonHolder(
                # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="return myFunction()")
                Submit('submit', 'RUN', css_class='btn btn-primary', onclick="return printChecked()")
                # onsubmit="alert('Neat!'); return false")

            )
        )

    def clean(self):

        cleaned_data = super(sRNABenchForm, self).clean()
        print(cleaned_data.get('species'))
        if not cleaned_data.get('species') and not cleaned_data.get('mirna_profiled'):
            self.add_error('species', 'Species or a miRBase short name tag are required')
            self.add_error('mirna_profiled', 'Species or a miRBase short name tag are required')

        if cleaned_data.get('predict_mirna') and cleaned_data.get('library_mode'):
            self.add_error('library_mode', 'Genome mode is needed for miRNA prediction')
        # if not cleaned_data.get('guess_adapter') and cleaned_data.get('adapter_chosen')=='' and cleaned_data.get('adapter_manual')=='':
        if sum([bool(cleaned_data.get('guess_adapter')), bool(cleaned_data.get('adapter_chosen') != ''),
                bool(cleaned_data.get('adapter_manual') != '')]) != 1:
            print(sum([bool(cleaned_data.get('guess_adapter')), bool(cleaned_data.get('adapter_chosen') == ''),
                       bool(cleaned_data.get('adapter_manual') == '')]))
            self.add_error('guess_adapter',
                           'Choose either an adapter from the list, enter it manually or select `guess the adapter sequence`')
            self.add_error('adapter_chosen',
                           'Choose either an adapter from the list, enter it manually or select `guess the adapter sequence`')
            self.add_error('adapter_manual',
                           'Choose either an adapter from the list, enter it manually or select `guess the adapter sequence`')
        if cleaned_data.get('guess_adapter') and not cleaned_data.get('species'):
            self.add_error('species', 'if `guess the adapter sequence`, an input genome is required')
        if cleaned_data.get('highconf') and cleaned_data.get('mirDB'):
            self.add_error('highconf', 'Choose either miRBase or MirGeneDB for high confidence annotation')
            self.add_error('mirDB', 'Choose either miRBase or MirGeneDB for high confidence annotation')

        return cleaned_data

    @staticmethod
    def upload_files(cleaned_data, FS):
        libs_files = []
        name_modifier = cleaned_data.get('job_name')
        url = cleaned_data.get('url')
        sra_input = cleaned_data.get('sra_input')
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

            extension = os.path.basename(url).split('.')[-1]
            if name_modifier is not None:
                dest = os.path.join(FS.location, str(name_modifier) + "." + extension).replace(" ", "")
            else:
                dest = os.path.join(FS.location, os.path.basename(url))

            ifile, headers = urllib.request.urlretrieve(url, filename=dest)
        elif sra_input:
            ifile = sra_input

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
        # os.system("mkdir " + FS.location)
        out_dir = FS.location
        conf['out_dir'] = out_dir
        libs_files = self.upload_files(cleaned_data, FS)
        lib_mode = cleaned_data.get('library_mode')
        # is_solid = str(cleaned_data.get('is_solid')).lower()
        guess_adapter = str(cleaned_data.get('guess_adapter')).lower()
        predict_mirna = str(cleaned_data.get('predict_mirna')).lower()
        no_libs = cleaned_data.get('no_libs')
        highconf = cleaned_data.get('highconf')
        mirDB = cleaned_data.get('mirDB')
        # recursive_adapter_trimming = str(cleaned_data.get('recursive_adapter_trimming')).lower()
        recursive_adapter_trimming = str(cleaned_data.get('adapter_recursive_trimming')).lower()
        species = [i.db_ver for i in cleaned_data['species']]
        assemblies = [i.db for i in cleaned_data['species']]
        short_names = [i.shortName for i in cleaned_data['species']]
        micrornas_species = ':'.join(short_names)
        adapter = cleaned_data['adapter_chosen'] or cleaned_data['adapter_manual']
        if adapter == "EMPTY":
            adapter = None
        nucleotides_5_removed = str(cleaned_data['nucleotides_5_removed'])
        adapter_length = str(cleaned_data['adapter_length'])
        adapter_mismatch = str(cleaned_data['adapter_mismatch'])
        seed_length = str(cleaned_data['seed_length'])
        mismatches = str(cleaned_data['mismatches'])
        aligment_type = str(cleaned_data['aligment_type'])
        min_read_count = str(cleaned_data['min_read_count'])
        min_read_length = str(cleaned_data['min_read_length'])
        max_multiple_mapping = str(cleaned_data['max_multiple_mapping'])
        homologous = cleaned_data['homologous'] if cleaned_data['homologous'] != '' else None
        species_annotation_file = SpeciesAnnotationParser(CONF["speciesAnnotation"])
        species_annotation = species_annotation_file.parse()
        db = CONF["db"]

        new_conf = SRNABenchConfig(species_annotation, db, FS.location, "EMPTY", iszip="true",
                                   # RNAfold="RNAfold2",
                                   bedGraph="true", writeGenomeDist="true", predict=predict_mirna,
                                   graphics="true",
                                   species=species, assembly=assemblies, short_names=short_names,
                                   adapter=adapter,
                                   recursiveAdapterTrimming=recursive_adapter_trimming, libmode=lib_mode,
                                   nolib=no_libs,
                                   microRNA=micrornas_species, removeBarcode=nucleotides_5_removed,
                                   adapterMinLength=adapter_length, adapterMM=adapter_mismatch,
                                   seed=seed_length,
                                   noMM=mismatches, alignType=aligment_type, minRC=min_read_count,
                                   solid="",
                                   guessAdapter=guess_adapter, highconf=highconf, mirDB=mirDB,
                                   homolog=homologous,
                                   user_files=libs_files, minReadLength=min_read_length,
                                   mBowtie=max_multiple_mapping)

        conf_file_location = os.path.join(FS.location, "conf.txt")
        new_conf.write_conf_file(conf_file_location)
        ####Remove input_line
        f = open(conf_file_location, "r")
        lines = f.readlines()
        f.close()
        f = open(conf_file_location, "w")
        for line in lines:
            if not line.startswith("input=EMPTY"):
                f.write(line)
        f.close()

        input_data = cleaned_data.get("input_hidden").split(",")
        if not os.path.exists(os.path.join(MEDIA_ROOT,self.folder,"launched")):
            os.mkdir(os.path.join(MEDIA_ROOT,self.folder,"launched"))
        onlyfiles = [f for f in os.listdir(os.path.join(MEDIA_ROOT, pipeline_id))
                     if os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, pipeline_id), f))]
        onlyfiles.remove("SRR_files.txt")
        onlyfiles.remove("URL_files.txt")
        onlyfiles.remove("conf.txt")

        SRR_list = []
        with open(os.path.join(MEDIA_ROOT, pipeline_id, "SRR_files.txt"), "r") as SRR_file:
            for ix,SRR in enumerate(SRR_file.readlines()):
                SRR_list.append(SRR.rstrip())
        URL_list = []
        with open(os.path.join(MEDIA_ROOT, pipeline_id, "URL_files.txt"), "r") as URL_file:
            for ix, URL in enumerate(URL_file.readlines()):
                URL_list.append(URL.rstrip())

        general_config = " "
        with open(os.path.join(MEDIA_ROOT,pipeline_id,"conf.txt"),"r") as conf_file:
            general_config = conf_file.read()

        job_list = []
        for i in input_data:
            new_id = generate_uniq_id()
            out_dir = os.path.join(MEDIA_ROOT, new_id)
            os.mkdir(out_dir)
            clase, ix = i.rstrip().split("_")
            if clase == "file":
                input_file = onlyfiles[int(ix)]
                full_path = os.path.join(MEDIA_ROOT,new_id,input_file)
                shutil.copyfile(os.path.join(MEDIA_ROOT,new_id,input_file), os.path.join(out_dir,input_file))

            if clase == "SRR":
                input_file = SRR_list[int(ix)]
                full_path = input_file

            if clase == "URL":
                url = URL_list[int(ix)]
                dest = os.path.join(out_dir, os.path.basename(url))
                ifile, headers = urllib.request.urlretrieve(url, filename=dest)
                input_file = dest
                full_path = input_file


                #ifile, headers = urllib.request.urlretrieve(url, filename=dest)
            line = "input=" + input_file + "\n"
            config = line + general_config
            conf_file_location = os.path.join(out_dir,"conf.txt")
            with open(conf_file_location,"w") as conf_fi:
                conf_fi.write(config)
            name = new_id + '_bench'
            configuration = {
                'pipeline_id': new_id,
                'out_dir': out_dir,
                'name': name,
                'conf_input': conf_file_location,
                'type': 'sRNAbench'
            }
            configuration_file_path = os.path.join(out_dir, 'conf.json')
            JobStatus.objects.create(job_name=name, pipeline_key=new_id, job_status="not_launched",
                                     start_time=datetime.now(),
                                     all_files=full_path,
                                     modules_files="",
                                     pipeline_type="sRNAbench",
                                     )
            with open(configuration_file_path, 'w') as conf_file:
                json.dump(configuration, conf_file, indent=True)
            if QSUB:
                call = 'qsub -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                    configuration_file_path=configuration_file_path,
                    job_name=name,
                    sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh'))
                os.system(call)
                js = JobStatus.objects.get(pipeline_key=new_id)
                js.status.create(status_progress='sent_to_queue')
                js.job_status = 'sent_to_queue'
                js.save()
            job_list.append(new_id)
        # name = pipeline_id + '_bench'
        # configuration = {
        #     'pipeline_id': pipeline_id,
        #     'out_dir': out_dir,
        #     'name': name,
        #     'conf_input': conf_file_location,
        #     'type': 'sRNAbench'
        # }
        #
        # JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not_launched",
        #                          start_time=datetime.now(),
        #                          all_files=ifile,
        #                          modules_files="",
        #                          pipeline_type="sRNAbench",
        #                          )
        # configuration_file_path = os.path.join(out_dir, 'conf.json')
        # with open(configuration_file_path, 'w') as conf_file:
        #     json.dump(configuration, conf_file, indent=True)
        return pipeline_id

    def create_call(self):
        pipeline_id = self.folder
        pipeline_id = self.create_conf_file(self.cleaned_data, pipeline_id)

        onlyfiles = [f for f in os.listdir(os.path.join(MEDIA_ROOT, pipeline_id))
                     if os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, pipeline_id), f))]
        onlyfiles.remove("SRR_files.txt")
        onlyfiles.remove("URL_files.txt")
        onlyfiles.remove("conf.txt")

        return pipeline_id

        # if QSUB:
        #     return 'qsub -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
        #         configuration_file_path=configuration_file_path,
        #         job_name=name,
        #         sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id
        # else:
        #     return '{sh} {configuration_file_path}'.format(
        #         configuration_file_path=configuration_file_path,
        #         sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run.sh')), pipeline_id


# class PhotoForm(forms.ModelForm):
#     # def __init__(self, *args, **kwargs):
#     #     self.request_path = kwargs.pop("request_path", None)
#     #     super(PhotoForm, self).__init__(*args, **kwargs)
#
#     #title = models.CharField(max_length=255, blank=True)
#     file = models.FileField(upload_to= '%Y%m%d%H%M')
#     #uploaded_at = models.DateTimeField(auto_now_add=True)
