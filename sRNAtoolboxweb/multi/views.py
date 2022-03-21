import time
import glob
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views import View
from django.views.generic import FormView, DetailView

from .forms import PhotoForm, MultiURLForm,sRNABenchForm
from .models import Photo
from django.core.urlresolvers import reverse, reverse_lazy
import string
import random
from django.views.generic import RedirectView
from django.shortcuts import redirect
from os import listdir
import os
from sRNAtoolboxweb.settings import MEDIA_ROOT, MEDIA_URL, SUB_SITE
from progress.models import JobStatus
import shutil
import datetime
import json
import re
import pandas as pd
import csv
from collections import OrderedDict

def make_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)


def generate_uniq_id(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_id():
    is_new = True
    while is_new:
        pipeline_id = generate_uniq_id()
        if not JobStatus.objects.filter(pipeline_key=pipeline_id):
            return pipeline_id



def new_upload(request):
    # request.session['error_message'] = 'test'
    random_ID = generate_id()
    url = reverse('multi:multi_new') + random_ID
    return redirect(url)


class MultiUploadView(FormView):
    #template_name = 'bench.html'
    #form_class = sRNABenchForm
    #success_url = reverse('photos:multi_start')

    def get_form_kwargs(self):
        '''This goes in the Update view'''
        kwargs = super(MultiUploadView, self).get_form_kwargs()  # put your view name in the super

        #kwargs["folder"] = self.request.path
        return kwargs

    def get(self, request,**kwargs):
        path = request.path
        folder = path.split("/")[-1]
        onlyfiles = []
        if os.path.exists(os.path.join(MEDIA_ROOT,folder)):
            onlyfiles = [[f,os.path.join(MEDIA_URL, folder, f)] for f in listdir(os.path.join(MEDIA_ROOT,folder)) if
                     os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, folder), f))]

            for x in ["conf.txt","SRR_files.txt","URL_files.txt"]:
                if [x,os.path.join(MEDIA_URL, folder, x)] in onlyfiles:
                    onlyfiles.remove([x,os.path.join(MEDIA_URL, folder, x)])

        else:
            onlyfiles = []
            os.mkdir(os.path.join(MEDIA_ROOT,folder))
            JobStatus.objects.create(job_name=folder+"_multi", pipeline_key=folder, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 all_files=" ",
                                 modules_files=" ",
                                 pipeline_type="multiupload",
                                 )
        return render(self.request, 'multiupload.html', {'file_list': onlyfiles, "request_path":path, "form": MultiURLForm })
        #return render(self.request, 'multiupload.html', {'file_list': [os.path.join(MEDIA_ROOT,folder),os.path.join(MEDIA_ROOT,folder)]})

    def post(self, request):
        #time.sleep(1)  # You don't need this line. This is just to delay the process so you can see the progress bar testing locally.
        form = PhotoForm(self.request.POST, self.request.FILES)
        path = request.path
        folder = path.split("/")[-1]
        make_folder(os.path.join(MEDIA_ROOT,folder))
        if "file" in self.request.FILES:
            if form.is_valid():
                photo = form.save()
                onlyfiles = [f for f in listdir(os.path.join(MEDIA_ROOT, folder))
                             if os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, folder), f))]
                name = photo.file.name.split("/")[-1]
                shutil.move(os.path.join(MEDIA_ROOT,photo.file.name), os.path.join(MEDIA_ROOT, folder, name))
                if name in onlyfiles:
                    data = {'is_valid': False}
                else:
                    data = {'is_valid': True, 'name': name, 'url': os.path.join(MEDIA_URL,folder,name)}

                return JsonResponse(data)

        else:
            dfolder = os.path.join(MEDIA_ROOT, folder)
            form = MultiURLForm(self.request.POST, self.request.FILES, dest_folder= dfolder)
            form.is_valid()
            form.clean()
            if form.is_valid():
                url = reverse('multi:multi_launch') + folder
            #url = reverse('photos:multi_start')
                return redirect(url)

