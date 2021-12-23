import datetime
import os
import urllib

from django import forms
from django.core.files.storage import FileSystemStorage
from django.http import Http404

from progress.models import JobStatus
from sRNAtoolboxweb.settings import BASE_DIR
from sRNAtoolboxweb.settings import MEDIA_ROOT
from utils.pipeline_utils import generate_uniq_id
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Field, HTML
from sRNAtoolboxweb.settings import MEDIA_ROOT, CONF, QSUB, BASE_DIR

class RemovedupForm(forms.Form):
    ifile = forms.FileField(label='Upload input file(Fasta file)', required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)
    string = forms.CharField(label='Provide a string of characters to be dropped out from the sequence names',
                             required=False)
    duplicates = forms.BooleanField(label='Remove also duplicate  SEQUENCES', required=False)

    def __init__(self, *args, **kwargs):
        super(RemovedupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "ifile",
                "url",
                "string",
                "duplicates",

                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))

            )
        )

    def clean(self):
        cleaned_data = super(RemovedupForm, self).clean()
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

    def create_call(self):

        pipeline_id = self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        ifile = self.cleaned_data.get("ifile")
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url = self.cleaned_data.get("url")
            extension = os.path.basename(url).split('.')[-1]
            dest = os.path.join(FS.location, os.path.basename(url))
            ifile, headers = urllib.request.urlretrieve(url, filename=dest)

        else:
            raise Http404

        name = pipeline_id + '_h_rd'
        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 #finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                )

        return 'qsub -v pipeline="helper",mode="rd",key="{pipeline_id}",outdir="{out_dir}",inputfile="{input_file}",string="{string}",remove="true",name="{name}" -N {job_name} {sh}'.format(
                pipeline_id=pipeline_id,
                out_dir=out_dir,
                input_file=os.path.join(FS.location, ifile),
                string=self.cleaned_data.get("string"),
                name=name,
                job_name=name,
                sh= os.path.join(BASE_DIR+ '/core/bash_scripts/run_helper_remove_duplicates.sh')
            ), pipeline_id

class RemovedupForm2(forms.Form):
    ifile = forms.FileField(label='Upload input file(Fasta file)', required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)


    duplicates = forms.BooleanField(label='Remove duplicate  SEQUENCES too', required=False)
    paste_IDs = forms.BooleanField(label='Merge IDs from duplicate SEQUENCES', required=False)
    string = forms.CharField(label='Manipulate the sequences names (remove certain string)',
                             required=False)

    def __init__(self, *args, **kwargs):
        super(RemovedupForm2, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "ifile",
                "url",
                "duplicates",
                "paste_IDs",
                "string",

                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))

            )
        )

    def clean(self):
        cleaned_data = super(RemovedupForm2, self).clean()
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

    def create_call(self):

        pipeline_id = self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        ifile = self.cleaned_data.get("ifile")
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url = self.cleaned_data.get("url")
            extension = os.path.basename(url).split('.')[-1]
            dest = os.path.join(FS.location, os.path.basename(url))
            ifile, headers = urllib.request.urlretrieve(url, filename=dest)

        else:
            raise Http404

        name = pipeline_id + '_h_rd'
        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 #finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                 outdir=out_dir
                                )
        config_location = os.path.join(out_dir, "conf.txt")
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': config_location,
            'type': 'helper'
        }
        if self.cleaned_data.get("paste_IDs"):
            mode = "RDG"
        else:
            mode = "RD"
        rd_string = " "
        if self.cleaned_data.get("duplicates"):
           rd_string = "removeDupSeq=true\n"

        with open(config_location, "w+") as file:
            file.write("input=" + os.path.join(out_dir, ifile) + "\n")
            file.write("mode=" + mode + "\n")
            file.write("output=" + out_dir + "\n")
            file.write("string=" + self.cleaned_data.get("string") + "\n")
            file.write(rd_string)
        import json
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)

        if QSUB:
            return 'qsub -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id

class ExtractForm(forms.Form):
    ifile = forms.FileField(label='Upload input file(Fasta file)', required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)
    string = forms.CharField(label='Provide a string the characters used to select the sequences',
                             required=True)

    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "ifile",
                "url",
                "string",

                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))



            )
        )
    def clean(self):
        cleaned_data = super(ExtractForm, self).clean()
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

    def create_call(self):

        pipeline_id = self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        ifile = self.cleaned_data.get("ifile")
        url = self.cleaned_data.get("url")
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url = self.cleaned_data.get("url")
            extension = os.path.basename(url).split('.')[-1]
            dest = os.path.join(FS.location, os.path.basename(url))
            ifile, headers = urllib.request.urlretrieve(url, filename=dest)

        else:
            raise Http404

        name = pipeline_id + '_h_extract'

        config_location=os.path.join(out_dir,"conf.txt")
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': config_location,
            'type': 'helper'
        }

        with open(config_location, "w+") as file:
            file.write("input="+os.path.join(out_dir,ifile)+"\n")
            file.write("mode=FA\n")
            file.write("output="+out_dir+"\n")
            file.write("search="+self.cleaned_data.get("string")+"\n")
        import json
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 #finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                 outdir=out_dir,
                                )
        if QSUB:
            return 'qsub -q fast -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id
        #return pipeline_id, "touch /opt/sRNAtoolbox/sRNAtoolboxweb/upload/S3LLSLVRW36VI06/ele.txt"
        #return pipeline_id, "runPipelines " +configuration_file_path

