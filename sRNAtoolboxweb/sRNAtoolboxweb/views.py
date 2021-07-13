import itertools

import django_tables2 as tables
from django.conf import settings
from django.contrib.auth.decorators import login_required


from progress.models import JobStatus

counter = itertools.count()
from FileModels.jBrowserParser import JBrowserParser
import datetime
import os
from functools import reduce

__author__ = 'antonior'

# Create your views here.
from django.shortcuts import render, redirect

from django.conf import settings
from sRNAtoolboxweb.manage_plot import stacked_bars_state_percentage,stacked_bars_state,job_type

PIPELINETYPES_URL = {
    "sRNAfuncTerms": "srnafuncterms",
    "sRNAde": "srnade",
    "sRNAbench": "srnabench",
    "sRNAblast": "srnablast",
    "mirconstarget": "mirconstarget",
    "mirnafunctargets": "mirnafunctargets",
    "jBrowser": "jBrowser",
    "dejbrowser": "srnajbrowserde",
    "gFree": "srnagfree",
    "multiupload" : "multiupload"
}



def index(request):
    return render(request, 'index.html', {'description': "z"})

def manual(request):
    return redirect("http://bioinfo5.ugr.es/static/WebManual_sRNAtoolbox.pdf")


def blank(request):
    return render(request, 'blank.html', {})

def version(request):
    results={}
    #results["sRNAfuncTerms"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAfuncTerms", job_status="Finished")]
    results["sRNAde"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAde", job_status="Finished") if job.finish_time]
    results["sRNAbench"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAbench", job_status="Finished")if job.finish_time]
    results["sRNAblast"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAblast", job_status="Finished")if job.finish_time]
    #results["miRNAfuncTargets"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="mirnafunctargets", job_status="Finished")]
    #results["jBrowser"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="jBrowser", job_status="Finished")]
    #results["jBrowserDE"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="dejbrowser", job_status="Finished")]
    results["miRNAconsTarget"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="mirconstarget", job_status="Finished")if job.finish_time]



    for key in results:

        results[key] = [reduce(lambda x, y: x + y, results[key]) / len(results[key]),  len(results[key])]
        results[key][0] = "%s days, %.2dh: %.2dm: %.2ds" % (results[key][0].days,results[key][0].seconds//3600,(results[key][0].seconds//60)%60, results[key][0].seconds%60)


    return render(request, 'Common/VersionControlDonwloads.html', results)

@login_required
def management(request):
    results={}
    #results["sRNAfuncTerms"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAfuncTerms", job_status="Finished")]
    results["sRNAde"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAde", job_status="Finished") if job.finish_time]
    results["sRNAbench"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAbench", job_status="Finished")if job.finish_time]
    results["sRNAblast"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="sRNAblast", job_status="Finished")if job.finish_time]
    #results["miRNAfuncTargets"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="mirnafunctargets", job_status="Finished")]
    #results["jBrowser"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="jBrowser", job_status="Finished")]
    #results["jBrowserDE"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="dejbrowser", job_status="Finished")]
    results["miRNAconsTarget"] = [(job.finish_time - job.start_time) for job in JobStatus.objects.filter(pipeline_type="mirconstarget", job_status="Finished")if job.finish_time]
    results["status_plot"] = stacked_bars_state()
    results["status_plot_perc"] = stacked_bars_state_percentage()
    results["type_plot_perc"] = job_type()


    # for key in results:
    #
    #     results[key] = [reduce(lambda x, y: x + y, results[key]) / len(results[key]),  len(results[key])]
    #     results[key][0] = "%s days, %.2dh: %.2dm: %.2ds" % (results[key][0].days,results[key][0].seconds//3600,(results[key][0].seconds//60)%60, results[key][0].seconds%60)
    #

    return render(request, 'Common/Management.html', results)

def search(request):
    errors = {'errors': []}

    if "job_id" in request.POST:
        job_id = request.POST["job_id"]

        try:
            new_record = JobStatus.objects.get(pipeline_key=job_id)

            p_type = new_record.pipeline_type

            if p_type not in PIPELINETYPES_URL:
                errors['errors'].append("Sorry, we do not support search of helper tools results")
                return render(request, "error_page.html", errors)
            else:
                return redirect(settings.SUB_SITE+"/jobstatus/" + job_id)

        except:
            errors['errors'].append(job_id +" job not found, please check if the id is correct and job is currently active. Web Results will be stored for 15 days")
            return render(request, "error_page.html", errors)

    else:
         return render(request, 'index.html')


def testing(request):

    context = {}

    return render(request, "testing.html", context)




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


def define_table(columns, typeTable):
    """
    :param columns: Array with names of columns to show
    :return: a class of type TableResults
    """

    attrs = dict((c, tables.Column()) for c in columns if c != "url")

    attrs2 = dict((c, tables.URLColumn()) for c in columns if c == "url")
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

    def __gt__(self, other):
        if self.name > other.name:
            return True
        else:
            return False

    def __lt__(self, other):
        if self.name < other.name:
            return True
        else:
            return False

    def __eq__(self, other):
        if self.name == other.name:
            return True
        else:
            return False

def cultivar(request):

    job_id = "K6CU1U2W2W8OM26"

    new_record = JobStatus.objects.get(pipeline_key=job_id)
    assert isinstance(new_record, JobStatus)
    tables = []
    results={}

    for file in new_record.bed_files:
        parser = JBrowserParser(file)
        list_d = [obj for obj in parser.parse()]
        header = list_d[0].get_sorted_attr()
        id = "_".join(os.path.basename(file).split("_")[:-1])
        r = Result(id, define_table(header, 'TableResult')(list_d))
        tables.append(r)

    results["id"] = job_id
    results["date"] = new_record.start_time + datetime.timedelta(days=15)
    results["tables"] = sorted(tables)


    return render(request, "static_pages/jbrowserDE_result_static.html", results)



