# Create your views here.
import datetime
import itertools
import os
import urllib

import django_tables2 as tables
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic import FormView
from sRNAtoolboxweb.settings import BASE_DIR,MEDIA_ROOT,MEDIA_URL, SUB_SITE
from DataModels.params_bench import ParamsBench
from DataModels.sRNABenchConfig import SRNABenchConfig
from FileModels.IsomirParser import IsomirParser
from FileModels.MAParser import MAParser
from FileModels.NovelParser import NovelParser
from FileModels.GeneralParser import GeneralParser
from FileModels.SAParser import SAParser
from FileModels.TRNAParser import TRNAParser
from FileModels.matureParser import MatureParser
from FileModels.matureParserSa import MatureParserSA
from FileModels.mirbaseMainParser import MirBaseParser
from FileModels.speciesAnnotationParser import SpeciesAnnotationParser
from FileModels.speciesParser import SpeciesParser
from progress.models import JobStatus
from .forms import miRNAgFreeForm, FileForm
from utils import pipeline_utils
from utils.sysUtils import make_dir
from sRNABench.bench_plots_func import full_read_length,read_length_type,mapping_stat,top_miRNA_plot
from FileModels.deStatsParser import DeStatsParser
from FileModels.summaryParser import LinksParser, BWParser
from sRNAtoolboxweb.utils import render_modal
from django.utils.safestring import mark_safe
import pandas as pd
import string
import random
import shutil
from django.http import JsonResponse
import json
import subprocess
import re
import plotly.graph_objs as go
from plotly.offline import plot
import math


#CONF = json.load(file("/shared/sRNAtoolbox/sRNAtoolbox.conf"))
CONF = settings.CONF
SPECIES_PATH = CONF["species"]
SPECIES_ANNOTATION_PATH = CONF["speciesAnnotation"]
DB = CONF["db"]
FS = FileSystemStorage(CONF["sRNAtoolboxSODataPath"])
counter = itertools.count()

def roundup100(x):
    return int(math.ceil(x / 100.0)) * 100

def roundup10(x):
    return int(math.ceil(x / 10.0)) * 10

def make_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)

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

    attrs = dict((c, tables.Column()) for c in columns if c != "align" and c != "align_" and c != "link")
    attrs2 = dict((c, tables.TemplateColumn('<a href="{% url "show_align" id "pre-microRNA" record.align %}">align</a>')) for c in columns if c == "align")
    # attrs2 = dict((c, tables.TemplateColumn('<a href="{% url "show_align" id "pre-microRNA" record.align %}">align</a>')) for c in columns if c == "align")
    #attrs2 = dict((c, tables.TemplateColumn('<a href="{% url "sRNABench.views.show_align" id "hairpin" record.align %}">align</a>')) for c in columns if c == "align")
    attrs.update(attrs2)
    attrs3 = dict((c, tables.TemplateColumn('<a href="{% url "show_align" id "novel" record.align_ %}">align</a>')) for c in columns if c == "align_")
    #attrs3 = dict((c, tables.TemplateColumn('<a href="{% url "sRNABench.views.show_align" id "novel" record.align_ %}">align</a>')) for c in columns if c == "align_")
    attrs.update(attrs3)
    attrs4 = dict(
        (c, tables.TemplateColumn('<a href="{{record.link}}" class="btn btn-primary btn-sm" target="_blank" role="button" aria-pressed="true">Download data</a>')) for c in
        columns if c == "link")
    attrs.update(attrs4)




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

def define_table2(columns, typeTable):
    """
    :param columns: Array with names of columns to show
    :return: a class of type TableResults
    """

    attrs = dict((c, tables.Column()) for c in columns)
    # attrs2 = dict((c, tables.TemplateColumn('<a href="{% url "show_align" id "pre-microRNA" record.align %}">align</a>')) for c in columns if c == "align")
    # # attrs2 = dict((c, tables.TemplateColumn('<a href="{% url "show_align" id "pre-microRNA" record.align %}">align</a>')) for c in columns if c == "align")
    # #attrs2 = dict((c, tables.TemplateColumn('<a href="{% url "sRNABench.views.show_align" id "hairpin" record.align %}">align</a>')) for c in columns if c == "align")
    # attrs.update(attrs2)
    # attrs3 = dict((c, tables.TemplateColumn('<a href="{% url "show_align" id "novel" record.align_ %}">align</a>')) for c in columns if c == "align_")
    # #attrs3 = dict((c, tables.TemplateColumn('<a href="{% url "sRNABench.views.show_align" id "novel" record.align_ %}">align</a>')) for c in columns if c == "align_")
    # attrs.update(attrs3)




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

def define_table_BigWig(columns, typeTable):
    """
    :param columns: Array with names of columns to show
    :return: a class of type TableResults
    """

    attrs = dict((c, tables.Column()) for c in columns if c != "link")
    # attrs = dict((c, tables.Column()) for c in columns if c != "Link to results")
    attrs2 = dict((c, tables.TemplateColumn(
        '<a href="{{record.link}}" class="btn btn-primary btn-sm" target="_blank" role="button" aria-pressed="true">Download data</a>'))
                  for c in columns if c == "link")
    # attrs2 = dict((c, tables.TemplateColumn('<a href="{{record.link}" class="btn btn-primary btn-sm" role="button" aria-pressed="true">Go to results</a>')) for c in columns if c == "Link to results")
    # attrs2 = dict((c, tables.TemplateColumn('<a href="{{ settings.SUB_SITE }}/{{record.method}}" class="btn btn-primary btn-sm" role="button" aria-pressed="true">Go to results</a>')) for c in columns if c == "Link to results")
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


