# Create your views here.
import datetime
import itertools
import os
import urllib

import django_tables2 as tables
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from DataModels.sRNABlastConfig import SRNABlastConfig
from FileModels.BlastParsers import BlastParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import make_dir
from django.views.generic import FormView
from sRNAblast.forms import sRNAblastForm
from django.core.urlresolvers import reverse_lazy
from django.conf import settings

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

    return render(request, 'blast.html', {})


def run(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    guess_adapter = None
    recursive_adapter_trimming = None
    local = None
    ifile = ""

    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)


    if "reads_file" in request.FILES:
        file_to_update = request.FILES['reads_file']
        uploaded_file = str(file_to_update)
        if str(file_to_update).split(".")[1] not in ["fastq", "fa", "rc"]:
            return render(request, "error_page.html",  {"errors": ['Reads file extension must be: "fastq", "fa", "rc" ".'+str(file_to_update).split(".")[1]+'" found']})
        FS.save(uploaded_file, file_to_update)
        ifile = os.path.join(FS.location, uploaded_file)


    elif request.POST["bench_id"].replace(" ", "") != "":
        id = request.POST["bench_id"]
        file_to_copy = os.path.join("/shared/sRNAtoolbox/webData", id, "reads.fa")
        #os.system("head  -n 50 " + file_to_copy + " > " + os.path.join(FS.location, "reads.fa"))
        #ifile = os.path.join(FS.location, "reads.fa")
        ifile = file_to_copy

    elif request.POST["reads_url"].replace(" ", "") != "":
        url_input = request.POST["reads_url"]
        dest = os.path.join(FS.location, os.path.basename(url_input))
        handler = urllib.URLopener()
        handler.retrieve(url_input, dest)
        ifile = dest

    else:
        return render(request, "error_page.html",  {"errors": ["Read File, URL or sRNAbench ID must be provided"]})



    if "guessAdapter" in request.POST:
        guess_adapter = "true"

    adapter = request.POST["adapter"]
    maxReads = request.POST["maxReads"]
    minEvalue = request.POST["minEvalue"]
    if minEvalue.replace(" ", "") != "":
        try:
            float(minEvalue)
        except:
            return render(request, "error_page.html",  {"errors": ["Read File, URL or sRNAbench ID must be provided"]})

    else:
        minEvalue = "10"


    minrc = "1"
    alter_adapter = request.POST["alterAdapter"].upper().replace(" ", "")
    blastDB = request.POST["blastDB"]
    if len(alter_adapter) > 1:
        adapter = alter_adapter
    if adapter == "XXX":
        adapter = None

    adapter_minLength = request.POST["adapterMinLength"]
    adapterMM = request.POST["adapterMM"]

    if "recursiveAdapterTrimming" in request.POST:
        recursive_adapter_trimming = "true"

    if "local" in request.POST:
        blastDB = "/shared/blastDB/nt"
        local = "true"


    newConf = SRNABlastConfig(blastDB, "/shared/exec/blast/blastn", FS.location, "/shared/sRNAbenchDB", ifile, minrc,
                              maxReads=maxReads,
                              minEvalue=minEvalue,
                              adapter=adapter,
                              recursiveAdapterTrimming=recursive_adapter_trimming,
                              adapterMinLength=str(adapter_minLength), adapterMM=str(adapterMM),
                              guessAdapter=guess_adapter,
                              local=local
    )

    conf_file_location = os.path.join(FS.location, "conf.txt")
    newConf.write_conf_file(conf_file_location)

    os.system(
        'qsub -v pipeline="blast",configure="' + conf_file_location + '",key="' + pipeline_id + '",outdir="' + FS.location + '",name="' + pipeline_id
        + '_sRNAblast' + '" -N ' + pipeline_id + '_sRNAblast /shared/sRNAtoolbox/core/bash_scripts/run_sRNAblast.sh')

    return redirect("/srnatoolbox/jobstatus/srnablast/?id=" + pipeline_id)




