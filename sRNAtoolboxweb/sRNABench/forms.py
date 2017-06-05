import copy
from crispy_forms.bootstrap import Accordion, AccordionGroup, Tab
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Field
from django import forms


def create_collapsable_div(*fields, **kwargs):
    title = kwargs['title']
    c_id = kwargs['c_id']
    extra = ''
    if 'extra_title' in kwargs:
        extra = kwargs['extra_title']
    panel_title = HTML('<h4 class="panel-title"><a data-toggle="collapse" href="#'+c_id+'">'+title+'</a>'+extra+'</h4>')
    panel_heading = Div(panel_title, css_class='panel-heading')
    form_group = Div(*fields, css_class='form-group')
    body = Div(form_group, css_class='panel-body')
    panel_collapse = Div(body, css_class="panel-collapse collapse", css_id=c_id)
    panel = Div(panel_heading, panel_collapse, css_class="panel panel-default")
    return panel

def render_modal(modal):
    return '<a  data-toggle="modal" data-target="#'+modal+'" class="btn btn-link"><i class="fa fa-question-circle"> </i></a>'


class sRNABenchForm(forms.Form):
    ADAPTERS = (
        (None, "Select Adapter to trim off"),
        ("TGGAATTCTCGGGTGCCAAGG", "Illumina RA3 - TGGAATTCTCGGGTGCCAAGG"),
        ("UCGUAUGCCGUCUUCUGCUUGU", "Illumina(alternative) - UCGUAUGCCGUCUUCUGCUUGU", ),
        ("330201030313112312", "SOLiD(SREK) - 330201030313112312"),
    )

    ALIGMENT_TYPES = (
        ('n', 'bowtie seed alignment(only mismatches in seed region count)'),
        ('v', 'full read alignment(all mismatches count)'),
    )


    ifile = forms.FileField(label='Upload the reads (fastq.gz, fa.gz or rc.gz)' + render_modal('SRNAinput'),
                            required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)
    job_name = forms.CharField(label='Provide a Job Name.  (Leave blank to use fileName)',
                             required=False)
    # species
    library_mode = forms.BooleanField(label='Do not map to genome (Library mode)', required=False)
    no_libs = forms.BooleanField(label='Do not profile other ncRNAs  (you are interested in known microRNAs only!)', required=False)
    # Adapter Trimming
    guess_adapter = forms.BooleanField(label='Guess the adapter sequence  (not recommended!)', required=False)
    adapter_chosen = forms.ChoiceField(choices=ADAPTERS)
    adapter_manual = forms.CharField(label='Or Provide adapter sequence', required=False)
    adapter_length = forms.IntegerField(label='Minimum Adapter Length', max_value=12, min_value=6, initial=10)
    adapter_mismatch = forms.IntegerField(label='Max. mismatches in adapter detection', max_value=2, min_value=0, initial=1)
    adapter_recursive_trimming = forms.BooleanField(label='Recursive Adapter trimming', required=False)
    # MicroRNA Analysis
    genome_mir = forms.BooleanField(label='Use the miRNAs for the species from the selected genomes', required=False)
    highconf = forms.BooleanField(label='Use high confidence microRNAs from miRBase', required=False)
    mirna_profiled = forms.CharField(
        label='Specify the microRNAs that should be profiled (for example, hsa (human), mmu (mouse) or hsa:hsv1 '
              '(human and herpes simplex virus):',
        required=False,
    )
    homologous = forms.CharField(label='Analyse homologous microRNAs (can be set to "all"):', required=False)
    # Parameters
    is_solid = forms.BooleanField(label='The input is SOLiD', required=False)
    predict_mirna = forms.BooleanField(label='Predict New miRNAs', required=False)
    aligment_type = forms.ChoiceField(choices=ALIGMENT_TYPES, initial='n')
    seed_length = forms.IntegerField(label='Select the seed length for alignment', max_value=21, min_value=17, initial=20)
    min_read_count = forms.IntegerField(label='Minimum Read Count: ', max_value=10, min_value=1, initial=2)
    min_read_length = forms.IntegerField(label='Min. Read Length ', max_value=17, min_value=15, initial=15)
    mismatches = forms.IntegerField(label='Allowed number of mismatches (either to the genome or libraries)', max_value=2, min_value=0, initial=2)
    nucleotides_5_removed = forms.IntegerField(label='Remove 5\' barcode', max_value=6, min_value=0, initial=0)
    max_multiple_mapping = forms.IntegerField(label='Maximum Number of Multiple Mappings', max_value=40, min_value=1, initial=10)

    def __init__(self, *args, **kwargs):
        super(sRNABenchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                '',
                'ifile',
                Field('url',css_class='form-control'),
                Field('job_name', css_class='form-control'),
            ),

            create_collapsable_div(
                'library_mode',
                'no_libs',
                title='Select species', c_id='2',
                extra_title=render_modal('Species')
            ),

            create_collapsable_div(
                Fieldset(
                'Adapter Selection',
                'guess_adapter',
                Field('adapter_chosen', css_class='form-control'),
                Field('adapter_manual', css_class='form-control')
                ),Fieldset(
                    'Trimming Options',
                Field('adapter_length', css_class='form-control'),
                Field('adapter_mismatch', css_class='form-control'),
                'adapter_recursive_trimming'),
                title='Adapter Trimming', c_id='3'
            ),

            create_collapsable_div(
                Fieldset(
                'miRNA Analysis Options',
                'genome_mir',
                'highconf'
                ),
                Fieldset(
                'Species Selection',
                Field('mirna_profiled',css_class='form-control'),
                Field('homologous',css_class='form-control'),
                ),
                title='MicroRNA analysis', c_id='4'
            ),

            create_collapsable_div(
                'is_solid',
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

            ButtonHolder(
                Submit('submit', 'RUN', css_class='btn btn-primary')
            )
        )

    def clean(self):
        cleaned_data = super(sRNABenchForm, self).clean()
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