def generate_uniq_id(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_id():
    is_new = True
    while is_new:
        pipeline_id = generate_uniq_id()
        if not JobStatus.objects.filter(pipeline_key=pipeline_id):
            return pipeline_id

def input(request):
    """
    :rtype : render
    :param request: posts and gets
    :return: html with main of functerms
    """

    species_file = SpeciesParser(SPECIES_PATH)
    print(SPECIES_PATH)
    array_species = species_file.parse()
    species_dict = {}
    # form = sRNABenchForm()
    form = ""
    for species in array_species:
        if species.sp_class in species_dict:
            species_dict[species.sp_class].append(species)
        else:
            species_dict[species.sp_class] = [species]
    return render(request, 'bench.html', {"species_data": species_dict, "form": form})


def run(request):
    libs_files = []
    pipeline_id = pipeline_utils.generate_uniq_id()
    lib_mode = False
    no_libs = False
    species = []
    assemblies = []
    guess_adapter = None
    recursive_adapter_trimming = None
    high_conf = False
    solid = None
    ifile = ""
    mircro_names = []
    name_modifier = None

    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)

    if len(request.POST["job_name"].replace(" ", "")) > 1:
        name_modifier = request.POST["job_name"].replace(" ", "")

    if "reads_file" in request.FILES:
        file_to_update = request.FILES['reads_file']

        extension = ".".join(str(file_to_update).split(".")[1:])

        if extension not in ["fastq", "fa", "rc", "fastq.gz", "fa.gz", "rc.gz", "txt", "txt.gz", "sra"]:
            return render(request, "error_page.html", {"errors": ['Reads file extension must be: "fastq", "fa", "rc", "rc.gz", "fa.gz", "fastq.gz" , "txt", "txt.gz", "sra". We have detected: ' +  extension + ' please use one of the supported formats']})


        if name_modifier is not None:
            uploaded_file = str(name_modifier) + "." + extension
        else:
            uploaded_file = str(file_to_update).replace(" ", "")
        FS.save(uploaded_file, file_to_update)
        ifile = os.path.join(FS.location, uploaded_file)

    elif request.POST["reads_url"].replace(" ", "") != "":
        url_input = request.POST["reads_url"]

        extension = ".".join(os.path.basename(url_input).split(".")[1:])

        if extension not in ["fastq", "fa", "rc", "fastq.gz", "fa.gz", "rc.gz", "txt", "txt.gz", "sra"]:
            return render(request, "error_page.html", {"errors": [
                'Reads file extension must be: "fastq", "fa", "rc", "rc.gz", "fa.gz", "fastq.gz", "txt", "txt.gz", "sra"  ".' + extension + '" found']})


        if name_modifier is not None:
            dest = os.path.join(FS.location, str(name_modifier) + "." + extension).replace(" ", "")
        else:
            dest = os.path.join(FS.location, os.path.basename(url_input))


        handler = urllib.URLopener()
        handler.retrieve(url_input, dest)
        ifile = dest

    else:
        return render(request, "error_page.html", {"errors": ["Read File or URL must be provided"]})

    if "user_files" in request.FILES:
        for i, afile in enumerate(request.FILES.getlist("user_files")):
            file_to_update = afile
            uploaded_file = str(file_to_update).replace(" ", "")
            FS.save(uploaded_file, file_to_update)
            libs_files.append(os.path.join(FS.location, uploaded_file))

    if "user_urls" in request.POST:
        for i, url in enumerate(request.POST.getlist("user_urls")):
            if url != "":
                libfile = urllib.URLopener()
                dest = os.path.join(FS.location, os.path.basename(url)).replace(" ", "")
                libfile.retrieve(url, dest)
                libs_files.append(dest)

    if "libMode" in request.POST:
        lib_mode = True

    if "noLibs" in request.POST:
        no_libs = True

    for specie in request.POST.getlist("species"):
        if specie != "":
            species.append(specie.split(":")[2])
            assemblies.append(specie.split(":")[1])
            mircro_names.append(specie.split(":")[0])

    if "guessAdapter" in request.POST:
        guess_adapter = "true"

    adapter = request.POST["adapter"]
    alter_adapter = request.POST["alterAdapter"].upper().replace(" ", "")

    if len(alter_adapter) > 1:
        adapter = alter_adapter
    if adapter == "XXX":
        adapter = None

    adapter_minLength = request.POST["adapterMinLength"]
    adapterMM = request.POST["adapterMM"]

    if "recursiveAdapterTrimming" in request.POST:
        recursive_adapter_trimming = "true"

    if "highconf" in request.POST:
        high_conf = True

    mir = request.POST["miR"]
    homolog = request.POST["homolog"]

    if len(homolog) < 1:
        homolog = None

    if "genomeMiR" in request.POST:
        mir = ":".join(mircro_names)

    if "solid" in request.POST:
        solid = "true"

    rc = request.POST["rc"]
    mm = request.POST["mm"]
    seed = request.POST["seed"]
    align_type = request.POST["alignType"]
    remove_barcode = request.POST["removeBarcode"]
    minReadLength = request.POST["minReadLength"]
    mBowtie = request.POST["mBowtie"]

    if "predict" in request.POST:
        predict="true"
    else:
        predict=None

    species_annotation_file = SpeciesAnnotationParser(SPECIES_ANNOTATION_PATH)
    species_annotation = species_annotation_file.parse()

    newConf = SRNABenchConfig(species_annotation, DB, FS.location, ifile, iszip="true",
                              RNAfold="RNAfold2",
                              bedGraph="true", writeGenomeDist="true", predict=predict, graphics="true",
                              species=species, assembly=assemblies, short_names=mircro_names, adapter=adapter,
                              recursiveAdapterTrimming=recursive_adapter_trimming, libmode=lib_mode, nolib=no_libs,
                              microRNA=mir, removeBarcode=str(remove_barcode),
                              adapterMinLength=str(adapter_minLength), adapterMM=str(adapterMM), seed=str(seed),
                              noMM=str(mm), alignType=str(align_type), minRC=str(rc), solid=solid,
                              guessAdapter=guess_adapter, highconf=high_conf, homolog=homolog,
                              user_files=libs_files, minReadLength=minReadLength, mBowtie=mBowtie)

    conf_file_location = os.path.join(FS.location, "conf.txt")
    newConf.write_conf_file(conf_file_location)

    os.system(
        'qsub -v pipeline="bench",configure="' + conf_file_location + '",key="' + pipeline_id + '",outdir="' + FS.location + '",name="' + pipeline_id
        + '_sRNAbench' + '" -N ' + pipeline_id + '_sRNAbench /shared/sRNAtoolbox/core/bash_scripts/run_sRNAbench.sh')

    return redirect("/srnatoolbox/jobstatus/srnabench/?id=" + pipeline_id)


def result(request):
    if 'id' in request.GET:
        try:
            job_id = request.GET['id']
            new_record = JobStatus.objects.get(pipeline_key=job_id)
            assert isinstance(new_record, JobStatus)

            if new_record.job_status == "Finished":
                return redirect("http://bioinfo5.ugr.es/sRNAtoolbox/sRNAbench/sRNAbench.php?launched=true&id=" + job_id)
            else:
                return redirect("/srnatoolbox/jobstatus/srnabench/?id=" + job_id)
        except:
            return redirect("/srnatoolbox/jobstatus/srnabench/?id=" + job_id)
    else:
        redirect("/srnatoolbox/srnabench")


def add_sumimg(new_record, results):
    sumimgs = []
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "mappingStat.png")):
        sumimgs.append(os.path.join(new_record.pipeline_key, "graphs", "mappingStat.png"))
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "byLength_stack.png")):
        sumimgs.append(os.path.join(new_record.pipeline_key, "graphs", "byLength_stack.png"))
    if len(sumimgs) != 0:
        results["sumimgs"] = sumimgs


def add_preimg(new_record, results):
    imgs = []
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "readLengthFull.png")):
        imgs.append([os.path.join(new_record.pipeline_key, "graphs", "readLengthFull.png"), "Read Length Distribution of Raw Input Reads"])
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "readLengthAnalysis.png")):
        imgs.append([os.path.join(new_record.pipeline_key, "graphs", "rnaComposition_readLength.png"), "Read Length Distribution of Reads in Analysis"])
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "mappedReadsLenghtDist.png")):
        imgs.append([os.path.join(new_record.pipeline_key, "graphs", "genomeMappedReads.png"), "Read Length Distribution of Genome mapped reads"])
    if len(imgs) != 0:
        results["preimgs"] = imgs


def add_mirimg(new_record, results):
    imgs = []
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "microRNA_species.png")):
        imgs.append(os.path.join(new_record.pipeline_key, "graphs", "microRNA_species.png"))
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "microRNA_top.png")):
        imgs.append(os.path.join(new_record.pipeline_key, "graphs", "microRNA_top.png"))
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "isomiR_NTA.png")):
        imgs.append(os.path.join(new_record.pipeline_key, "graphs", "isomiR_NTA.png"))
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "isomiR_otherVariants.png")):
        imgs.append(os.path.join(new_record.pipeline_key, "graphs", "isomiR_otherVariants.png"))
    if len(imgs) != 0:
        results["mirimg"] = imgs


