import glob
import os
from time import strftime, gmtime

from core_utils.mongoDB import mongoDB
from core_utils.sysUtils import make_dir
from pipelines import configfile
from pipelines.pipelines import Pipeline


class sRNAfuncTermsPipeline(Pipeline):
    def __init__(self, annotation_list, pipeline_key, job_name, outdir, inputf, specie, type="list", exp="false", parameters=""):
        super(sRNAfuncTermsPipeline, self).__init__(pipeline_key, job_name, outdir, "sRNAfuncTerms", parameters)

        self.exp = exp
        self.number_of_mirs = 0
        self.specie = configfile.GO[specie]
        self.annotation_list = annotation_list
        self.input = inputf
        self.type = type
        self.outdir_enrichment = os.path.join(self.outdir, "outdirEnrichment")
        make_dir(self.outdir_enrichment)
        self.list_targets_file = os.path.join(self.outdir, "targets_list.txt")

    def run(self):

        """
        Task: Run Pipeline
        """
        self.initialize_pipeline_status()

        # run target finding
        log_msg = self.generate_targets_from_list()
        self.actualize_pipeline_progress(log_msg)
        if self.mid_checks():
            # run Enrichement Analysis
            if self.type == "list":
                self.call_make_enrichment_analysis("user_list")
            elif self.type == "top":
                self.call_make_enrichment_analysis("top_mirna")
            elif self.type == "de":
                self.call_make_enrichment_analysis("de_mirna")

            self.set_finish_time()
            self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def generate_targets_from_list(self):
        """
        Task: Get a targets for miRNAs in list
        :return: success or fail message
        :rtype: str
        """
        log_msg = (strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Finding targets process starts")
        # self.logger.write(log_msg + "\n")
        self.actualize_pipeline_progress(log_msg)
        try:
            fdw = open(self.list_targets_file, "w")
            con = mongoDB("localhost", "Targets")

            fd = open(self.input)
            i = 0
            targets = set()

            for i, line in enumerate(fd):
                mirna = line.replace(" ", "").replace("\n", "").replace("\r", "").split("\t")[0]

                query = {"miRNAname": mirna}
                results = con.find("Experimental", query)
                if results is not None:
                    for result in results:
                        target = result["targets"][0]["uniprot"]
                        targets.add(target)

                if self.exp == "false":
                    query = {"miRNAname": mirna, "number": {"$gt": 1}}
                    results = con.find("Predicted", query)
                    if results is not None:
                        for result in results:
                            target = result["transcripts"]
                            targets.add(target)


                for target in targets:
                    pair = (mirna, target)
                    fdw.write("\t".join(pair) + "\n")
                    self.number_of_mirs += 1

            fdw.close()

            log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: " + str(
                self.number_of_mirs) + " targets founds for " + str(i + 1) + " miRNAs"
            # self.logger.write(log_msg + "\n")
            return log_msg

        except IOError:

            log_msg = "IOError: file " + self.input + " not found"
            self.error_logger.write(log_msg + "\n")
            self.change_pipeline_status("Error")
            return log_msg

    def mid_checks(self):
        if self.number_of_mirs == 0:
            log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " ERROR: " + str(
                self.number_of_mirs) + "targets are not enough to perform Enrichement Analysis"
            self.actualize_pipeline_progress(log_msg)
            return False
        else:
            return True


    def call_make_enrichment_analysis(self, base):
        """
        Task: Call java to perform enrichment analysis
        :param base: basename
        """
        for annotation in self.annotation_list:

            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " INFO: Enrichement Analysis starts(" + annotation + " terms)"
            self.actualize_pipeline_progress(log_msg)
            # self.logger.write(log_msg + "\n")

            if annotation == "go":
                table = self.specie
            else:
                table = self.specie

            os.system("java -jar " + self.configuration.path_to_makeenrichmentanalysis + " input=" + self.list_targets_file +
                      " table=" + table + " output=" + self.outdir_enrichment + " name=" + base)

            all_files = glob.glob(os.path.join(self.outdir_enrichment, "*all.eda"))
            module_files = glob.glob(os.path.join(self.outdir_enrichment, "*modules.eda"))

            self.set_out_files(all_files, module_files)

            log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Enrichement Analysis finished"
            self.actualize_pipeline_progress(log_msg)
            # self.logger.write(log_msg + "\n")

    def set_out_files(self, all_files, modules_files):
        """
        :param all_files: files *_all stored
        :param modules_files: files *_modules stored
        """

        zip_file = os.path.join(self.outdir, "sRNAfuncTerms_full_Result.zip")
        os.system("cd " + self.outdir + "; zip -r " + zip_file + " " + " *")

        update = {"all_files": all_files, "modules_files": modules_files, "zip_file": zip_file}
        self.raw_update(update)