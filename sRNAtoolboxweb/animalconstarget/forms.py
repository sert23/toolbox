import datetime
import os
import urllib
from django import forms
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from progress.models import JobStatus
from sRNAtoolboxweb.settings import BASE_DIR, CONF
from FileModels.speciesParser import SpeciesParser
from sRNAtoolboxweb.settings import MEDIA_ROOT,QSUB
from utils.pipeline_utils import generate_uniq_id
from django.conf import settings
from django.core.files.base import ContentFile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, ButtonHolder, Submit

SPECIES_PATH = settings.CONF["species"]
PATH_TO_DB=CONF["db"]


from FileModels.TargetConsensusParser import TargetConsensusParser

# complete_species = {}
# species_file = SpeciesParser(SPECIES_PATH)
# array_species = species_file.parse()





class AMirconsForm(forms.Form):
    import csv
    from operator import itemgetter

    animals_dict={}
    with open(os.path.join(PATH_TO_DB,"species.txt"), 'rt') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            if row[0]=="animal":
                animals_dict[row[3]] =  row[5]
    choice_list=[]
    with open(os.path.join(PATH_TO_DB,"targetAnnot.txt"), 'rt') as tsvfile:
        rows = csv.reader(tsvfile,delimiter='\t')
        for row in rows:
            if animals_dict.get(row[0]) :
                current = (row[2] , animals_dict[row[0]] + " (3'UTRs)")
                choice_list.append(current)

    choice_list = sorted(choice_list, key= itemgetter(1))

    #species = ((os.path.join(os.path.join(PATH_TO_DB,"utr"), key),key[0:-9].replace("_", " ")) for (key) in onlyfiles)


    mirfile = forms.FileField(label='Upload miRNAs file', required=False)
    utrfile = forms.FileField(label='Upload targets file', required=False)

    utrchoice = forms.ChoiceField(label="Or choose UTR from the list",choices=choice_list,required=False)

    mirtext = forms.CharField(label="Or paste your miRNAs here",widget=forms.Textarea,required=False)
    utrtext = forms.CharField(label="Or paste your targets here",widget=forms.Textarea,required=False)

    seed = forms.BooleanField(label='Simple seed analysis', required=False)
    targetspy=forms.BooleanField(label='TargetSpy', required=False)
    miranda=forms.BooleanField(label='Miranda', required=False)
    PITA=forms.BooleanField(label='PITA', required=False)

    seed_par=forms.CharField(label="Seed analysis parameters",required=False, initial=" ")
    target_par=forms.CharField(label="TargetSpy parameters",required=False, initial=" ")
    miranda_par = forms.CharField(label="Miranda Parameters", required=False, initial=" ")
    PITA_par = forms.CharField(label="PITA parameters", required=False, initial=" ")

    def __init__(self, *args, **kwargs):
        super(AMirconsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Choose miRNA input',
                Field('mirfile', css_class='form-control'),
                Field('mirtext', css_class='form-control')),
            Fieldset(
                'Choose target input',
                Field('utrfile', css_class='form-control'),
                'utrchoice',
                Field('utrtext', css_class='form-control')),
            Fieldset(
                'Choose programs and parameters',
                'seed',
                Field('seed_par', css_class='form-control'),
                'targetspy',
                Field('target_par', css_class='form-control'),
                'miranda',
                Field('miranda_par', css_class='form-control'),
                'PITA',
                Field('PITA_par', css_class='form-control'),

            ),

            ButtonHolder(
                Submit('submit', 'RUN', css_class='btn btn-primary')
            )
        )


    def clean(self):
        cleaned_data = super(AMirconsForm, self).clean()
        if not cleaned_data.get('mirfile') and not cleaned_data.get('mirtext'):
            self.add_error('mirfile', 'miRNA input is required')
            self.add_error('mirtext', 'miRNA input is required')
        if not cleaned_data.get('utrfile') and not cleaned_data.get('utrtext') and not cleaned_data.get('utrchoice'):
            self.add_error('utrfile', 'UTR input is required')
            self.add_error('utrtext', 'UTR input is required')
            self.add_error('utrchoice', 'UTR input is required')
        if not cleaned_data.get('seed') and not cleaned_data.get('targetspy') and not cleaned_data.get('miranda') and not cleaned_data.get('PITA') and not cleaned_data.get('psRobot') and not cleaned_data.get('tapir_fasta') and not cleaned_data.get('tapir_RNAhyb'):
            self.add_error('targetspy', 'At least one program should be chosen')
            self.add_error('miranda', 'At least one program should be chosen')
            self.add_error('PITA', 'At least one program should be chosen')
            self.add_error('seed','At least one program should be chosen')
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
        mirfile = self.cleaned_data.get("mirfile")
        utrfile= self.cleaned_data.get("utrfile")
        program_list=[]
        param_list=[]
        if self.cleaned_data.get('seed'):
            program_list.append("SEED")
            param_list.append(self.cleaned_data.get("seed_par"))
        if self.cleaned_data.get('targetspy'):
            program_list.append("TS")
            param_list.append(self.cleaned_data.get("target_par"))
        if self.cleaned_data.get('miranda'):
            program_list.append("MIRANDA")
            param_list.append(self.cleaned_data.get("miranda_par"))
        if self.cleaned_data.get('PITA'):
            program_list.append("PITA")
            param_list.append(self.cleaned_data.get("PITA_par"))
        program_string = ":".join(program_list)
        if mirfile:
            file_to_update = mirfile
            uploaded_file = str(file_to_update).replace(" ", "_").replace("(","").replace(")","")
            mirfile = FS.save(uploaded_file, file_to_update)
        else:
            mirtext=self.cleaned_data.get("mirtext")
            content = ContentFile(mirtext)
            mirfile=FS.save("mirs.fa", content)

        if utrfile:
            file_to_update = utrfile
            uploaded_file = str(file_to_update).replace(" ", "_").replace("(", "").replace(")", "")
            utrfile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("utrtext"):
            utrtext = self.cleaned_data.get("utrtext")
            content = ContentFile(utrtext)
            utrfile=FS.save('utrs.fa', content)

        else:
            utrfile = self.cleaned_data.get('utrchoice')

        name = pipeline_id + '_mirconstarget'

        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            "mirna_file": mirfile,
            "utr_file": utrfile,
            "program_string": program_string,
            #"parameter_string": '":"'.join(param_list),
            "parameter_string": "\"'" + " : ".join(param_list) + "'\"" ,
            'type': 'miRNAconstarget'
         }
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        import json
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 #finish_time=datetime.time(0, 0),
                                 all_files=[mirfile,utrfile],
                                 modules_files="",
                                 pipeline_type="mirconstarget",
                                )

        if QSUB:
            return 'qsub -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id
        else:
            return '{sh} {configuration_file_path}'.format(
                configuration_file_path=configuration_file_path,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run.sh')), pipeline_id