def add_preproc(params, results):
    preproc = {}
    raw = int(params.params["readsRaw"])
    preproc["Raw reads:"] = str(raw)
    if "readsAdapterFound" in params.params:
        preproc["Adapter trimmed"] = str(int(params.params['readsAdapterFound'])) + " (" + str(round(
            int(params.params['readsAdapterFound']) * 100.0 / raw, 2)) + "%)"

    else:
        preproc["Input was adapter trimmed"] = ""
    preproc["Length filtered (min):"] = str(int(params.params['readsLengthFilteredMin'])) + " (" + str(round(
        int(params.params['readsLengthFilteredMin']) * 100.0 / raw, 2)) + "%)"

    preproc["Quality filtered:"] = str(int(params.params['readsQRCfiltered'])) + " (" + str(round(
        int(params.params['readsQRCfiltered']) * 100.0 / raw, 2))+ "%)"

    preproc["Reads in analysis:"] = str(int(params.params['reads'])) + " (" + str(round(int(params.params['reads']) * 100.0 / raw, 2)) + "%)"

    if len(preproc.keys()) > 0:
        results["preproc"] = preproc


def add_mirprof(params, results):
    mirprof = {}
    try:
        mirprof["Detected mature miR:"] = str(int(params.params['detectedMature'])) + " (" + str(round(
            int(params.params['detectedMature']) * 100.0 / int(params.params['matureDB']), 2)) + "%)"
        mirprof["Reads mapped to miRNAs:"] = str(int(params.params['readsRCmatureSense'])) + " (" + str(round(
            int(params.params['readsRCmatureSense']) * 100.0 / int(params.params['assignedRC']), 2)) + "%)"
            #int(params.params['detectedMature']) * 100.0 / int(params.params['matureDB']), 2)) + "%)"
    except:
        mirprof["Detected mature miR:"] = str(0)
    try:
        mirprof["Detected hairpin miR:"] = str(int(params.params['detectedHairpin'])) + " (" + str(round(
            int(params.params['detectedHairpin']) * 100.0 / int(params.params['hairpinDB']), 2)) + "%)"
        mirprof["Reads mapped to miRBase hairpins:"] = str(int(params.params['readsRChairpinSense'])) + " (" + str(round(
            int(params.params['readsRChairpinSense']) * 100.0 / int(params.params['assignedRC']), 2)) + "%)"
    except:
        mirprof["Reads mapped to miRBase hairpins:"] = str(0)
    if len(mirprof.keys()) > 0:
        results["mirprof"] = mirprof

def add_mirdown(params, outdir ,results):
    mirdown = {}
    if os.path.exists(os.path.join(outdir,"mature_sense.grouped")):
        mirdown["miRNA profile (Single Assignment):"] = os.path.join(outdir,"mature_sense.grouped").replace(MEDIA_ROOT,MEDIA_URL)
    if os.path.exists(os.path.join(outdir, "mature_sense_SA.grouped")):
        mirdown["miRNA profile (Multiple Assignment):"] = os.path.join(outdir, "mature_sense_SA.grouped").replace(MEDIA_ROOT,MEDIA_URL)
    if os.path.exists(os.path.join(outdir, "microRNAannotation.txt")):
        mirdown["isomiR profile:"] = os.path.join(outdir, "microRNAannotation.txt").replace(MEDIA_ROOT,MEDIA_URL)
    if os.path.exists(os.path.join(outdir, "reads.annotation")):
        mirdown["isomiR annotation:"] = os.path.join(outdir, "reads.annotation").replace(MEDIA_ROOT,MEDIA_URL)

    if len(mirdown.keys()) > 0:
        results["mirdown"] = mirdown

        # int(params.params['detectedMature']) * 100.0 / int(params.params['matureDB']), 2)) + "%)"
def add_mapping_result(new_record, parameters, results):
    mapping_results = {}
    if os.path.exists(os.path.join(new_record.outdir, "graphs", "genomeDistribution.png")):
        genomeDistribution = os.path.join(new_record.pipeline_key, "graphs", "genomeDistribution.png")
        results["genomeDistribution"] = genomeDistribution
    if 'readsRCgenomeMapped' in parameters:
        raw = int(parameters["reads"])
        raw_unique = int(parameters["readsUnique"])

        mapping_results["Genome mapped reads:"] = str(int(parameters['readsRCgenomeMapped'])) + "(" + str(round(
            int(parameters['readsRCgenomeMapped']) * 100.0 / raw, 2)) + "%)"

        mapping_results["Unique Genome mapped reads:"] = str(int(parameters['readsURgenomeMapped'])) + "(" + str(round(
            int(parameters['readsURgenomeMapped']) * 100.0 / raw_unique, 2)) + "%)"


        print(mapping_results)

    elif 'assignedRC' in parameters:
        raw = int(parameters["readsRaw"])
        mapping_results["Genome mapped reads:"] = str(int(parameters['assignedRC'])) + "(" + str(round(
            int(parameters['assignedRC']) * 100.0 / raw, 2)) + "%)"

    if len(mapping_results.keys()) > 0:
        results["mapping_results"] = mapping_results


def add_libs(parameters, results,config):
    libs = {}
    if config.params.get("libs"):
        for i, lib in enumerate(config.params.get("libs")):
        #for i, lib in enumerate(config.params["libs"]):
            print(lib)
            val = lib.split("/")[-1].split(".")[0]
            if "desc" in config.params:
                #print(parameters["desc"][i])
                try:
                    desc = parameters["desc"][i]
                    print(desc)
                except:
                   desc = val
            else:
                desc = val

            if "readsRC" + val + "Sense" in parameters:
                libs[(desc, val)] = {}
                print(val)
                print("in sense")
                try:
                    libs[(desc, val)]["Mapped reads in sense direction:"] = str(parameters["readsRC" + val + "Sense"]) + \
                    "(" + str(round(int(parameters["readsRC" + val + "Sense"]) * 100.0 / int(parameters['assignedRC']), 2)) + "%)"
                except:
                    libs[(desc, val)]["Mapped reads in sense direction:"] = str(parameters[val + "Sense"]) + "(" + str(round(0)) + "%)"

            if "readsRC" +val + "ASense" in parameters:
                try:
                    libs[(desc, val)]["Mapped reads in antisense direction:"] = str(parameters["readsRC"+val + "ASense"]) +\
                    "(" + str(round(int(parameters["readsRC" + val + "ASense"]) * 100.0 / int(parameters["assignedRC"]), 2)) + "%)"
                except:
                    libs[(desc, val)]["Mapped reads in sense direction:"] = str(parameters[val + "ASense"]) + "(" + str(round(0)) + "%)"

    if len(list(libs.keys())) > 0:
            results["libs"] = libs


def add_novel(new_record, results):
    novel = {}
    if os.path.exists(os.path.join(new_record.outdir, "novel.txt")):
        num_lines = sum(1 for line in open(os.path.join(new_record.outdir, "novel.txt")))
        #novel["Predicted novel microRNAS: "] = parameters["novelMiR"] + " with a total read count: " + parameters["readsNovel"]
        novel["new hairpins predicted: "] = str(num_lines-1)
        results["novel"] = novel


def add_trna(results):
    trna = True
    results["trna"] = trna

import time

# def BW_download():



def check_image_files(input_list, seconds=5):

    input_list = [f.replace(MEDIA_URL,MEDIA_ROOT) for f in input_list]
    #out_path1 = out_path1.replace(media_root, media_url)
    for i in range(seconds):
        a_exist = [f for f in input_list if os.path.isfile(f)]
        if len(input_list) > len(a_exist):
            time.sleep(1)
        else:
            return True

