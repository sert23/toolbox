# Create your views here.
import datetime
import itertools
import os

import django_tables2 as tables
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from FileModels.jBrowserParser import JBrowserParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import make_dir

counter = itertools.count()

FS = FileSystemStorage("/shared/sRNAtoolbox/webData")



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


def input(request):
    return render(request, 'jBrowser.html', {})

def run(request):
    if request.POST["bench_id"].replace(" ", "") != "":
        pipeline_id = pipeline_utils.generate_uniq_id()
        bench_id = request.POST["bench_id"]
        FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
        make_dir(FS.location)
        outdir = FS.location

        os.system('qsub -v pipeline="jbrowser",bench_id="' + bench_id + '",key="' + pipeline_id + '",outdir="' + outdir +
                  '",name="' + pipeline_id + '_jbrowser"' + ' -N ' + pipeline_id + '_jbrowser /shared/sRNAtoolbox/core/bash_scripts/run_sRNAjbrowser.sh')

        return redirect("/srnatoolbox/jobstatus/srnajbrowser/?id=" + pipeline_id)

    else:
        return render(request, "error_page.html", {"errors": ["sRNAbench ID must be provided"]})



def result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        assert isinstance(new_record, JobStatus)

        tables = []
        results = {}
        if new_record.job_status == "Finished":
            for file in new_record.bed_files:
                parser = JBrowserParser(file)
                list_d = [obj for obj in parser.get_firsts(10)]
                header = list_d[0].get_sorted_attr()
                id = "_".join(os.path.basename(file).split("_")[:-1])
                r = Result(id, define_table(header, 'notformattable')(list_d))
                tables.append(r)

            results["tables"] = tables
            try:
                results["parameters"] = new_record.parameters
            except:
                pass
            results["id"] = job_id
            results["date"] = new_record.start_time + datetime.timedelta(days=15)

            return render(request, "jbrowser_result.html", results)

        else:
            return redirect("/srnatoolbox/jobstatus/srnajbrowser/?id=" + job_id)

    else:
        return redirect("/srnatoolbox/srnajbrowser")


def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    outdir = FS.location
    os.system('qsub -v pipeline="jbrowser",bench_id="' + 'F33H7949W0C2FFY' + '",key="' + pipeline_id + '",outdir="' + outdir +
              '",name="' + pipeline_id + '_jbrowser"' + ' -N ' + pipeline_id + '_jbrowser /shared/sRNAtoolbox/core/bash_scripts/run_sRNAjbrowser.sh')

    return redirect("/srnatoolbox/jobstatus/srnajbrowser/?id=" + pipeline_id)
