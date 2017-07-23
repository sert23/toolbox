import glob
import os
from time import strftime, gmtime

from pipelines.pipelines import Pipeline


class sRNAjBrowserPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, sid=None, parameters=""):
        super(sRNAjBrowserPipeline, self).__init__(pipeline_key, job_name, outdir, "jBrowser", parameters)

        self.sid = sid


    def run(self):
        self.initialize_pipeline_status()
        self.call_srnajbrowser()
        self.set_out_files()
        self.set_finish_time()
        self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def call_srnajbrowser(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAjBrowser Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        cmd = "java -jar " + self.configuration.path_to_srnajbrowser + " /shared/sRNAtoolbox/sRNAtoolbox.conf " + self.sid + " " + self.pipeline_key
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAjBrowser Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

    def set_out_files(self):
        query = {"pipeline_key": self.pipeline_key}
        bed_file = glob.glob(os.path.join(self.configuration.path_to_out, self.sid, "*jBrowser.bed"))

        # self.logger.write(os.path.join(PATH_TO_OUT, self.sid, "*jBrowser.bed") + "\n")
        update = {"bed_files": bed_file}
        self.raw_update(update)


class sRNAdejBrowserPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, sid=None, groups=None, length=None, parameters=""):
        super(sRNAdejBrowserPipeline, self).__init__(pipeline_key, job_name, outdir, "dejbrowser", parameters)

        self.length = length
        self.groups = groups
        self.sid = sid


    def run(self):
        self.initialize_pipeline_status()
        self.call_srnajbrowser()
        self.set_out_files()
        self.set_finish_time()
        self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def call_srnajbrowser(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAjBrowserDE Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        if self.length is not None:
            cmd = "java -jar " + self.configuration.path_to_srnajbrowserde + " /shared/sRNAtoolbox/sRNAtoolbox.conf " + self.pipeline_key \
                  + " " + self.sid + " " + self.groups + " " + self.length
        else:
            cmd = "java -jar " + self.configuration.path_to_srnajbrowserde + " /shared/sRNAtoolbox/sRNAtoolbox.conf " \
                  + self.pipeline_key + " " + self.sid + " " + self.groups

        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAjBrowserDE Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

    def set_out_files(self):
        query = {"pipeline_key": self.pipeline_key}
        bed_file = glob.glob(os.path.join(self.outdir, "*jBrowser.bed"))
        print (bed_file)

        # self.logger.write(os.path.join(PATH_TO_OUT, self.sid, "*jBrowser.bed") + "\n")
        update = {"bed_files": bed_file}
        self.raw_update(update)