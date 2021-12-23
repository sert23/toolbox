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

# Create your views here.

def generate_uniq_id(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_id():
    is_new = True
    while is_new:
        pipeline_id = generate_uniq_id()
        if not JobStatus.objects.filter(pipeline_key=pipeline_id):
            return pipeline_id

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
        if ("SRA.txt" not in f) and ("links.txt" not in f) and ("drive.json" not in f) and ("dropbox.txt" not in f):
            outf = f.replace(input_folder, files_folder)
            shutil.move(f, outf)
            input_dict[f] = { "input" : f , "name" : "", "input_type" : "uploaded file"}

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

    dict_path = os.path.join(output_folder, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file)
    json_file.close()
    drive_path = os.path.join(input_folder, "drive.json")
    drive_file = open(dict_path, "r")
    drive_dict = json.load(dict_path)
    drive_file.close()
    for k in drive_dict.keys():
        print(k)


class Launch(FormView):
    # template_name = 'newBench/new_bench.html'
    # template_name = 'Messages/miRgFree/drive_test.html'
    # form_class = miRNAgFreeForm
    # success_url = reverse_lazy("MIRG")
    # success_url = reverse_lazy("MIRG")

    def get(self, request, **kwargs):
        path = request.path
        param_dict = request.GET
        config_lines = []
        oldID = param_dict.get("jobId")
        new_jobID = generate_uniq_id()
        old_folder_path = os.path.join(MEDIA_ROOT, oldID)
        folder_path = os.path.join(MEDIA_ROOT, new_jobID)
        files_path = os.path.join(folder_path,"files")
        if not os.path.exists(os.path.join(folder_path)):
            os.mkdir(os.path.join(folder_path))
        if not os.path.exists(os.path.join(files_path)):
            os.mkdir(os.path.join(files_path))

        json_file = open(os.path.join(folder_path,"input.json"), "w")
        json.dump({}, json_file, indent=6)
        json_file.close()
        move_files(old_folder_path, folder_path)
        move_SRA(old_folder_path, folder_path)
        move_link(old_folder_path, folder_path)
        # move_drive(old_folder_path, folder_path)
        move_dropbox(old_folder_path, folder_path)
        # data_url = reverse_lazy("multi:multi_new") + jobID
        # mirgeneDB = parse_mirgeneDB()
        # print(data_url)
        return render(self.request, 'newBench/new_bench.html', {"jobID": new_jobID,
                                                                # "data_url": data_url,
                                                                # "mirgenedb_list": mirgeneDB,

                                                                })





    # def post(self, request, *args, **kwargs):
    #     request.POST._mutable = True
    #     #print(SPECIES_PATH)
    #     request.POST['species'] = request.POST['species_hidden'].split(',')
    #     print(request.POST['species'])
    #     print(request.POST['species_hidden'].split(','))
    #     request.POST._mutable = False
    #     return super(MirG, self).post(request, *args, **kwargs)
    #
    # def form_valid(self, form):
    #     # This method is called when valid form data has been POSTed.
    #     # It should return an HttpResponse.
    #
    #     form.clean()
    #     call, pipeline_id = form.create_call()
    #     self.success_url = reverse_lazy('srnabench') + '?id=' + pipeline_id
    #
    #     print(call)
    #     os.system(call)
    #     js = JobStatus.objects.get(pipeline_key=pipeline_id)
    #     js.status.create(status_progress='sent_to_queue')
    #     js.job_status = 'sent_to_queue'
    #     js.save()
    #     return super(MirG, self).form_valid(form)
    #
    # def print_file_locat(self, form):
    #     print(form.cleaned_data)

# class NewUpload(FormView):
#
#     template_name = 'miRNAgFree/multi_status.html'
#
#     def get(self, request, **kwargs):
#         path = request.path
#
#         jobID = request.GET.get('jobId', None)
#         folder_path = os.path.join(MEDIA_ROOT,jobID)
#
#         # ignore_list = ["dropbox.txt", "drive.json","links.txt", "SRA.txt", "config.txt", "IDs"]
#         files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
#
#         param_dict = request.GET
#
#         if not "conf.txt" in files:
#             make_config(request)
#             IDs = assign_IDs(folder_path)
#             for line in IDs:
#                 print(line)
#                 ik, ifile, itype = line
#                 # to_launch.append([generate_id(), k.rstrip(), "Drive"])
#
#                 JobStatus.objects.create(job_name=" ", pipeline_key=ik, job_status="not_launched",
#                                          start_time=datetime.datetime.now(),
#                                          all_files=ifile,
#                                          modules_files="",
#                                          pipeline_type="miRNAgFree",
#                                          outdir = os.path.join(MEDIA_ROOT,ik)
#                                          )
#             JobStatus.objects.create(job_name=" ", pipeline_key=jobID, job_status="not_launched",
#                                      start_time=datetime.datetime.now(),
#                                      all_files=" ",
#                                      modules_files="",
#                                      pipeline_type="multiupload",
#                                      )
#             data = dict()
#             data["running"] = False
#             IDs = []
#             with open(os.path.join(folder_path, "IDs"), 'r') as rfile:
#                 lines = rfile.readlines()
#                 for line in lines:
#                     IDs.append(line.rstrip().split("\t"))
#
#             jobs_tbody = []
#             for i in IDs:
#                 # print(i[0])
#                 new_record = JobStatus.objects.get(pipeline_key=i[0])
#                 job_stat = new_record.job_status
#                 if job_stat != "Finished":
#                     data["running"] = True
#                 if job_stat == "sent_to_queue":
#                     job_stat = "In queue"
#                 start = new_record.start_time.strftime("%H:%M:%S, %d %b %Y")
#                 if new_record.finish_time:
#                     finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
#                 else:
#                     finish = "-"
#                 click = '<a href="' + SUB_SITE + '/jobstatus/' + i[0] + '" target="_blank" > Go to results </a>'
#                 jobs_tbody.append([i[0], job_stat.replace("_"," "), start, finish, i[1], click])
#
#             js_headers = json.dumps([{"title": "job ID"},
#                                      {"title": "Status"},
#                                      {"title": "Started"},
#                                      {"title": "Finished"},
#                                      {"title": "Input"},
#                                      # { "title": "Select" }])
#                                      {"title": 'Go to'}
#                                      ])
#             data["tbody"] = json.dumps(jobs_tbody)
#             data["thead"] = js_headers
#             data["id"] = jobID
#             data["refresh_rate"] = 5
#
#             return render(self.request, 'miRNAgFree/multi_status.html', data)
#
#         elif param_dict.get("protocol"):
#
#             return redirect(reverse_lazy("launch" )+ "?jobId=" + jobID)
#
#         else:
#             data = dict()
#             data["running"] = False
#             IDs = []
#             with open(os.path.join(folder_path,"IDs"), 'r') as rfile:
#                 lines = rfile.readlines()
#                 for line in lines:
#                     IDs.append(line.rstrip().split("\t"))
#
#             with open(os.path.join(folder_path, "conf.txt"), "r") as cfile:
#                 config_content = cfile.read()
#
#             jobs_tbody = []
#             for i in IDs:
#                 # print(i[0])
#                 new_record = JobStatus.objects.get(pipeline_key=i[0])
#                 job_stat = new_record.job_status
#
#                 ### launching job
#                 # if job_stat == "downloading":
#                 #     # launch
#                 #     c_path = make_config_json(i[0])
#                 #     comm = create_call(i[0], c_path)
#                 #     # print("HERE")
#                 #     # print(comm)
#                 #     os.system(comm)
#                 #     new_record.job_status = 'sent_to_queue'
#
#
#                 if job_stat == "not_launched":
#
#                     # new folder
#                     dest_folder = os.path.join(MEDIA_ROOT,i[0])
#                     make_folder(dest_folder)
#                     # new config
#
#                     config_path = os.path.join(dest_folder,"conf.txt")
#                     input_type = i[2]
#                     input_line = make_input_line(folder_path, i[0], input_type, i[1])
#                     output_line = "output=" + os.path.join(MEDIA_ROOT,i[0]) + "\n"
#                     new_content = input_line + output_line + config_content
#                     with open(config_path,"w") as cf:
#                         cf.write(new_content)
#
#                     # launch
#                     c_path = make_config_json(i[0])
#                     comm = create_call(i[0], c_path)
#                     os.system(comm)
#                     new_record.job_status = 'sent_to_queue'
#                     new_record.save()
#                     if len(IDs) == 1:
#                         return redirect(reverse_lazy('progress', kwargs={"pipeline_id": i[0]}))
#                 if job_stat != "Finished" and job_stat != "Finished with Errors":
#                     data["running"] = True
#                 if job_stat == "sent_to_queue":
#                     job_stat = "In queue"
#                 start = new_record.start_time.strftime("%H:%M:%S, %d %b %Y")
#                 if new_record.finish_time:
#                     finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
#                 else:
#                     finish = "-"
#                 job_stat = new_record.job_status
#                 click = '<a href="' + SUB_SITE + '/jobstatus/' + i[0] + '" target="_blank" > Go to results </a>'
#                 jobs_tbody.append([i[0], job_stat.replace("_"," "), start, finish, i[1], click])
#
#             js_headers = json.dumps([{"title": "job ID"},
#                                      {"title": "Status"},
#                                      {"title": "Started"},
#                                      {"title": "Finished"},
#                                      {"title": "Input"},
#                                      # { "title": "Select" }])
#                                      {"title": 'Go to'}
#                                      ])
#             # print(jobs_tbody)
#             data["tbody"] = json.dumps(jobs_tbody)
#
#             data["thead"] = js_headers
#             data["id"] = jobID
#             data["refresh_rate"] = 90
#             return render(self.request, 'miRNAgFree/multi_status.html', data)