# Create your views here.

# Create your views here.
import datetime
import itertools
import os

import django_tables2 as tables
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from FileModels.TargetConsensusParser import TargetConsensusParser
from FileModels.sRNAfuncParsers import EdaFile
from FileModels.speciesParser import SpeciesParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import make_dir
from django.views.generic import FormView
from django.core.urlresolvers import reverse_lazy
from miRNAfuncTargets.forms import MirFuncForm
from progress.models import JobStatus
from utils import pipeline_utils


counter = itertools.count()
TOOLS = ["TS", "MIRANDA", "PITA", "PSROBOT", "TAPIR_FASTA", "TAPIR_HYBRID"]

CONF = settings.CONF
#CONF = json.load(file("/shared/sRNAtoolbox/sRNAtoolbox.conf"))
SPECIES_PATH = CONF["species"]
FS = FileSystemStorage(CONF["sRNAtoolboxSODataPath"])

class TableResultenrich(tables.Table):
    """
    Class to serialize table of results
    """
    go_id = tables.Column("GO")
    go_term = tables.Column("functional annotation")
    Proteins_inBackGround = tables.Column("background (positive)")
    number_protein = tables.Column("targets (positive)")
    notInGeneList = tables.Column("targets (negative)")
    pvalue = tables.Column("p-value")
    FDR = tables.Column("FDR")
    RE = tables.Column("RE")
    type = tables.Column("type")

    class Meta:
        orderable = False
        attrs = {'class': 'table table-striped table-bordered table-hover dataTable no-footer',
                 "id": lambda: "table_%d" % next(counter)}
        empty_text = "Results not found!"
        order_by = ("target",)


class TableResultModule(tables.Table):
    """
    Class to serialize table of module results
    """
    go_id = tables.Column("GO")
    go_term = tables.Column("functional annotation")
    Proteins_inBackGround = tables.Column("background (positive)")
    number_protein = tables.Column("targets (positive)")
    notInGeneList = tables.Column("targets (negative)")
    pvalue = tables.Column("p-value")
    FDR = tables.Column("FDR")
    RE = tables.Column("RE")
    type = tables.Column("type")
    module = tables.Column("miRNA Module")

    class Meta:
        orderable = False
        attrs = {'class': 'table table-striped table-bordered table-hover dataTable no-footer',
                 "id": lambda: "table_%d" % next(counter)}
        empty_text = "Results not found!"
        order_by = ("target",)


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
        attrs2 = dict((c, tables.TemplateColumn(
            '<a href="http://www.ncbi.nlm.nih.gov/nuccore/{{record.mRNA}}">{{record.mRNA}}</a>')) for c in columns if
                      c == "mRNA")
    else:
        attrs2 = dict((c, tables.TemplateColumn(
            '<a href="http://plants.ensembl.org/Multi/Search/Results?q={{record.mRNA}}">{{record.mRNA}}</a>')) for c in
                      columns if c == "mRNA")
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
    species_file = SpeciesParser(SPECIES_PATH)
    array_species = species_file.parse()
    all_species = []

    for species in array_species:
        if species.full:
            all_species.append((",".join([species.db, species.sp_class]), species.scientific))
    return render(request, 'miRNAfuncTargets.html', {"species": all_species})


class MirFuncTarget(FormView):
    template_name = 'miRNAtarget.html'
    form_class = MirFuncForm
    success_url = reverse_lazy("MIRFUNC")

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

        return super(AMirConsTarget, self).form_valid(form)


