# Create your views here.
import os
import time
from subprocess import Popen, PIPE

from django.http import Http404
from django.shortcuts import render, redirect
from django.views.generic import DetailView
from rest_framework import generics
from rest_framework.generics import UpdateAPIView, RetrieveAPIView, CreateAPIView

from models import JobStatus, Status
from sRNAtoolboxweb.settings import CONF
from serializers import JobStatusSerializer, StatusSerializer


class Msg():
    """
    Class to manage texts of job status
    """

    def __init__(self, msg):
        """
        :param msg: text of msg status
        """
        self.text = msg
        if msg.find("INFO") >= 0:
            self.type = "info"

        elif msg.find("SUCCESS") >= 0:
            self.type = "success"

        elif msg.find("WARNING") >= 0:
            self.type = "warning"
        elif msg.find("ERROR") >= 0:
            self.type = "error"
        else:
            self.type = "None"


def queue_Status(id):
    outputs = Popen("qstat -f", shell=True, stdout=PIPE).communicate()[0].replace(" ", "").split("\n")
    is_job = False
    for line in outputs:
        if line.startswith("Job_Name"):
            if id in line:
                is_job = True

        if line.startswith("job_state") and is_job:
            return line.split("=")[1]
    return None


def load_status_from_file(id):
    log = os.path.join(CONF['sRNAtoolboxSODataPath'], id, "logFile")
    log_txt = os.path.join(CONF['sRNAtoolboxSODataPath'], id, "logFile.txt")

    if os.path.isfile(log):
        log_file = log
    elif os.path.isfile(log_txt):
        log_file = log_txt
    else:
        return []

    fd = file(log_file)
    msgs = [Msg(t) for t in fd.readlines() if Msg(t).type != "None"]
    fd.close()

    return  msgs



class JobStatusDetail(DetailView):

    model = JobStatus
    slug_field = 'pipeline_key'
    slug_url_kwarg = 'pipeline_id'
    template_name = 'progress.html'

    @staticmethod
    def get_context_with_messages(job_status):
        msgs = [Msg(t) for t in job_status.job_status_progress]
        msgs += load_status_from_file(job_status.pipeline_key)
        error = False
        for msg in msgs:
            if msg.type == "error":
                error = True

        if error:
            return {'msgs': msgs,
                    "url": "/srnatoolbox/" + job_status.tool + "/results/?id=" + job_status.pipeline_key,
                    "id": job_status.pipeline_key}
        else:
            return {'running': True,
                    'msgs': msgs, "url": "/srnatoolbox/" + job_status.tool + "/results/?id=" + job_status.pipeline_key,
                    "id": job_status.pipeline_key}

    @staticmethod
    def get_running_context_for_srnabench(job_status):
        if os.path.exists(os.path.join(job_status.outdir, "parameters.txt")):
            return redirect("/srnatoolbox/" + job_status.tool + "/results/?id=" + job_status.pipeline_key)
        else:
            return JobStatusDetail.get_context_with_messages(job_status)

    @staticmethod
    def get_context_finished_with_errors(job_status):
        msgs = [Msg(t) for t in job_status.job_status_progress]
        msgs += load_status_from_file(job_status.pipeline_key)
        return {'msgs': msgs,
                "url": "/srnatoolbox/" + job_status.tool + "/results/?id=" + job_status.pipeline_key,
                "id": job_status.pipeline_key}

    @staticmethod
    def get_error_context(job_status):
        return {'msgs': [Msg(
            "ERROR: An error occured with your job:" + job_status.pipeline_key + "\nPlease report it indicating the jobID")],
            "id": job_status.pipeline_key}

    @staticmethod
    def get_context_qw(job_status):
        return {'running': True, 'queue': True, 'msgs': [Msg("INFO: Job is queue waiting")], "id": job_status.pipeline_key}


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(JobStatusDetail, self).get_context_data(**kwargs)
        status = queue_Status(kwargs.get('pipeline_id'))
        job_status = context.get('object')
        if status == 'R' or status == 'E':
            if job_status.job_status == 'send_to_queue':
                time.sleep(5)
                job_status = JobStatus.objects.get(pipeline_key=kwargs.get('pipeline_id'))
                if job_status.job_status == 'send_to_queue':
                    return self.get_error_context(job_status)
            if job_status.job_status == 'Running':
                if job_status.tool == 'srnabench':
                    return self.get_running_context_for_srnabench(job_status)
                else:
                    return self.get_context_with_messages(job_status)
            if job_status.job_status == 'Finished':
                return redirect("/srnatoolbox/" + job_status.tool + "/results/?id=" + job_status.pipeline_key)
            elif job_status.job_status == "Finished with Errors":
                return self.get_context_finished_with_errors(job_status)
            else:
                return self.get_error_context(job_status)
        if status is not None:
            return self.get_context_qw(job_status)
        else:
            if job_status.job_status == 'send_to_queue':
                return self.get_error_context(job_status)
            if job_status.job_status == "Finished":
                if job_status.tool == "srnabench" and not os.path.exists(os.path.join(job_status.outdir, "parameters.txt")):
                    return self.get_error_context(job_status)
                else:
                    return redirect("/srnatoolbox/" + job_status.tool + "/results/?id=" + job_status.pipeline_key)
            elif job_status.job_status == "Finished with Errors":
                return self.get_context_finished_with_errors(job_status)
            else:
                return self.get_error_context(job_status)


class ProgressAPI(RetrieveAPIView, UpdateAPIView):
    model = JobStatus
    serializer_class = JobStatusSerializer
    lookup_field = 'pipeline_key'
    lookup_url_kwarg = 'pipeline_id'
    queryset = JobStatus.objects.all()

class ProgressCreate(CreateAPIView):
    model = JobStatus
    serializer_class = JobStatusSerializer


class AddStatus(UpdateAPIView):
    serializer_class = StatusSerializer
    def get_object(self):
        pipeline_key = self.kwargs.get('pipeline_id')
        try:
            job_status = JobStatus.objects.get(pipeline_key=pipeline_key)
        except:
            raise Http404
        return Status(JobStatus=job_status)
