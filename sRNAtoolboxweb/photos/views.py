import time

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View

from .forms import PhotoForm
from .models import Photo
from django.core.urlresolvers import reverse, reverse_lazy
import string
import random
from django.views.generic import RedirectView
from django.shortcuts import redirect
from os import listdir
import os
from sRNAtoolboxweb.settings import MEDIA_ROOT
from progress.models import JobStatus
import shutil

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
    url = reverse('photos:multi_start') + random_ID
    return redirect(url)



class MultiUploadView(View):
    def get(self, request):
        path = request.path
        folder = path.split("/")[-1]
        onlyfiles = []
        if os.path.exists(os.path.join(MEDIA_ROOT,folder)):
            onlyfiles = [f for f in listdir(os.path.join(MEDIA_ROOT,folder)) if
                     os.path.isfile(os.path.join(os.path.join(MEDIA_ROOT, folder), f))]
        else:
            onlyfiles = []
            os.mkdir(os.path.join(MEDIA_ROOT,folder))
        #photos_list = Photo.objects.all()
        #return render(self.request, 'multiupload.html', {'photos': photos_list})
        #return render(self.request, 'multiupload.html', {'file_list': onlyfiles})
        return render(self.request, 'multiupload.html', {'file_list': onlyfiles})

    def post(self, request):
        time.sleep(1)  # You don't need this line. This is just to delay the process so you can see the progress bar testing locally.
        form = PhotoForm(self.request.POST, self.request.FILES)
        path = request.path
        folder = path.split("/")[-1]
        if form.is_valid():
            photo = form.save()
            name = photo.file.name.split("/")[-1]
            shutil.copyfile(os.path.join(MEDIA_ROOT,photo.file.name), os.path.join(MEDIA_ROOT, folder, name))
            #shutil.move(os.path.join(MEDIA_ROOT,photo.file.name), os.path.join(MEDIA_ROOT, folder, name))
            #os.rename(photo.file.name, os.path.join(MEDIA_ROOT, folder, name))
            data = {'is_valid': True, 'name': name, 'url': ""}
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


class DragAndDropUploadView(View):
    def get(self, request):
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
