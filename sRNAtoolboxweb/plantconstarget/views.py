# Create your views here.
import datetime
import itertools
import os

import django_tables2 as tables
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from sRNAtoolboxweb.settings import MEDIA_ROOT, CONF, QSUB, BASE_DIR, MEDIA_URL
from django.views.generic import FormView
from django.core.urlresolvers import reverse_lazy
from plantconstarget.forms import PMirconsForm

from FileModels.TargetConsensusParser import TargetConsensusParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import make_dir
#import forms

counter = itertools.count()

FS = FileSystemStorage("/shared/sRNAtoolbox/webData")
TOOLS = ["TS", "MIRANDA", "PITA", "PSROBOT", "TAPIR_FASTA", "TAPIR_HYBRID"]


class TableStatic(tables.Table):
    """
    Class to serialize table of results
    """

    class Meta:
        orderable = False
        attrs = {'class': 'table table-striped',
                 "id": lambda: "table_%d" % next(counter)}
        empty_text = "Results not found!"
        order_by = ("name",)

class TableResult(tables.Table):
    """
    Class to serialize table of results
    """

    class Meta:
        orderable = False
        attrs = {'class': 'table table-striped table-bordered table-hover dataTable no-footer',
                 "id": lambda: "table_%d" % next(counter)}
        empty_text = "Results not found!"
        order_by = ("name",)


def define_table(columns, typeTable, plants=False):
    """
    :param columns: Array with names of columns to show
    :return: a class of type TableResults
    """

    attrs = dict((c, tables.Column()) for c in columns if c != "mRNA")

    if not plants:
        attrs2 = dict((c, tables.TemplateColumn('<a href="http://www.ncbi.nlm.nih.gov/nuccore/{{record.mRNA}}">{{record.mRNA}}</a>')) for c in columns if c == "mRNA")
    else:
        attrs2 = dict((c, tables.TemplateColumn('<a href="http://plants.ensembl.org/Multi/Search/Results?q={{record.mRNA}}">{{record.mRNA}}</a>')) for c in columns if c == "mRNA")
    attrs.update(attrs2)
    if typeTable == "TableResult":
        attrs['Meta'] = type('Meta', (),
                             dict(attrs={'class': 'table table-striped table-bordered table-hover dataTable no-footer',
                                         "id": lambda: "table_%d" % next(counter)},
                                  ordenable=False,
                                  empty_text="Results not found!",
                                  order_by=("name",)))
    else:
        attrs['Meta'] = type('Meta', (),
                             dict(attrs={'class': 'table table-striped',
                                         "id": "notformattable"},
                                  ordenable=False,
                                  empty_text="Results not found!",
                                  order_by=("name",)))



    klass = type('TableResult', (tables.Table,), attrs)
    return klass


class Result():
    """
    Class to manage tables results and meta-info
    """

    def __init__(self, name, table):
        self.name = name.capitalize()
        self.content = table
        self.id = name.replace(" ", "_")


def input(request):
    return render(request, 'miRNAtarget.html', {})

def run(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)

    miRNA_file = ""
    utr_file = ""
    program_list = []
    parameters_list = []

    if "miRNA_file" in request.FILES:
        file_to_update = request.FILES['miRNA_file']
        uploaded_file = str(file_to_update).replace(" ", "").replace(")", "").replace("(", "")
        if str(file_to_update).split(".")[1] not in ["fa", "fasta", "mfasta", "mfa", "txt"]:
            return render(request, "error_page.html",  {"errors": ['miRNAs file extension must be: fa, fasta, mfasta, mfa or txt. ".'+str(file_to_update).split(".")[1]+'" found']})
        FS.save(uploaded_file, file_to_update)
        miRNA_file = os.path.join(FS.location, uploaded_file)

    if "utr_file" in request.FILES:
        file_to_update = request.FILES['utr_file']
        uploaded_file = str(file_to_update).replace(" ", "").replace(")", "").replace("(", "")
        if str(file_to_update).split(".")[1] not in ["fa", "fasta", "mfasta", "mfa", "txt"]:
            return render(request, "error_page.html",  {"errors": ['UTRs file extension must be: fa, fasta, mfasta, mfa or txt. ".'+str(file_to_update).split(".")[1]+'" found']})
        FS.save(uploaded_file, file_to_update)
        utr_file = os.path.join(FS.location, uploaded_file)


    if not ("miRNA_file" in request.FILES and "utr_file" in request.FILES):
        return render(request, "error_page.html",  {"errors": ["miRNAs file and UTR file should be provided"]})

    for program in request.POST.getlist("programs"):
        program_list.append(program)

    program_string = ":".join(program_list)

    if len(program_list) < 1:
        return render(request, "error_page.html",  {"errors": ["At least one program should be chosen"]})

    for i, Parameter in enumerate(request.POST.getlist("Parameters")):
        if TOOLS[i] in program_list:
            parameters_list.append(Parameter)

    parameter_string = ":".join(parameters_list).replace("-", "55-55")

    if parameter_string == "":
        parameter_string = "".join([":" for i in program_list])



    outdir = FS.location

    os.system('qsub -v pipeline="mirconstarget",program_string="' + program_string + '",parameter_string="' + parameter_string + '",key="' + pipeline_id + '",outdir="' + outdir + '",miRNA_file="' + miRNA_file + '",utr_file="' + utr_file +
              '",name="' + pipeline_id + '_mirconstarget"' + ' -N ' + pipeline_id + '_mirconstarget /shared/sRNAtoolbox/core/bash_scripts/run_mirnatarget.sh')


    return redirect("/srnatoolbox/jobstatus/mirconstarget/?id=" + pipeline_id)

