import time

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.views.generic import FormView
from sRNABench.forms import sRNABenchForm

from .forms import PhotoForm, MultiURLForm
from .models import Photo
from django.core.urlresolvers import reverse, reverse_lazy
import string
import random
from django.views.generic import RedirectView
from django.shortcuts import redirect
from os import listdir
import os
from sRNAtoolboxweb.settings import MEDIA_ROOT, MEDIA_URL
from progress.models import JobStatus
import shutil
import datetime
import json


def generate_uniq_id(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_id():
    is_new = True
    while is_new:
        pipeline_id = generate_uniq_id()
        if not JobStatus.objects.filter(pipeline_key=pipeline_id):
            return pipeline_id

class GetIDView(RedirectView):
    #template_name = 'home/about.html'
    random_ID = generate_uniq_id()
    link = reverse_lazy('photos:progress_bar_upload')
    #url = link + "new/" +random_ID


def new_upload(request):
    #request.session['error_message'] = 'test'
    random_ID = generate_id()
    url = reverse('photos:multi_new') + random_ID
    return redirect(url)



class MultiUploadView(FormView):
    #template_name = 'bench.html'
    #form_class = sRNABenchForm
    #success_url = reverse('photos:multi_start')

    def get_form_kwargs(self):
        '''This goes in the Update view'''
        kwargs = super(MultiUploadView, self).get_form_kwargs()  # put your view name in the super
        kwargs["request_path"] = self.request.path
        return kwargs

    def get(self, request,**kwargs):
        path = request.path
        folder = path.split("/")[-1]
        onlyfiles = []
        if os.path.exists(os.path.join(MEDIA_ROOT,folder)):
            onlyfiles = [[f,os.path.join(MEDIA_URL, folder, f)] for f in listdir(os.path.join(MEDIA_ROOT,folder)) if
                     os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, folder), f))]
        else:
            onlyfiles = []
            os.mkdir(os.path.join(MEDIA_ROOT,folder))
            JobStatus.objects.create(job_name=folder+"_multi", pipeline_key=folder, job_status="not_launched",
                                 start_time=datetime.datetime.now(),
                                 all_files="",
                                 modules_files="",
                                 pipeline_type="multiupload",
                                 )
        return render(self.request, 'multiupload.html', {'file_list': onlyfiles, "request_path":path, "form": MultiURLForm })
        #return render(self.request, 'multiupload.html', {'file_list': [os.path.join(MEDIA_ROOT,folder),os.path.join(MEDIA_ROOT,folder)]})

    def post(self, request):
        #time.sleep(1)  # You don't need this line. This is just to delay the process so you can see the progress bar testing locally.
        form = PhotoForm(self.request.POST, self.request.FILES)
        path = request.path
        folder = path.split("/")[-1]
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
                url = reverse('photos:multi_launch') + folder
            #url = reverse('photos:multi_start')
                return redirect(url)

class MultiLaunchView(FormView):
    template_name = 'multi_launch.html'
    #template_name = 'multiupload.html'
    form_class = sRNABenchForm

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        query_id = str(self.request.path_info).split("/")[-1]
        # content_folder = os.path.join(MEDIA_ROOT, query_id, "queryOutput")
        input_folder = os.path.join(MEDIA_ROOT, query_id)
        onlyfiles = [f for f in listdir(os.path.join(MEDIA_ROOT, query_id))
                             if os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, query_id), f))]
        onlyfiles.remove("SRR_files.txt")
        onlyfiles.remove("URL_files.txt")
        table_data=[]
        for ix,file in enumerate(onlyfiles):
            id = "file_"+ str(ix)
            link = '<a href="'+ os.path.join(MEDIA_URL,query_id,file) +'">'+file+'</a>'
            status = "Not launched"
            checkbox = "<input type='checkbox' value='" + id + "' name='to_list'>"
            table_data.append([link, status, checkbox])

        with open(os.path.join(MEDIA_ROOT, query_id, "SRR_files.txt"), "r") as SRR_file:
            for ix,SRR in enumerate(SRR_file.readlines()) :
                file_name = SRR.rstrip()
                id = "SRR_" + str(ix)
                link = '<a href="https://www.ncbi.nlm.nih.gov/sra/?term='+ file_name +'">'+file_name+'</a>'
                status = "Not launched"
                checkbox = "<input type='checkbox' value='" + id + "' name='to_list'>"
                table_data.append([link, status, checkbox])

        with open(os.path.join(MEDIA_ROOT, query_id, "URL_files.txt"), "r") as URL_file:
            for URL in URL_file.readlines():
                if len(URL) > 19:
                    file_name ="(...)" + URL.rstrip()[-20:]
                else:
                    file_name = URL.rstrip()
                id = "URL_" + str(ix)
                link = '<a href="' + URL.rstrip() + '">' + file_name + '</a>'
                status = "Not launched"
                checkbox = "<input type='checkbox' value='" + id + "' name='to_list'>"
                table_data.append([link, status, checkbox])

        #table_data.append(["dummy","dummier","dummiest"])

        js_data = json.dumps(table_data)
        js_headers = json.dumps([{ "title": "Input" },
                                { "title": "Status" },
                                { "title": "Select" }])
        # print(js_data)
        context["table_data"] = js_data
        context["table_headers"] = js_headers

        return context

    def form_valid(self, form):
        form.clean()

        # call, pipeline_id = form.create_call()
        # self.success_url = reverse_lazy('mirconstarget') + '?id=' + pipeline_id


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