def load_table(input_file,title):
   parser = DeStatsParser(input_file)
   stats = [obj for obj in parser.parse()]
   header = stats[0].get_sorted_attr()
   stats_result = Result(title, define_table(header, 'TableResult')(stats))
   return stats_result

def read_message(file_path):
    with open(file_path, 'r') as file:
        data = file.read().replace('\n', '<br>')
    return data



def result_new(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)

        results = {}
        image_list = []
        results["id"] = job_id
        print(os.path.join(new_record.outdir, "results.txt"))
        if os.path.exists(os.path.join(new_record.outdir, "message.txt")):
            results["user_message"] = read_message(os.path.join(new_record.outdir, "message.txt"))

        # if (new_record.job_status == "Finished" and os.path.exists(os.path.join(new_record.outdir, "results.txt"))):
        if os.path.exists(os.path.join(new_record.outdir, "results.txt")):
            params = ParamsBench(os.path.join(new_record.outdir, "parameters.txt"), os.path.join(new_record.outdir, "results.txt"),os.path.join(new_record.outdir, "conf.txt"))

            config_params = ParamsBench(os.path.join(new_record.outdir, "conf.txt"))
            if new_record.job_status == "Running":
                results["running"] = True

            if os.path.exists(new_record.outdir):

                parameters = params.params
                #Show Genome tab
                if parameters.get("species") != "NA":
                    results["Genome_mode"] = True

                #Reference used
                if parameters.get("miRNA_ref"):
                    results["mirna_ref"] = parameters.get("miRNA_ref")
                else:
                    results["mirna_ref"] = "miRBase"

                 #Summary
                add_sumimg(new_record, results)
                if os.path.exists(os.path.join(new_record.outdir,"preprocWeb.txt")):
                    with open(os.path.join(new_record.outdir,"preprocWeb.txt"),"r") as pre_f:
                        p_summary = pre_f.read()
                    results["preproc_sum"] = p_summary
                # try:
                #     results["readLen_sum"] = Full_read_length_divs(new_record.outdir)
                # except:
                #     results["readLen_sum"] = None
                results["readLen_sum"] = full_read_length(new_record.outdir)
                image_list.append(results["readLen_sum"][0][1])
                image_list.append(results["readLen_sum"][1][1])

                results["readLen_type"] = read_length_type(new_record.outdir)
                image_list.append(results["readLen_type"][0][1])

                results["mapping_stat_table"] = make_table_gen(os.path.join(new_record.outdir,"stat","mappingStat_libs_sensePref_web.txt"),
                                                               "Profiling results by RNA type.")
                                                 #"Profiling results by RNA type.")
                results["mapping_stat_plot"] = mapping_stat(new_record.outdir)
                image_list.append(results["mapping_stat_plot"] [0][1])

                # results["modal_test"] = results["readLen_sum"][0][0]
                # results["modal_id"] = results["readLen_sum"][0][2]

                #Preproc
                # if "inputFinished" in parameters:
                #     add_preproc(params, results)
                #     add_preimg(new_record, results)

                #Genome Mapping
                if "species" in parameters:
                    add_mapping_result(new_record, parameters, results)

                if os.path.exists(os.path.join(new_record.outdir,"bigwig","download.txt")):
                    down_file = os.path.join(new_record.outdir,"bigwig","download.txt")
                    parser = BWParser(down_file)
                    table = [obj for obj in parser.parse(MEDIA_ROOT,MEDIA_URL)]
                    header = table[0].get_sorted_attr()
                    dt = Result("BigWig Download", define_table(header, 'TableResult')(table))
                    results["down_table"] = dt
                if os.path.exists(os.path.join(new_record.outdir, "bigwig", "trackhub.txt")):
                    with open(os.path.join(new_record.outdir, "bigwig", "trackhub.txt"), 'r') as myfile:
                        results["UCSC_link"] = myfile.read()



                #MicroRNA summary
                if "microRNA" in parameters:
                    if "detectedMature" in parameters:
                        add_mirimg(new_record, results)
                        add_mirprof(params, results)
                        add_mirdown(params, new_record.outdir ,results)

                    # results["miRNA_plots"] = top_miRNA_plot(os.path.join(new_record.outdir,"stat","microRNA_top.txt"), "Top 10 miRNAs")
                    # image_list.append(results["miRNA_plots"][0][1])

                #sRNA summary
                if "libs" in parameters:
                    add_libs(parameters, results, config_params)

                #New Mirna
                if os.path.exists(os.path.join(new_record.outdir, "novel.txt")):
                    add_novel(new_record, results)
                if os.path.exists(os.path.join(new_record.outdir, "tRNA_mature_sense.grouped")):
                    add_trna(results)

                import glob
                files = glob.glob(new_record.outdir + "/*.zip")
                files.sort(key=os.path.getmtime)
                zip_file = files[-1]

                if os.path.exists(zip_file):
                    #zip_file = os.path.join(new_record.outdir, "sRNAbench.zip")
                    zip_file = "/".join(zip_file.split("/")[-2:])
                    results["zip"] = zip_file

                try:
                    web_par_path = os.path.join(new_record.outdir, "parametersWeb.txt")
                    with open(web_par_path,"r") as web_par_file:
                        web_pars = web_par_file.read()
                    results["parameters"] = web_pars
                    results["parameters"]=results["parameters"].replace(MEDIA_ROOT,"")
                except:
                    pass

                results["date"] = new_record.start_time + datetime.timedelta(days=15)
            ex_out = check_image_files(image_list, 15)
            return render(request, "srnabench_result.html", results)

        else:

            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))
    else:
        return redirect(reverse_lazy('BENCH'))