class EnsemblForm(forms.Form):
    ifile = forms.FileField(label='Upload input file(Ensembl file)', required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)

    def __init__(self, *args, **kwargs):
        super(EnsemblForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "ifile",
                "url",
                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))))

    def clean(self):
        cleaned_data = super(EnsemblForm, self).clean()
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

    def create_call(self):

        pipeline_id = self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        ifile = self.cleaned_data.get("ifile")
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url = self.cleaned_data.get("url")
            extension = os.path.basename(url).split('.')[-1]
            dest = os.path.join(FS.location, os.path.basename(url))
            ifile, headers = urllib.request.urlretrieve(url, filename=dest)

        else:
            raise Http404

        name = pipeline_id + '_h_ens'
        config_location = os.path.join(out_dir, "conf.txt")
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': config_location,
            'type': 'helper'
        }
        with open(config_location, "w+") as file:
            file.write("input=" + os.path.join(out_dir, ifile) + "\n")
            file.write("mode=ENS\n")
            file.write("output=" + out_dir + "\n")
        import json
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)
        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 #finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                 outdir=FS.location,
                                )

        if QSUB:
            return 'qsub -q fast -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id

class NcbiForm(forms.Form):
    ifile = forms.FileField(label='Upload input file(NCBI file)', required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)

    def __init__(self, *args, **kwargs):
        super(NcbiForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "ifile",
                "url",

                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))))

    def clean(self):
        cleaned_data = super(NcbiForm, self).clean()
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

    def create_call(self):

        pipeline_id = self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        ifile = self.cleaned_data.get("ifile")
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url = self.cleaned_data.get("url")
            extension = os.path.basename(url).split('.')[-1]
            dest = os.path.join(FS.location, os.path.basename(url))
            ifile, headers = urllib.request.urlretrieve(url, filename=dest)

        else:
            raise Http404

        name = pipeline_id + '_h_ncbi'
        config_location = os.path.join(out_dir, "conf.txt")
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': config_location,
            'type': 'helper'
        }
        with open(config_location, "w+") as file:
            file.write("input=" + os.path.join(out_dir, ifile) + "\n")
            file.write("mode=NCBI\n")
            file.write("output=" + out_dir + "\n")
        import json
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)
        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                 outdir=FS.location,
                                 )
        if QSUB:
            return 'qsub -q fast -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id

class RnacentralForm(forms.Form):
    species = forms.CharField(label='Provide a Species Name  (Must be Scientific Name):',
                             required=False)
    taxonomy = forms.CharField(label='Or provide a Taxonomy Name :',
                             required=False)

    def __init__(self, *args, **kwargs):
        super(RnacentralForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "species",
                "taxonomy",
                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))))

    def clean(self):
        cleaned_data = super(RnacentralForm, self).clean()
        if not cleaned_data.get('species') and not cleaned_data.get('taxonomy'):
            self.add_error('species', 'One of these two fields is required')
            self.add_error('taxonomy', 'One of these two fields is required')
        if cleaned_data.get('species') and cleaned_data.get('taxonomy'):
            self.add_error('species', 'Choose either species or taxon')
            self.add_error('taxonomy', 'Choose either species or taxon')
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
        name = pipeline_id + '_h_rnac'
        species=self.cleaned_data.get('species')
        taxonomy=self.cleaned_data.get('taxonomy')
        name = pipeline_id + '_h_central'
        config_location = os.path.join(out_dir, "conf.txt")
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': config_location,
            'type': 'helper'
        }

        with open(config_location, "w+") as file:
            file.write("input=" + os.path.join(CONF["db"],"dbs/rnacentral_active.fasta" ) + "\n")
            file.write("taxonFile="+os.path.join(CONF["db"],"dbs/taxonomy_full.txt" ) + "\n")
            file.write("mode=RNAC \n")
            file.write("output=" + out_dir + "\n")
            if self.cleaned_data.get('species'):
                species = species.replace(" ", "_")
                file.write("species=" + species + "\n")
            elif self.cleaned_data.get('taxonomy'):
                taxonomy = taxonomy.replace(" ", "_")
                file.write("taxon="+taxonomy+"\n")

        import json
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)

        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files= " ",
                                 modules_files="",
                                 pipeline_type="helper",
                                 outdir=FS.location,
                                 )
        if QSUB:
            return 'qsub -q fast -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id

