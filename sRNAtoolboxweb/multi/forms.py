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
    return Species.objects.all().order_by('sp_class', 'specie')


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
        # (None, "Select Adapter to trim off"),
        ("EMPTY", "Input reads are already trimmed"),
        ("TGGAATTCTCGGGTGCCAAGG", "Illumina RA3 - TGGAATTCTCGGGTGCCAAGG"),
        ("UCGUAUGCCGUCUUCUGCUUGU", "Illumina(alternative) - UCGUAUGCCGUCUUCUGCUUGU", ),
        ("330201030313112312", "SOLiD(SREK) - 330201030313112312"),
    )

    ALIGMENT_TYPES = (
        ('n', 'bowtie seed alignment(only mismatches in seed region count)'),
        ('v', 'full read alignment(all mismatches count)'),
    )

    #mirdb_list = [(None, "Do not use MirGeneDB")]
    mirdb_list = []
    fh = open(CONF["mirDbPath"])
    for line in fh:
        mirdb_list.append((line.rstrip(), line.rstrip()))


    ifile = forms.FileField(label='Upload the reads (fastq.gz, fa.gz or rc.gz)' + render_modal('SRNAinput'),
                            required=False)
    sra_input = forms.CharField(label='Or provide a SRA ID (starting with SRR or ERR)', required=False)
    url = forms.URLField(label=mark_safe('Or provide a URL for large files <strong class="text-success"> (recommended!)</strong>'), required=False)
    job_reuse = forms.CharField(label='Reuse input from previous sRNAbench job using jobID',
                             required=False)
    # species
    library_mode = forms.BooleanField(label='Do not map to genome (Library mode)' + render_modal('library_mode'), required=False)
    no_libs = forms.BooleanField(label='Do not profile other ncRNAs  (you are interested in known microRNAs only!)' + render_modal('other_ncrnas'), required=False)
    species = CategoriesField(queryset=m, required=False, label="Species"+ render_modal('species_dropdown'))

    # Adapter Trimming<div class="alert alert-danger">
    #guess_adapter = forms.BooleanField(label=mark_safe('<strong >Guess the adapter sequence<strong style="color:Red;"> (not recommended!)</strong>'), required=False)
    guess_adapter = forms.BooleanField(label=mark_safe('<strong >Guess the adapter sequence <strong class="text-danger"> (not recommended!)</strong>'), required=False)
    #guess_adapter = forms.BooleanField(label='Guess the adapter sequence  (not recommended!)', required=False) <strong>My Condition is</strong>
    adapter_chosen = forms.ChoiceField(choices=ADAPTERS, required=False)
    adapter_manual = forms.CharField(label='Provide adapter sequence', required=False)
    adapter_length = forms.IntegerField(label='Minimum Adapter Length', max_value=12, min_value=6, initial=10)
    adapter_mismatch = forms.IntegerField(label='Max. mismatches in adapter detection', max_value=2, min_value=0, initial=1)
    adapter_recursive_trimming = forms.BooleanField(label='Recursive Adapter trimming', required=False, initial=False)
    nucleotides_3_removed = forms.IntegerField(label='Remove 3\' nucleotides from random adapter', max_value=15, min_value=0, initial=0)

    #Reads preprocessing

    protocols = [
        # ("EMPTY", mark_safe("Input reads are already trimmed")),

        ("Illumina", mark_safe("Illumina TrueSeq&#153; (280916)" + render_modal('Illumina'))),
        ("NEBnext", mark_safe("NEBnext&#153;" + render_modal('NEB'))),
        ("Bioo", mark_safe("Bioo Scientific Nextflex&#153; (v2,v3)" + render_modal('Bioo'))),
        ("SMARTer", mark_safe("Clonetech SMARTer&#153;" + render_modal('Smarter'))),
        ("Qiagen", mark_safe("Qiagen&#153; (with UMIs)" + render_modal('Qiagen'))),
        ("Custom", mark_safe("Customized protocol" + render_modal('Custom')))]
    library_protocol = forms.ChoiceField(label="", choices=protocols, required=False, widget=forms.RadioSelect())

    #Quality Control

    quality_method = forms.ChoiceField(label="Filtering method" + render_modal('quality_filter'), choices=[(None, "No quality filter"),("mean","Use minimum mean quality score"),
                                                   ("min","Use minimum quality score threshold per sequenced nucleotide")], required=False, initial= None)
    phred_encode = forms.ChoiceField(label="Phred Score Encoding" + render_modal('phred_encode'), choices=[(33, "Phred+33 (Default)"),(64,"Phred+64")], required=False)
    quality_threshold = forms.IntegerField(label='Phred Score Threshold', max_value=35, min_value=20, initial=20, required=False)
    maximum_positions = forms.IntegerField(label='Maximum number of positions allowed below quality threshold', max_value=3, min_value=0, initial=0,required=False)

    # MicroRNA Analysis
    referenceDB = forms.ChoiceField(label="", choices=[("miRBase","Use miRBase (default)"),("highconf","Use high-confidence miRNAs only (miRBase)"),("MirGeneDB","Use a MirGeneDBv2.0 tag")], initial="miRBase", required=False, widget=forms.RadioSelect())
    genome_mir = forms.BooleanField(label='Use the miRNAs for the species from the selected genomes', required=False)
    highconf = forms.BooleanField(label='Use high confidence microRNAs from miRBase', required=False, initial=False)
    mirDB = forms.ChoiceField(label="", choices=mirdb_list, required=False)
    mirna_profiled = forms.CharField(
        label='Use miRBase tag(s) to define your miRNA reference annotation (microRNAs from selected species used by default)',
            required=False, initial="", widget=forms.TextInput(attrs={'placeholder': "e.g: hsa (human),mmu (mouse) or hsa:hsv1(human and herpes simplex virus)"}))

    homologous = forms.CharField(label='Analyse homologous microRNAs (can be set to "all"):', required=False)

    # Parameters
    is_solid = forms.BooleanField(label='The input is SOLiD', required=False)
    predict_mirna = forms.BooleanField(label='Predict New miRNAs', required=False)
    aligment_type = forms.ChoiceField(choices=ALIGMENT_TYPES, initial='n')
    seed_length = forms.IntegerField(label='Select the seed length for alignment', max_value=21, min_value=17, initial=20)
    min_read_count = forms.IntegerField(label='Minimum Read Count: ', max_value=10, min_value=1, initial=2)
    min_read_length = forms.IntegerField(label='Min. Read Length ', max_value=17, min_value=15, initial=15)
    mismatches = forms.IntegerField(label='Allowed number of mismatches (either to the genome or libraries)', max_value=2, min_value=0, initial=1)
    nucleotides_5_removed = forms.IntegerField(label='Remove 5\' barcode (number of nucleotides) ', max_value=6, min_value=0, initial=0)
    max_multiple_mapping = forms.IntegerField(label='Maximum Number of Multiple Mappings', max_value=40, min_value=1, initial=10)

    #Profile
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

            # create_collapsable_div(

            # TabHolder(
            #     Tab('Upload',
            #         # Div('ifile'),
            #         'ifile'
            #         # Div('field_name_2')
            #         ),
            #     Tab('URL/link',
            #         Field('url', css_class='form-control'),
            #         ),
            #     Tab('SRA Run ID',
            #         Field('sra_input', css_class='form-control'),
            #         ),
            #     Tab('Reuse Job',
            #         Field('job_reuse', css_class='form-control')
            #         )
            # ),
            #     title="Choose your input",
            #     extra_title=render_modal('Choose_Input'),
            #     c_id='1',
            #     open=True
            #     ),

            # Fieldset(
            #     '',
            #     'ifile',
            #     Field('sra_input', css_class='form-control'),
            #     Field('url',css_class='form-control'),
            #     Field('job_name', css_class='form-control'),
            #     Field('species_hidden', name='species_hidden')
            # ),

            create_collapsable_div(
                Field('species'),
                Field('species_hidden', name='species_hidden'),
                Field('input_hidden', name='input_hidden'),
                Div('library_mode', 'no_libs', css_id='genome-div'),

                title='Select species', c_id='2',
                extra_title=render_modal('Species'),
                open=True

            ),
            create_collapsable_div(
                Fieldset(
                    'Select sequencing library protocol',
                    Div(InlineRadios('library_protocol'), css_class="col-md-12")),
                Div(Fieldset(
                    'Custom preprocessing options',
                    "guess_adapter",
                    Field('adapter_chosen', css_class='form-control'),
                    Field('adapter_manual', css_class='form-control'),
                    'adapter_length',
                    'adapter_mismatch',
                    'nucleotides_5_removed',
                    'nucleotides_3_removed',
                    'adapter_recursive_trimming'),css_id="Adapter_Custom"),
                title='Reads preprocessing', c_id='3',
                open=True
            ),

            create_collapsable_div(

                    # '<small class="text-danger"> These parameters only apply if you provide fastq formatted input </small>.',
                    #'<p class="text-danger"> These parameters only apply if you provide fastq formatted input </p>.',
                    Field('quality_method', css_class='form-control'),
                    Field("phred_encode",  css_class='form-control'),
                    Field('quality_threshold'),
                    Div(Field('maximum_positions'),
                        css_id="Div_max"),
                title='Quality Control', c_id='35',
                extra_title='<small><b class="text-danger"> These parameters only apply if you provide fastq formatted input.</b></small>'
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
                'Species Selection' + render_modal('mirna_species'),
                Field('mirna_profiled',css_class='form-control'),
                'predict_mirna'
                # Field('homologous',css_class='form-control'),
                ),
                title='MicroRNA analysis', c_id='4'
            ),

            create_collapsable_div(
                #'is_solid',

                Field('aligment_type', css_class='form-control'),
                Field('seed_length', css_class='form-control'),
                Field('min_read_count', css_class='form-control'),
                Field('min_read_length', css_class='form-control'),
                Field('mismatches', css_class='form-control'),

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
                #Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                # Submit('submit', 'RUN', css_class='btn btn-primary')
                # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="return validation()")
                Div(Submit('submit', 'RUN', css_class='btn btn-primary', onclick="return saveChecked()" ),
                    css_id="button_div", title="")
        # Submit('submit', mark_safe('<a href="#" data-toggle="tooltip" title="Hooray!">Hover over me</a>'),
        #        css_class='btn btn-primary', onclick="return saveChecked()")
                       #onsubmit="alert('Neat!'); return false")

            )
        )

    def clean(self):
        cleaned_data = super(sRNABenchForm, self).clean()

        #species
        print(cleaned_data.get('species'))
        if sum([bool(cleaned_data.get('species')), bool(cleaned_data.get('mirna_profiled')), cleaned_data.get("referenceDB")== "MirGeneDB" ]) < 1:
            self.add_error('species','Species or miRBase/MirGeneDB short name tag(s) are required')
            self.add_error('referenceDB','Species or miRBase/MirGeneDB short name tag(s) are required')
            self.add_error('mirna_profiled', 'Species or miRBase/MirGeneDB short name tag(s) are required')

        #preprocessing
        if not cleaned_data.get("library_protocol"):
            self.add_error('library_protocol', 'Choose one provided or custom protocol ')

        #predict
        if cleaned_data.get('predict_mirna') and cleaned_data.get('library_mode'):
            self.add_error('library_mode', 'Mapping to genome is necessary for miRNA prediction')
            self.add_error('predict_mirna', 'Mapping to genome is necessary for miRNA prediction')

        # if not cleaned_data.get('guess_adapter') and cleaned_data.get('adapter_chosen')=='' and cleaned_data.get('adapter_manual')=='':
        # if sum([bool(cleaned_data.get('guess_adapter')), bool(cleaned_data.get('adapter_chosen')!=''), bool(cleaned_data.get('adapter_manual')!='')]) != 1:
        #     print(sum([bool(cleaned_data.get('guess_adapter')), bool(cleaned_data.get('adapter_chosen')==''), bool(cleaned_data.get('adapter_manual')=='')]))
        #     self.add_error('guess_adapter', 'Choose either an adapter from the list, enter it manually or select `guess the adapter sequence`')
        #     self.add_error('adapter_chosen', 'Choose either an adapter from the list, enter it manually or select `guess the adapter sequence`')
        #     self.add_error('adapter_manual', 'Choose either an adapter from the list, enter it manually or select `guess the adapter sequence`')
        # if cleaned_data.get('guess_adapter') and not cleaned_data.get('species'):
        #     self.add_error('species', 'if `guess the adapter sequence`, an input genome is required')

        return cleaned_data

    @staticmethod
    def upload_files(cleaned_data, FS):
        libs_files = []
        name_modifier = cleaned_data.get('job_name')
        url = cleaned_data.get('url')
        sra_input = cleaned_data.get('sra_input')
        job_reuse = cleaned_data.get("job_reuse")
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

            #ifile, headers = urllib.request.urlretrieve(url, filename=dest)
            ifile = url
        elif sra_input:
            ifile = sra_input
        elif job_reuse:
            jobID = job_reuse
            new_record = JobStatus.objects.get(pipeline_key=jobID)
            conf = os.path.join(new_record.outdir,"conf.txt")
            input_f = ""
            with open(conf, "r") as conf_file:
                lines = conf_file.readlines()
                for line in lines:
                    if line.startswith("input="):
                        input_f = line.rstrip().split("=")[1]
            ifile = input_f

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
        #Input
        ifile, libs_files = self.upload_files(cleaned_data, FS)

        #Species
        species = [i.db_ver for i in cleaned_data['species']]
        assemblies = [i.db for i in cleaned_data['species']]
        short_names = [i.shortName for i in cleaned_data['species']]
        micrornas_species = ':'.join(short_names)
        if cleaned_data.get("mirna_profiled"):
            micrornas_species = cleaned_data.get("mirna_profiled")
        lib_mode = cleaned_data.get('library_mode')
        no_libs = cleaned_data.get('no_libs')
        is_solid = "false"

        #Reads preprocessing
        protocol = cleaned_data.get('library_protocol')
        adapter_length = str(cleaned_data['adapter_length'])
        adapter_mismatch = str(cleaned_data['adapter_mismatch'])
        nucleotides_5_removed = str(cleaned_data['nucleotides_5_removed'])
        remove3pBases = str(cleaned_data['nucleotides_3_removed'])
        recursive_adapter_trimming = str(cleaned_data.get('adapter_recursive_trimming')).lower()

        #initialize variables
        umi = None
        iterative5pTrimming = None

        guess_adapter = "false"
        if protocol == "Illumina":
            adapter = "TGGAATTCTCGGGTGCCAAGGG"
        elif protocol == "NEBnext":
            adapter = "AGATCGGAAGAGCACACGTCT"
        elif protocol == "Bioo":
            adapter = "TGGAATTCTCGGGTGCCAAGGG"
            remove3pBases = "4"
            nucleotides_5_removed = "4"
        elif protocol == "SMARTer":
            adapter = "AAAAAAAAAA"
            iterative5pTrimming = 4
        elif protocol == "Qiagen":
            umi = "3pA12"
            adapter = "AACTGTAGGCACCATCAAT"
        elif protocol == "Custom":
            protocol= None
            if cleaned_data.get('guess_adapter'):
                guess_adapter = "true"
                adapter = "EMPTY"
            elif cleaned_data.get("adapter_manual"):
                adapter = cleaned_data.get("adapter_manual")
                guess_adapter = "false"
            elif cleaned_data.get("adapter_chosen"):
                adapter = cleaned_data.get("adapter_chosen")
                guess_adapter = "false"

        if adapter== "EMPTY":
            adapter = None

        #Quality Control

        qualityType = cleaned_data.get("quality_method")
        minQ = None
        phred_encode = None
        maximum_positions = None

        if qualityType == "mean":
            minQ = cleaned_data.get("quality_threshold")
            phred_encode = cleaned_data.get("phred_encode")
        elif qualityType == "min":
            minQ = cleaned_data.get("quality_threshold")
            phred_encode = cleaned_data.get("phred_encode")
            maximum_positions = cleaned_data.get("maximum_positions")
        else:
            qualityType=None


        # Reference DB
        if cleaned_data.get("referenceDB") == "highconf":
            highconf = True
        else:
            highconf = False
        if cleaned_data.get("referenceDB") == "MirGeneDB":
            mirDB = cleaned_data.get('mirDB')
        else:
            mirDB = None
        predict_mirna = str(cleaned_data.get('predict_mirna')).lower()

        #Parameters
        seed_length = str(cleaned_data['seed_length'])
        mismatches = str(cleaned_data['mismatches'])
        aligment_type = str(cleaned_data['aligment_type'])
        min_read_count = str(cleaned_data['min_read_count'])
        min_read_length = str(cleaned_data['min_read_length'])
        max_multiple_mapping = str(cleaned_data['max_multiple_mapping'])


        species_annotation_file = SpeciesAnnotationParser(CONF["speciesAnnotation"])
        species_annotation = species_annotation_file.parse()
        db = CONF["db"]


        new_conf = SRNABenchConfig(species_annotation, db, FS.location, "EMPTY", iszip="true",
                                  #RNAfold="RNAfold2",
                                  bedGraph="true", writeGenomeDist="true", predict=predict_mirna, graphics="true",
                                  species=species, assembly=assemblies, short_names=short_names, adapter=adapter,
                                  recursiveAdapterTrimming=recursive_adapter_trimming, libmode=lib_mode, nolib=no_libs,
                                  microRNA=micrornas_species, removeBarcode=nucleotides_5_removed,
                                  adapterMinLength=adapter_length, adapterMM=adapter_mismatch,
                                  seed=seed_length,
                                  noMM=mismatches, alignType=aligment_type, minRC=min_read_count, solid=is_solid,
                                  guessAdapter=guess_adapter, highconf=highconf, mirDB=mirDB,
                                  user_files=libs_files, minReadLength=min_read_length, mBowtie=max_multiple_mapping,
                                   remove3pBases = remove3pBases, umi=umi, iterative5pTrimming=iterative5pTrimming,
                                   qualityType=qualityType,minQ=minQ, phred=phred_encode, maxQfailure=maximum_positions,
                                   protocol=protocol, Rscript="/opt/local/R-3.5.3/bin/Rscript")

        conf_file_location = os.path.join(FS.location, "conf.txt")
        new_conf.write_conf_file(conf_file_location)

        f = open(conf_file_location, "r")
        lines = f.readlines()
        f.close()
        f = open(conf_file_location, "w")
        for line in lines:
            if not (line.startswith("input=EMPTY") or line.startswith("output=")):
                f.write(line)
        f.close()
        input_data = cleaned_data.get("input_hidden").split(",")
        if not os.path.exists(os.path.join(MEDIA_ROOT, self.folder, "launched")):
            os.mkdir(os.path.join(MEDIA_ROOT, self.folder, "launched"))
        onlyfiles = [f for f in os.listdir(os.path.join(MEDIA_ROOT, pipeline_id))
                     if os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, pipeline_id), f))]
        onlyfiles.remove("SRR_files.txt")
        onlyfiles.remove("URL_files.txt")
        onlyfiles.remove("conf.txt")

        SRR_list = []
        with open(os.path.join(MEDIA_ROOT, pipeline_id, "SRR_files.txt"), "r") as SRR_file:
            for ix, SRR in enumerate(SRR_file.readlines()):
                SRR_list.append(SRR.rstrip())
        URL_list = []
        with open(os.path.join(MEDIA_ROOT, pipeline_id, "URL_files.txt"), "r") as URL_file:
            for ix, URL in enumerate(URL_file.readlines()):
                URL_list.append(URL.rstrip())

        general_config = " "
        with open(os.path.join(MEDIA_ROOT, pipeline_id, "conf.txt"), "r") as conf_file:
            general_config = conf_file.read()

        job_list = []
        for i in input_data:
            new_id = generate_uniq_id()
            out_dir = os.path.join(MEDIA_ROOT, new_id)
            os.mkdir(out_dir)
            clase, ix = i.rstrip().split("_")
            if clase == "file":
                input_file = onlyfiles[int(ix)]
                full_path = os.path.join(MEDIA_ROOT, new_id, input_file)
                shutil.copyfile(os.path.join(MEDIA_ROOT, pipeline_id, input_file), os.path.join(out_dir, input_file))

            if clase == "SRR":
                input_file = SRR_list[int(ix)]
                full_path = input_file

            if clase == "URL":
                url = URL_list[int(ix)]
                # dest = os.path.join(out_dir, os.path.basename(url))
                # ifile, headers = urllib.request.urlretrieve(url, filename=dest)
                # input_file = dest
                full_path = url

                # ifile, headers = urllib.request.urlretrieve(url, filename=dest)
            line = "input=" + full_path + "\n"
            line2 = "output=" + out_dir + "\n"
            config = line + line2 + general_config
            conf_file_location = os.path.join(out_dir, "conf.txt")
            with open(conf_file_location, "w") as conf_fi:
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
                                     outdir=out_dir,
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
            os.system("touch " + os.path.join(MEDIA_ROOT, self.folder, "launched", new_id))
            job_list.append(new_id)

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

