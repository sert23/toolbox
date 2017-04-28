# Create your views here.
import os

from django.shortcuts import render, redirect
import time
from models import JobStatus
from subprocess import Popen, PIPE, STDOUT, call


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
    log = os.path.join("/shared/sRNAtoolbox/webData/", id, "logFile")
    log_txt = os.path.join("/shared/sRNAtoolbox/webData/", id, "logFile.txt")

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


def progress(request, tool):
    """
    :type request: render
    :rtype : render
    :param request: posts and gets
    :return: html with results of srnafuncterms
    """

    if 'id' in request.GET:
        job_id = request.GET['id']
        status = queue_Status(job_id)

        if status == 'R' or status == 'E':
            try:
                new_record = JobStatus.objects.get(pipeline_key=job_id)
            except:
                time.sleep(2)
                try:
                    new_record = JobStatus.objects.get(pipeline_key=job_id)
                except:
                    return render(request, 'progress.html', {'msgs': [Msg(
                        "ERROR: An error occured with your job:" + job_id + "\nPlease report it indicating the jobID")], "id": job_id})

            assert isinstance(new_record, JobStatus)
            if (new_record.job_status == "Running" and tool != "srnabench") or (new_record.job_status == "Running" and tool == "srnabench" and not os.path.exists(os.path.join(new_record.outdir, "parameters.txt"))):
                msgs = [Msg(t) for t in new_record.job_status_progress]
                msgs = msgs + load_status_from_file(job_id)

                error = False
                for msg in msgs:
                    if msg.type == "error":
                        error = True

                if error:
                    return render(request, 'progress.html', {'msgs': msgs, "url": "/srnatoolbox/" + tool + "/results/?id=" + job_id, "id": job_id})
                else:
                    return render(request, 'progress.html', {'running': True, 'msgs': msgs, "url": "/srnatoolbox/" + tool + "/results/?id=" + job_id, "id": job_id})


            elif new_record.job_status == "Finished" or (new_record.job_status == "Running" and tool == "srnabench" and os.path.exists(os.path.join(new_record.outdir, "parameters.txt"))):

                if tool == "srnabench" and not os.path.exists(os.path.join(new_record.outdir, "parameters.txt")):

                    return render(request, 'progress.html', {'msgs': [Msg(
                        "ERROR: An error occured with your job:" + job_id + "\nPlease report it indicating the jobID")], "id": job_id})

                return redirect("/srnatoolbox/" + tool + "/results/?id=" + job_id)



            elif new_record.job_status == "Finished with Errors":
                msgs = [Msg(t) for t in new_record.job_status_progress]
                msgs = msgs + load_status_from_file(job_id)
                return render(request, 'progress.html', {'msgs': msgs, "url": "/srnatoolbox/" + tool + "/results/?id=" + job_id, "id": job_id})

            else:
                return render(request, 'progress.html', {'error': True, 'msgs': [Msg(
                    "ERROR: An error occured with your job:" + job_id + "\nPlease report it indicating the jobID")], "id": job_id})

        elif status == 'Q':
            return render(request, 'progress.html', {'running': True, 'queue': True, 'msgs': [Msg("INFO: Job is queue waiting")], "id": job_id})

        elif status is not None:
            return render(request, 'progress.html', {'running': True, 'queue': True, 'msgs': [Msg("INFO: Job is queue waiting")], "id": job_id})



        else:
            try:
                new_record = JobStatus.objects.get(pipeline_key=job_id)
            except:
                return render(request, 'progress.html', {'error': True, 'msgs': [Msg(
                    "ERROR: An error occured with your job:" + job_id + "\nPlease report it indicating the jobID")], "id": job_id})

            assert isinstance(new_record, JobStatus)
            if new_record.job_status == "Finished":

                if tool == "srnabench" and not os.path.exists(os.path.join(new_record.outdir, "parameters.txt")):
                    return render(request, 'progress.html', {'msgs': [Msg(
                        "ERROR: An error occured with your job:" + job_id + "\nPlease report it indicating the jobID")], "id": job_id})
                else:
                    return redirect("/srnatoolbox/" + tool + "/results/?id=" + job_id)

            elif new_record.job_status == "Finished with Errors":
                msgs = [Msg(t) for t in new_record.job_status_progress]
                msgs = msgs + load_status_from_file(job_id)
                return render(request, 'progress.html', {'msgs': msgs, "url": "/srnatoolbox/" + tool + "/results/?id=" + job_id, "id": job_id})
            else:
                return render(request, 'progress.html', {'error': True, 'msgs': [Msg(
                    "ERROR: An error occured with your job:" + job_id + "\nPlease report it indicating the jobID")], "id": job_id})