def render_table(request, mode, job_id, lib=""):

    result={}
    result["id"] = job_id
    new_record = JobStatus.objects.get(pipeline_key=job_id)


    if mode == "pre-microRNA":
        result["title"] = "Mapping results to pre-microRNA"
        ifile = os.path.join(new_record.outdir, "hairpin_sense.grouped")
        parser = MirBaseParser(ifile)
        #parser = MatureParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "microRNA"

        except:
            r = Result(id, define_table(["Empty"], 'TableResult')([]))

    if mode == "mature":
        result["title"] = "Profiling of mature microRNAs (Multiple Assignment of reads, i.e. the reads are assigned to all loci or reference sequences to which they map with the same quality)"
        ifile = os.path.join(new_record.outdir, "mature_sense.grouped")
        parser = MatureParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "microRNA"
        except:
            pass

    if mode == "maturesa":
        result["title"] = "Profiling of mature microRNAs (Single Assignment of reads; each read is only assigned once, i.e. to the loci or reference sequence with the highest read count)"
        ifile = os.path.join(new_record.outdir, "mature_sense_SA.grouped")
        parser = MatureParserSA(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "microRNA"
        except:
            pass

    if mode == "old_isomir":
        result["title"] = "isomiR summary: (NTA: non-templated addition; lv=length variant; E=extension; T=trimmed; mv=multi-variant)"
        ifile = os.path.join(new_record.outdir, "stat", "isomiR_summary.txt")
        parser = IsomirParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "microRNA"
        except:
            pass

    if mode == "isomir":
        result["title"] = "isomiR summary: (NTA: non-templated addition; lv=length variant; E=extension; T=trimmed; mv=multi-variant)"
        ifile = os.path.join(new_record.outdir, "stat", "isomiR_summary.txt")
        parser = GeneralParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "microRNA"
        except:
            pass

    if mode == "novel":
        result["title"] = mark_safe("Novel microRNAs" + render_modal('novel_tab'))
        ifile = os.path.join(new_record.outdir, "novel.txt")
        parser = NovelParser(ifile)
        #parser = MatureParser(ifile)
        #parser = TRNAParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            #r = Result(id, define_table(["header1", "header2", "header3"], 'TableResult')(table[:500]))
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            #result["sec"] = "novel"
            result["sec"] = "trna"
        except:
            pass

    if mode == "general":
        result["title"] = "merengue"
        ifile = os.path.join(new_record.outdir, "GRCh38_p10_RNAcentral_sense_SA.grouped")
        parser = GeneralParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        header = table[0].get_sorted_attr()
        r = Result(id, define_table(header, 'TableResult')(table[:500]))
        result["table"] = r
        result["sec"] = "trna"

    if mode == "trna":
        result["title"] = "tRNA mapped reads"
        ifile = os.path.join(new_record.outdir, "tRNA_mature_sense.grouped")
        parser = TRNAParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "trna"
        except:
            pass

    if mode == "MA":
        result["title"] = mark_safe(lib + " (Multiple Assignment)" + render_modal('SRNAinput'))

        ifile = os.path.join(new_record.outdir, lib + "_sense.grouped")
        parser = MAParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "libs"
        except:
            pass

    if mode == "SA":
        result["title"] = lib
        ifile = os.path.join(new_record.outdir, lib + "_sense_SA.grouped")
        parser = SAParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "libs"
        except:
            pass

    if mode == "MA_antisense":
        result["title"] = lib
        ifile = os.path.join(new_record.outdir, lib + "_antisense.grouped")
        parser = MAParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "libs"
        except:
            pass

    if mode == "SA_antisense":
        result["title"] = lib
        ifile = os.path.join(new_record.outdir, lib + "_antisense_SA.grouped")
        parser = SAParser(ifile)
        table = [obj for obj in parser.parse()]
        id = "table"
        try:
            header = table[0].get_sorted_attr()
            r = Result(id, define_table(header, 'TableResult')(table[:500]))
            result["table"] = r
            result["sec"] = "libs"
        except:
            pass

    return render(request, "tables_srnabench.html", result)


def make_table_gen(input_file,id):
    id = id
    ifile = input_file
    parser = GeneralParser(ifile)
    table = [obj for obj in parser.parse()]
    header = table[0].get_sorted_attr()
    r = Result(id, define_table(header, 'TableResult')(table[:500]))
    return r



def show_align(request, job_id, type, name):

        result={}
        result["id"] = job_id
        new_record = JobStatus.objects.get(pipeline_key=job_id)
        outdir = new_record.outdir
        if type == "pre-microRNA":
            ifile = os.path.join(outdir, "hairpin", name + ".align")
            if os.path.exists(ifile):
                content = open(ifile).readlines()
            else:
                content = "No Alignment available. Read count below threshold"
            desc = "alignment to pre-microRNA"
            back = "pre-microRNA"

        elif type == "novel":
            ifile = os.path.join(outdir, "novel", name + ".align")
            content = open(ifile).readlines()
            desc = "Alignment to predicted microRNA"
            back = "novel"

        else:
            return redirect(reverse("sRNABench.views.input"))

        result["back"] = back
        result["desc"] = desc
        result["name"] = name
        result["align"] = "".join(content)

        return render(request, "align.html", result)

class upload_files(FormView):

    def post(self, request):
        path = request.path
        folder = path.split("/")[-1]
        make_folder(os.path.join(MEDIA_ROOT,folder))

        upload_folder=os.path.join(MEDIA_ROOT, folder, "uploads" )
        make_folder(upload_folder)
        if "file" in self.request.FILES:
            form = FileForm(request.POST, request.FILES)
            print("file in POST " + folder)
            if form.is_valid():
                print("valid form " + folder)
                ufile = form.save()

                is_new = True
                name = ufile.file.name.split("/")[-1]
                temp_path = ufile.file.name
                dest_path = os.path.join(upload_folder, name)
                if os.path.exists(dest_path):
                    is_new = False
                url = dest_path.replace(MEDIA_ROOT,MEDIA_URL)
                print(name)
                shutil.move(os.path.join(MEDIA_ROOT, ufile.file.name), dest_path)
                print(MEDIA_URL)
                data = {'is_valid': is_new, 'name': name, 'url': url}
                print(folder)
                return JsonResponse(data)
            else:
                data = {}
                data["alert"] = True
                return JsonResponse(data)

def ajax_dropbox(request):
    data ={}
    folder = request.GET.get('id', None)
    files = request.GET.get('files', None)
    dest_folder = os.path.join(MEDIA_ROOT, folder)
    make_folder(dest_folder)
    dest_file = os.path.join(dest_folder, "dropbox.txt")
    sample_list = files.split(",")
    sample_list = [x.strip(' ') for x in sample_list]
    sample_list = list(filter(None, sample_list))
    if os.path.exists(dest_file):
        with open(dest_file,"r") as sf:
            lines = sf.read().split("\n")
        c_samples = []
        for s in sample_list:
            if s not in lines:
                c_samples.append(s)
        sample_list = c_samples
    with open(dest_file, "a") as lf:
        for s in set(sample_list):
            lf.write(s + "\n")

    unique_samples = list(set(sample_list))
    data["links"] = unique_samples
    data["samples"] = [x.split("/")[-1] for x in unique_samples]
    return JsonResponse(data)


def ajax_receive_input(request):

    folder = request.GET.get('id', None)
    dest_folder = os.path.join(MEDIA_ROOT,folder)
    make_folder(dest_folder)
    SRA_input = request.GET.get("SRA_input", None)
    links_input = request.GET.get("links_input", None)
    if SRA_input:
        sample_list = SRA_input.split("\n")
        input_type = "SRA"
        dest_file = os.path.join(dest_folder,"SRA.txt")
    elif links_input:
        sample_list = links_input.split("\n")
        input_type = "filelink"
        dest_file = os.path.join(dest_folder, "links.txt")

    sample_list = [x.strip(' ') for x in sample_list]
    sample_list = list(filter(None, sample_list))


    if os.path.exists(dest_file):
        with open(dest_file,"r") as sf:
            lines = sf.read().split("\n")
        c_samples = []
        for s in sample_list:
            if s not in lines:
                c_samples.append(s)
        sample_list = c_samples
    with open(dest_file, "a") as lf:
        for s in set(sample_list):
            lf.write(s + "\n")

    data = {}
    data["id"] = folder
    unique_samples = list(set(sample_list))
    data["samples"] = unique_samples
    if SRA_input:
        data["links"] = ["https://www.ncbi.nlm.nih.gov/sra/?term="+x for x in unique_samples]
    elif links_input:
        data["links"] = unique_samples
    data["input_type"] = input_type
    return JsonResponse(data)

def ajax_drive(request):
    data = {}

    folder = request.GET.get('id', None)
    dest_folder = os.path.join(MEDIA_ROOT, folder)
    make_folder(dest_folder)
    dest_file = os.path.join(dest_folder, "drive.json")

    ids = request.GET.getlist('ids[]', None)
    sample_list = request.GET.getlist('names[]', None)
    urls = request.GET.getlist('urls[]', None)
    token = request.GET.get('token', None)

    sample_dict = dict()

    for n,i in enumerate(sample_list):

        sample_dict[i] = [i,
                          ids[n],
                          urls[n],
                          token]

    if os.path.exists(dest_file):
        try:
            with open(dest_file, "r") as read_file:
                old_samples = json.load(read_file)
        except:
            old_samples = {}

        unrepeated_keys = [k for k in sample_dict if k not in old_samples.keys()]

        if len(old_samples.keys()) > 0:
            old_keep = {k : old_samples[k] for k in old_samples.keys() if k not in unrepeated_keys}
            sample_dict.update(old_keep)
    else:
        unrepeated_keys = sample_dict.keys()

    with open(dest_file, "w") as write_file:
        json.dump(sample_dict,write_file)

    # samples_req = {k : sample_dict[k] for k in sample_dict.keys() if k in unrepeated_keys}

    data["samples"] = sample_dict
    data["samples_k"] = list(unrepeated_keys)
    # js_string = json.dumps(data)
    # data = json.loads(js_string)
    return JsonResponse(data)

def drive_del(folder,input_name):

    dest_file = os.path.join(folder, "drive.json")
    with open(dest_file, "r") as read_file:
        old_samples = json.load(read_file)
    old_samples.pop(input_name)

    if len(old_samples.keys()) > 0:
        with open(dest_file, "w") as write_file:
            json.dump(old_samples,write_file)
    else:
        os.remove(dest_file)


def ajax_del(request):
    data = {}
    folder = request.GET.get('id', None)
    dest_folder = os.path.join(MEDIA_ROOT,folder)
    del_string = request.GET.get('to_del', None)
    if del_string == "ALL":
        shutil.rmtree(dest_folder)
        make_folder(dest_folder)
        return JsonResponse(data)

    input_type,in_string = del_string.split("::")
    writing_file = os.path.join(dest_folder,"writing")

    if input_type == "uploaded":
        os.remove(os.path.join(dest_folder,in_string))
        return JsonResponse(data)
    elif input_type == "drive":
        drive_del(dest_folder,in_string)
        return JsonResponse(data)
    elif input_type == "SRA":
        samples_file = os.path.join(dest_folder,"SRA.txt")
    elif input_type == "filelink":
        samples_file = os.path.join(dest_folder, "links.txt")
    elif input_type == "dropbox":
        samples_file = os.path.join(dest_folder, "dropbox.txt")
    while os.path.exists(writing_file):
        time.sleep(1)
    with open(samples_file, "r") as f:
        lines = f.readlines()
    os.system("touch " + writing_file)
    with open(samples_file, "w") as f:
        for line in lines:
            if line.strip("\n") != in_string:
                f.write(line)
    os.remove(writing_file)

    return JsonResponse(data)




def make_config(req_obj):

    param_dict = req_obj.GET
    config_lines = []
    #input parameters
    # sra_string = param_dict.get("sra_input")
    # jobID = param_dict.get("jobId")
    outID = param_dict.get("jobId")
    make_folder(os.path.join(MEDIA_ROOT,outID))
    uploadID = param_dict.get("uploadID")
    dest_file = os.path.join(MEDIA_ROOT, outID, "conf.txt")
    # free lines
    config_lines.append("maxUR=-1")
    config_lines.append("maxUR=mm=1")
    config_lines.append("type=rules")
    config_lines.append("mode=lax")
    config_lines.append("onlyCluster=true")
    config_lines.append("miRdb=2")
    config_lines.append("minAlignLength=20")
    config_lines.append("minNrReadsInFamily=3")
    config_lines.append("minNrMismatchesFamily=2")
    config_lines.append("bindings=16")
    config_lines.append("thresholdCluster=0.9")

    #advanced parameters

    ref_species = param_dict.get("species_hidden")
    if ref_species:
        if ref_species == "GUESS":
            config_lines.append("guessSpecies=true")
            # print("GUESS")
        else:
            # short, assembly = ref_species.split(",")
            short = ref_species
            # config_lines.append("species="+assembly)
            config_lines.append("microRNA="+short)

    protocol = param_dict.get("protocol")

    if protocol == "TRIMMED":
        protocol = None
    if protocol == "GUESS":
        protocol = "guess"

    if protocol == "Custom":
        protocol = None
        adapter_manual = param_dict.get("adapter_manual")
        if adapter_manual:
            config_lines.append("adapter=" + adapter_manual)
        else:
            config_lines.append("adapter=" + param_dict.get("adapter_chosen"))

        # adapter length
        config_lines.append("adapter=" + str(param_dict.get("adapter_length")))
        config_lines.append("adapter=" + str(param_dict.get("adapter_mismatch")))
        config_lines.append("adapter=" + str(param_dict.get("nucleotides_5_removed")))
        config_lines.append("adapter=" + str(param_dict.get("nucleotides_3_removed")))
        config_lines.append("adapter=" + str(param_dict.get('adapter_recursive_trimming')).lower())


    if protocol:
        line = "protocol=" + protocol
        config_lines.append(line)

    #output folder
    # results_folder = os.path.join(MEDIA_ROOT, jobID, "query")
    # config_lines.append("output=" + results_folder)
    # config_lines.append("p=6")
    file_content = "\n".join(config_lines)
    with open(dest_file,"w") as cf:
        cf.write(file_content)

    return outID

def assign_IDs(input_folder):

    ignore_list = ["dropbox.txt", "drive.json", "links.txt", "SRA.txt", "conf.txt", "launched"]
    to_launch = []
    all_files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f)) ]
    # generate_id()
    #files
    files = [f for f in os.listdir(input_folder) if (os.path.isfile(os.path.join(input_folder, f)) and f not in ignore_list)]
    if files:
        for f in files:
            to_launch.append([ generate_id(), os.path.join(input_folder,f) , "file"  ])
    if "SRA.txt" in all_files:
        with open(os.path.join(input_folder,"SRA.txt"), 'r') as rfile:
            lines = rfile.readlines()
        for line in lines:
            to_launch.append([generate_id(), line.rstrip(), "SRA"])

    if "links.txt" in all_files:
        with open(os.path.join(input_folder,"links.txt"), 'r') as rfile:
            lines = rfile.readlines()
        for line in lines:
            to_launch.append([generate_id(), line.rstrip(), "filelink"])

    if "dropbox.txt" in all_files:
        with open(os.path.join(input_folder,"dropbox.txt"), 'r') as rfile:
            lines = rfile.readlines()
        for line in lines:
            to_launch.append([generate_id(), line.rstrip(), "Dropbox"])

    if "drive.json" in all_files:
        with open(os.path.join(input_folder,"drive.json"), 'r') as rfile:
            data = json.load(rfile)
        for k in list(data.keys()):
            to_launch.append([generate_id(), k.rstrip(),"Drive"])

    dest_file = os.path.join(input_folder,"IDs")
    with open(dest_file, 'w') as wfile:
        for line in to_launch:
            wfile.write( "\t".join(line)+"\n" )


    return to_launch