class sRNABenchForm2(forms.Form):
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
                Submit('submit', mark_safe('<a href="#" data-toggle="tooltip" title="Hooray!">Hover over me</a>'),
                       css_class='btn btn-primary', onclick="return saveChecked()")
                #Submit('submit', 'RUN', css_class='btn btn-primary', onclick="return saveChecked()")
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
            if not (line.startswith("input=EMPTY") or line.startswith("output=")):
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
                shutil.copyfile(os.path.join(MEDIA_ROOT,pipeline_id,input_file), os.path.join(out_dir,input_file))

            if clase == "SRR":
                input_file = SRR_list[int(ix)]
                full_path = input_file

            if clase == "URL":
                url = URL_list[int(ix)]
                full_path = url

                #ifile, headers = urllib.request.urlretrieve(url, filename=dest)
            # line = "input=" + input_file + "\n"
            line = "input=" + full_path + "\n"
            line2= "output="+ out_dir + "\n"
            config = line + line2 + general_config
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
                                     outdir = out_dir,
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
            os.system("touch " + os.path.join(MEDIA_ROOT, self.folder, "launched", new_id))
            job_list.append(new_id)

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





# class PhotoForm(forms.ModelForm):
#     # def __init__(self, *args, **kwargs):
#     #     self.request_path = kwargs.pop("request_path", None)
#     #     super(PhotoForm, self).__init__(*args, **kwargs)
#
#     #title = models.CharField(max_length=255, blank=True)
#     file = models.FileField(upload_to= '%Y%m%d%H%M')
#     #uploaded_at = models.DateTimeField(auto_now_add=True)
