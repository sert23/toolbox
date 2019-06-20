import glob
import os
from time import strftime, gmtime

import pygal
from pygal.style import LightColorizedStyle

from pipelines.pipelines import Pipeline
from FileModels.BlastParsers import BlastParser


class sRNAblastPipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir, config_file=None, parameters = ""):
        super(sRNAblastPipeline, self).__init__(pipeline_key, job_name, outdir, "sRNAblast", parameters)
        self.conf = config_file
        self.outdir=outdir
        self.job_name=job_name

    def run(self):
        self.initialize_pipeline_status()
        self.change_pipeline_status("Running")
        self.call_srnablast()
        self.create_graphics()
        self.change_pipeline_status("Finished")
        self.set_out_files()
        if self.post_checks():
            self.set_finish_time()
            self.change_pipeline_status("Finished")
        self.change_pipeline_status("Finished")
        # self.logger.close()
        self.error_logger.close()

    def call_srnablast(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: sRNAblast Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        cmd = "java -Xmx8000m -jar " + self.configuration.path_to_srnablast + " " + self.conf
        print(cmd)
        self.change_pipeline_status("Running")
        os.system(cmd)
        self.set_java_command_line(cmd)


        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: sRNAblast Analysis finished"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

    def create_graphics(self):
        tax_file = os.path.join(self.outdir, "tax.out")
        species_file = os.path.join(self.outdir, "speciesSA.out")
        if os.path.isfile(tax_file):
            parser = BlastParser(tax_file, "tax",20000)
            tax = [obj for obj in parser.parse()]
            self.create_pie([(tx.Taxonomy, tx.Percentage_Read_Count) for tx in tax], "Taxonomy Percentage Read Count",
                            os.path.join(self.outdir, "tax"))

        if os.path.isfile(tax_file):
            parser = BlastParser(species_file, "species",20000)
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
        species_file = os.path.join(self.outdir, "speciesSA.out")
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
        # update = {"blast_file": blast_file, "species_file": species_file, "zip_file": zip_file, "tax_file": tax_file,
        #              "tax_svg": tax_svg, "species_svg": species_svg}

        #self.raw_update(update)