class MultiLaunchView(FormView):
    template_name = 'multi_launch.html'
    #template_name = 'multiupload.html'
    form_class = sRNABenchForm

    def get_form_kwargs(self):
        kwargs = super(MultiLaunchView, self).get_form_kwargs()
        path = self.request.path
        folder = path.split("/")[-1]
        kwargs['dest_folder'] = folder
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        query_id = str(self.request.path_info).split("/")[-1]
        # content_folder = os.path.join(MEDIA_ROOT, query_id, "queryOutput")
        input_folder = os.path.join(MEDIA_ROOT, query_id)
        onlyfiles = [f for f in listdir(os.path.join(MEDIA_ROOT, query_id))
                             if os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, query_id), f))]
        onlyfiles.remove("SRR_files.txt")
        onlyfiles.remove("URL_files.txt")
        if "conf.txt" in onlyfiles:
            onlyfiles.remove("conf.txt")
        table_data=[]
        for ix,file in enumerate(onlyfiles):
            id = "file_"+ str(ix)
            link = '<a href="'+ os.path.join(MEDIA_URL,query_id,file) +'">'+file+'</a>'
            status = "Not launched"
            checkbox = "<input type='checkbox' value='" + id + "' name='to_list' checked=true>"
            table_data.append([link, status, checkbox])

        with open(os.path.join(MEDIA_ROOT, query_id, "SRR_files.txt"), "r") as SRR_file:
            for ix,SRR in enumerate(SRR_file.readlines()) :
                file_name = SRR.rstrip()
                id = "SRR_" + str(ix)
                link = '<a href="https://www.ncbi.nlm.nih.gov/sra/?term='+ file_name +'">'+file_name+'</a>'
                status = "Not launched"
                checkbox = "<input type='checkbox' value='" + id + "' name='to_list' checked=true>"
                table_data.append([link, status, checkbox])

        with open(os.path.join(MEDIA_ROOT, query_id, "URL_files.txt"), "r") as URL_file:
            for ix,URL in enumerate(URL_file.readlines()):
                if len(URL) > 45:
                    file_name = URL.rstrip()[0:15] +  "(...)" + URL.rstrip()[-20:]
                else:
                    file_name = URL.rstrip()
                id = "URL_" + str(ix)
                link = '<a href="' + URL.rstrip() + '">' + file_name + '</a>'
                status = "Not launched"
                checkbox = "<input type='checkbox' value='" + id + "' name='to_list' checked=true>"
                table_data.append([link, status, checkbox])

        #table_data.append(["dummy","dummier","dummiest"])

        js_data = json.dumps(table_data)
        js_headers = json.dumps([{ "title": "Input" },
                                { "title": "Status" },
                                # { "title": "Select" }])
                                { "title": '<input type="checkbox" checked=true id="flowcheckall" value="" />&nbsp;All' }])
        # print(js_data)
        context["table_data"] = js_data
        context["table_headers"] = js_headers
        context["job_id"] = query_id

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
        return super(MultiLaunchView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        form.clean()
        pipeline_id = form.create_call()
        self.success_url = reverse_lazy('srnabench') + '?id=' + pipeline_id

        #os.system(call)
        js = JobStatus.objects.get(pipeline_key=pipeline_id)
        js.status.create(status_progress='sent_to_queue')
        js.job_status = 'sent_to_queue'
        js.save()
        return super(MultiLaunchView, self).form_valid(form)

        # call, pipeline_id = form.create_call()
        # self.success_url = reverse_lazy('mirconstarget') + '?id=' + pipeline_id

def RelaunchMultiOld(request):
    old_ID = str(request.path_info).split("/")[-1]

    random_ID = generate_id()

    if os.path.exists(os.path.join(MEDIA_ROOT, old_ID)):
        os.mkdir(os.path.join(MEDIA_ROOT, random_ID))
        JobStatus.objects.create(job_name=random_ID + "_multi", pipeline_key=random_ID, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 all_files=" ",
                                 modules_files=" ",
                                 pipeline_type="multiupload",
                                 )
        for f in listdir(os.path.join(MEDIA_ROOT, old_ID)):
           if f != "conf.txt":
               if os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, old_ID), f)):
                   shutil.copy(os.path.join(MEDIA_ROOT, old_ID, f), os.path.join(MEDIA_ROOT, random_ID, f))

    if os.path.exists(os.path.join(MEDIA_ROOT, random_ID)):
        url = reverse('multi:multi_launch') + random_ID
        return redirect(url)




    url = reverse('multi:multi_launch') + old_ID
    # url = reverse('multi:multi_launch') + random_ID
    return redirect(url)