def parse_mirgeneDB():
    file_path = CONF.get("MirGeneDB_data")
    with open(file_path, "r") as read_file:
        lines = read_file.readlines()

    db_list = []
    for line in lines[1:]:
        row = line.rstrip().split("\t")
        db_list.append([":".join([row[1].capitalize(),row[3],row[5]]), row[2]])

    return db_list



class MirG(FormView):
    template_name = 'miRNAgFree.html'
    # template_name = 'Messages/miRgFree/drive_test.html'
    form_class = miRNAgFreeForm
    success_url = reverse_lazy("MIRG")

    def get(self, request,**kwargs):
        path = request.path
        jobID = generate_uniq_id()
        folder_path = os.path.join(MEDIA_ROOT,jobID)
        # os.mkdir(folder_path)
        data_url = reverse_lazy("multi:multi_new") + jobID
        mirgeneDB = parse_mirgeneDB()
        print(data_url)
        return render(self.request, 'miRNAgFree.html', { "jobID":jobID,
                                                         "data_url": data_url,
                                                         "mirgenedb_list": mirgeneDB,

                                                         })

    def post(self, request, *args, **kwargs):
        request.POST._mutable = True
        #print(SPECIES_PATH)
        request.POST['species'] = request.POST['species_hidden'].split(',')
        print(request.POST['species'])
        print(request.POST['species_hidden'].split(','))
        request.POST._mutable = False
        return super(MirG, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.

        form.clean()
        call, pipeline_id = form.create_call()
        self.success_url = reverse_lazy('srnabench') + '?id=' + pipeline_id

        print(call)
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        return super(MirG, self).form_valid(form)

    def print_file_locat(self, form):
        print(form.cleaned_data)


def make_input_line(init_folder, id, itype, input_field):

    if itype == "SRA" or itype == "filelink" or itype == "Dropbox" or itype == "file":
        input_line = "input=" + input_field + "\n"
        return input_line
    elif itype == "Drive":
        dest_file = os.path.join(init_folder, "drive.json")
        with open(dest_file, "r") as read_file:
            samples = json.load(read_file)

        try:
            name, fileid, url, token = samples.get(input_field)

            g_url = "https://www.googleapis.com/drive/v3/files/{}?alt=media".format(fileid)
            res_file = os.path.join(MEDIA_ROOT, id, name)
            input_line = "input=@drive;" + ";".join([g_url,res_file,token]) + "\n"

            touch_file = os.path.join(MEDIA_ROOT,id, "drive_downloaded")
            make_folder(os.path.join(MEDIA_ROOT,id))
            command = 'curl -H "Authorization: Bearer ' + token + '"' + " " + g_url + ' -o "' + res_file + '";touch ' + touch_file
            # command = 'curl -H "Authorization: Bearer ' + token + '"' + " " + g_url + ' -o "' + res_file + '"'
            comand_list = ["curl","-H", '"Authorization: Bearer ' + token + '"', g_url, "-o", '"{}"'.format(res_file)]
            comand_list = ["touch", os.path.join(MEDIA_ROOT,id, "test")]
            # time.sleep(1)
            #
            # subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            #                            shell=True)

            # with open(touch_file,"w") as tf:
            #     tf.write(command)
            # subprocess.Popen(comand_list)
            # os.system(command)
            # input_line = + res_file + "\n"

            return input_line
        except:
            return None


def create_call(pipeline_id, configuration_file_path):
    # pipeline_id = self.generate_id()
    name = pipeline_id + '_mirg'
    return 'qsub -v c="{configuration_file_path}" -N {job_name} {sh}'.format(
        configuration_file_path=configuration_file_path,
        job_name=name,
        sh=os.path.join(os.path.dirname(BASE_DIR) + '/core/bash_scripts/run_qsub.sh'))


def make_config_json(pipeline_id):
    cdict = {"pipeline_id": pipeline_id,
             "name": pipeline_id + "_miRg",
             "type": "miRNAgFree",
             "conf_input": os.path.join(MEDIA_ROOT, pipeline_id, "conf.txt"),
             "out_dir": os.path.join(MEDIA_ROOT, pipeline_id)}

    with open(os.path.join(MEDIA_ROOT, pipeline_id,"config.json"), "w") as write_file:
        json.dump(cdict, write_file)

    return os.path.join(MEDIA_ROOT, pipeline_id, "config.json"  )

class MirGLaunch(FormView):

    template_name = 'miRNAgFree/multi_status.html'

    def get(self, request, **kwargs):
        path = request.path

        jobID = request.GET.get('jobId', None)
        folder_path = os.path.join(MEDIA_ROOT,jobID)

        # ignore_list = ["dropbox.txt", "drive.json","links.txt", "SRA.txt", "config.txt", "IDs"]
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        param_dict = request.GET

        if not "conf.txt" in files:
            make_config(request)
            IDs = assign_IDs(folder_path)
            for line in IDs:
                print(line)
                ik, ifile, itype = line
                # to_launch.append([generate_id(), k.rstrip(), "Drive"])

                JobStatus.objects.create(job_name=" ", pipeline_key=ik, job_status="not_launched",
                                         start_time=datetime.datetime.now(),
                                         all_files=ifile,
                                         modules_files="",
                                         pipeline_type="miRNAgFree",
                                         outdir = os.path.join(MEDIA_ROOT,ik)
                                         )
            JobStatus.objects.create(job_name=" ", pipeline_key=jobID, job_status="not_launched",
                                     start_time=datetime.datetime.now(),
                                     all_files=" ",
                                     modules_files="",
                                     pipeline_type="multiupload",
                                     )
            data = dict()
            data["running"] = False
            IDs = []
            with open(os.path.join(folder_path, "IDs"), 'r') as rfile:
                lines = rfile.readlines()
                for line in lines:
                    IDs.append(line.rstrip().split("\t"))

            jobs_tbody = []
            for i in IDs:
                # print(i[0])
                new_record = JobStatus.objects.get(pipeline_key=i[0])
                job_stat = new_record.job_status
                if job_stat != "Finished":
                    data["running"] = True
                if job_stat == "sent_to_queue":
                    job_stat = "In queue"
                start = new_record.start_time.strftime("%H:%M:%S, %d %b %Y")
                if new_record.finish_time:
                    finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
                else:
                    finish = "-"
                click = '<a href="' + SUB_SITE + '/jobstatus/' + i[0] + '" target="_blank" > Go to results </a>'
                jobs_tbody.append([i[0], job_stat.replace("_"," "), start, finish, i[1], click])

            js_headers = json.dumps([{"title": "job ID"},
                                     {"title": "Status"},
                                     {"title": "Started"},
                                     {"title": "Finished"},
                                     {"title": "Input"},
                                     # { "title": "Select" }])
                                     {"title": 'Go to'}
                                     ])
            data["tbody"] = json.dumps(jobs_tbody)
            data["thead"] = js_headers
            data["id"] = jobID
            data["refresh_rate"] = 5

            return render(self.request, 'miRNAgFree/multi_status.html', data)

        elif param_dict.get("protocol"):

            return redirect(reverse_lazy("launch" )+ "?jobId=" + jobID)

        else:
            data = dict()
            data["running"] = False
            IDs = []
            with open(os.path.join(folder_path,"IDs"), 'r') as rfile:
                lines = rfile.readlines()
                for line in lines:
                    IDs.append(line.rstrip().split("\t"))

            with open(os.path.join(folder_path, "conf.txt"), "r") as cfile:
                config_content = cfile.read()

            jobs_tbody = []
            for i in IDs:
                # print(i[0])
                new_record = JobStatus.objects.get(pipeline_key=i[0])
                job_stat = new_record.job_status

                ### launching job
                # if job_stat == "downloading":
                #     # launch
                #     c_path = make_config_json(i[0])
                #     comm = create_call(i[0], c_path)
                #     # print("HERE")
                #     # print(comm)
                #     os.system(comm)
                #     new_record.job_status = 'sent_to_queue'


                if job_stat == "not_launched":

                    # new folder
                    dest_folder = os.path.join(MEDIA_ROOT,i[0])
                    make_folder(dest_folder)
                    # new config

                    config_path = os.path.join(dest_folder,"conf.txt")
                    input_type = i[2]
                    input_line = make_input_line(folder_path, i[0], input_type, i[1])
                    output_line = "output=" + os.path.join(MEDIA_ROOT,i[0]) + "\n"
                    new_content = input_line + output_line + config_content
                    with open(config_path,"w") as cf:
                        cf.write(new_content)

                    # launch
                    c_path = make_config_json(i[0])
                    comm = create_call(i[0], c_path)
                    os.system(comm)
                    new_record.job_status = 'sent_to_queue'
                    new_record.save()
                    if len(IDs) == 1:
                        return redirect(reverse_lazy('progress', kwargs={"pipeline_id": i[0]}))
                if job_stat != "Finished" and job_stat != "Finished with Errors":
                    data["running"] = True
                if job_stat == "sent_to_queue":
                    job_stat = "In queue"
                start = new_record.start_time.strftime("%H:%M:%S, %d %b %Y")
                if new_record.finish_time:
                    finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
                else:
                    finish = "-"
                job_stat = new_record.job_status
                click = '<a href="' + SUB_SITE + '/jobstatus/' + i[0] + '" target="_blank" > Go to results </a>'
                jobs_tbody.append([i[0], job_stat.replace("_"," "), start, finish, i[1], click])

            js_headers = json.dumps([{"title": "job ID"},
                                     {"title": "Status"},
                                     {"title": "Started"},
                                     {"title": "Finished"},
                                     {"title": "Input"},
                                     # { "title": "Select" }])
                                     {"title": 'Go to'}
                                     ])
            # print(jobs_tbody)
            data["tbody"] = json.dumps(jobs_tbody)

            data["thead"] = js_headers
            data["id"] = jobID
            data["refresh_rate"] = 90
            return render(self.request, 'miRNAgFree/multi_status.html', data)

def plot_barplot(input_mirna,input_values, scale=None, input_variable=None):

    data = [go.Bar(name=input_variable,
                   x=input_mirna,
                   y=input_values,
                   # marker=dict(color=perc_df.bar_color.values),
                   # hovertemplate="%{x}p: %{y}",
                   showlegend=False
                   )]

    if scale == "log10":
        scale = "log"
        # dtick = "D2"
        dtick = 1
    else:
        scale = "linear"
        dtick = float(roundup100(max(input_values)/4))
        # dtick = 1

    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=200,
            b=200,
            t=100,
            pad=4
        ),
        title=input_variable,
        font=dict(size=18),
        # autosize=False,
        # height=650,
        # width=1150,
        xaxis=dict(
            title=""),
        yaxis=dict(
            type=scale,
            automargin=True,
            # ticksuffix='%',
            tickprefix="   ",
            dtick=dtick,
            title=input_variable + "\n<br>")
    )
    fig = go.Figure(data=data, layout=layout)

    div = plot(fig, show_link=False, auto_open=False, include_plotlyjs=False, output_type="div",
               config={'editable': True})

    return div

