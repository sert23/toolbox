import os
from time import strftime, gmtime

from pipelines.pipelines import Pipeline
#from progress.models import JobStatus
import os
import time
import urllib.request

class sRNAbenchPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, config_file=None, parameters=""):
        super(sRNAbenchPipeline, self).__init__(pipeline_key, job_name, outdir, "sRNAbench", parameters)

        self.conf = config_file
        self.outdir = outdir

    def run(self):
        self.initialize_pipeline_status()
        self.download_url()
        self.call_srnabench()
        self.set_finish_time()
        time.sleep(10)
        if os.path.exists(os.path.join(self.outdir,"results.txt")):
            self.change_pipeline_status("Finished")
        else:
            self.change_pipeline_status("Finished with Errors")
        # self.logger.close()
        self.error_logger.close()

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

    def call_srnabench(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAbench Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        cmd = "java -Xmx30000m -jar " + self.configuration.path_to_srnabech + " " + self.conf
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAbench Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")
