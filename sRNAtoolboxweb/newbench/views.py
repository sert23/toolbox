from django.shortcuts import render
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
from sRNAtoolboxweb.settings import BASE_DIR,MEDIA_ROOT,MEDIA_URL, SUB_SITE, MATRIX_GENERATOR_DICT, CONF
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
from multi.forms import PhotoForm, sRNABenchForm, sRNABenchForm_withDBs
from sRNABench.forms import contaminaForm
# from .forms import miRNAgFreeForm, FileForm
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
from collections import OrderedDict
import time

# Create your views here.

def generate_uniq_id(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_id():
    is_new = True
    while is_new:
        pipeline_id = generate_uniq_id()
        if not JobStatus.objects.filter(pipeline_key=pipeline_id):
            return pipeline_id

def get_files_fullpath(input_folder):

    folders = [os.path.join(input_folder, x) for x in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, x))]

    return folders

def move_files(input_folder, output_folder):

    dict_path = os.path.join(output_folder,"input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file)
    json_file.close()

    files_to_move = get_files_fullpath(input_folder)
    files_folder = os.path.join(output_folder,"files")
    for f in files_to_move:
        if ("SRA.txt" not in f) and ("links.txt" not in f) and ("drive.json" not in f) and ("dropbox.txt" not in f and ("redirect" not in f)):
            outf = f.replace(input_folder, files_folder)
            shutil.move(f, outf)
            name = f.split("/")[-1]
            input_dict[f] = { "input" : f , "name" : name, "input_type" : "uploaded file"}

    json_file = open(dict_path, "w")
    json.dump(input_dict, json_file, indent=6)
    json_file.close()


def move_SRA(input_folder, output_folder):
    dict_path = os.path.join(output_folder, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file)
    json_file.close()
    SRA_file = os.path.join(input_folder,"SRA.txt")
    if os.path.exists(SRA_file):
        with open(SRA_file, 'r') as rfile:
            lines = rfile.readlines()
            for line in lines:
                s = line.rstrip()
                input_dict[s] = {"input": s, "name": "", "input_type": "SRA"}

        json_file = open(dict_path, "w")
        json.dump(input_dict, json_file, indent=6)
        json_file.close()



def move_link(input_folder, output_folder):
    dict_path = os.path.join(output_folder, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file)
    json_file.close()
    links_file = os.path.join(input_folder, "links.txt")
    if os.path.exists(links_file):
        with open(links_file, 'r') as rfile:
            lines = rfile.readlines()
            for line in lines:
                s = line.rstrip()
                input_dict[s] = {"input": s, "name": "", "input_type": "download link"}

        json_file = open(dict_path, "w")
        json.dump(input_dict, json_file, indent=6)
        json_file.close()

def move_dropbox(input_folder, output_folder):
    dict_path = os.path.join(output_folder, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file)
    json_file.close()
    dropbox_file = os.path.join(input_folder, "dropbox.txt")
    if os.path.exists(dropbox_file):
        with open(dropbox_file, 'r') as rfile:
            lines = rfile.readlines()
            for line in lines:
                s = line.rstrip()
                input_dict[s] = {"input": s, "name": "", "input_type": "download link"}
        json_file = open(dict_path, "w")
        json.dump(input_dict, json_file, indent=6)
        json_file.close()

def move_drive(input_folder, output_folder):
    # curl - H
    # "Authorization: Bearer $token" "https://www.googleapis.com/drive/v3/files/$id?alt=media" - o
    # "$file"
    backvalue = False
    dict_path = os.path.join(output_folder, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file)
    json_file.close()
    drive_path = os.path.join(input_folder, "drive.json")
    if not os.path.exists(drive_path):
        return backvalue
    drive_file = open(drive_path, "r")
    drive_dict = json.load(drive_file)
    drive_file.close()

    for k in drive_dict.keys():
        filename, fileid, link, token = drive_dict[k]
        link_id = "https://www.googleapis.com/drive/v3/files/" + fileid + "?alt=media"
        cmd = 'curl -H "Authorization: Bearer ' + token + '" "' + link_id +'" -o "{}"'
        cmd = "curl -H 'Authorization: Bearer " + token + "' '" + link_id + "' -o '{}'"
        input_dict[filename] = {"input": filename, "name": filename,
                                "input_type": "Drive", "link": link_id, "token": token, "cmd" : cmd
                                }
        backvalue = True
    json_file = open(dict_path, "w")
    json.dump(input_dict, json_file, indent=6)
    json_file.close()
    return backvalue

def make_download_name(input_name):
    # pieces = input_name.split(".")
    down_name = input_name + ".downloading"
    cmd = "touch " + down_name
    cmd2 = "rm " + down_name
    return cmd, cmd2

def download_drive(input_json, output_folder):
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    json_file = open(input_json, "r")
    input_dict = json.load(json_file)
    json_file.close()
    for s in input_dict:
        s_dict = input_dict[s]
        if s_dict["input_type"] == "Drive":
            link = s_dict["link"]
            filename = os.path.join(output_folder, s_dict["name"])
            token = s_dict["token"]
            cmd = s_dict["cmd"]
            cmd = cmd.format(filename)
            start, end = make_download_name(filename)

            command = start + cmd + end

            # ret = subprocess.run(command, capture_output=False, shell=True)
            ret = subprocess.Popen("{}; {}; {}".format(start, cmd, end), shell=True)
            # ret = subprocess.Popen("{}; {};".format(start, cmd), shell=True)
            # ret = subprocess.Popen(cmd, shell=True)



class NewUpload(FormView):
    # template_name = 'newBench/new_bench.html'
    # template_name = 'Messages/miRgFree/drive_test.html'
    # form_class = miRNAgFreeForm
    # success_url = reverse_lazy("MIRG")
    # success_url = reverse_lazy("MIRG")

    def get(self, request,**kwargs):
        path = request.path
        jobID = generate_id()
        folder_path = os.path.join(MEDIA_ROOT,jobID)
        # os.mkdir(folder_path)
        data_url = reverse_lazy("multi:multi_new") + jobID
        # mirgeneDB = parse_mirgeneDB()
        print(data_url)
        return render(self.request, 'newBench/new_bench.html', { "jobID":jobID,
                                                         "data_url": data_url,
                                                         # "mirgenedb_list": mirgeneDB,

                                                         })


class Launch(FormView):
    # TODO if folder already exists omit creation
    template_name = 'newBench/parameters.html'
    # template_name = 'Messages/miRgFree/drive_test.html'

    form_class = sRNABenchForm_withDBs
    # form_class = sRNABenchForm

    def get_form_kwargs(self):
        kwargs = super(Launch, self).get_form_kwargs()
        parameters = self.request.GET
        folder = parameters["jobId"]
        kwargs['orig_folder'] = folder
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        # path = request.path
        param_dict = self.request.GET
        # config_lines = []
        oldID = param_dict.get("jobId")
        old_folder_path = os.path.join(MEDIA_ROOT, oldID)
        # oldID = self.kwargs.get("jobId")
        new_jobID = generate_uniq_id()
        old_files = [f for f in os.listdir(old_folder_path) if f.startswith("redirect")]
        # mark new ID in old folder, if present, ignore new_jobID

        if len(old_files) > 0:
            name = old_files[0]
            new_jobID = name.split("_")[1]
        else:
            os.system("touch " + os.path.join(old_folder_path,"redirect_" +  new_jobID))
        folder_path = os.path.join(MEDIA_ROOT, new_jobID)
        files_path = os.path.join(folder_path,"files")
        if not os.path.exists(os.path.join(folder_path)):
            os.mkdir(os.path.join(folder_path))
        if not os.path.exists(os.path.join(files_path)):
            os.mkdir(os.path.join(files_path))

        if not old_files:
            json_path = os.path.join(folder_path, "input.json")
            json_file = open(json_path, "w")
            json.dump({}, json_file, indent=6)
            json_file.close()
            move_files(old_folder_path, folder_path)
            move_SRA(old_folder_path, folder_path)
            move_link(old_folder_path, folder_path)
            move_dropbox(old_folder_path, folder_path)

            if move_drive(old_folder_path, folder_path):
                # print("x")
                # download drive files background
                drive_path = os.path.join(files_path, "drive_temp")
                os.mkdir(drive_path)
                download_drive(json_path, drive_path)

        #build samples table
        dict_path = os.path.join(folder_path, "input.json")
        json_file = open(dict_path, "r")
        input_dict = json.load(json_file)
        json_file.close()

        table_data = []
        for k in input_dict.keys():
            object = input_dict[k]
            input_line = object["input"]
            input_type = object["input_type"]
            input_name = object["name"]
            if input_type == "Drive":
                downloading_path = os.path.join(folder_path,"files", "drive_temp", input_name + ".downloading")
                downloaded_path = os.path.join(folder_path,"files", "drive_temp", input_name)
                if os.path.exists(downloading_path):
                    status = "downloading"
                elif os.path.exists(downloaded_path):
                    status = "downloaded"
                else:
                    status = "download failed"
            else:
                status = "not launched"

            # id = "file_"+ str(ix)
            # link = '<a href="'+ os.path.join(MEDIA_URL,query_id,file) +'">'+file+'</a>'
            # status = "Not launched"
            checkbox = "<input type='checkbox' value='" + "' name='to_list' checked=true>"
            table_data.append([input_line, status, checkbox])

        js_data = json.dumps(table_data)
        js_headers = json.dumps([{"title": "Input"},
                                 {"title": "Status"},
                                 {"title": '<input type="checkbox" checked=true id="flowcheckall" value="" />&nbsp;All'}])

        context["table_data"] = js_data
        context["table_headers"] = js_headers
        context["job_id"] = new_jobID
        context["annotate_url"] = reverse_lazy("annotate") + new_jobID
        # context["form"] = reverse_lazy("annotate") + sRNABenchForm
        # data_url = reverse_lazy("multi:multi_new") + jobID
        # mirgeneDB = parse_mirgeneDB()
        # print(data_url)

        # "input"

        annotate_url = reverse_lazy("annotate") + new_jobID
        return context

    def post(self, request, *args, **kwargs):

        # path = request.path
        # folder = path.split("/")[-1]
        # form = MultiURLForm(self.request.POST, self.request.FILES, dest_folder=folder)

        request.POST._mutable = True
        #print(SPECIES_PATH)
        request.POST['species'] = request.POST['species_hidden'].split(',')

        # spikes = request.FILES.get('spikes')
        # if spikes:
        #     fs = FileSystemStorage()
        #     time_stamp = datetime.datetime.now().strftime("%m%d%Y%H%M%S")
        #     filename = fs.save(os.path.join(MEDIA_ROOT, "multi", time_stamp + "_test_spike.fa"), spikes)
        #     request.POST['spikes_path'] = "test_spike.fa"

        print(request.POST['species'])
        print(request.POST['species_hidden'].split(','))
        request.POST._mutable = False
        return super(Launch, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        form.clean()
        pipeline_id = form.create_call()
        self.success_url = reverse_lazy('srnabench') + '?id=' + pipeline_id

        # os.mkdir(os.path.join(MEDIA_ROOT, pipeline_id))
        JobStatus.objects.create(job_name=pipeline_id + "_multi", pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 all_files=" ",
                                 modules_files=" ",
                                 pipeline_type="multiupload",
                                 )

        #os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        return super(Launch, self).form_valid(form)

class ReLaunch(FormView):
    # TODO if folder already exists omit creation
    template_name = 'newBench/parameters.html'
    # template_name = 'Messages/miRgFree/drive_test.html'

    form_class = sRNABenchForm_withDBs
    # form_class = sRNABenchForm

    def get_form_kwargs(self):
        kwargs = super(ReLaunch, self).get_form_kwargs()
        parameters = self.request.GET
        folder = parameters["jobId"]
        kwargs['orig_folder'] = folder
        kwargs['is_relaunch'] = True

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        # path = request.path
        param_dict = self.request.GET
        # config_lines = []
        jobID = param_dict.get("jobId")
        folder_path = os.path.join(MEDIA_ROOT, jobID)
        # old_folder_path = os.path.join(MEDIA_ROOT, oldID)
        # oldID = self.kwargs.get("jobId")

        #build samples table
        dict_path = os.path.join(folder_path, "input.json")
        json_file = open(dict_path, "r")
        input_dict = json.load(json_file)
        json_file.close()

        table_data = []
        for k in input_dict.keys():
            object = input_dict[k]
            input_line = object["input"]
            input_type = object["input_type"]
            input_name = object["name"]
            status = "not launched"


            # id = "file_"+ str(ix)
            # link = '<a href="'+ os.path.join(MEDIA_URL,query_id,file) +'">'+file+'</a>'
            # status = "Not launched"
            checkbox = "<input type='checkbox' value='" + "' name='to_list' checked=true>"
            table_data.append([input_line, status, checkbox])

        js_data = json.dumps(table_data)
        js_headers = json.dumps([{"title": "Input"},
                                 {"title": "Status"},
                                 {"title": '<input type="checkbox" checked=true id="flowcheckall" value="" />&nbsp;All'}])

        context["table_data"] = js_data
        context["table_headers"] = js_headers
        context["job_id"] = jobID
        context["annotate_url"] = reverse_lazy("annotate") + jobID


        annotate_url = reverse_lazy("annotate") + jobID
        return context

    def post(self, request, *args, **kwargs):

        # path = request.path
        # folder = path.split("/")[-1]
        # form = MultiURLForm(self.request.POST, self.request.FILES, dest_folder=folder)

        request.POST._mutable = True
        #print(SPECIES_PATH)
        request.POST['species'] = request.POST['species_hidden'].split(',')
        print(request.POST['species'])
        print(request.POST['species_hidden'].split(','))
        request.POST._mutable = False
        return super(ReLaunch, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        form.clean()
        pipeline_id = form.create_call()
        self.success_url = reverse_lazy('srnabench') + '?id=' + pipeline_id

        # os.mkdir(os.path.join(MEDIA_ROOT, pipeline_id))
        JobStatus.objects.create(job_name=pipeline_id + "_multi", pipeline_key=pipeline_id, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 all_files=" ",
                                 modules_files=" ",
                                 pipeline_type="multiupload",
                                 )

        #os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        return super(ReLaunch, self).form_valid(form)

def ajax_matrix_selectors(request):
    data = {}
    jobID = request.GET.get("id")
    current_file_type = request.GET.get("file_type")

    file_type_dict = MATRIX_GENERATOR_DICT.get(current_file_type)
    data["filetypes"] = list(MATRIX_GENERATOR_DICT.keys())
    data["selected_type"] = current_file_type
    data["files"] = file_type_dict.get("file")
    data["units"] = file_type_dict.get("column")

    # data["message"] = "the message is that it worked"
    return JsonResponse(data)

def make_grpStr(jobID):
    dict_path = os.path.join(MEDIA_ROOT, jobID, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file, object_pairs_hook=OrderedDict)
    jobs = []
    annotated = True
    annotations = []
    for k in input_dict.keys():
        c_dict = input_dict[k]
        jobs.append(c_dict.get("jobID"))
        name = c_dict.get("name_annotation")
        if name:
            annotations.append(name)
        else:
            annotated = False
    jobs_clean = [i for i in jobs if i]
    if annotated and len(annotations) == len(jobs_clean):
        sampledesc = ":".join(annotations)
        grp = ",".join(jobs_clean)
        final_string = grp + " sampleDesc=" + sampledesc + " "
        return final_string
    else:
        grp = ",".join(jobs_clean)
        return grp

def make_grpStr_old(jobID):
    dict_path = os.path.join(MEDIA_ROOT, jobID, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file, object_pairs_hook=OrderedDict)
    jobs = []
    annotated = True
    annotations = []
    for k in input_dict.keys():
        c_dict = input_dict[k]
        jobs.append(c_dict.get("jobID"))
        group = c_dict.get("group_annotation")
        if group:
            annotations.append(group)
        else:
            annotated = False
    jobs_clean = [i for i in jobs if i]
    if annotated and len(annotations) == len(jobs_clean):
        matdesc = ",".join(annotations)
        grp = ",".join(jobs_clean)
        final_string = grp + " matrixDesc=" + matdesc + " "
        return final_string
    else:
        grp = ",".join(jobs_clean)
        return grp


def find_file_of_interest(folder_path):
    interest_file = [f for f in os.listdir(folder_path) if f.endswith(".mat")][0]
    full_path = os.path.join(folder_path, interest_file)
    #change extension
    new_name = full_path.replace(".mat", ".tsv")
    shutil.move(full_path, new_name)
    return new_name

def ajax_read_length(request):
    data_dict = {}
    file_path = request.GET.get('matrix_location', None)
    file_path = file_path.replace(MEDIA_URL, MEDIA_ROOT)
    file_name = os.path.basename(file_path)
    annotation_name = file_name.split("_minExpr")[0]
    annotation_name = annotation_name.replace("_"," ")
    with open(file_path, "r") as rf:
        rl_df = pd.read_csv(rf, sep="\t")

    lengths = list(rl_df["read length"])
    rl_df.drop('read length', inplace=True, axis=1)
    rl_df['mean'] = rl_df.mean(axis=1)
    values = list(rl_df["mean"])
    data_dict["message"] = "it's working"

    # values = [0 if i < 0.1 else i for i in values]
    min_width = 40
    # if 40 > min_width:
    #     min_width = 40
    for i,x in enumerate(values):
        if float(x) > 0.1 and i > 40:
            min_width = i
    data = [go.Bar(name="",
                   x=lengths,
                   y=values,
                   # marker=dict(color=perc_df.bar_color.values),
                   # hovertemplate="%{x}p: %{y}",
                   showlegend=False
                   )]
    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=50,
            t=100,
            pad=4
        ),
        title=str(annotation_name) + " reads",
        font=dict(size=18),
        # autosize=False,
        # height=650,
        # width=1150,
        xaxis=dict(
            range=[0,min_width],
            title="Read length (nt)"),
        yaxis=dict(
            # type=scale,
            automargin=True,
            ticksuffix='%',
            tickprefix="   ",
            # dtick=dtick,
            title="Percentage of reads" + "\n<br>"
        )
    )
    fig = go.Figure(data=data, layout=layout)

    div = plot(fig, show_link=False, auto_open=False, include_plotlyjs=False, output_type="div",
               config={'editable': True})

    data_dict["plot"] = div
    return JsonResponse(data_dict)


def matrix_generator(request):
    context = {}
    jobID = request.GET.get("jobID")
    try:
        is_fromDE = request.GET.get("is_fromDE")
        file_type = request.GET.get("matrix_file_type")
        annot_file = '"' + str(request.GET.get("matrix_annotation")) + '"'
        column = request.GET.get("matrix_unit")
        file_type_dict = MATRIX_GENERATOR_DICT.get(file_type)
        params = file_type_dict.get("fixedParam")
        output_folder = os.path.join(MEDIA_ROOT, "matrix_temp", time.strftime("%Y%m%d-%H%M%S") + "_" + generate_id() + "_" + jobID)
        os.mkdir(output_folder)
        exec_path = CONF.get("exec")
        jar_file = os.path.join(exec_path, "sRNAde.jar")
        context["file_type"] = file_type
        if is_fromDE:
            print("x")
        else:
            try:
                grpString = make_grpStr(jobID)
                line = "java -jar " + jar_file + " " + params + " colData={column} statFiles={annot_file} input={base_folder} grpString={jobs} output={output_folder}"
                command_line = line.format(column=column,
                                           annot_file=annot_file,
                                           base_folder=MEDIA_ROOT,
                                           jobs=grpString,
                                           output_folder=output_folder)
                with open(os.path.join(output_folder,"line"), "w") as wf:
                    wf.write(command_line)
                os.system(command_line)
                serving_matrix = find_file_of_interest(output_folder)
                context["download_url"] = serving_matrix.replace(MEDIA_ROOT, MEDIA_URL)
                context["go_back_url"] = os.path.join(reverse_lazy("progress_status"), jobID)

                return render(request, "newBench/download_matrix_file.html", context)
            except:
                context["go_back_url"] = os.path.join(reverse_lazy("progress_status"), jobID)
                context["error_message"] = "There was an unexpected error. Please report it using the following code " + output_folder
                return render(request, "newBench/download_matrix_file.html", context)
    except:
        context["go_back_url"] = os.path.join(reverse_lazy("progress_status"), jobID)
        context["error_message"] = "There was an unexpected error. Please report it using the following code " + jobID
        return render(request, "newBench/download_matrix_file.html", context)


class contaminaBench(FormView):
    template_name = 'newBench/contamination.html'
    form_class = contaminaForm
    success_url = reverse_lazy("contamination")

    def post(self, request, *args, **kwargs):
        # request.POST._mutable = True
        # #print(SPECIES_PATH)
        # request.POST['species'] = request.POST['species_hidden'].split(',')
        # print(request.POST['species'])
        # print(request.POST['species_hidden'].split(','))
        # request.POST._mutable = False
        return super(contaminaBench, self).post(request, *args, **kwargs)

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
        return super(contaminaBench, self).form_valid(form)

    def print_file_locat(self, form):
        print(form.cleaned_data)
