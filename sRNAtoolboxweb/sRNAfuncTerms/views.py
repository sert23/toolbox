import datetime
import itertools
import os

import django_tables2 as tables
import xlrd
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from FileModels.sRNAdeparser import SRNAdeParser
from FileModels.sRNAfuncParsers import EdaFile
from FileModels.speciesParser import SpeciesParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import istext
from utils.sysUtils import make_dir

counter = itertools.count()
TOOLS = ["TS", "MIRANDA", "PITA", "PSROBOT", "TAPIR_FASTA", "TAPIR_HYBRID"]

#CONF = json.load(file("/shared/sRNAtoolbox/sRNAtoolbox.conf"))
CONF = settings.CONF
SPECIES_PATH = CONF["species"]
FS = FileSystemStorage(CONF["sRNAtoolboxSODataPath"])





class TableResult(tables.Table):
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


class Result():
    """
    Class to manage tables results and meta-info
    """

    def __init__(self, name, table):
        self.name = name.capitalize()
        self.content = table
        self.id = name.replace(" ", "_")


def functerms(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with main of functerms
    """
    species_file = SpeciesParser(SPECIES_PATH)
    array_species = species_file.parse()
    all_species = []

    for species in array_species:
        if species.hasTargetSequencesAndGO:
            all_species.append((species.db, species.scientific))
    return render(request, 'functerms.html',{"species": all_species})


def run(request):
    """
    :rtype : redirect
    :param request: posts and gets
    :return: redirect to results
    """
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    fdw = file(FS.location+"/error.txt", "w")
    annotations = ["go"]
    go_table = request.POST["db_table"]

    """
    if "go" in request.POST:
        annotations.append("go")
    if "kegg" in request.POST:
        annotations.append("kegg")
    if "biocyc" in request.POST:
        annotations.append("biocyc")"""
    outdir = FS.location
    exp = "false"

    if "exp" in request.POST:
        exp = "true"

    if "list" in request.FILES:
        # Upload file
        file_to_update = request.FILES['list']
        uploaded_file = str(file_to_update)
        FS.save(uploaded_file, file_to_update)
        mir_list = os.path.join(FS.location, uploaded_file)

        if not istext(mir_list):
            return render(request, "error_page.html", {"errors": ["miRNA list file should be a text file"]})

    elif request.POST["id"] != "":

        try:
            new_record = JobStatus.objects.get(pipeline_key=request.POST["id"])
        except:
            return render(request, "error_page.html", {"errors": ["Job with ID: " + request.POST["id"] + " does not exist."]})

        mirna_file = os.path.join("/shared/sRNAtoolbox/webData", request.POST["id"], "miRBase_main.txt")

        if os.path.isfile(mirna_file):
            fd = file(mirna_file)
            mir_list = os.path.join(FS.location, "top_10_" + os.path.basename(mirna_file))
            fdw = file(mir_list, "w")
            fd.readline()
            i = 0

            while i < 10:
                fdw.write(fd.readline().split("\t")[0] + "\n")
                i += 1

        else:
            return render(request, "error_page.html", {"errors": ["Job with ID: " + request.POST["id"] + " has not the appropriate results to launch sRNAFuncterms"]})

    elif request.POST["de_id"] != "":
        try:
            new_record = JobStatus.objects.get(pipeline_key=request.POST["de_id"])
        except:
            return render(request, "error_page.html", {"errors": ["Job with ID: " + request.POST["de_id"] + " does not exist."]})

        assert isinstance(new_record, JobStatus)

        all_consensus = []

        if new_record.job_status == "Finished":

            for xls in new_record.xls_files:
                workbook = xlrd.open_workbook(xls)
                names = workbook.sheet_names()
                Selection = [name for name in names if "Selection" in name]

                if Selection > 0:
                    parser = SRNAdeParser(xls, "none")
                    list_d = [obj for obj in parser.get_consensus(*Selection)]
                    all_consensus = all_consensus + list_d

            mir_list = os.path.join(FS.location, "differential_expression_mirna_all_condition.txt")

            fdw = file(mir_list, "w")

            for consensus in all_consensus:
                fdw.write(consensus.miRNA_Name + "\n")
            fdw.close()

        else:
            return render(request, "error_page.html", {"errors": ["Job with ID: " + request.POST["de_id"] + " has not the appropriate results to launch sRNAFuncterms"]})

    else:
        return render(request, "error_page.html", {"errors": ["sRNAde ID, sRNAbench ID or miRNA list file should be provided"]})

    # call qsub
    fdw.write('qsub -v pipeline="functerms",annot="' + ",".join(annotations) + '",outdir="' + outdir + '",go_table="' + go_table + '",exp="' + exp + '",key="' +
              pipeline_id + '",name="' + pipeline_id + '_functerms",input="' + mir_list + '",type="list"  -N ' +
              pipeline_id + '_functerms /shared/sRNAtoolbox/core/bash_scripts/run_sRNAfuncterms.sh')
    os.system('qsub -v pipeline="functerms",annot="' + ",".join(annotations) + '",outdir="' + outdir + '",go_table="' + go_table + '",exp="' + exp + '",key="' +
              pipeline_id + '",name="' + pipeline_id + '_functerms",input="' + mir_list + '",type="list"  -N ' +
              pipeline_id + '_functerms /shared/sRNAtoolbox/core/bash_scripts/run_sRNAfuncterms.sh')

    return redirect("/srnatoolbox/jobstatus/srnafuncterms/?id=" + pipeline_id)


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

        if new_record.job_status == "Finished":

            results_eda_all = []
            results_eda_module = []
            for f in new_record.all_files:
                eda = EdaFile(f, "all")
                term_list = [term.__dict__ for term in eda.parse()]

                name = " ".join(os.path.basename(f).replace("_all.eda", "").split("_")[2:])

                results_eda_all.append(Result(name, TableResult(term_list)))
                results_eda_all.sort(key=lambda x: x.name)

            for f in new_record.modules_files:
                eda = EdaFile(f, "module")
                term_list = [term.__dict__ for term in eda.parse()]

                name = " ".join(os.path.basename(f).replace("_modules.eda", "").split("_")[2:])

                results_eda_module.append(Result(name, TableResultModule(term_list)))
                results_eda_module.sort(key=lambda x: x.name)

            zip_file = "/".join(new_record.zip_file.split("/")[-2:])

            id= job_id
            date = new_record.start_time + datetime.timedelta(days=15)
            results = {'finish': True, 'tables_all': results_eda_all, 'tables_modules': results_eda_module,
                       'zip': zip_file, 'id': id, 'date': date}
            try:
                results["parameters"] = new_record.parameters
            except:
                pass


            return render(request, 'functerms_results.html', results)

        else:
            return redirect("/srnatoolbox/jobstatus/srnafuncterms/?id=" + job_id)

    else:
        return redirect("/srnatoolbox/srnafuncterms")


def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)

    annotations = ["go"]
    go_table = "goa_hsa"
    exp = "true"
    outdir = FS.location
    mir_list = "/shared/sRNAtoolbox/testData/functerms_test_data.txt"

    os.system('qsub -v pipeline="functerms",annot="' + ",".join(annotations) + '",outdir="' + outdir + '",go_table="' + go_table + '",exp="' + exp + '",key="' +
              pipeline_id + '",name="' + pipeline_id + '_functerms",input="' + mir_list + '",type="list"  -N ' +
              pipeline_id + '_functerms /shared/sRNAtoolbox/core/bash_scripts/run_sRNAfuncterms.sh')

    return redirect("/srnatoolbox/jobstatus/srnafuncterms/?id=" + pipeline_id)