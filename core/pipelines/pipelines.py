from abc import abstractmethod
from abc import ABCMeta
import re
import pygal
import requests
from FileModels.BlastParsers import BlastParser
from pygal.style import LightColorizedStyle
from checkers import *
from FileModels.TargetConsensusParser import TargetConsensusParser


__author__ = 'antonior'
import sys

sys.path.append("/shared/")
from utils.sysUtils import make_dir
from utils.mongoDB import mongoDB
import os
from time import gmtime, strftime
from datetime import datetime
import glob
import configfile

import json

CONF = json.load(file("/shared/sRNAtoolbox/sRNAtoolbox.conf"))

PATH_TO_OUT = CONF["sRNAtoolboxSODataPath"]
PATH_TO_MakeEnrichmentAnalysis = os.path.join(CONF["exec"], "sRNAfuncTerms.jar")
PATH_TO_MakeDE = os.path.join(CONF["exec"], "sRNADE.jar")
PATH_TO_SRNABECH = os.path.join(CONF["exec"], "sRNAbench.jar")
PATH_TO_SRNABLAST = os.path.join(CONF["exec"], "sRNAblast.jar")
PATH_TO_SRNAJBROWSER = os.path.join(CONF["exec"], "sRNAjBrowser.jar")
PATH_TO_SRNAJBROWSERDE = os.path.join(CONF["exec"], "sRNAjBrowserDE.jar")
PATH_TO_MIRNATARGET = os.path.join(CONF["exec"], "miRNAconsTargets.jar")
PATH_TO_SRNAGFREE = os.path.join(CONF["exec"], "miRNAgFree.jar")
PATH_TO_HELPERS = os.path.join(CONF["exec"], "sRNAhelper.jar")
TAXON_FILE = CONF["tax"]
TRNA_FILE = CONF["tRNA"]
RNAC_FILE = CONF["RNAcentral"]
MIRNACONSTARGETS_PLANTS = os.path.join(CONF["exec"], "miRNAconsTargets_plants.py")


