import os
from time import strftime, gmtime, sleep
#from progress.models import JobStatus
from pipelines.pipelines import Pipeline


class helpersPipelines(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, conf_input, mode=None, inputfile=None, species=None,
                 taxon=None, string=None,
                 remove=None):
        super(helpersPipelines, self).__init__(pipeline_key, job_name, outdir, conf_input,parameters="")
        self.conf_input=conf_input
        self.pipeline_id=pipeline_key

    def run(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Helper tool Starts"
        self.actualize_pipeline_progress(log_msg)
        # cmd="sRNAhelper "+ self.conf_input
        cmd = "java -jar " + self.configuration.path_to_helpers + " " + self.conf_input
        os.system(cmd)
        self.change_pipeline_status("Running")
        # self.change_pipeline_status("Finished")
        self.set_java_command_line(cmd)
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Helper tool finished"
        self.actualize_pipeline_progress(log_msg)
        # self.change_pipeline_status("Finished")
        if self.set_out_files():
            self.set_finish_time()
            # sleep(4)
            self.change_pipeline_status("Finished")

    def run1(self):
        self.initialize_pipeline_status()
        if self.mode == "ensembl":
            self.mode_ensmble()
        elif self.mode == "rnacentral":
            self.mode_rnacentral()
        elif self.mode == "ncbi":
            self.mode_ncbi()
        elif self.mode == "rd":
            self.mode_remove_duplicates()
        elif self.mode == "trna":
            self.mode_tRNA()
        elif self.mode == "extract":
            self.mode_extractFasta()
        else:
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()
                               ) + " ERROR: Unknown mode. Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)

        if self.set_out_files():
            self.set_finish_time()
            self.change_pipeline_status("Finished")

        self.error_logger.close()

    def mode_ensmble(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Ensembl Parser Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + self.configuration.path_to_helpers + " " + " ".join(
            ["mode=ENS", "input=" + self.inputfile, "output=" + self.outdir])

        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Ensembl Parser finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_rnacentral(self):

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: RNACentral Parser Starts"
        self.actualize_pipeline_progress(log_msg)
        if self.species:
            self.species = self.species.replace("_", " ")
            cmd = "java -jar " + self.configuration.path_to_helpers + " " + " ".join(
                ["mode=RNAC", "input=" + self.configuration.rnac_file,
                 "output=" + self.outdir,
                 'species="' + self.species + '"'])
            os.system(cmd)
            self.set_java_command_line(cmd)

        elif self.taxon:
            self.taxon = self.taxon.replace("_", " ")
            cmd = "java -jar " + self.configuration.path_to_helpers + " " + " ".join(
                ["mode=RNAC", "input=" + self.configuration.rnac_file,
                 "output=" + self.outdir, "taxonFile=" + self.configuration.taxon_file,
                 'taxon"' + self.taxon + '"'])
            os.system(cmd)
            self.set_java_command_line(cmd)


        else:
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " ERROR: Not species or taxons were provided. " \
                                           "Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: RNACentral Parser finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_tRNA(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: genomic tRNA parse Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + self.configuration.path_to_helpers + " " + " ".join(
            ["mode=TRNA", "input=" + self.configuration.trna_file,
             "output=" + self.outdir, "species=" + self.species])

        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: genomic tRNA parse finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_ncbi(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: NCBI Parser Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + self.configuration.path_to_helpers + " " + " ".join(
            ["mode=NCBI", "input=" + self.inputfile,
             "output=" + self.outdir])
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: NCBI Parser finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_remove_duplicates(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Remove Duplicates from fasta file Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + self.configuration.path_to_helpers + " " + " ".join(["mode=RD", "input=" + self.inputfile,
                                                                                  "output=" + self.outdir,
                                                                                  "replace=" + self.string,
                                                                                  "removeDupSeq=" + self.remove])
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Remove Duplicates from fasta file finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_extractFasta(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Sequences Extraction from fasta file Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + self.configuration.path_to_helpers + " " + " ".join(["mode=FA", "input=" + self.inputfile,
                                                                                  "output=" + self.outdir,
                                                                                  "search=" + self.string])
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S",
                           gmtime()) + " SUCCESS: Sequences Extraction from fasta file Starts finished"
        self.actualize_pipeline_progress(log_msg)

    def set_out_files(self):
        fd = open(os.path.join(self.outdir, "logFile.txt"))
        backvalue = "result"
        for line in fd:
            if "BACKVALUE" in line:
                value = line.replace("\n", "").split(" ")[-1]
                backvalue = (value)

        zip_file = os.path.join(backvalue + ".zip")
        if backvalue != "":
            os.system("cd " + self.outdir + "; zip " + zip_file + " " + os.path.basename(backvalue))
            self.error_logger.write("cd self.outdir; zip " + zip_file + " " + os.path.basename(backvalue))

            # js = JobStatus.objects.get(pipeline_key=self.pipeline_id)
            # js.status.create(status_progress='sent_to_queue')
            # js.zip_file = zip_file

            return True
        else:
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " ERROR:Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)
            return False