def result(request):

    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)


        results = {}

        if new_record.job_status == "Finished":

            plants = False
            min = 2


            results["parameters"] = new_record.parameters

            try:
                for param in new_record.parameters.split("\n"):
                    if "Programs:" in param:
                        min = len(param.split(" ")[1].split(":"))
            except:
                print("do nothing")

            try:
                if "PSROBOT" in new_record.parameters or "TAPIR_FASTA" in new_record.parameters or "TAPIR_HYBRID" in new_record.parameters:
                    plants = True
                    min = 1
            except:
                print("do nothing")

            parser = TargetConsensusParser(new_record.consensus_file)
            list_d = [obj for obj in parser.get_by_n(min)]
            id = "table"
            try:
                header = list_d[0].get_sorted_attr()
                # r = Result(id, define_table(header, 'TableResult', plants)(list_d))
                r = Result(id, define_table(header, 'TableResult', plants)(list_d))
                # results[id] = Result(id, define_table(["Results"], 'TableResult', plants)(
                #     [{"Results": "Results not found!"}]))
                results[id] = r
            except:
                results[id] = Result(id, define_table(["Results"], 'TableResult', plants)([{"Results": "Results not found!"}]))

            all_files = [x for x in os.listdir(new_record.outdir) if os.path.isfile(os.path.join(new_record.outdir, x))]
            files_to_serve = [x for x in all_files if (x.startswith("multipleTargets") or x.startswith("perTranscript") or x.startswith("positionalConsensus"))]
            init_url = new_record.outdir.replace(MEDIA_ROOT, MEDIA_URL)
            positional_files = [ [x, os.path.join(init_url, x)] for x in files_to_serve ]


            results["zip"] = "/".join(new_record.zip_file.split("/")[-2:])
            #return render(request, "mirconstarget_result.html", results)
            try:
                results["parameters"] = new_record.parameters
            except:
                pass
            results["id"] = job_id
            results["date"] = new_record.start_time + datetime.timedelta(days=15)
            results["positional_files"] = positional_files
            return render(request, "mirconstarget_result.html", results)

        else:
            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))

    else:
        return redirect(reverse_lazy('MIRCONS'))


def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)

    os.system('cp /shared/sRNAtoolbox/testData/rno_miR.fa ' + FS.location)
    os.system('cp /shared/sRNAtoolbox/testData/rn5_refSeq_3utr.fa ' + FS.location)

    miRNA_file = os.path.join(FS.location, "rno_miR.fa")
    utr_file = os.path.join(FS.location, "rn5_refSeq_3utr.fa")

    outdir = FS.location

    os.system('qsub -v pipeline="mirconstarget",program_string="' + "TS:MIRANDA" + '",key="' + pipeline_id + '",outdir="' + outdir + '",miRNA_file="' + miRNA_file +
              '",utr_file="' + utr_file +
              '",name="' + pipeline_id + '_mirconstarget"' + ' -N ' + pipeline_id + '_mirconstarget /shared/sRNAtoolbox/core/bash_scripts/run_mirnatarget.sh')



    return redirect("/srnatoolbox/jobstatus/mirconstarget/?id=" + pipeline_id)

class PMirConsTarget(FormView):
    template_name = 'pmiRNAtarget.html'
    form_class = PMirconsForm
    success_url = reverse_lazy("MIRCONS")

    #success_url = reverse_lazy("mirconstarget")


    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.clean()
        call, pipeline_id = form.create_call()
        self.success_url = reverse_lazy('mirconstarget') + '?id=' + pipeline_id


        print(call)
        os.system("source /opt/venv/sRNAtoolbox2019/bin/activate")
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()

        return super(PMirConsTarget, self).form_valid(form)




# class Bench(FormView):
#     template_name = 'bench.html'
#     form_class = sRNABenchForm
#     success_url = reverse_lazy("BENCH")
#
#     def post(self, request, *args, **kwargs):
#         request.POST._mutable = True
#         request.POST['species'] = request.POST['species_hidden'].split(',')
#         request.POST._mutable = False
#         return super(Bench, self).post(request, *args, **kwargs)
#
#     def form_valid(self, form):
#         # This method is called when valid form data has been POSTed.
#         # It should return an HttpResponse.
#         call, pipeline_id = form.create_call()
#         self.success_url = reverse_lazy('srnabench') + '?id=' + pipeline_id
#
#         print(call)
#         os.system(call)
#         js = JobStatus.objects.get(pipeline_key=pipeline_id)
#         js.status.create(status_progress='sent_to_queue')
#         js.job_status = 'sent_to_queue'
#         js.save()
#         return super(Bench, self).form_valid(form)
