# Create your views here.
import datetime
import itertools
import os
import urllib

import django_tables2 as tables
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from .forms import sRNAconsForm
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import make_dir
from django.views.generic import FormView
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from FileModels.sRNAconsParsers import sRNAconsParser

#SPECIES_PATH = '/shared/data/sRNAbench/species.csv'
#SPECIES_ANNOTATION_PATH = '/shared/data/sRNAbench/annotation.txt'
#FS = FileSystemStorage("/shared/sRNAtoolbox/webData")
CONF = settings.CONF
FS = FileSystemStorage(CONF["sRNAtoolboxSODataPath"])

counter = itertools.count()


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
    attrs = dict((c, tables.Column()) for c in columns)
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
    """
    :rtype : render
    :param request: posts and gets
    :return: html with main of functerms
    """
    return render(request, 'sRNAcons/srnacons_input.html', {})



def result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        assert isinstance(new_record, JobStatus)

        results = {}
        results["id"] = job_id
        if new_record.job_status == "Finished":
            results["info"] = "Correct"
            results["date"] = new_record.start_time + datetime.timedelta(days=15)

            try:
                results["parameters"] = new_record.parameters
            except:
                pass

            if os.path.exists(os.path.join(new_record.outdir,"identicalSequenceRelation.tsv")):
                try:
                    parser = sRNAconsParser(os.path.join(new_record.outdir, "sRNA2Species.txt"), "srna2species", 500)
                    srna2sp = [obj for obj in parser.parse()]
                    header = srna2sp[0].get_sorted_attr()
                    blast_result = Result("Conservation depth of each smallRNA", define_table(header, 'TableResult')(srna2sp))
                    results["srna2sp"] = blast_result
                except:
                    pass

                try:            
                    parser = sRNAconsParser(os.path.join(new_record.outdir, "species2SRNA.txt"), "species2srna", 500)
                    srna2sp = [obj for obj in parser.parse()]
                    header = srna2sp[0].get_sorted_attr()
                    blast_result = Result("Input sequences contained in each species", define_table(header, 'TableResult')(srna2sp))
                    results["sp2srna"] = blast_result
                except:
                    pass
            else:
                results["error"] = "Some errors were detected, please email with the number of this jobID ("+job_id+") to the administrator of the website."
            return render(request, 'sRNAcons/srnacons_result.html', results)
        else:
            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))
    else:
        return redirect(settings.SUB_SITE)


class sRNAcons(FormView):
    template_name = 'sRNAcons/srnacons_input.html'
    form_class = sRNAconsForm

    success_url = reverse_lazy("srnacons")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        self.success_url = reverse_lazy('srnacons') + '?id=' + pipeline_id
        return super(sRNAcons, self).form_valid(form)