def result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        print("new record")
        print(new_record.outdir)
        assert isinstance(new_record, JobStatus)

        results = {}
        results["id"] = job_id
        #if True:
        if new_record.job_status == "Finished":

            try:
                parser = BlastParser(os.path.join(new_record.outdir, "blast.out"), "blast", 500)
                # parser = BlastParser("/opt/sRNAtoolbox/sRNAtoolboxweb/upload/P19XKMOHJEZ09ZG/blast.out", "blast", 100)
                blast = [obj for obj in parser.parse()]
                print("here print")
                print(blast)
                header = blast[0].get_sorted_attr()
                blast_result = Result("Read Processing Statistic", define_table(header, 'TableResult')(blast))
                results["blast"] = blast_result
            except:
                results["blast"] = Result("Read Processing Statistic", define_table([], 'TableResult')([]))

            try:
                parser = BlastParser(os.path.join(new_record.outdir, "speciesSA.out"), "species", 50)
                species = [obj for obj in parser.parse()]
                header = species[0].get_sorted_attr()
                species_result = Result("Read Processing Statistic", define_table(header, 'TableResult')(species))
                results["species"] = species_result
            except:
                results["species"] = Result("Read Processing Statistic", define_table([], 'TableResult')([]))

            try:
                parser = BlastParser(os.path.join(new_record.outdir, "tax.out"), "tax", 50)
                tax = [obj for obj in parser.parse()]
                header = tax[0].get_sorted_attr()
                tax_result = Result("Read Processing Statistic", define_table(header, 'TableResult')(tax))
                results["taxonomy"] = tax_result
            except:
                results["taxonomy"] = Result("Read Processing Statistic", define_table([], 'TableResult')([]))

            results["zip"] =new_record.zip_file

            try:
                with open(os.path.join(new_record.outdir,"parameters.txt"), 'r') as myfile:
                    parameters = myfile.read()


                #results["parameters"] = "\\n".join(list(open(par_file).readlines())).replace("\n",""),
                results["parameters"] = parameters
                #results["species_figure"] = os.path.join("/",new_record.outdir, "species.svg")
                # results["species_figure"] = "/".join(new_record.species_svg.split("/")[-2:])
            except:
                pass

            species_figure = new_record.pipeline_key
            if os.path.exists(os.path.join(new_record.outdir,"species.svg")):
                results["species_figure"] = "/"+new_record.pipeline_key+"/species.svg"

            if os.path.exists(os.path.join(new_record.outdir,"tax.svg")):
                results["tax_figure"] = "/"+new_record.pipeline_key+"/tax.svg"




            results["date"] = new_record.start_time + datetime.timedelta(days=15)


            return render(request, "blast_result.html", results)
        else:
            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))

    else:
        return (reverse_lazy('SRNABLAST'))



def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    guess_adapter = None
    recursive_adapter_trimming = None
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    id = "4XVGNWRUK0ZCUM1"
    file_to_copy = os.path.join("/shared/sRNAtoolbox/webData", id, "reads.fa")
    #os.system("head  -n 50 " + file_to_copy + " > " + os.path.join(FS.location, "reads.fa"))
    #ifile = os.path.join(FS.location, "reads.fa")
    ifile=file_to_copy
    adapter = None
    adapter_minLength = "10"
    adapterMM = "1"

    newConf = SRNABlastConfig("nr", "/shared/exec/blast/blastn", FS.location, "/shared/sRNAbenchDB", ifile, "1",
                              maxReads="10",
                              minEvalue="10",
                              adapter=adapter,
                              recursiveAdapterTrimming=recursive_adapter_trimming,
                              adapterMinLength=str(adapter_minLength), adapterMM=str(adapterMM),
                              guessAdapter=guess_adapter,
                              local=None)


    conf_file_location = os.path.join(FS.location, "conf.txt")
    newConf.write_conf_file(conf_file_location)
    os.system(
        'qsub -v pipeline="blast",configure="' + conf_file_location + '",key="' + pipeline_id + '",outdir="' + FS.location + '",name="' + pipeline_id
        + '_sRNAblast' + '" -N ' + pipeline_id + '_sRNAblast /shared/sRNAtoolbox/core/bash_scripts/run_sRNAblast.sh')

    return redirect("/srnatoolbox/jobstatus/srnablast/?id=" + pipeline_id)


class SRNABlast(FormView):
    template_name = 'new_blast.html'
    form_class = sRNAblastForm
    success_url = reverse_lazy("SRNABLAST")

    #success_url = reverse_lazy("mirconstarget")


    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.clean()
        call, pipeline_id = form.create_call()
        self.success_url = reverse_lazy('srnablast') + '?id=' + pipeline_id

        print(call)
        os.system("source /opt/venv/sRNAtoolbox2019/bin/activate")
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()

        return super(SRNABlast, self).form_valid(form)