def RelaunchMulti(request):
    old_ID = str(request.path_info).split("/")[-1]

    random_ID = generate_id()
    old_dir = os.path.join(MEDIA_ROOT, old_ID)

    if os.path.exists(old_dir):
        os.mkdir(os.path.join(MEDIA_ROOT, random_ID))
        JobStatus.objects.create(job_name=random_ID + "_multi", pipeline_key=random_ID, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 all_files=" ",
                                 modules_files=" ",
                                 pipeline_type="multiupload",
                                 )
        shutil.copy(os.path.join(MEDIA_ROOT, old_ID, "input.json"), os.path.join(MEDIA_ROOT, old_ID, "input.json"))
        os.system("touch " + old_dir)

        if os.path.exists(os.path.join(MEDIA_ROOT, random_ID)):
            url = reverse('multi:multi_launch') + random_ID
            return redirect(url)




    url = reverse('multi:multi_launch') + old_ID
    # url = reverse('multi:multi_launch') + random_ID
    return redirect(url)

def multiDownload(request):
    path = request.path
    folder = path.split("/")[-1]
    jobs_folder = os.path.join(MEDIA_ROOT, folder, "launched")
    launched_ids = [f for f in listdir(jobs_folder) if os.path.isfile(os.path.join(jobs_folder, f))]
    data = {}
    data["files"] = []
    regex = re.compile(r'.*genome.parsed.zip')

    for i in launched_ids:
        new_record = JobStatus.objects.get(pipeline_key=i)
        job_stat = new_record.job_status
        if job_stat == "Finished":
            full_path = os.path.join(MEDIA_ROOT, i)
            rexp = full_path + "/*.zip"
            list_of_files = sorted(glob.iglob(rexp), key=os.path.getctime, reverse=True)

            # glob.iglob(files_path), key = os.path.getctime, reverse = True)
            # list_of_files = glob.glob(rexp)  # * means all if need specific format then *.csv
            # latest_file = max(list_of_files, key=os.path.getctime)
            # list_of_files.remove('')
            filtered = [e.replace(MEDIA_ROOT,MEDIA_URL) for e in list_of_files if not regex.match(e)]
            latest_file = filtered[0]
            data["files"].append(latest_file)


    return JsonResponse(data)

def download_list(multi_id):

    folder = multi_id
    jobs_folder = os.path.join(MEDIA_ROOT, folder, "launched")
    launched_ids = [f for f in listdir(jobs_folder) if os.path.isfile(os.path.join(jobs_folder, f))]
    data = {}
    data["files"] = []
    regex = re.compile(r'.*genome.parsed.zip')

    for i in launched_ids:
        new_record = JobStatus.objects.get(pipeline_key=i)
        job_stat = new_record.job_status
        if job_stat == "Finished":
            full_path = os.path.join(MEDIA_ROOT, i)
            rexp = full_path + "/*.zip"
            list_of_files = sorted(glob.iglob(rexp), key=os.path.getctime, reverse=True)

            # glob.iglob(files_path), key = os.path.getctime, reverse = True)
            # list_of_files = glob.glob(rexp)  # * means all if need specific format then *.csv
            # latest_file = max(list_of_files, key=os.path.getctime)
            # list_of_files.remove('')
            filtered = [e.replace(MEDIA_ROOT,MEDIA_URL) for e in list_of_files if not regex.match(e)]
            latest_file = filtered[0]
            data["files"].append(latest_file)


    return data["files"]

# def ajax_annot_cell(request):
#
#     if request.method == 'POST':
#         jobID = request.GET.get("jobID")
#         # topN = int(request.GET.get("top"))
#
#         new_record = JobStatus.objects.get(pipeline_key=jobID)
#         myfile = request.FILES['myfile']
#         fs = FileSystemStorage(location=folder)  # defaults to   MEDIA_ROOT
#         filename = fs.save(myfile.name, myfile)
#         file_url = fs.url(filename)
#         return render(request, 'upload.html', {
#             'file_url': file_url
#         })
#
#     data = {}
#     data["jobID"] = jobID
#     data["topN"] = topN
#     data["url"] = "https://genecodis.genyo.es/gc4/externalquery&org=9606&genes=" + ",".join(result)
#     return JsonResponse(data)

def ajax_annot_file(request):
    print("x")

def check_file(file_path):

    print("x")

def read_annot_file(file_path):
    # input sheet should have headder
    # TODO checks
    if file_path.endswith("xls") or file_path.endswith("xlsx"):
        annot_df = pd.read_excel(file_path)
    else:
        s = csv.Sniffer()
        d = s.sniff(
            open(file_path).read(100)).delimiter
        annot_df = pd.read_csv(file_path, d)

    return annot_df