class TrnaparserForm(forms.Form):
    species = forms.CharField(label='Provide a Species Name  (Must be Scientific Name):',
                              required=True)

    def __init__(self, *args, **kwargs):
        super(TrnaparserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "species",
                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))))

    def clean(self):
        cleaned_data = super(TrnaparserForm, self).clean()
        if not cleaned_data.get('species') :
            self.add_error('species', 'This field is required')
        return cleaned_data

    def generate_id(self):
        is_new = True
        while is_new:
            pipeline_id = generate_uniq_id()
            if not JobStatus.objects.filter(pipeline_key=pipeline_id):
                return pipeline_id

    def create_call(self):

        species= self.cleaned_data.get('species').replace(" ", "")
        pipeline_id = self.generate_id()
        FS = FileSystemStorage()
        FS.location = os.path.join(MEDIA_ROOT, pipeline_id)
        os.system("mkdir " + FS.location)
        out_dir = FS.location
        name = pipeline_id + '_h_trna'
        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 #all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                 )

        return 'qsub -v pipeline="helper",mode="trna",key="{pipeline_id}",outdir="{out_dir}",species="{species}",name="{name}" -N {job_name} {sh}'.format(
                pipeline_id=pipeline_id,
                out_dir=out_dir,
                species=species.replace(" ", ""),
                name=name,
                job_name=name,
                sh=os.path.join(BASE_DIR + '/core/bash_scripts/run_helper_trna.sh')
            )

class FasubsetForm(forms.Form):
    ifile = forms.FileField(label='Upload input file(Fasta file)', required=False)
    url = forms.URLField(label='Or provide a URL for big files (recommended!)', required=False)
    faids = forms.CharField(label="Paste the fasta IDs you want to subset from file ", widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(FasubsetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                "ifile",
                "url",
                HTML("""<br>"""),
                "faids",

                HTML("""<br>"""),
                ButtonHolder(
                    # Submit('submit', 'RUN', css_class='btn btn-primary', onclick="alert('Neat!'); return true")
                    Submit('submit', 'RUN', css_class='btn btn-primary'))))
    def clean(self):
        cleaned_data = super(FasubsetForm, self).clean()
        if not cleaned_data.get('ifile') and not cleaned_data.get('url'):
            self.add_error('ifile', 'One of these two fields is required')
            self.add_error('url', 'One of these two fields is required')
        if not cleaned_data.get('faids'):
            self.add_error('faids', 'This field is required')
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
        if ifile:
            file_to_update = ifile
            uploaded_file = str(file_to_update)
            ifile = FS.save(uploaded_file, file_to_update)
        elif self.cleaned_data.get("url"):
            url = self.cleaned_data.get("url")
            extension = os.path.basename(url).split('.')[-1]
            dest = os.path.join(FS.location, os.path.basename(url))
            ifile, headers = urllib.request.urlretrieve(url, filename=dest)
        else:
            raise Http404
        listfile = "listFile.txt"
        with open(os.path.join(out_dir, listfile), "w+") as file:
            file.write(self.cleaned_data.get("faids"))
        name = pipeline_id + '_h_fasubset'
        config_location = os.path.join(out_dir, "conf.txt")
        configuration = {
            'pipeline_id': pipeline_id,
            'out_dir': out_dir,
            'name': name,
            'conf_input': config_location,
            'type': 'helper'
        }
        with open(config_location, "w+") as file:
            file.write("inputList=" + os.path.join(out_dir, listfile) + "\n")
            file.write("inputFasta=" + os.path.join(out_dir, ifile) + "\n")
            file.write("outBase=" + out_dir + "\n")

        import json
        configuration_file_path = os.path.join(out_dir, 'conf.json')
        with open(configuration_file_path, 'w') as conf_file:
            json.dump(configuration, conf_file, indent=True)
        JobStatus.objects.create(job_name=name, pipeline_key=pipeline_id, job_status="not launched",
                                 start_time=datetime.datetime.now(),
                                 # finish_time=datetime.time(0, 0),
                                 all_files=ifile,
                                 modules_files="",
                                 pipeline_type="helper",
                                 outdir=FS.location,
                                 )
        if QSUB:
            return 'qsub -q fast -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
                configuration_file_path=configuration_file_path,
                job_name=name,
                sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh')), pipeline_id