# Create your views here.
# Create your views here.
import datetime
import itertools

import django_tables2 as tables
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from FileModels.jBrowserParser import JBrowserParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import *

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


def input(request):
    return render(request, 'dejbrowser.html', {})


def run(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    input = ""
    outdir = FS.location



    if len(request.POST["id"].replace(" ", "")) > 0:
        input = request.POST["id"]
        length = request.POST["length"]
        desc = request.POST["desc"]



        response = check_ids_param(input, desc, length)

        if response is not True:
            return render(request, "error_page.html", response)



        if len(length.replace(" ", "")) > 0:
            os.system('qsub -v pipeline="dejbrowser",groups="' + desc + '",key="' + pipeline_id + '",outdir="' + outdir +
                    '",length="' + length + '",name="' + pipeline_id + '_dejbrowser",bench_id="' + input +
                    '" -N ' + pipeline_id + '_dejbrowser /shared/sRNAtoolbox/core/bash_scripts/run_sRNAdejbrowser.sh')

        else:
            os.system('qsub -v pipeline="dejbrowser",groups="' + desc + '",key="' + pipeline_id + '",outdir="' + outdir +
                    '",name="' + pipeline_id + '_dejbrowser",bench_id="' + input +
                    '" -N ' + pipeline_id + '_dejbrowser /shared/sRNAtoolbox/core/bash_scripts/run_sRNAdejbrowser_nolength.sh')




        return redirect("/srnatoolbox/jobstatus/srnajbrowserde/?id=" + pipeline_id)

    else:
        return render(request, "error_page.html", {"errors": ["sRNAbench IDs must be provided"]})




def check_ids_param(idlist, desc, length):
    groups = idlist.split("#")
    samples = desc.split("#")
    length_groups = length.split(":")
    errors = {'errors': []}

    for job_id in groups:
        try:
            new_record = JobStatus.objects.get(pipeline_key=job_id)
            if not os.path.exists(new_record.outdir):
                errors['errors'].append(job_id +" result of job not found, please check if the id is correct and job is currently active.")
        except:
            errors['errors'].append(job_id +" job not found, please check if the id is correct and job is currently active.")




    if not len(samples) == len(groups):
        errors['errors'].append('The number of samples group is different in "list of SRNAbench IDs" and "Sample groups". '
                           'Please use "#" in order to split samples')

    if len(length_groups) != 1:
        for l in length_groups:
            if len(l.split("-")) == 2:
                upper, lower = l.split("-")
                try:
                    int(upper)
                    int(lower)
                except:
                    errors['errors'].append('Please provide a numeric interval. ' + l + " was provided")
            else:
                errors['errors'].append('Please provide a valid interval. ' + l + " was provided")

    if len(errors['errors']) == 0:
        return True

    else:
        return errors

def result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        assert isinstance(new_record, JobStatus)
        tables = []
        results={}
        if new_record.job_status == "Finished":
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
            try:
                results["parameters"] = new_record.parameters
            except:
                pass

            return render(request, "jbrowserDE_result.html", results)

        else:
            return redirect("/srnatoolbox/jobstatus/srnajbrowserde/?id=" + job_id)

    else:
        return redirect("/srnatoolbox/srnajbrowserde")


def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    outdir = FS.location
    os.system('qsub -v pipeline="dejbrowser",groups="' + "cell#exosome" + '",key="' + pipeline_id + '",outdir="' + outdir +
                    '",name="' + pipeline_id + '_dejbrowser",bench_id="' + "RG5TRAJIOOFS7II#F33H7949W0C2FFY" +
                    '" -N ' + pipeline_id + '_dejbrowser /shared/sRNAtoolbox/core/bash_scripts/run_sRNAdejbrowser_nolength.sh')

    return redirect("/srnatoolbox/jobstatus/srnajbrowserde/?id=" + pipeline_id)