def annotate_input(jobID, annotation_file):
    dict_path = os.path.join(MEDIA_ROOT, jobID, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file, object_pairs_hook=OrderedDict)
    json_file.close()

    annot_df = read_annot_file(annotation_file)
    # inputs = annot_df["Input"].tolist()
    for index, row in annot_df.iterrows():
        i = row[0]
        if input_dict.get(i):
            shallow_dict = input_dict.get(i)
            c_key = i
        else:
            succesful = False
            for k in input_dict.keys():
                if k.endswith("/" + i):
                    shallow_dict = input_dict.get(k)
                    c_key = k
                    succesful = True
            if not succesful:
                continue

        shallow_dict["name_annotation"] = str(row[1])
        shallow_dict["group_annotation"] = str(row[2])
        input_dict[c_key] = shallow_dict

    json_file = open(dict_path, "w")
    json.dump(input_dict, json_file, indent=6)
    json_file.close()



def generate_download_template(request):
    parameters = request.GET
    folder = parameters["jobId"]
    dict_path = os.path.join(MEDIA_ROOT, folder, "input.json")
    json_file = open(dict_path, "r")
    input_dict = json.load(json_file, object_pairs_hook=OrderedDict)
    json_file.close()

    annot_df = pd.DataFrame(columns=['Input', 'Name', 'Group'])
    for i,k in enumerate(input_dict.keys()):
        shallow_dict = input_dict.get(k)
        row = []
        if shallow_dict.get("input_type") == "uploaded file":
            input_string = shallow_dict.get("name")
        else:
            input_string = shallow_dict.get("input")
        name = shallow_dict.get("name_annotation", "")
        group = shallow_dict.get("group_annotation", "")

        annot_df.loc[i] = pd.Series({'Input': input_string, 'Name': name, 'Group': group})

    # test_file = os.path.join(MEDIA_ROOT, folder, "test.xlsx")
    template_file = os.path.join(MEDIA_ROOT, folder, "template.xlsx")
    annot_df.to_excel(template_file, index=False)
    # os.system("touch " + test_file)
    url = template_file.replace(MEDIA_ROOT, MEDIA_URL)
    return redirect(url)



class Annotate(DetailView):
    model = JobStatus
    slug_field = 'pipeline_key'
    slug_url_kwarg = 'pipeline_id'
    template_name = 'newBench/annotate.html'
    def post(self, request, *args, **kwargs):

        context = {}
        path = str(request.path_info)
        jobId = path.split("/")[-1]
        # destination_path = os.path.join(MEDIA_ROOT, jobId, "hey.txt")
        annotation_folder = os.path.join(MEDIA_ROOT, jobId, "annotation")
        if not os.path.exists(annotation_folder):
            os.mkdir(annotation_folder)
        else:
            shutil.rmtree(annotation_folder)
            os.mkdir(annotation_folder)
        # to_upload = request.FILES['annotationInputFile']
        to_upload = request.FILES.get('annotationInputFile')
        fs = FileSystemStorage(location=annotation_folder)
        filename = fs.save(to_upload.name, to_upload)
        try:
            annotate_input(jobId, os.path.join(annotation_folder, filename))
        except:
            # shutil.rmtree(annotation_folder)
            # os.mkdir(annotation_folder)
            error_file = os.path.join(annotation_folder, "error.error")
            os.system("touch " + error_file)
            # context["error_message"] = "There was some error parsing your file. Please check again the format and requirements."

        return redirect(reverse_lazy('multi:multi_annotate') + jobId)

    def render_to_response(self, context,  **response_kwargs):

        job_status = context.get('object')
        pipeline_id = job_status.pipeline_key
        jobs_folder = os.path.join(MEDIA_ROOT,pipeline_id,"launched")
        if not os.path.exists(jobs_folder):
            return redirect(reverse_lazy("launch")+ "?jobId=" + pipeline_id)

        error_file = os.path.join(MEDIA_ROOT, pipeline_id, "annotation", "error.error")
        if os.path.exists(error_file):
            context["error_message"] = "There was some error parsing your file. Please check the format and requirements again to fix it."


        output_folder = os.path.join(MEDIA_ROOT, pipeline_id)
        dict_path = os.path.join(output_folder, "input.json")
        json_file = open(dict_path, "r")
        input_dict = json.load(json_file, object_pairs_hook=OrderedDict)
        json_file.close()

        samples = []

        for i,k in enumerate(input_dict.keys()):
            c_dict = input_dict[k]
            input_line = c_dict["input"]
            orig_input = input_line
            if "/" in input_line:
                input_line = input_line.split("/") [-1]
            name_annotation = c_dict.get("name_annotation", "Not annotated")
            if name_annotation == "nan":
                name_annotation = "Not annotated"
            group_annotation = c_dict.get("group_annotation", "Not annotated")
            if group_annotation == "nan":
                group_annotation = "Not annotated"
            samples.append([orig_input, input_line, name_annotation, group_annotation, i])


        context["all_samples"] = samples
        context["jobID"] = pipeline_id
        context["go_back_url"] = reverse_lazy("multi:multi_status") + pipeline_id

        context["user_message"] = "This page is still in development, " \
                                  "please do not use it as it will probably not work. Thank you "


        return super(Annotate, self).render_to_response(context, **response_kwargs)