def run(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    # fdw = file(FS.location+"/error.txt", "w")
    miRNA_file = ""
    utr_file = ""
    program_list = []
    parameters_list = []
    species, sp_class = request.POST["db_table"].split(",")

    if "miRNA_file" in request.FILES:
        file_to_update = request.FILES['miRNA_file']
        uploaded_file = str(file_to_update)
        if str(file_to_update).split(".")[1] not in ["fa", "fasta", "mfasta", "mfa", "txt"]:
            return render(request, "error_page.html", {"errors": [
                'miRNAs file extension must be: fa, fasta, mfasta, mfa or txt. ".' + str(file_to_update).split(".")[
                    1] + '" found']})
        FS.save(uploaded_file, file_to_update)
        miRNA_file = os.path.join(FS.location, uploaded_file)

    if "utr_file" in request.FILES:
        file_to_update = request.FILES['utr_file']
        uploaded_file = str(file_to_update)
        if str(file_to_update).split(".")[1] not in ["fa", "fasta", "mfasta", "mfa", "txt"]:
            return render(request, "error_page.html", {"errors": [
                'UTRs file extension must be: fa, fasta, mfasta, mfa or txt. ".' + str(file_to_update).split(".")[
                    1] + '" found']})
        FS.save(uploaded_file, file_to_update)
        utr_file = os.path.join(FS.location, uploaded_file)
    else:
        utr_file = species

    if not "miRNA_file" in request.FILES:
        return render(request, "error_page.html", {"errors": ["miRNAs file should be provided"]})

    for program in request.POST.getlist("programs"):
        program_list.append(program)

    program_string = ":".join(program_list)



    if len(program_list) < 1:
        return render(request, "error_page.html", {"errors": ["At least one program should be chosen"]})

    for i, Parameter in enumerate(request.POST.getlist("Parameters")):
        if TOOLS[i] in program_list:
            parameters_list.append(Parameter)

    parameter_string = ":".join(parameters_list).replace("-", "55-55")

    if parameter_string == "":
        parameter_string = "".join([":" for i in program_list])

    outdir = FS.location

    # fdw.write('qsub -v pipeline="mirnafunctargets",program_string="' + program_string + '",parameter_string="' + parameter_string + '",key="' + pipeline_id + '",outdir="' + outdir + '",miRNA_file="' + miRNA_file + '",utr_file="' + utr_file + '",go_table="' + species +
    #     '",name="' + pipeline_id + '_mirnafunctargets"' + ' -N ' + pipeline_id + '_mirnafunctargets /shared/sRNAtoolbox/core/bash_scripts/run_mirnafunctargets.sh')

    os.system(
        'qsub -v pipeline="mirnafunctargets",program_string="' + program_string + '",parameter_string="' + parameter_string + '",key="' + pipeline_id + '",outdir="' + outdir + '",miRNA_file="' + miRNA_file + '",utr_file="' + utr_file + '",go_table="' + species +
        '",name="' + pipeline_id + '_mirnafunctargets"' + ' -N ' + pipeline_id + '_mirnafunctargets /shared/sRNAtoolbox/core/bash_scripts/run_mirnafunctargets.sh')

    return redirect("/srnatoolbox/jobstatus/mirnafunctargets/?id=" + pipeline_id)


def result(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with results of srnafuncterms
    """
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        assert isinstance(new_record, JobStatus)

        results = {}

        if new_record.job_status == "Finished":
            plants = False
            min = 2

            try:
                results["parameters"] = new_record.parameters

                for param in new_record.parameters.split("\n"):
                    if "Programs:" in param:
                        min = len(param.split(" ")[1].split(":"))

                if "PSROBOT" in new_record.parameters or "TAPIR_FASTA" in new_record.parameters or "TAPIR_HYBRID" in new_record.parameters:
                    plants = True
                    min = 1
            except:
                pass

            parser = TargetConsensusParser(new_record.consensus_file)
            list_d = [obj for obj in parser.get_by_n(min)]
            id = "table"

            try:
                header = list_d[0].get_sorted_attr()
                r = Result(id, define_table(header, 'TableResult', plants)(list_d))
                results[id] = r
            except:
                results[id] = Result(id, define_table(["Results"], 'TableResult', plants)(
                    [{"Results": "Results not found!"}]))

            results["consensus_result"] = new_record.consensus_file.replace("/shared/sRNAtoolbox/webData/", "")

            results_eda_all = []
            results_eda_module = []
            for f in new_record.all_files:
                eda = EdaFile(f, "all")
                term_list = [term.__dict__ for term in eda.parse()]

                name = " ".join(os.path.basename(f).replace("_all.eda", "").split("_")[2:])

                results_eda_all.append(Result(name, TableResultenrich(term_list)))
                results_eda_all.sort(key=lambda x: x.name)

            for f in new_record.modules_files:
                eda = EdaFile(f, "module")
                term_list = [term.__dict__ for term in eda.parse()]

                name = " ".join(os.path.basename(f).replace("_modules.eda", "").split("_")[2:])

                results_eda_module.append(Result(name, TableResultModule(term_list)))
                results_eda_module.sort(key=lambda x: x.name)

            zip_file = "/".join(new_record.zip_file.split("/")[-2:])

            results['finish'] = True
            results['tables_all'] = results_eda_all
            results['tables_modules'] = results_eda_module
            results['zip'] = zip_file
            try:
                results["parameters"] = new_record.parameters
            except:
                pass

            results["id"] = job_id
            results["date"] = new_record.start_time + datetime.timedelta(days=15)

            return render(request, 'miRNAfuncTargets_results.html', results)

        else:
            return redirect("/srnatoolbox/jobstatus/mirnafunctargets/?id=" + job_id)

    else:
        return redirect("/srnatoolbox/mirnafunctargets")


def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    outdir = FS.location
    program_string = "TS:MIRANDA:PITA"
    parameter_string = ":::"

    os.system('cp /shared/sRNAtoolbox/testData/rno_miR.fa ' + FS.location)
    os.system('cp /shared/sRNAtoolbox/testData/rn5_refSeq_3utr.fa ' + FS.location)

    miRNA_file = os.path.join(FS.location, "rno_miR.fa")
    utr_file = os.path.join(FS.location, "rn5_refSeq_3utr.fa")
    go_table = "goa_hsa"

    os.system(
        'qsub -v pipeline="mirnafunctargets",program_string="' + program_string + '",parameter_string="' + parameter_string + '",key="' + pipeline_id + '",outdir="' + outdir + '",miRNA_file="' + miRNA_file + '",utr_file="' + utr_file + '",go_table="' + go_table +
        '",name="' + pipeline_id + '_mirnafunctargets"' + ' -N ' + pipeline_id + '_mirnafunctargets /shared/sRNAtoolbox/core/bash_scripts/run_mirnafunctargets.sh')

    return redirect("/srnatoolbox/jobstatus/mirnafunctargets/?id=" + pipeline_id)
