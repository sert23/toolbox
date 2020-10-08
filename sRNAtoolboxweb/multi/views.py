import time
import glob
from django.shortcuts import render, redirect
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

def RelaunchMulti(request):
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
