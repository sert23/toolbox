# Create your views here.
import datetime
import itertools

from django.core.urlresolvers import reverse_lazy
import django_tables2 as tables
import pygal
import xlrd
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from pygal.style import LightGreenStyle
from .forms import DEForm

from FileModels.deStatsParser import DeStatsParser
from FileModels.sRNAdeparser import SRNAdeParser
from FileModels.GeneralParser import GeneralParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import *
from django.views.generic import FormView
from sRNAde.de_plots import make_seq_plot, make_length_plot, make_full_length_plot, make_length_genome_plot, \
                            make_genome_dist_plot, general_plot, general_plot_cols
import pandas as pd
import json

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


class Result:
    """
    Class to manage tables results and meta-info
    """

    def __init__(self, name, table):
        self.name = name.capitalize()
        self.content = table
        self.id = name.replace(" ", "_")


def de(request):
    return render(request, 'de.html', {})


def check_ids_param(idlist, samples, desc, pvalue, prob):
    groups = idlist.split("#")
    samples = samples.split("#")
    errors = {'errors': []}

    if not len(samples) == len(groups):
        errors['errors'].append(
            'The number of samples group is different in "list of sRNAbench IDs" and "Sample groups". '
            'Please use "#" in order to split samples')

    if (not len(idlist.replace("#", "").split(":")) != len(desc.split(":"))) and desc != "":
        errors['errors'].append(
            'The number of samples is different in "list of sRNAbench IDs"  and "List of Sample Description". '
            'Please use ":" in order to split samples')

    try:
        if float(pvalue) > 1.0 or float(pvalue) < 0:
            errors['errors'].append('The p-value must be in [0,1]: "' + pvalue + '" was found')
    except:
        errors['errors'].append('The p-value is not a valid Float number')

    try:
        if float(prob) > 1.0 or float(prob) < 0:
            errors['errors'].append('The probability must be in [0,1]: "' + prob + '" was found')

    except:
        errors['errors'].append('The probability value is not a valid Float number')

    if len(errors['errors']) == 0:
        return True

    else:
        return errors


def check_mat_file(mat):
    if istext(mat) and istabfile(mat):
        return True
    else:
        return {"errors": ["Matrix file must be a tab-separated text file"]}