def ajax_pie(request):

    miRNAs = request.GET.get('miRNAs', None)
    jobID = request.GET.get('id', None)
    variable = request.GET.get('variable', None)
    mirna_list = miRNAs.split(",")
    new_record = JobStatus.objects.get(pipeline_key=jobID)
    expression_file = os.path.join(new_record.outdir, "microRNAs.txt")
    with open(expression_file, "r") as ef:
        expression_df = pd.read_csv(ef, sep="\t")

    labels = ['Oxygen','Hydrogen','Carbon_Dioxide','Nitrogen']
    values = [4500, 2500, 1053, 500]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    div = plot(fig, show_link=False, auto_open=False, include_plotlyjs=False, output_type="div",
               config={'editable': True})
    data = {}
    data["plot"] = div
    # data["values"] = selected_df[variable].tolist()
    # data["jobID"] = jobID

    return JsonResponse(data)



def ajax_barplot(request):

    miRNAs = request.GET.get('miRNAs', None)
    jobID = request.GET.get('id', None)
    variable = request.GET.get('variable', None)
    scale = request.GET.get('scale', None)
    mirna_list = miRNAs.split(",")
    new_record = JobStatus.objects.get(pipeline_key=jobID)
    expression_file = os.path.join(new_record.outdir, "microRNAs.txt")
    with open(expression_file, "r") as ef:
        expression_df = pd.read_csv(ef, sep="\t")

    selected_df = expression_df[expression_df["name"].isin(mirna_list)]
    selected_df = selected_df[["name",variable]]

    data = {}
    data["plot"] = plot_barplot(selected_df["name"].tolist(), selected_df[variable].tolist(), scale, variable)
    data["values"] = selected_df[variable].tolist()
    data["jobID"] = jobID


    return JsonResponse(data)