# https://arn.ugr.es/srnatoolbox/multiupload/status/0SM8DZFZPQL2YE3
class MultiStatusViewAnnot(DetailView):
    model = JobStatus
    slug_field = 'pipeline_key'
    slug_url_kwarg = 'pipeline_id'
    template_name = 'newBench/multi_status_annot.html'

    def render_to_response(self, context,  **response_kwargs):

        job_status = context.get('object')
        pipeline_id = job_status.pipeline_key
        jobs_folder = os.path.join(MEDIA_ROOT,pipeline_id,"launched")
        if not os.path.exists(jobs_folder):
            return redirect(reverse_lazy("launch")+ "?jobId=" + pipeline_id)


        launched_ids = [f for f in listdir(jobs_folder) if os.path.isfile(os.path.join(jobs_folder,f))]
        context["ids_strings"] = ",".join(launched_ids)

        dict_path = os.path.join(MEDIA_ROOT, pipeline_id, "input.json")
        json_file = open(dict_path, "r")
        input_dict = json.load(json_file, object_pairs_hook=OrderedDict)
        json_file.close()

        # make annotation compatible
        short_dict = {os.path.basename(x):input_dict.get(x) for x in input_dict.keys()}

        jobs_tbody = []
        context["running"] = False
        # if len(launched_ids)>3:
        #     context["launchDE"] = True
        finished = 0
        for id in launched_ids:

            job = '<a href="'+SUB_SITE+'/jobstatus/' + id +'" target="_blank" >' + id +'</a>'
            new_record = JobStatus.objects.get(pipeline_key=id)

            # ptype = new_record.pipeline_type
            # if ptype == "miRNAgFree":
            #     return redirect(reverse_lazy("mirgfree:"))

            job_stat = new_record.job_status
            if job_stat == "sent_to_queue":
                job_stat = "In queue"
            if job_stat == "Running" or job_stat == "In queue":
                context["running"] = True
            if job_stat == "Finished":
                finished = finished+1
            start = new_record.start_time.strftime("%H:%M:%S, %d %b %Y")
            #finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
            if new_record.finish_time:
                finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
            else:
                finish = "-"
            input_config = os.path.join(MEDIA_ROOT,id,"conf.txt")
            with open(input_config,"r") as f:
                input_line = os.path.basename(f.readlines()[0][6:])
            # job_stat = "sent_to_queue"
            click = '<a href="'+SUB_SITE+'/jobstatus/' + id +'" target="_blank" > Go to results </a>'
            outdir = new_record.outdir
            annot_dict = short_dict.get(input_line.rstrip(), {})
            name_annotation = annot_dict.get("name_annotation", "Not annotated")
            if name_annotation == "nan":
                name_annotation = "Not annotated"
            group_annotation = annot_dict.get("group_annotation", "Not annotated")
            if group_annotation == "nan":
                group_annotation = "Not annotated"
            annot_dict["jobID"] = id
            short_dict[input_line.rstrip()] = annot_dict
            jobs_tbody.append([job, job_stat, start,finish ,input_line.rstrip(), name_annotation, group_annotation])
            # jobs_tbody.append([job, job_stat, start,finish ,input_line, click])




        if finished > 3 and (not context["running"]):
            context["launchDE"] = True


        js_data = json.dumps(jobs_tbody)
        js_headers = json.dumps([{"title": "job ID"},
                                 {"title": "Status"},
                                 {"title": "Started"},
                                 {"title": "Finished"},
                                 {"title": "Input"},
                                 {"title": "Name"},
                                 {"title": "Group"},
                                 # { "title": "Select" }])
                                 # {"title": 'Go to'}

                                 ]
                                )
        #
        #
        #
        # THIS ALTERS THE INPUT.JSON
        #
        #
        #
        json_file = open(os.path.join(MEDIA_ROOT, pipeline_id, "input.json"), "w")
        json.dump(short_dict, json_file, indent=6)
        json_file.close()

        context["tbody"] = js_data
        context["thead"] = js_headers
        context["njobs"] = len(jobs_tbody)
        context["id"] = pipeline_id
        context["download_list"] = download_list(pipeline_id)
        return super(MultiStatusViewAnnot, self).render_to_response(context, **response_kwargs)

