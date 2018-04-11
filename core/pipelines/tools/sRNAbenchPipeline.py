import os
from time import strftime, gmtime

from pipelines.pipelines import Pipeline


class sRNAbenchPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, config_file=None, parameters=""):
        super(sRNAbenchPipeline, self).__init__(pipeline_key, job_name, outdir, "sRNAbench", parameters)

        self.conf = config_file

    def run(self):
        self.initialize_pipeline_status()
        self.call_srnabench()
        self.set_finish_time()
        self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def call_srnabench(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAbench Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        cmd = "java -Xmx8000m -jar " + self.configuration.path_to_srnabech + " " + self.conf
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAbench Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")
