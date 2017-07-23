import glob
import os
from time import strftime, gmtime

from pipelines.pipelines import Pipeline


class sRNAgFreePipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, input, minReadLength, maxReadLength, microRNA, minRC,
                 novelStrict, noMM, parameters=""):
        super(sRNAgFreePipeline, self).__init__(pipeline_key, job_name, outdir, "gFree", parameters)

        self.minRC = minRC
        self.microRNA = microRNA
        self.maxReadLength = maxReadLength
        self.minReadLength = minReadLength
        self.novelStrict = novelStrict
        self.input = input
        self.noMM = noMM


    def run(self):
        self.initialize_pipeline_status()
        self.call_sRNAgFree()
        if self.set_out_files():
            self.set_finish_time()
            self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def call_sRNAgFree(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAgFree Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        cmd = "java -jar " + self.configuration.path_to_srnagfree + " " + " ".join(["input=" + self.input, "output=" + self.outdir,
                                                                 "minReadLength=" + self.minReadLength,
                                                                 "maxReadLength=" + self.maxReadLength,
                                                                 "microRNA=" + self.microRNA, "minRC=" + self.minRC,
                                                                 "dbPath=/shared/sRNAbenchDB/",
                                                                 "novelStrict=" + self.novelStrict, "noMM=" + self.noMM]
        )
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAgFree Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

    def set_out_files(self):
        info_file = os.path.join(self.outdir, "info.txt")
        micro_file = os.path.join(self.outdir, "microRNAs.txt")
        allfiles = glob.glob(os.path.join(self.outdir, "*"))

        if not os.path.isfile(info_file) or not os.path.isfile(micro_file):
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " ERROR:Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)
            return False

        else:
            zip_file = os.path.join(self.outdir, "sRNAblast_full_Result.zip")
            os.system("cd " + self.outdir + "; zip -r " + zip_file + " " + " *")

            update = {"info_file": info_file, "micro_file": micro_file, "zip_file": zip_file, "all_files": allfiles}
            self.raw_update(update)
            return True