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
from crispy_forms.bootstrap import TabHolder,Tab

SPECIES_PATH = settings.CONF["species"]
PATH_TO_DB=CONF["db"]


from FileModels.TargetConsensusParser import TargetConsensusParser

# complete_species = {}
# species_file = SpeciesParser(SPECIES_PATH)
# array_species = species_file.parse()





class MirFuncForm(forms.Form):
    import csv
    from operator import itemgetter

    plants_dict={}
    with open(os.path.join(PATH_TO_DB,"species.txt"), 'rt') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            if row[0]=="plant":
                plants_dict[row[3]] =  row[5]
    choice_list=[]
    with open(os.path.join(PATH_TO_DB,"targetAnnot.txt"), 'rt') as tsvfile:
        rows = csv.reader(tsvfile,delimiter='\t')
        for row in rows:
            if plants_dict.get(row[0]) :
                if row[2] != "-":
                    current = (row[2] , plants_dict[row[0]] + " (3'UTRs)")
                    choice_list.append(current)

    choice_list = sorted(choice_list, key= itemgetter(1))
    choice_list = [(None, "None selected")]+ choice_list

    cdna_list = []
    with open(os.path.join(PATH_TO_DB, "targetAnnot.txt"), 'rt') as tsvfile:
        rows = csv.reader(tsvfile, delimiter='\t')
        for row in rows:
            if plants_dict.get(row[0]) :
                if row[1] != "-":
                    current = (row[1] , plants_dict[row[0]] + " (cDNA)")
                    cdna_list.append(current)

    cdna_list = sorted(cdna_list, key=itemgetter(1))
    cdna_list=[(None, "None selected")]+cdna_list

    #species = ((os.path.join(os.path.join(PATH_TO_DB,"utr"), key),key[0:-9].replace("_", " ")) for (key) in onlyfiles)

    mirfile = forms.FileField(label='Upload miRNAs file', required=False)
    utrfile = forms.FileField(label='Upload targets file', required=False)

    utrchoice = forms.ChoiceField(label="Or choose UTR from the list",choices=choice_list,required=False)
    cdnachoice = forms.ChoiceField(label="Or choose cDNA from Ensembl",choices=cdna_list,required=False)

    mirtext = forms.CharField(label="Or paste your miRNAs here",widget=forms.Textarea,required=False)
    utrtext = forms.CharField(label="Or paste your targets here",widget=forms.Textarea,required=False)

    psRobot = forms.BooleanField(label='psRobot', required=False)
    tapir_fasta=forms.BooleanField(label='TAPIR FASTA engine', required=False)
    tapir_RNA=forms.BooleanField(label='TAPIR RNAhybrid engine', required=False)

    psRobot_par=forms.CharField(label="psRobot parameters",required=False, initial=" ")
    tapir_fasta_par=forms.CharField(label="TAPIR FASTA engine parameters",required=False, initial=" ")
    tapir_RNA_par = forms.CharField(label="TAPIR RNAhybrid engine Parameters", required=False, initial=" ")

    jobID = forms.CharField(
        label='Launch functargets from previous miRNAconstarget finished job', required=False)

    def __init__(self, *args, **kwargs):
        super(MirFuncForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            TabHolder(
                Tab('Using jobID',
                    Field('jobID', css_class='form-control')
                    ),
                Tab('Lolailo')
            ))
        #     Fieldset(
        #         'Choose miRNA input',
        #         Field('mirfile', css_class='form-control'),
        #         Field('mirtext', css_class='form-control')),
        #     Fieldset(
        #         'Choose target input',
        #         Field('utrfile', css_class='form-control'),
        #         'utrchoice',
        #         'cdnachoice',
        #         Field('utrtext', css_class='form-control')),
        #     Fieldset(
        #         'Choose programs and parameters',
        #         'psRobot',
        #         Field('psRobot_par', css_class='form-control'),
        #         'tapir_fasta',
        #         Field('tapir_fasta_par', css_class='form-control'),
        #         'tapir_RNA',
        #         Field('tapir_RNA_par', css_class='form-control'),
        #
        #     ),
        #
        #     ButtonHolder(
        #         Submit('submit', 'RUN', css_class='btn btn-primary')
        #     )
        # )


    def clean(self):
        cleaned_data = super(MirFuncForm, self).clean()
        if not cleaned_data.get('mirfile') and not cleaned_data.get('mirtext'):
            self.add_error('mirfile', 'miRNA input is required')
            self.add_error('mirtext', 'miRNA input is required')
        if not cleaned_data.get('utrfile') and not cleaned_data.get('utrtext') and not cleaned_data.get('utrchoice') and not cleaned_data.get('cdnachoice'):
            self.add_error('utrfile', 'UTR or other target input is required')
            self.add_error('utrtext', 'UTR or other target input is required')
            self.add_error('utrchoice', 'UTR or other target input is required')
            self.add_error('cdnachoice', 'UTR or other target input is required')
        if not cleaned_data.get('psRobot') and not cleaned_data.get('tapir_fasta') and not cleaned_data.get('tapir_RNA') :
            self.add_error('psRobot', 'At least one program should be chosen')
            self.add_error('tapir_fasta', 'At least one program should be chosen')
            self.add_error('tapir_RNA', 'At least one program should be chosen')

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

        if self.cleaned_data.get('psRobot'):
            program_list.append("PSROBOT")
            param_list.append(self.cleaned_data.get("psRobot_par"))
        if self.cleaned_data.get('tapir_fasta'):
            program_list.append("TAPIR_FASTA")
            param_list.append(self.cleaned_data.get("tapir_fasta_par"))
        if self.cleaned_data.get('tapir_RNA'):
            program_list.append("TAPIR_HYBRID")
            param_list.append(self.cleaned_data.get('tapir_RNA_par'))
        program_string = ":".join(program_list)
        if mirfile:
            file_to_update = mirfile
            uploaded_file = str(file_to_update)
            mirfile = FS.save(uploaded_file, file_to_update)
        else:
            mirtext=self.cleaned_data.get("mirtext")
            content = ContentFile(mirtext)
            mirfile=FS.fileUpload.save("mirs.fa", content)
            FS.save()
        if utrfile:
            file_to_update = utrfile
            uploaded_file = str(file_to_update)
            utrfile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("utrtext"):
            utrtext = self.cleaned_data.get("utrtext")
            content = ContentFile(utrtext)
            utrfile=FS.fileUpload.save('utrs.fa', content)
            FS.save()
        elif self.cleaned_data.get("utrchoice"):
            utrfile = self.cleaned_data.get('utrchoice')
        else:
            utrfile = self.cleaned_data.get('cdnachoice')

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



