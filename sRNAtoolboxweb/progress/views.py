# Create your views here.
import os
import time
from subprocess import Popen, PIPE

from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView
from rest_framework import generics
from rest_framework.generics import UpdateAPIView, RetrieveAPIView, CreateAPIView
from progress.models import JobStatus, Status
from sRNAtoolboxweb.settings import CONF, SUB_SITE
from progress.serializers import JobStatusSerializer, StatusSerializer
from django.core.urlresolvers import reverse


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
    with Popen(["qstat", "-f"], stdout=PIPE) as proc:
        outputs = proc.stdout.read().decode("utf8").replace(" ", "").split("\n")
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

    fd = open(log_file)
    msgs = [Msg(t) for t in fd.readlines() if Msg(t).type != "None"]
    fd.close()

    return  msgs

def parse_web_log(id):
    new_record = JobStatus.objects.get(pipeline_key=id)
    log_path = os.path.join(new_record.outdir,"logFile.txt")
    tagged = ""
    if os.path.exists(log_path):
        with open(log_path,"r") as log_file:
            for line in log_file.readlines():
                if " WEB:" in line:
                    rem,keep = line.rstrip().split("WEB:")
                    tagged = tagged + keep +"\n"

        return tagged
    else:
        return None


class JobStatusDetail(DetailView):

    model = JobStatus
    slug_field = 'pipeline_key'
    slug_url_kwarg = 'pipeline_id'
    template_name = 'progress.html'

    @staticmethod
    def get_context_with_messages(job_status):
        msgs = [Msg(t.status_progress) for t in job_status.status.all()]
        msgs += load_status_from_file(job_status.pipeline_key)
        error = False
        for msg in msgs:
            if msg.type == "error":
                error = True

        if error:
            return {'msgs': msgs,
                    #"url": "/srnatoolbox/" + job_status.pipeline_type + "/results/?id=" + job_status.pipeline_key,
                    "url": "/jobstatus/" + job_status.pipeline_key,
                    "id": job_status.pipeline_key,
                    "pipe_type": job_status.pipeline_type}
        else:
            return {'running': True,
                    'msgs': msgs, "url": "/jobstatus/" + job_status.pipeline_key,
                    #'msgs': msgs, "url": "/srnatoolbox/" + job_status.pipeline_type + "/results/?id=" + job_status.pipeline_key,
                    "id": job_status.pipeline_key,
                    "pipe_type": job_status.pipeline_type}

    @staticmethod
    def get_running_context_for_srnabench(job_status):
        if os.path.exists(os.path.join(job_status.outdir, "parameters.txt")) and os.path.exists(os.path.join(job_status.outdir, "results.txt")):
            return JobStatusDetail.get_context_with_messages(job_status)
        #     #return redirect("/srnatoolbox/" + job_status.pipeline_type + "/results/?id=" + job_status.pipeline_key)
        #     return redirect("/jobstatus/" + job_status.pipeline_key)
        # else:


    @staticmethod
    def get_context_finished_with_errors(job_status):
        """

        :param job_status:
        :type job_status: JobStatus
        :return:
        """
        msgs = [Msg(t.status_progress) for t in job_status.status.all()]
        msgs += load_status_from_file(job_status.pipeline_key)
        return {'msgs': msgs,
                #"url": "/srnatoolbox/" + job_status.pipeline_type + "/results/?id=" + job_status.pipeline_key,
                "url": "/jobstatus/" + job_status.pipeline_key,
                "id": job_status.pipeline_key,
                "pipe_type": job_status.pipeline_type}

    @staticmethod
    def get_error_context(job_status):
        """

        :param job_status:
        :type job_status: JobStatus
        :return:
        """
        web_log = parse_web_log(job_status.pipeline_key)

        initial_url = reverse_lazy(job_status.pipeline_type.lower())

        if job_status.pipeline_type == "sRNAbench":
            go_back_url = reverse_lazy(job_status.pipeline_type.lower())[:-7]

        elif job_status.pipeline_type == "helper":
            go_back_url = SUB_SITE
        else:
            go_back_url = reverse_lazy(job_status.pipeline_type.lower())[:-6]

        if web_log:
            return {'msgs': [Msg(
            "ERROR: An error occurred with your job:" + job_status.pipeline_key + "\nPlease report it indicating the jobID")],
            "id": job_status.pipeline_key, "web_log": web_log, "go_back_url": go_back_url   }
            # "id": job_status.pipeline_key, "web_log": web_log, "go_back_url": "memeee"  }
        else:
            return {'msgs': [Msg(
            "ERROR: An error occurred with your job:" + job_status.pipeline_key + "\nPlease report it indicating the jobID")],
            "id": job_status.pipeline_key, "go_back_url": go_back_url   }



    @staticmethod
    def get_context_qw(job_status):

        def qstat_pos(jobID):
            import subprocess

            # Set up the echo command and direct the output to a pipe
            p1 = subprocess.Popen(['qstat', '-a'], stdout=subprocess.PIPE)
            output = str(p1.communicate()[0])
            lines = output.split("\\n")
            count = 0
            # qstat -a
            for l in lines:
                if l[0].isdigit():
                    data = l.split()
                    if data[3].startswith(jobID):
                        # plist.append(data[1],data[4])
                        if data[9] == "Q":
                            count += 1
                            return count
                        elif data[9] == "R":
                            return 0
                    elif data[9] == "Q":
                        count += 1

        position = qstat_pos(job_status.pipeline_key)
        if position < 1:
            running = True
            queue = False
            out_message = "INFO: Your job is running"
        else:
            running = False
            queue = True
            out_message = "INFO: Job is queue waiting"

        return {'running': running, 'queue': queue, 'msgs': [Msg(out_message)], "id": job_status.pipeline_key, "position": str(position)}
        # return {'running': True, 'queue': True, 'msgs': [Msg("INFO: Job is queue waiting")], "id": job_status.pipeline_key, "position": str(position)}


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(JobStatusDetail, self).get_context_data(**kwargs)
        job_status = context.get('object')
        if job_status.pipeline_type == 'multiupload':
            context["type"] = "multi"
            return context

        if job_status.job_status == 'Finished':
            return {}

        status = queue_Status(job_status.pipeline_key)
        if status == 'R' or status == 'E' or status == 'C':
            if job_status.job_status == 'sent_to_queue':
                return self.get_context_qw(job_status)
            if job_status.job_status == 'Running':
                if job_status.pipeline_type == 'sRNAbench':
                    #return self.get_running_context_for_srnabench(job_status)
                    print("lele")
                    return self.get_context_with_messages(job_status)
                else:
                    return self.get_context_with_messages(job_status)
            if job_status.job_status == 'Finished':
                if job_status.pipeline_type == 'sRNAbench':
                    new_record = JobStatus.objects.get(pipeline_key=job_status.pipeline_key)
                    #status = queue_Status(job_status.pipeline_key)
                    if not os.path.exists(os.path.join(new_record.outdir, "results.txt")):
                        return self.get_error_context(job_status)
                # return redirect("/srnatoolbox/" + job_status.pipeline_type + "/results/?id=" + job_status.pipeline_key)
                return {}
            elif job_status.job_status == "Finished with Errors":
                if job_status.pipeline_type == "sRNAbench" and os.path.exists(
                        os.path.join(job_status.outdir, "results.txt")):
                    return {}
                else:
                    return self.get_error_context(job_status)
            else:
                return self.get_error_context(job_status)
        if status is not None:
            return self.get_context_qw(job_status)
        else:
            if job_status.job_status == 'sent_to_queue':
                return self.get_error_context(job_status)
            if job_status.job_status == "Finished":
                time.sleep(5)
                if job_status.pipeline_type == "sRNAbench" and not os.path.exists(os.path.join(job_status.outdir, "results.txt")):
                    return self.get_error_context(job_status)
                else:
                    # return redirect("/srnatoolbox/" + job_status.pipeline_type + "/results/?id=" + job_status.pipeline_key)
                    return {}
            elif job_status.job_status == "Finished with Errors":
                if job_status.pipeline_type == "sRNAbench" and os.path.exists(
                        os.path.join(job_status.outdir, "results.txt")):
                    return {}
                #return self.get_context_finished_with_errors(job_status)
                else:
                    return self.get_error_context(job_status)

            else:
                # print("y qué voy a hacer")
                return self.get_error_context(job_status)

    def render_to_response(self, context, **response_kwargs):
        if context:
            if context.get("type"):
                job_status = self.object
                context["go_back_url"] = reverse_lazy(job_status.pipeline_type.lower())
                # context["type_lower"] = job_status.pipeline_type.lower()
                if context["type"] == "multi":
                    job_status = context.get('object')
                    url = reverse('multi:multi_status') + job_status.pipeline_key
                    return redirect(url)

            return super(JobStatusDetail, self).render_to_response(context, **response_kwargs)

        job_status = self.object
        return redirect(reverse_lazy(job_status.pipeline_type.lower()) + "?id=" + job_status.pipeline_key)
        #return redirect(reverse_lazy(job_status.pipeline_type.lower()) + "/results/?id=" + job_status.pipeline_key)



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
            #raise Http404
            raise HttpResponseBadRequest
        return Status(JobStatus=job_status)