def old_result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)

        results = {}
        results["id"] = job_id
        if new_record.job_status == "Finished":
            new_record.xls_files = new_record.xls_files.split(',')
            new_record.heatmaps = new_record.heatmaps.split(',')
            for file in new_record.xls_files:
                workbook = xlrd.open_workbook(file)
                names = workbook.sheet_names()
                Selection = [name for name in names if "Selection" in name]
                for sheet in Selection:
                    parser = SRNAdeParser(file, sheet)
                    list_d = [obj for obj in parser.parse()]
                    header = list_d[0].get_sorted_attr()
                    id = sheet.split("_")[-1] + "_" + "_".join(os.path.basename(file).split(".")[0].split("_")[-3:])
                    r = Result(id, define_table(header, 'TableResult')(list_d))
                    if "NOISeq" in sheet:
                        if "noiseqtable" in results:
                            results["noiseqtable"].append(r)
                        else:
                            results["noiseqtable"] = [r]

                    if "deSeq" in sheet:
                        if "deseqtable" in results:
                            results["deseqtable"].append(r)
                        else:
                            results["deseqtable"] = [r]

                    if "edgeR" in sheet:
                        if "edgertable" in results:
                            results["edgertable"].append(r)
                        else:
                            results["edgertable"] = [r]

                if len(Selection) > 0:
                    parser = SRNAdeParser(file, "none")
                    id = "_".join(os.path.basename(file).split(".")[0].split("_")[-3:])
                    list_d = [obj for obj in parser.get_consensus(*Selection)]
                    if len(list_d) > 1:
                        header = list_d[0].get_sorted_attr()
                        r = Result(id, define_table(header, 'TableResult')(list_d))
                        if "consensus" in results:
                            results["consensus"].append(r)
                        else:
                            results["consensus"] = [r]

            if new_record.stats_file and os.path.isfile(new_record.stats_file):
                parser = DeStatsParser(new_record.stats_file)
                stats = [obj for obj in parser.parse()]
                header = stats[0].get_sorted_attr()
                stats_result = Result("Read Processing Statistic", define_table(header, 'TableResult')(stats))
                results["stats"] = stats_result

                labels = [obj.sample for obj in stats]
                results["figures"] = []
                # adapter
                try:
                    adapter_chart = pygal.Bar(x_label_rotation=90, disable_xml_declaration=True, style=LightGreenStyle,
                                              show_legend=False)
                    adapter_chart.title = 'Adapter Cleaned'
                    adapter_chart.x_labels = labels
                    values = [float(obj.adapter_cleaned) / float(obj.raw_reads) * 100 for obj in stats]
                    adapter_chart.add("values", values)
                    adapter_fig = os.path.join(new_record.outdir, "fig_adapter") + ".svg"
                    adapter_chart.render_to_file(adapter_fig)
                    results["figures"].append("/".join(adapter_fig.split("/")[-3:]))
                except:
                    pass


                #analysis
                try:
                    analysis_chart = pygal.Bar(x_label_rotation=90, disable_xml_declaration=True, style=LightGreenStyle,
                                               show_legend=False)
                    analysis_chart.title = 'Reads in Analysis'
                    analysis_chart.x_labels = labels
                    values = [float(obj.reads_in_analysis) / float(obj.raw_reads) * 100 for obj in stats]
                    analysis_chart.add("values", values)
                    analysis_fig = os.path.join(new_record.outdir, "fig_analysis") + ".svg"
                    analysis_chart.render_to_file(analysis_fig)
                    results["figures"].append("/".join(analysis_fig.split("/")[-3:]))
                except:
                    pass



                #Mapped
                try:
                    mapped_chart = pygal.Bar(x_label_rotation=90, disable_xml_declaration=True, style=LightGreenStyle,
                                             show_legend=False)
                    mapped_chart.title = 'Genome Mapped Reads'
                    mapped_chart.x_labels = labels
                    values = [float(obj.genome_mapped_reads) / float(obj.reads_in_analysis) * 100 for obj in stats]
                    mapped_chart.add("values", values)
                    mapped_fig = os.path.join(new_record.outdir, "fig_mapped") + ".svg"
                    mapped_chart.render_to_file(mapped_fig)
                    results["figures"].append("/".join(mapped_fig.split("/")[-3:]))
                except:
                    pass

                #unique mapped
                try:
                    unique_chart = pygal.Bar(x_label_rotation=90, disable_xml_declaration=True, style=LightGreenStyle,
                                             show_legend=False)
                    unique_chart.title = 'Unique Reads Mapped to Genome'
                    unique_chart.x_labels = labels
                    values = [float(obj.unique_reads_mapped_to_genome) / float(obj.unique_reads_in_analysis) * 100 for obj
                              in stats]
                    unique_chart.add("values", values)
                    unique_fig = os.path.join(new_record.outdir, "unique_fig") + ".svg"
                    unique_chart.render_to_file(unique_fig)
                    results["figures"].append("/".join(unique_fig.split("/")[-3:]))
                except:
                    pass


            if len(new_record.heatmaps) == 2:
                results["heatmap"] = ["/".join(heatmap.split("/")[-3:]) for heatmap in new_record.heatmaps]

            results["zip"] = "/".join(new_record.zip_file.split("/")[-3:])

            try:
                results["parameters"] = new_record.parameters
            except:
                pass

            results["id"] = job_id
            results["date"] = new_record.start_time + datetime.timedelta(days=15)

            return render(request, "de_result.html", results)
        else:
            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))

    else:
        return redirect(reverse_lazy('srnade'))


