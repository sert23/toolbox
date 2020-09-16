import os
from time import strftime, gmtime

from pipelines.pipelines import Pipeline
#from progress.models import JobStatus
import os
import time
import urllib.request

class miRNAgFreePipe(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, config_file=None, parameters=""):
        super(miRNAgFreePipe, self).__init__(pipeline_key, job_name, outdir, "miRNAgFree", parameters)

        self.conf = config_file
        self.outdir = outdir

    def run(self):
        self.initialize_pipeline_status()
        self.change_pipeline_status("Running")
        self.download_url()
        self.download_drive()
        self.call_mirg()
        self.set_finish_time()
        time.sleep(10)
        if os.path.exists(os.path.join(self.outdir,"summaryReport.txt")):
            self.change_pipeline_status("Finished")
        else:
            self.change_pipeline_status("Finished with Errors")
        # self.logger.close()
        self.error_logger.close()

    def download_drive(self):
        is_drive = False
        with open(self.conf, "r") as  config_r:
            lines = config_r.readlines()
        for line in lines:
            if line.startswith("input=@drive"):
                is_drive = True
                dparams = line.split(";")
                command = 'curl -H "Authorization: Bearer ' + dparams[3] + '"' + " " + dparams[1] + ' -o "' + dparams[2] + '"'
                os.system(command)
                new_line = "input=" + dparams[2] + "\n"
        if is_drive:
            with open(self.conf, "w") as config_w:
                for line in lines:
                    if line.startswith("input="):
                        config_w.write(new_line)
                    else:
                        config_w.write(line)

    def download_url(self):
        with open(self.conf, "r") as  config_r:
            lines = config_r.readlines()
        for line in lines:
            if line.startswith("input=URL@"):
                url= line.split("@")[1]
                dest = os.path.join(self.outdir, os.path.basename(url))
                ifile, headers = urllib.request.urlretrieve(url, filename=dest)
                new_line ="input="+dest+"\n"
        with open(self.conf, "w") as  config_w:
            for line in lines:
                if line.startswith("input=URL@"):
                    config_w.write(new_line)
                else:
                    config_w.write(line)

    def call_mirg(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: miRNAgFree Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        cmd = "java -Xmx8000m -jar " + self.configuration.path_to_mirg + " " + self.conf
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: miRNAgFree Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")
