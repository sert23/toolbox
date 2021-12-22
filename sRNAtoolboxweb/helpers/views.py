# Create your views here.
import os
import urllib

from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic import FormView

from helpers.forms import ExtractForm, NcbiForm
from helpers.forms import RemovedupForm2, EnsemblForm, RnacentralForm, TrnaparserForm, FasubsetForm
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import make_dir
from django.conf import settings


FS = FileSystemStorage("/shared/sRNAtoolbox/webData")


def ncbi(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with ncbi helper
    """

    

    return render(request, 'helpers.html', {"tool": "NCBI Parser", "tool_url": "ncbiparser", "input": "NCBI file"})


def ens(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with ens helper
    """
    return render(request, 'helpers.html',
                  {"tool": "Ensembl Parser", "tool_url": "ensemlparser", "input": "Ensembl file"})


def rnac(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with rnac helper
    """
    return render(request, 'helpers.html',
                  {"tool": "RNA Central Parser", "tool_url": "rnacentralparser", "species": True, "tax": True})


def trna(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with trna helper
    """
    return render(request, 'helpers.html', {"tool": "Genomic tRNA Parser", "tool_url": "trnaparser", "species": True})


def rd(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with Remove Duplicate helper
    """
    return render(request, 'helpers.html', {"tool": "Remove duplicates from a fasta file",
                                            "tool_url": "removedup", "input": "Fasta file", "duplicates": True})


def extract(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with extract sequences helper
    """
    return render(request, 'helpers.html', {"tool": "Extract Sequences from a fasta file",
                                            "tool_url": "extract", "input": "Fasta file", "extract": True})

def fasubset(requestFasubset):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with trna helper
    """
    return render(requestFasubset, 'helpers.html', {"tool": "Fasta subset", "tool_url": "fasubset"})



def run(request, tool):
    pipeline_id = pipeline_utils.generate_uniq_id()
    species = None
    taxonomy = None
    ifile = None
    string = None
    remove = "false"

    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    fdw = open(os.path.join(FS.location,"error.txt"),"w")
    if tool == "removedup" or tool == "extract":

        if "ifile" in request.FILES:
            file_to_update = request.FILES['ifile']
            uploaded_file = str(file_to_update)
            if str(file_to_update).split(".")[1] not in ["fa", "fasta", "gz"]:
                return render(request, "error_page.html", {"errors": [
                    'File extension must be: "fa" or "fasta".' + str(file_to_update).split(".")[
                        1] + '" found']})
            FS.save(uploaded_file, file_to_update)
            ifile = os.path.join(FS.location, uploaded_file)

        elif request.POST["url"].replace(" ", "") != "":
            url_input = request.POST["url"]
            dest = os.path.join(FS.location, os.path.basename(url_input))
            handler = urllib.URLopener()
            handler.retrieve(url_input, dest)
            ifile = dest


        else:
            return render(request, "error_page.html", {"errors": ["URL of file must be provided"]})

        string = request.POST["string"]



        if tool == "removedup":
            if string.replace(" ", "") == "":
                return render(request, "error_page.html", {
                    "errors": ["A string of characters must be provided to be drop out from the sequence names"]})

            if "duplicates" in request.POST:
                remove = "true"

            os.system(
                'qsub -v pipeline="helper",mode="rd",key="' + pipeline_id + '",outdir="' + FS.location +
                '",inputfile="' + ifile + '",string="' + string + '",remove="' + remove + '",name="'
                + pipeline_id + '_h_rd' + '" -N ' + pipeline_id +
                '_h_rd /shared/sRNAtoolbox/core/bash_scripts/run_helper_remove_duplicates.sh')


        else:
            if string.replace(" ", "") == "":
                return render(request, "error_page.html",
                              {"errors": ["A string of characters must be provided to select the sequences:"]})

            os.system(
                'qsub -v pipeline="helper",mode="extract",key="' + pipeline_id + '",outdir="' + FS.location +
                '",inputfile="' + ifile + '",string="' + string + '",name="'
                + pipeline_id + '_h_extract' + '" -N ' + pipeline_id +
                '_h_extract /shared/sRNAtoolbox/core/bash_scripts/run_helper_extract.sh')

            fdw.write('qsub -v pipeline="helper",mode="extract",key="' + pipeline_id + '",outdir="' + FS.location +
                '",inputfile="' + ifile + '",string="' + string + '",name="'
                + pipeline_id + '_h_extract' + '" -N ' + pipeline_id +
                '_h_extract /shared/sRNAtoolbox/core/bash_scripts/run_helper_extract.sh')





    if tool == "ncbiparser" or tool == "ensemlparser":

        if "ifile" in request.FILES:
            file_to_update = request.FILES['ifile']
            uploaded_file = str(file_to_update)
            FS.save(uploaded_file, file_to_update)
            ifile = os.path.join(FS.location, uploaded_file)

        elif request.POST["url"].replace(" ", "") != "":
            url_input = request.POST["url"]
            dest = os.path.join(FS.location, os.path.basename(url_input))
            handler = urllib.URLopener()
            handler.retrieve(url_input, dest)
            ifile = dest

        else:
            return render(request, "error_page.html", {"errors": ["URL of file must be provided"]})

        if tool == "ncbiparser":
            os.system(
                'qsub -v pipeline="helper",mode="ncbi",key="' + pipeline_id + '",outdir="' + FS.location +
                '",inputfile="' + ifile + '",name="' + pipeline_id + '_h_ncbi' + '" -N ' + pipeline_id +
                '_h_ncbi /shared/sRNAtoolbox/core/bash_scripts/run_helper_ncbi.sh')
        else:
            os.system(
                'qsub -v pipeline="helper",mode="ensembl",key="' + pipeline_id + '",outdir="' + FS.location +
                '",inputfile="' + ifile + '",name="' + pipeline_id + '_h_ens' + '" -N ' + pipeline_id +
                '_h_ens /shared/sRNAtoolbox/core/bash_scripts/run_helper_ensembl.sh')

    if tool == "rnacentralparser":
        species = request.POST["species"]
        if species.replace(" ", "") == "":
            taxonomy = request.POST["taxonomy"]
            taxonomy = taxonomy.replace(" ", "_")
            os.system(
                'qsub -v pipeline="helper",mode="rnacentral",key="' + pipeline_id + '",outdir="' + FS.location +
                '",taxon="' + taxonomy + '",name="' + pipeline_id + '_h_rnac' + '" -N ' + pipeline_id +
                '_h_rca /shared/sRNAtoolbox/core/bash_scripts/run_helper_rnacentral_taxon.sh')
        else:
            species = species.replace(" ", "_")
            fdw.write('qsub -v pipeline="helper",mode="rnacentral",key="' + pipeline_id + '",outdir="' + FS.location +
                '",species="' + species + '",name="' + pipeline_id + '_h_rnac' + '" -N ' + pipeline_id +
                '_h_rca /shared/sRNAtoolbox/core/bash_scripts/run_helper_rnacentral.sh')
            os.system(
                'qsub -v pipeline="helper",mode="rnacentral",key="' + pipeline_id + '",outdir="' + FS.location +
                '",species="' + species + '",name="' + pipeline_id + '_h_rnac' + '" -N ' + pipeline_id +
                '_h_rca /shared/sRNAtoolbox/core/bash_scripts/run_helper_rnacentral.sh')


    if tool == "trnaparser":
        species = request.POST["species"]
        if species.replace(" ", "") == "":
            return render(request, "error_page.html", {"errors": ['Species can\'t be empty']})
        else:
            species = species.replace(" ", "_")
            os.system(
                'qsub -v pipeline="helper",mode="trna",key="' + pipeline_id + '",outdir="' + FS.location +
                '",species="' + species + '",name="' + pipeline_id + '_h_trna' + '" -N ' + pipeline_id +
                '_h_trna /shared/sRNAtoolbox/core/bash_scripts/run_helper_trna.sh')

    if tool == "fasubset":

        if "ifile" in request.FILES:
            file_to_update = request.FILES['ifile']
            uploaded_file = str(file_to_update)
            FS.save(uploaded_file, file_to_update)
            ifile = os.path.join(FS.location, uploaded_file)

        elif request.POST["url"].replace(" ", "") != "":
            url_input = request.POST["url"]
            dest = os.path.join(FS.location, os.path.basename(url_input))
            handler = urllib.URLopener()
            handler.retrieve(url_input, dest)
            ifile = dest

        else:
            return render(request, "error_page.html", {"errors": ["URL of file must be provided"]})

        os.system(
                'qsub -v pipeline="helper",mode="fasubset",key="' + pipeline_id + '",outdir="' + FS.location +
                '",inputfile="' + ifile + '",name="' + pipeline_id + '_h_fasubset' + '" -N ' + pipeline_id +
                '_h_ncbi /shared/sRNAtoolbox/core/bash_scripts/run_helper_ncbi.sh')
    #return redirect("/srnatoolbox/jobstatus/helper/?id=" + pipeline_id)
    return redirect("/srnatoolbox_dev/")


def result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        assert isinstance(new_record, JobStatus)

        # check if fasubset and redirect to its results
        if 'h_fasubset' in new_record.job_name:
          print (job_id)
          return redirect(reverse_lazy('result_Fasubset') + '?id=' + job_id)      
          #return redirect(reverse_lazy('result_Fasubset', kwargs={"id": job_id}))
            
        results = {}
        results["jobID"]=new_record.pipeline_key
        if new_record.job_status == "Finished":
            fd = open(os.path.join(new_record.outdir, "logFile.txt"))
            backvalue = "result"
            info_string = ""
            for line in fd:
                if "BACKVALUE" in line:
                    value = line.replace("\n", "").split(" ")[-1]
                    backvalue = value
                if "INFO" in line or "SUCCESS" in line:
                    jumpline = line + "\n"
                    info_string += line

            zip_file = os.path.join(backvalue + ".zip").split("/")[-1]
            if os.path.exists(backvalue+".zip"):
                #results["result"] = os.path.join(new_record.outdir ,"mature.txt.zip")
                results["result"] = os.path.join(new_record.pipeline_key,zip_file)
                results["info"] = info_string


            return render(request, 'helper_result.html', results)

        else:
            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))
    else:
        return redirect(settings.SUB_SITE)

def result_Fasubset(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        assert isinstance(new_record, JobStatus)

        results = {}
        results["jobID"]=new_record.pipeline_key
        if new_record.job_status == "Finished":
            fd = open(os.path.join(new_record.outdir, "log.txt"))
            backvalue = "result"
            info_string = ""
            for line in fd:
                if "Filtered fastafile" in line:
                  value = line.replace("\n", "").split(",")[-1]
                  backvalue = value
                if "File: ID mappings" in line:
                  mappings = line.replace("\n", "").split(",")[-1]
                if "ERROR" in line:
                    jumpline = line + "\n"
                    info_string += line
#            zip_file = os.path.join(backvalue + ".zip").split("/")[-1]
 #           if os.path.exists(backvalue+".zip"):
                #results["result"] = os.path.join(new_record.outdir ,"mature.txt.zip")
#                results["result"] = os.path.join(new_record.pipeline_key,zip_file)
                results["result"] = os.path.join(new_record.pipeline_key,backvalue)
                results["mappings"] = os.path.join(new_record.pipeline_key,mappings.split("/")[-1])
                results["info"] = info_string

            return render(request, 'helpers/helper_result_fasubset.html', results)
        else:
            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))
    else:
        return redirect(settings.SUB_SITE)


class RemoveDup(FormView):
    #template_name = 'helpers/helpers_extract.html'
    template_name = 'helpers/helpers_removedup.html'
    #form_class = ExtractForm
    form_class = RemovedupForm2

    success_url = reverse_lazy("removedup")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('helper') + '?id=' + pipeline_id
        return super(RemoveDup, self).form_valid(form)

class Extract(FormView):
    template_name = 'helpers/helpers_extract.html'
    form_class = ExtractForm

    success_url = reverse_lazy("extract")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call,pipeline_id = form.create_call()
        #os.system("touch /opt/sRNAtoolbox/sRNAtoolboxweb/upload/HYE70LP0YVFX5DQ/lelo.txt")
        #os.system("source /opt/venv/sRNAtoolbox2019/bin/activate;"+"touch /opt/sRNAtoolbox/sRNAtoolboxweb/upload/HYE70LP0YVFX5DQ/hello.txt;echo "+call+"|qsub")
        # with open('/opt/sRNAtoolbox/sRNAtoolboxweb/upload/HYE70LP0YVFX5DQ/hello.txt', 'a') as the_file:
        #     the_file.write(call)
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('helper') + '?id=' + pipeline_id
        return super(Extract, self).form_valid(form)

class Ensembl(FormView):
    template_name = 'helpers/helpers_ensembl.html'
    #template_name = 'helpers/helpers_extract.html'
    form_class = EnsemblForm

    success_url = reverse_lazy("ensembl")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        # with open('/opt/sRNAtoolbox/sRNAtoolboxweb/upload/HYE70LP0YVFX5DQ/hello.txt', 'a') as the_file:
        #     the_file.write(call)
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('helper') + '?id=' + pipeline_id
        return super(Ensembl, self).form_valid(form)

class NCBI(FormView):
    template_name = 'helpers/helpers_ncbi.html'
    form_class = NcbiForm

    success_url = reverse_lazy("ncbi")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('helper') + '?id=' + pipeline_id
        return super(NCBI, self).form_valid(form)

class RNAcentral(FormView):
    template_name = 'helpers/helpers_rnacentral.html'
    form_class = RnacentralForm

    success_url = reverse_lazy("rnacentral")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('helper') + '?id=' + pipeline_id
        return super(RNAcentral, self).form_valid(form)

class Trna(FormView):
    template_name = 'helpers/helpers_trnaparser.html'
    form_class =TrnaparserForm

    success_url = reverse_lazy("trna")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('helper') + '?id=' + pipeline_id
        return super(Trna, self).form_valid(form)

class Fasubset(FormView):
    template_name = 'helpers/helpers_fasubset.html'
    form_class = FasubsetForm

    success_url = reverse_lazy("fasubset")
    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('result_Fasubset') + '?id=' + pipeline_id
        return super(Fasubset, self).form_valid(form)