def fill_blanks(input_seq, final_length):

    blank_number = final_length - len(input_seq)
    return input_seq + " " * blank_number


def ajax_fetch_pile(request):
    name = request.GET.get('name', None)
    names = name.split("_")
    name = names[0]
    print(name)
    jobID = request.GET.get('id', None)
    print(jobID)
    filename = os.path.join(MEDIA_ROOT,jobID,"align",name+".salign")
    with open(filename,"r") as af:
        lines = af.readlines()
    seq = lines[0]
    seq = re.sub("[0-9]+", "", seq)
    # lines[0] = "<b>" + lines[0] + "</b>"

    new_lines = []
    lengths = []
    for line in lines[1:]:
        sequence,count = line.split("\t")
        # new_lines.append(sequence)
        lengths.append(len(sequence))

    m = max(lengths)
    for i,line in enumerate(lines):
        sequence, count = line.split("\t")
        n = fill_blanks(sequence, m)
        to_paste = n + "     " + count
        new_lines.append(to_paste)

    data = {}
    new_lines[0] = "<b>" + new_lines[0] + "</b>"
    data["pile"] = "".join(new_lines)
    # data["pile"] = "".join(lines)
    data["seq"] = seq
    return JsonResponse(data)

def jsonTabler(input_tsv,drops=[]):
    with open(input_tsv, "r") as ef:
        table_df = pd.read_csv(ef, sep="\t")
        table_df = table_df.drop(drops,axis=1)
        headers = list(table_df.columns.values)
        values = table_df.values.tolist()
        header_list = []
        for h in headers:
            header_list.append({"title": h})

        js_headers = json.dumps(header_list)
        js_body = json.dumps(values)

        return js_headers,js_body, headers



def results(request):
    if 'id' in request.GET:
        job_id = request.GET['id']
        new_record = JobStatus.objects.get(pipeline_key=job_id)

        context = {}
        context["id"] = job_id
        context["date"] = new_record.start_time + datetime.timedelta(days=15)
        # parameters
        web_par_path = os.path.join(new_record.outdir, "conf.txt")
        with open(web_par_path, "r") as web_par_file:
            web_pars = web_par_file.read()
        context["parameters"] = web_pars.replace(MEDIA_ROOT, "")

        #Summary
        summary_path = os.path.join(new_record.outdir, "summaryReport.txt")
        with open(summary_path, "r") as web_par_file:
            summary_content = web_par_file.read()
        context["summary_content"] = summary_content.replace(MEDIA_ROOT, "")

        #explore predictions

        expression_file = os.path.join(new_record.outdir,"microRNAs.txt")
        with open(expression_file,"r") as ef:
            expression_df = pd.read_csv(ef, sep="\t")
        pred_names = expression_df['name'].tolist()
        context["prediction_list"] = pred_names

        context["exp_headers"],context["exp_body"], context["expression_vars"] = jsonTabler(expression_file)

        print(context["exp_headers"])
        print(context["exp_body"])

        #graphs


        return render(request, "mirnagfree_result.html", context)

