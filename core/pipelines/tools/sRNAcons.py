import os
from time import strftime, gmtime

from pipelines.pipelines import Pipeline
#from progress.models import JobStatus
import os
import time
import urllib.request

class sRNAconsPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, config_file=None, parameters=""):
        super(sRNAconsPipeline, self).__init__(pipeline_key, job_name, outdir, "sRNAcons", parameters)

        self.conf = config_file
        self.outdir = outdir

    def run(self):
        self.initialize_pipeline_status()
        self.call_srnacons()
        self.set_finish_time()
        time.sleep(10)
        self.check_errors()

    def call_srnacons(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAcons Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")
        # java - jar / opt / sRNAtoolboxDB / exec / sRNAcons.jar conf.txt
        cmd = "java -Xmx8000m -jar " + self.configuration.path_to_srnabech + " " + self.conf
        cmd = "java -jar /opt/sRNAtoolboxDB/exec/sRNAcons.jar " + self.conf
        self.set_java_command_line(cmd)
        os.system(cmd)
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAcons Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")
    def check_errors(self):
        if os.path.exists(os.path.join(self.outdir, "identicalSequenceRelation.tsv")):
            self.change_pipeline_status("Finished")
        else:
            self.change_pipeline_status("Finished with Errors")
        self.error_logger.close()
