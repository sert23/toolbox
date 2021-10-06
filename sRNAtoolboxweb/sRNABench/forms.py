import json
from datetime import datetime
import os
import urllib.request

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Field, Div, Row
from crispy_forms.bootstrap import InlineRadios, TabHolder, Tab, Accordion,AccordionGroup

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
                    # option value="2533:Danio rerio">Zebrafish(GRCz10)
                    list.append((str(category.id) + ":" + category.scientific + " ", str(category)))
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
    #return Species.objects.all().order_by('sp_class')

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
    #highconf = forms.BooleanField(label='Use high confidence microRNAs from miRBase', required=False, initial=False)
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



    def __init__(self, *args, **kwargs):
        super(sRNABenchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(

            create_collapsable_div(

            TabHolder(
                Tab('Upload',
                    # Div('ifile'),
                    'ifile'
                    # Div('field_name_2')
                    ),
                Tab('URL/link',
                    Field('url', css_class='form-control'),
                    ),
                Tab('SRA Run ID',
                    Field('sra_input', css_class='form-control'),
                    ),
                Tab('Reuse Job',
                    Field('job_reuse', css_class='form-control')
                    )
            ),
                title="Choose your input",
                extra_title=render_modal('Choose_Input'),
                c_id='1',
                open=True
                ),

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
                Submit('submit', 'RUN', css_class='btn btn-primary', onclick="return validation()")
                       #onsubmit="alert('Neat!'); return false")

            )
        )

    def clean(self):
        cleaned_data = super(sRNABenchForm, self).clean()

        #Input files
        if sum([bool(cleaned_data.get('ifile')), bool(cleaned_data.get('url')!=''), bool(cleaned_data.get('sra_input')!=''),bool(cleaned_data.get('job_reuse')!='')]) != 1:
            self.add_error('ifile', 'Choose either file, URL, SRA Run ID or previous JobID as input')
            self.add_error('url', 'Choose either file, URL, SRA Run ID or previous JobID as input')
            self.add_error('sra_input', 'Choose either file, URL, SRA Run ID or previous JobID as input')
            self.add_error('job_reuse', 'Choose either file, URL, SRA Run ID or previous JobID as input')

        jobID = cleaned_data.get("job_reuse")
        if jobID:
            record = JobStatus.objects.get(pipeline_key=jobID)
            if not record:
                self.add_error('ifile', 'The jobID you provided could not be found')
                self.add_error('job_reuse', 'The jobID you provided could not be found')
            elif not (os.path.exists(record.outdir)):
                self.add_error('ifile', 'The jobID you provided must be older than 15 days so it was deleted')
                self.add_error('job_reuse', 'The jobID you provided must be older than 15 days so it was deleted')
            elif not record.pipeline_type == "sRNAbench":
                self.add_error('ifile', 'The jobID you provided is not an sRNAbench job')
                self.add_error('job_reuse', 'The jobID you provided is not an sRNAbench job')

        #species
        print(cleaned_data.get('species'))
        if sum([bool(cleaned_data.get('species')), bool(cleaned_data.get('mirna_profiled')), cleaned_data.get("referenceDB")== "MirGeneDB" ]) < 1:
            self.add_error('species','Species or miRBase/MirGeneDB short name tag(s) are required')
            self.add_error('referenceDB','Species or miRBase/MirGeneDB short name tag(s) are required')
            self.add_error('mirna_profiled', 'Species or miRBase/MirGeneDB short name tag(s) are required')

        #preprocessing
        if not cleaned_data.get("library_protocol"):
            self.add_error('library_protocol', mark_safe('<strong class="text-danger"> <i> Choose one provided or custom protocol </i></strong>'))
            # self.add_error(None, 'Choose one provided or custom protocol ')
            # self.add_error('library_protocol', 'Choose one provided or custom protocol ')

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
        os.system("mkdir " + FS.location)
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
            protocol = None
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


        new_conf = SRNABenchConfig(species_annotation, db, FS.location, ifile, iszip="true",
                                  #RNAfold="/usr/bin/RNAfold2",
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

        name = pipeline_id + '_bench'
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': conf_file_location,
            'type': 'sRNAbench'
        }

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.now(),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="sRNAbench",
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