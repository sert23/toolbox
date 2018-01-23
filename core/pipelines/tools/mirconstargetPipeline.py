import os
from time import strftime, gmtime

from pipelines.pipelines import Pipeline


class mirconstargetPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, mirna_file, utr_file, threads, program_string, parameter_string, parameters=""):
        super(mirconstargetPipeline, self).__init__(pipeline_key, job_name, outdir, "mirconstarget", parameters)

        self.parameter_string = parameter_string
        self.program_string = program_string
        self.threads = threads
        self.utr_file = utr_file
        self.mirna_file = mirna_file



    def run(self):
        self.initialize_pipeline_status()
        self.call_mirconstarget()
        self.set_out_files()
        self.set_finish_time()
        self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def call_mirconstarget(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: miRNAconstarget Analysis Starts"
        self.actualize_pipeline_progress(log_msg)

        if "PSROBOT" in self.program_string or "TAPIR_FASTA" in self.program_string or "TAPIR_HYBRID" in self.program_string:
            cmd = "cd " + self.outdir + "; python3 " + self.configuration.mirnaconstargets_plants + " " + " ".join(
                [self.mirna_file, self.utr_file, self.outdir, self.threads, self.program_string, self.parameter_string])
            os.system(cmd)
            self.set_java_command_line(cmd)

        else:
            #self.parameter_string = ":".join(['" '+ param + ' "' for param in self.parameter_string.split(":")])

            cmd = "cd " + self.outdir + ";  java -jar " + self.configuration.path_to_mirnatarget + " " + " ".join(
                [self.mirna_file, self.utr_file, self.outdir, self.threads, self.program_string, self.parameter_string])

            print(cmd)
            os.system(cmd)

            self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: miRNAconstarget Analysis finished"
        self.actualize_pipeline_progress(log_msg)


    def set_out_files(self):
        consensus_file = os.path.join(self.outdir, "consensus.txt")
        if not os.path.isfile(consensus_file):
            consensus_file = ""
        zip_file = os.path.join(self.outdir, "miRNAconsTarget_full_Result.zip")
        os.system("cd " + self.outdir + "; zip -r " + zip_file + " " + " *")

        update = {"consensus_file": consensus_file, "zip_file": zip_file}
        self.raw_update(update)