def result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        results = dict()
        results["id"] = job_id

        # Graphs
        config = pd.read_table(os.path.join(new_record.outdir, 'boxplot.config'), header=None)
        for index, row in config.iterrows():
            file, x_lab, y_lab, title = row[0:4]
            tag = row[4] + '_plot'
            results[tag] = general_plot(file, x_lab, y_lab, title)

        # Sequencing statistics
        try:
            x_lab, y_lab, title = ['', 'Number of reads', 'Sequencing statistics']
            seq_boxplot = general_plot_cols(os.path.join(new_record.outdir, 'sequencingStat.txt'), x_lab, y_lab, title)
            results["seq_stats"] = seq_boxplot
        except:
            results["seq_stats"] = None

        # Read length statistics
        try:
            length_full_plot = make_full_length_plot(os.path.join(new_record.outdir, 'readlen/readLengthFull_minExpr0_4.mat'))
            results["read_length_full_plot"] = length_full_plot
        except:
            results["read_length_full_plot"] = None

        try:
            length_plot = make_length_plot(os.path.join(new_record.outdir, 'readlen/readLengthAnalysis_minExpr0_4.mat'))
            results["read_length_analysis_plot"] = length_plot
        except:
            results["read_length_analysis_plot"] = None

        try:
            length_genome_plot = make_length_genome_plot(os.path.join(new_record.outdir, 'readlen/genomeMappedReads_minExpr0_4.mat'))
            results["read_length_genome_plot"] = length_genome_plot
        except:
            results["read_length_genome_plot"] = None

        # Tables
        tables_config = pd.read_table(os.path.join(new_record.outdir, 'tables.config'), header=None)
        for index, row in tables_config.iterrows():
            file, name = row[0:2]
            parser = GeneralParser(file)
            table = [obj for obj in parser.parse()]
            header = table[0].get_sorted_attr()
            r = Result(name, define_table(header, 'TableResult')(table))
            tag = row[2] + '_tab'
            results[tag] = r

        if new_record.job_status == "Finished":
            if new_record.stats_file and os.path.isfile(new_record.stats_file):
                parser = DeStatsParser(new_record.stats_file)
                stats = [obj for obj in parser.parse()]
                header = stats[0].get_sorted_attr()
                stats_result = Result("Read Processing Statistic", define_table(header, 'TableResult')(stats))
                results["stats"] = stats_result

                labels = [obj.sample for obj in stats]

            try:
                results["parameters"] = new_record.parameters
            except:
                pass

            results["id"] = job_id
            results["date"] = new_record.start_time + datetime.timedelta(days=15)

            return render(request, "de_result.html", results)
        else:
            return redirect(reverse_lazy('progress', kwargs={"pipeline_id": job_id}))

    else:
        return redirect(reverse_lazy('srnade'))


def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    outdir = FS.location
    os.system(
        'qsub -v pipeline="de",group="' + "control#cancer#metastasis" + '",key="' + pipeline_id + '",outdir="' + outdir +
        '",name="' + pipeline_id + '_de",input="' + "4BVIF1F8RQP4Q51:7YE5V1HDXM6P4F7:8QCU135VBZ7UFIP:W175Z9RPXC9EQ6U:RW80R79UQFIDDPA:LKS2ON7R65PUZY1:ROKDJE3MIRZHU3X:GE2V6V244P16YY2#F6TVYO1FV2G3YNP:K23Y0MXX90YQ218:2MLPVBAOYDWWQD8:LRNEGOCDIR0WO5X:2TZDR75098RXPY6:RF295V54D9L937L:SE7HDLBHQGPK9M8:7J73F7F4K2E2DD0:J67VJTPJMQ10VSJ#OF04GY3XAQRITSU:8ACJNG8K3ADYRX5:UC6BBCZDR77C4NW:14D8IYMD5TGQOGU:WZHXNYKJE8QMVXS:4FYIRMF0DJNOJXX:179A4W4IY4J2DVU:O91QYC2DQQK0D7Q:VW0I988EDIIE6XG"
        + '",iso="' + "true" +
        '",nt="' + "0.8" + '",dt="' + "0.05" + '",hmTop="' + '20' + '",hmPerc="' + '1' + '"  -N ' +
        pipeline_id + '_de /shared/sRNAtoolbox/core/bash_scripts/run_sRNAde.sh')

    return redirect("/srnatoolbox/jobstatus/srnade/?id=" + pipeline_id)


class De(FormView):
    template_name = 'de.html'
    form_class = DEForm
    success_url = reverse_lazy("DE")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        call, pipeline_id = form.create_call()
        self.success_url = reverse_lazy('srnade') + '?id=' + pipeline_id

        print(call)
        os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        return super(De, self).form_valid(form)