class MultiStatusView(DetailView):
    model = JobStatus
    slug_field = 'pipeline_key'
    slug_url_kwarg = 'pipeline_id'
    template_name = 'multi_status.html'

    def render_to_response(self, context,  **response_kwargs):

        job_status = context.get('object')
        pipeline_id = job_status.pipeline_key
        jobs_folder = os.path.join(MEDIA_ROOT,pipeline_id,"launched")
        if not os.path.exists(jobs_folder):
            return redirect(reverse_lazy("launch")+ "?jobId=" + pipeline_id)


        launched_ids = [f for f in listdir(jobs_folder) if os.path.isfile(os.path.join(jobs_folder,f))]
        context["ids_strings"] = ",".join(launched_ids)

        jobs_tbody = []
        context["running"] = False
        # if len(launched_ids)>3:
        #     context["launchDE"] = True
        finished = 0
        for id in launched_ids:

            job = '<a href="'+SUB_SITE+'/jobstatus/' + id +'" target="_blank" >' + id +'</a>'
            new_record = JobStatus.objects.get(pipeline_key=id)

            # ptype = new_record.pipeline_type
            # if ptype == "miRNAgFree":
            #     return redirect(reverse_lazy("mirgfree:"))

            job_stat = new_record.job_status
            if job_stat == "sent_to_queue":
                job_stat = "In queue"
            if job_stat == "Running" or job_stat == "In queue":
                context["running"] = True
            if job_stat == "Finished":
                finished = finished+1
            start = new_record.start_time.strftime("%H:%M:%S, %d %b %Y")
            #finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
            if new_record.finish_time:
                finish = new_record.finish_time.strftime("%H:%M, %d %b %Y")
            else:
                finish = "-"
            input_config = os.path.join(MEDIA_ROOT,id,"conf.txt")
            with open(input_config,"r") as f:
                input_line = os.path.basename(f.readlines()[0][6:])
            # job_stat = "sent_to_queue"
            click = '<a href="'+SUB_SITE+'/jobstatus/' + id +'" target="_blank" > Go to results </a>'
            outdir = new_record.outdir

            jobs_tbody.append([job, job_stat, start,finish ,input_line, click])
            #jobs_tbody.append([job, job_stat, start, finish, click])

        if finished > 3 and (not context["running"]):
            context["launchDE"] = True


        js_data = json.dumps(jobs_tbody)
        js_headers = json.dumps([{"title": "job ID"},
                                 {"title": "Status"},
                                 {"title": "Started"},
                                 {"title": "Finished"},
                                 {"title": "Input"},
                                 # { "title": "Select" }])
                                 {"title": 'Go to'}

                                 ]
                                )
        context["tbody"] = js_data
        context["thead"] = js_headers
        context["njobs"] = len(jobs_tbody)
        context["id"] = pipeline_id
        context["download_list"] = download_list(pipeline_id)
        return super(MultiStatusView, self).render_to_response(context, **response_kwargs)




class DragAndDropUploadView(View):
    def get(self, request,**kwargs):
        photos_list = Photo.objects.all()
        return render(self.request, 'photos/drag_and_drop_upload/index.html', {'photos': photos_list})

    def post(self, request):
        form = PhotoForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            photo = form.save()
            data = {'is_valid': True, 'name': photo.file.name, 'url': photo.file.url, "files" : ["a","b"]}
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


def clear_database(request):
    for photo in Photo.objects.all():
        photo.file.delete()
        photo.delete()
    return redirect(request.POST.get('next'))
