import glob
import os
from time import strftime, gmtime

from core_utils.mongoDB import mongoDB
from core_utils.sysUtils import make_dir
from pipelines import configfile
from pipelines.pipelines import Pipeline


class mirconsfunctargetPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, mirna_file, utr_file, threads, program_string, parameter_string,
                 go_species, parameters=""):
        super(mirconsfunctargetPipeline, self).__init__(pipeline_key, job_name, outdir, "mirnafunctargets", parameters)

        self.species = configfile.GO[go_species]
        self.parameter_string = parameter_string
        self.program_string = program_string
        self.threads = threads
        self.utr_file = utr_file
        self.mirna_file = mirna_file
        self.list_targets_file = ""
        self.outdir_enrichment = os.path.join(self.outdir, "outdirEnrichment")
        make_dir(self.outdir_enrichment)


    def run(self):
        self.initialize_pipeline_status()
        self.call_mirconstarget()
        if self.mid_check():
            self.call_make_enrichment_analysis("List")
            self.set_out_files()
            self.set_finish_time()
            self.change_pipeline_status("Finished")
        self.error_logger.close()

    def call_mirconstarget(self):

        if not os.path.isfile(self.utr_file):
            self.utr_file = configfile.UTR_FILES[self.utr_file]

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: miRNAconstarget Analysis Starts"
        self.actualize_pipeline_progress(log_msg)

        if 'psRobot' in self.program_string or 'tapir_fasta' in self.program_string or 'tapir_RNA' in self.program_string:
            cmd = "cd " + self.outdir + "; python3 " + self.configuration.mirnaconstargets_plants + " " + " ".join(
                [self.mirna_file, self.utr_file, self.outdir, self.threads, self.program_string, self.parameter_string])
            os.system(cmd)
            self.set_java_command_line(cmd)
        else:
            self.parameter_string = ":".join(['" '+param + ' "' for param in self.parameter_string.split(":")])

            cmd = "cd " + self.outdir + ";  java -jar " + self.configuration.path_to_mirnatarget + " " + " ".join(
                [self.mirna_file, self.utr_file, self.outdir, self.threads, self.program_string, self.parameter_string])
            os.system(cmd)
            self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: miRNAconstarget Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.actualize_log(log_msg)

    def mid_check(self):
        consensus_file = os.path.join(self.outdir, "consensus.txt")
        self.list_targets_file = os.path.join(self.outdir, "consensus_targets.txt")
        if os.path.isfile(consensus_file):
            if len(open(consensus_file).readlines()) < 1:
                log_msg = strftime("%Y-%m-%d %H:%M:%S",
                                   gmtime()) + " ERROR: Error found in consensus targets, maybe any targets was found. Please report it indicating the jobID: " + self.pipeline_key
                self.actualize_pipeline_progress(log_msg)
                return False
            else:
                self.extract_uniprots(consensus_file, self.list_targets_file)
                return True

    def extract_uniprots(self, consensus_file, outfile):
        fdw = open(outfile, "w")
        parser = TargetConsensusParser(consensus_file)
        conDB_mapping = mongoDB("localhost", "Uniprots")
        targets = [target for target in parser.get_by_n(len(self.program_string.split(":")) - 1)]
        added = []
        for target in targets:
            gene = target.mRNA
            miRNA = target.microRNA
            query = {"_id": gene}
            results = conDB_mapping.findOne("Uniprot_mapping", query)
            if results is not None:
                uniprot = results["uniprot"]
                towrite = miRNA + "\t" + uniprot + "\n"
                if towrite not in added:
                    fdw.write(towrite)
                    added.append(towrite)
            else:
                if gene.count("_") == 2:
                    gene.replace("_", ".").replace(".", "_", 1)
                    query = {"_id": "/^"+gene+"/"}
                    results = conDB_mapping.findOne("Uniprot_mapping", query)
                    if results is not None:
                        uniprot = results["uniprot"]
                        towrite = miRNA + "\t" + uniprot + "\n"
                        if towrite not in added:
                            fdw.write(towrite)
                            added.append(towrite)
        fdw.close()


    def call_make_enrichment_analysis(self, base):
        """
        Task: Call java to perform enrichment analysis
        :param base: basename
        """
        table = self.species

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Enrichement Analysis starts(" + "go" + " terms)"
        self.actualize_pipeline_progress(log_msg)

        os.system("java -jar " + self.configuration.path_to_makeenrichmentanalysis + " input=" + self.list_targets_file +
                  " table=" + table + " output=" + self.outdir_enrichment + " name=" + base)

        all_files = glob.glob(os.path.join(self.outdir_enrichment, "*all.eda"))
        module_files = glob.glob(os.path.join(self.outdir_enrichment, "*modules.eda"))

        self.set_out_files_enrichment(all_files, module_files)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Enrichement Analysis finished"
        self.actualize_pipeline_progress(log_msg)

    def set_out_files_enrichment(self, all_files, modules_files):
        """
        :param all_files: files *_all stored
        :param modules_files: files *_modules stored
        """
        update = {"all_files": all_files, "modules_files": modules_files}
        self.raw_update(update)


    def set_out_files(self):
        query = {"pipeline_key": self.pipeline_key}
        consensus_file = os.path.join(self.outdir, "consensus.txt")


        if not os.path.isfile(consensus_file):
            consensus_file = ""

        zip_file = os.path.join(self.outdir, "miRNAconsTarget_full_Result.zip")
        os.system("cd " + self.outdir + "; zip -r " + zip_file + " " + " *")

        update = {"consensus_file": consensus_file, "zip_file": zip_file}
        self.raw_update(update)