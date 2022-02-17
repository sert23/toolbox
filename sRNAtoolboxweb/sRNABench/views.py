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
from sRNAtoolboxweb.settings import BASE_DIR,MEDIA_ROOT,MEDIA_URL
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
from sRNABench.forms import sRNABenchForm
from utils import pipeline_utils
from utils.sysUtils import make_dir
from sRNABench.bench_plots_func import full_read_length,read_length_type,mapping_stat,top_miRNA_plot
from FileModels.deStatsParser import DeStatsParser
from FileModels.summaryParser import LinksParser, BWParser
from sRNAtoolboxweb.utils import render_modal
from django.utils.safestring import mark_safe
import pandas as pd
from django.http import JsonResponse

#CONF = json.load(file("/shared/sRNAtoolbox/sRNAtoolbox.conf"))
CONF = settings.CONF
SPECIES_PATH = CONF["species"]
SPECIES_ANNOTATION_PATH = CONF["speciesAnnotation"]
DB = CONF["db"]
FS = FileSystemStorage(CONF["sRNAtoolboxSODataPath"])
counter = itertools.count()


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
    form = sRNABenchForm()

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
            if parameters.get("microRNA") == "hsa":
                results["is_hsa"] = True
            else:
                results["is_hsa"] = False
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
            short_name = name.split(",")[0]
            afile = os.path.join(outdir, "hairpin", short_name + ".align")
            if os.path.exists(ifile):
                content = open(ifile).readlines()
            elif os.path.exists(afile):
                content = open(afile).readlines()
            else:
                content = "No Alignment available. Read count below threshold" + afile + short_name +" test" + name
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

def ajax_GeneCodis_top(request):
    jobID = request.GET.get("jobID")
    topN = int(request.GET.get("top"))

    new_record = JobStatus.objects.get(pipeline_key=jobID)
    outdir = new_record.outdir
    miRNA_file = os.path.join(outdir, "mature_sense.grouped")
    with open(miRNA_file, "r") as mf:
        miRNA_df = pd.read_csv(mf, sep="\t")

    names = list(miRNA_df["name"].unique())
    names = [i for i in names if i.startswith("hsa")]
    maxi = len(names)
    if topN < maxi:
        result = names[:topN]
    else:
        result = names

    # https://genecodis.genyo.es/gc4/externalquery&org=9606&genes=1,2,13,14,5

    data = {}
    data["jobID"] = jobID
    data["topN"] = topN
    data["names"] = result
    data["url"] = "https://genecodis.genyo.es/gc4/externalquery&org=9606&genes=" + ",".join(result)
    return JsonResponse(data)

class Bench(FormView):
    template_name = 'bench.html'
    form_class = sRNABenchForm
    success_url = reverse_lazy("BENCH")

    def post(self, request, *args, **kwargs):
        request.POST._mutable = True
        #print(SPECIES_PATH)
        request.POST['species'] = request.POST['species_hidden'].split(',')
        print(request.POST['species'])
        print(request.POST['species_hidden'].split(','))
        request.POST._mutable = False
        return super(Bench, self).post(request, *args, **kwargs)

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
        return super(Bench, self).form_valid(form)

    def print_file_locat(self, form):
        print(form.cleaned_data)


















def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)

    libs_files = []
    lib_mode = False
    no_libs = False
    guess_adapter = None
    recursive_adapter_trimming = None
    high_conf = False
    solid = None
    ifile = "/shared/sRNAtoolbox/testData/IK_exo.fastq.gz"

    adapter = "TGGAATTCTCGGGTGCCAAGG"
    species = ["hg19_5_mp", "NC_007605"]
    assemblies = ["hg19", "NC_007605"]
    mircro_names = ["hsa", "ebv"]

    mir = ":".join(mircro_names)
    homolog = ""

    adapter_minLength = "10"
    adapterMM = "1"

    outdir = FS.location

    rc = "2"
    mm = "0"
    seed = "20"
    align_type = "n"
    remove_barcode = "0"

    species_annotation_file = SpeciesAnnotationParser(SPECIES_ANNOTATION_PATH)
    species_annotation = species_annotation_file.parse()

    newConf = SRNABenchConfig(species_annotation, DB, FS.location, ifile, iszip="true",
                              RNAfold="RNAfold2",
                              bedGraph="true", writeGenomeDist="true", predict="true", graphics="true",
                              species=species, assembly=assemblies, adapter=adapter,
                              recursiveAdapterTrimming=recursive_adapter_trimming, libmode=lib_mode, nolib=no_libs,
                              microRNA=mir, removeBarcode=str(remove_barcode),
                              adapterMinLength=str(adapter_minLength), adapterMM=str(adapterMM), seed=str(seed),
                              noMM=str(mm), alignType=str(align_type), rc=str(rc), solid=solid,
                              guessAdapter=guess_adapter, highconf=high_conf, homolog=homolog,
                              user_files=libs_files)

    conf_file_location = os.path.join(FS.location, "conf.txt")
    newConf.write_conf_file(conf_file_location)

    os.system(
        'qsub -v pipeline="bench",configure="' + conf_file_location + '",key="' + pipeline_id + '",outdir="' + outdir + '",name="' + pipeline_id
        + '_sRNAbench' + '" -N ' + pipeline_id + '_sRNAbench /shared/sRNAtoolbox/core/bash_scripts/run_sRNAbench.sh')

    return redirect("/srnatoolbox/jobstatus/srnabench/?id=" + pipeline_id)