class Pipeline:
    __metaclass__ = ABCMeta

    def __init__(self, pipeline_key, job_name, outdir, tool, parameters):
        self.parameters = parameters
        self.tool = tool
        self.outdir = outdir
        make_dir(self.outdir)
        self.table_log = "progress_jobstatus"
        self.error_logger = file(os.path.join(self.outdir, "error_logFile.txt"), "w")
        # self.logger = file(os.path.join(self.outdir, "logFile.txt"), "w")

        # Pipeline key
        self.pipeline_key = pipeline_key

        # Open logDB connection
        self.job_name = job_name
        self.api_server = 'localhost'
        self.api_path = os.path.join(self.api_server, 'jobstatus', 'api')
        self.api_path_key = os.path.join(self.api_path, self.pipeline_key)
        self.api_path_add_status = os.path.join(self.api_path, self.pipeline_key, 'add_status')


    def initialize_pipeline_status(self):

        started_info = (strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Analysis starts")
        payload = {
            "job_status": "Running",
            "command_line": " ".join(sys.argv)
        }
        requests.patch(self.pipeline_key, json=payload)
        self.actualize_pipeline_progress(new_step=started_info)

    def actualize_pipeline_progress(self, new_step):
        payload = {
            "status_progress": new_step
        }
        requests.post(self.api_path_add_status, json=payload)
        if "ERROR" in new_step:
            self.change_pipeline_status("Finished with Errors")

    def change_pipeline_status(self, new_status):
        payload = {
            "job_status": new_status,
        }
        requests.patch(self.pipeline_key, json=payload)

    def set_finish_time(self):
        payload= {
            "finish_time": str(datetime.now())
        }
        requests.patch(self.pipeline_key, json=payload)

    def set_java_command_line(self, line):
        payload = {"java_commad_line": line}
        requests.patch(self.pipeline_key, json=payload)

    def raw_update(self, payload):
        requests.patch(self.pipeline_key, json=payload)


    # def actualize_log(self, log_msg):
    # self.logger.write(log_msg + "\n")

    @abstractmethod
    def run(self):
        pass


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
            fdw = file(self.list_targets_file, "w")
            con = mongoDB("localhost", "Targets")

            fd = file(self.input)
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

            os.system("java -jar " + PATH_TO_MakeEnrichmentAnalysis + " input=" + self.list_targets_file +
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


class sRNAdePipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, input, groups, desc, nt, dt, iso, hmp, hmt, md, parameters=""):
        super(sRNAdePipeline, self).__init__(pipeline_key, job_name, outdir, "sRNAde", parameters)

        self.md = md
        self.dt = dt
        self.iso = iso
        self.hmp = hmp
        self.hmt = hmt
        self.nt = nt
        self.desc = desc
        self.input = input
        self.groups = groups


    def run(self):
        self.initialize_pipeline_status()
        if self.pre_checks():
            self.call_make_de_analysis()
            self.set_out_files()
        if self.post_checks():
            self.set_finish_time()
            self.change_pipeline_status("Finished")
            # self.logger.close()
        self.error_logger.close()

    def pre_checks(self):
        if os.path.isfile(self.input):
            response = valid_mat_file_group(self.input, self.md.split(":"))
            if response is not True:
                self.error_logger.write(response + "\n")
                log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " " + response
                self.actualize_pipeline_progress(log_msg)
                return False
            else:
                return True
        else:
            return True

    def post_checks(self):
        xls_files = glob.glob(os.path.join(self.outdir, "*.xlsx"))
        if len(xls_files) == 0:
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " ERROR: Error found in Differential Expression Results, maybe input data have errors. Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)
            return False
        else:
            return True


    def call_make_de_analysis(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Differential Expression Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        if self.groups is not None:

            if self.desc is not None:

                cmd = "java -jar " + PATH_TO_MakeDE + " input=" + PATH_TO_OUT + " grpString=" + self.input + " iso=" + self.iso + " sampleDesc=" + self.desc + " hmTop=" + self.hmt + " hmPerc=" + self.hmp + " fdr=" + self.dt + " noiseq=" + self.nt + " grpDesc=" + self.groups + " output=" + self.outdir + " minRCexpr=5 rscripts=/shared/sRNAtoolbox/rscripts"
            else:
                cmd = "java -jar " + PATH_TO_MakeDE + " input=/shared/sRNAtoolbox/webData" + " grpString=" + self.input + " iso=" + self.iso + " hmTop=" + self.hmt + " hmPerc=" + self.hmp + " fdr=" + self.dt + " noiseq=" + self.nt + " grpDesc=" + self.groups + " output=" + self.outdir + " minRCexpr=5 rscripts=/shared/sRNAtoolbox/rscripts"
        else:
            cmd = "java -jar " + PATH_TO_MakeDE + " input=" + self.input + " iso=" + self.iso + " hmTop=" + self.hmt + " hmPerc=" + self.hmp + " fdr=" + self.dt + " noiseq=" + self.nt + " matrixDesc=" + self.md.replace(":", ",") + " output=" + self.outdir + " minRCexpr=5 rscripts=/shared/sRNAtoolbox/rscripts"

        self.set_java_command_line(cmd)
        os.system(cmd)


        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Differential Expression Analysis finished"
        self.actualize_pipeline_progress(log_msg)

    def set_out_files(self):
        xls_files = glob.glob(os.path.join(self.outdir, "*.xlsx"))
        heatmap = glob.glob(os.path.join(self.outdir, "*heatmap*.png"))
        zip_file = os.path.join(self.outdir, "sRNAde_full_Result.zip")
        stats_file = os.path.join(self.outdir, "sequencingStat.txt")
        if not os.path.exists(stats_file):
            stats_file = ""

        os.system("cd " + self.outdir + "; zip -r " + zip_file + " " + " *")
        update = {"heatmaps": heatmap, "xls_files": xls_files, "zip_file": zip_file, "stats_file": stats_file}
        self.raw_update(payload=update)


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

        cmd = "java -Xmx8000m -jar " + PATH_TO_SRNABECH + " " + self.conf
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAbench Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")



class sRNAblastPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, config_file=None, parameters=""):
        super(sRNAblastPipeline, self).__init__(pipeline_key, job_name, outdir, "sRNAblast", parameters)

        self.conf = config_file

    def run(self):
        self.initialize_pipeline_status()
        self.call_srnablast()
        self.create_graphics()
        self.set_out_files()
        if self.post_checks():
            self.set_finish_time()
            self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def call_srnablast(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAblast Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")


        cmd = "java -Xmx8000m -jar " + PATH_TO_SRNABLAST + " " + self.conf
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAblast Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

    def create_graphics(self):
        tax_file = os.path.join(self.outdir, "tax.out")
        species_file = os.path.join(self.outdir, "species.out")
        if os.path.isfile(tax_file):
            parser = BlastParser(tax_file, "tax")
            tax = [obj for obj in parser.parse()]
            self.create_pie([(tx.Taxonomy, tx.Percentage_Read_Count) for tx in tax], "Taxonomy Percentage Read Count",
                            os.path.join(self.outdir, "tax"))

        if os.path.isfile(tax_file):
            parser = BlastParser(species_file, "species")
            sp = [obj for obj in parser.parse()]
            self.create_pie([(s.specie, s.Percentage_Read_Count) for s in sp], "Species Percentage Read Count",
                            os.path.join(self.outdir, "species"))


    def create_pie(self, datas, tittle, outfile):
        pie_chart = pygal.Pie(style=LightColorizedStyle)
        pie_chart.title = tittle
        for data in datas:
            pie_chart.add(data[0], float(data[1]))
        pie_chart.render_to_file(outfile + ".svg")


    def post_checks(self):
        blast_file = os.path.join(self.outdir, "blast.out")
        if not os.path.exists(blast_file):
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " ERROR: Error found in Blast Results, maybe input data have errors. Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)
            return False
        else:
            return True


    def set_out_files(self):

        query = {"pipeline_key": self.pipeline_key}

        blast_file = os.path.join(self.outdir, "blast.out")
        species_file = os.path.join(self.outdir, "species.out")
        tax_file = os.path.join(self.outdir, "tax.out")
        tax_svg = os.path.join(self.outdir, "tax.svg")
        species_svg = os.path.join(self.outdir, "species.svg")
        allfiles = glob.glob(os.path.join(self.outdir, "*"))

        if not os.path.exists(blast_file):
            blast_file = ""
        else:
            parser = BlastParser(blast_file, "blast", 10)
            blast_file = os.path.join(self.outdir, "blast.sorted_by_rc.out")
            parser.sort_blast_by_rc(blast_file)

        if not os.path.exists(species_file):
            species_file = ""
        if not os.path.exists(tax_file):
            tax_file = ""

        if not os.path.exists(tax_svg):
            tax_svg = ""

        zip_file = os.path.join(self.outdir, "sRNAblast_full_Result.zip")
        os.system("cd " + self.outdir + "; zip -r " + zip_file + " " + " *")
        update = {"blast_file": blast_file, "species_file": species_file, "zip_file": zip_file, "tax_file": tax_file,
                     "tax_svg": tax_svg, "species_svg": species_svg}

        self.raw_update(update)


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
            cmd = "cd " + self.outdir + "; python3 " + MIRNACONSTARGETS_PLANTS + " " + " ".join(
                [self.mirna_file, self.utr_file, self.outdir, self.threads, self.program_string, self.parameter_string])
            os.system(cmd)
            self.set_java_command_line(cmd)

        else:
            self.parameter_string = ":".join(['" '+ param + ' "' for param in self.parameter_string.split(":")])


            cmd = "cd " + self.outdir + ";  java -jar " + PATH_TO_MIRNATARGET + " " + " ".join(
                [self.mirna_file, self.utr_file, self.outdir, self.threads, self.program_string, self.parameter_string])
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

        if "PSROBOT" in self.program_string or "TAPIR_FASTA" in self.program_string or "TAPIR_HYBRID" in self.program_string:
            cmd = "cd " + self.outdir + "; python3 " + MIRNACONSTARGETS_PLANTS + " " + " ".join(
                [self.mirna_file, self.utr_file, self.outdir, self.threads, self.program_string, self.parameter_string])
            os.system(cmd)
            self.set_java_command_line(cmd)
        else:
            self.parameter_string = ":".join(['" '+param + ' "' for param in self.parameter_string.split(":")])

            cmd = "cd " + self.outdir + ";  java -jar " + PATH_TO_MIRNATARGET + " " + " ".join(
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
            if len(file(consensus_file).readlines()) < 1:
                log_msg = strftime("%Y-%m-%d %H:%M:%S",
                                   gmtime()) + " ERROR: Error found in consensus targets, maybe any targets was found. Please report it indicating the jobID: " + self.pipeline_key
                self.actualize_pipeline_progress(log_msg)
                return False
            else:
                self.extract_uniprots(consensus_file, self.list_targets_file)
                return True

    def extract_uniprots(self, consensus_file, outfile):
        fdw = file(outfile, "w")
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

        os.system("java -jar " + PATH_TO_MakeEnrichmentAnalysis + " input=" + self.list_targets_file +
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

        cmd = "java -jar " + PATH_TO_SRNAJBROWSER + " /shared/sRNAtoolbox/sRNAtoolbox.conf " + self.sid + " " + self.pipeline_key
        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAjBrowser Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

    def set_out_files(self):
        query = {"pipeline_key": self.pipeline_key}
        bed_file = glob.glob(os.path.join(PATH_TO_OUT, self.sid, "*jBrowser.bed"))

        # self.logger.write(os.path.join(PATH_TO_OUT, self.sid, "*jBrowser.bed") + "\n")
        update = {"bed_files": bed_file}
        self.raw_update(update)


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

        cmd = "java -jar " + PATH_TO_SRNAGFREE + " " + " ".join(["input=" + self.input, "output=" + self.outdir,
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
            cmd = "java -jar " + PATH_TO_SRNAJBROWSERDE + " /shared/sRNAtoolbox/sRNAtoolbox.conf " + self.pipeline_key \
                  + " " + self.sid + " " + self.groups + " " + self.length
        else:
            cmd = "java -jar " + PATH_TO_SRNAJBROWSERDE + " /shared/sRNAtoolbox/sRNAtoolbox.conf " \
                  + self.pipeline_key + " " + self.sid + " " + self.groups

        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAjBrowserDE Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

    def set_out_files(self):
        query = {"pipeline_key": self.pipeline_key}
        bed_file = glob.glob(os.path.join(self.outdir, "*jBrowser.bed"))
        print bed_file

        # self.logger.write(os.path.join(PATH_TO_OUT, self.sid, "*jBrowser.bed") + "\n")
        update = {"bed_files": bed_file}
        self.raw_update(update)


class helpersPipelines(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, parameters="", mode=None, inputfile=None, species=None, taxon=None, string=None,
                 remove=None):
        super(helpersPipelines, self).__init__(pipeline_key, job_name, outdir, "helper" + "_" + mode, parameters)
        self.remove = remove
        self.string = string
        self.taxon = taxon
        self.species = species
        self.inputfile = inputfile
        self.mode = mode


    def run(self):
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
                               gmtime()) + " ERROR: Unknown mode. Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)

        if self.set_out_files():
            self.set_finish_time()
            self.change_pipeline_status("Finished")

        self.error_logger.close()


    def mode_ensmble(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Ensembl Parser Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + PATH_TO_HELPERS + " " + " ".join(["mode=ENS", "input=" + self.inputfile,
                                                               "output=" + self.outdir])

        os.system(cmd)
        self.set_java_command_line(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Ensembl Parser finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_rnacentral(self):

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: RNACentral Parser Starts"
        self.actualize_pipeline_progress(log_msg)
        if self.species:
            self.species = self.species.replace("_", " ")
            cmd = "java -jar " + PATH_TO_HELPERS + " " + " ".join(["mode=RNAC", "input=" + RNAC_FILE,
                                                                   "output=" + self.outdir,
                                                                   'species="' + self.species + '"'])
            os.system(cmd)
            self.set_java_command_line(cmd)

        elif self.taxon:
            self.taxon = self.taxon.replace("_", " ")
            cmd = "java -jar " + PATH_TO_HELPERS + " " + " ".join(["mode=RNAC", "input=" + RNAC_FILE,
                                                                   "output=" + self.outdir, "taxonFile=" + TAXON_FILE,
                                                                   'taxon"' + self.taxon + '"'])
            os.system(cmd)
            self.set_java_command_line(cmd)


        else:
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " ERROR: Not species or taxons were provided. Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)


        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: RNACentral Parser finished"
        self.actualize_pipeline_progress(log_msg)


    def mode_tRNA(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: genomic tRNA parse Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + PATH_TO_HELPERS + " " + " ".join(["mode=TRNA", "input=" + TRNA_FILE,
                                                               "output=" + self.outdir, "species=" + self.species])

        os.system(cmd)
        self.set_java_command_line(cmd)



        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: genomic tRNA parse finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_ncbi(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: NCBI Parser Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + PATH_TO_HELPERS + " " + " ".join(["mode=NCBI", "input=" + self.inputfile,
                                                               "output=" + self.outdir])
        os.system(cmd)
        self.set_java_command_line(cmd)


        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: NCBI Parser finished"
        self.actualize_pipeline_progress(log_msg)

    def mode_remove_duplicates(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Remove Duplicates from fasta file Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + PATH_TO_HELPERS + " " + " ".join(["mode=RD", "input=" + self.inputfile,
                                                               "output=" + self.outdir, "replace=" + self.string,
                                                               "removeDupSeq=" + self.remove])
        os.system(cmd)
        self.set_java_command_line(cmd)


        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Remove Duplicates from fasta file finished"
        self.actualize_pipeline_progress(log_msg)


    def mode_extractFasta(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Sequences Extraction from fasta file Starts"
        self.actualize_pipeline_progress(log_msg)
        cmd = "java -jar " + PATH_TO_HELPERS + " " + " ".join(["mode=FA", "input=" + self.inputfile,
                                                              "output=" + self.outdir, "search=" + self.string])
        os.system(cmd)
        self.set_java_command_line(cmd)


        log_msg = strftime("%Y-%m-%d %H:%M:%S",
                           gmtime()) + " SUCCESS: Sequences Extraction from fasta file Starts finished"
        self.actualize_pipeline_progress(log_msg)


    def set_out_files(self):
        fd = file(os.path.join(self.outdir, "logFile.txt"))
        backvalue = "result"
        for line in fd:
            if "BACKVALUE" in line:
                value = line.replace("\n", "").split(" ")[-1]
                backvalue = (value)

        zip_file = os.path.join(backvalue + ".zip")
        if backvalue != "":
            os.system("cd " + self.outdir + "; zip " + zip_file + " " + os.path.basename(backvalue))
            self.error_logger.write("cd self.outdir; zip " + zip_file + " " + os.path.basename(backvalue))

            update = {"zip_file": zip_file}
            self.raw_update(update)
            return True
        else:
            log_msg = strftime("%Y-%m-%d %H:%M:%S",
                               gmtime()) + " ERROR:Please report it indicating the jobID: " + self.pipeline_key
            self.actualize_pipeline_progress(log_msg)
            return False

