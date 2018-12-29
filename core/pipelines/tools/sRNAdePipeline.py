import glob
import os
from time import strftime, gmtime
import re
from pipelines.pipelines import Pipeline
#from django.conf import settings


class sRNAdePipeline(Pipeline):
    def __init__(self, pipeline_key, job_name, outdir,  input, groups, desc, nt, dt, iso, hmp, hmt, md, config_file=None, parameters="", media="/opt/sRNAtoolbox_prod/sRNAtoolboxweb/upload/"):
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
        self.outdir = outdir
        self.media = media
        self.media = media
        self.conf = config_file



    def run(self):
        self.initialize_pipeline_status()
        # if self.pre_checks():
        self.call_make_de_analysis()
        self.set_out_files()
    # if self.post_checks():
        self.set_finish_time()
        if os.path.exists(os.path.join(self.outdir, "results.txt")):
            self.change_pipeline_status("Finished")
        else:
            self.change_pipeline_status("Finished with Errors")
            # self.logger.close()
        self.error_logger.close()

    @staticmethod
    def valid_mat_file_group(mat, groups):
        fd = open(mat)
        if len(fd.readline().split("\t")) - 1 == len(groups.split(',')):
            return True
        else:
            return "ERROR: Number of columns in matrix file and number of group description given are different. Please provided one group name per sample in matrix file"

    def pre_checks(self):
        if os.path.isfile(self.input):
            response = self.valid_mat_file_group(self.input, self.md)
            if response is not True:
                self.error_logger.write(response + "\n")
                log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " " + response
                self.actualize_pipeline_progress(log_msg)
                return False
            else:
                return True
        else:
            return True

    # def post_checks(self):
    #     xls_files = glob.glob(os.path.join(self.outdir, "*.xlsx"))
    #     if len(xls_files) == 0:
    #         log_msg = strftime("%Y-%m-%d %H:%M:%S",
    #                            gmtime()) + " ERROR: Error found in Differential Expression Results, maybe input data have errors. Please report it indicating the jobID: " + self.pipeline_key
    #         self.actualize_pipeline_progress(log_msg)
    #         return False
    #     else:
    #         return True


    def call_make_de_analysis(self):
        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Differential Expression Analysis Starts"
        self.actualize_pipeline_progress(log_msg)
        # self.logger.write(log_msg + "\n")

        cmd = "java -Xmx8000m -jar " + self.configuration.path_to_makede + " " + self.conf
        self.set_java_command_line(cmd)
        os.system(cmd)


        # if self.groups is not None:
        #
        #     if self.desc is not "":
        #
        #         cmd = "java -jar " + self.configuration.path_to_makede + " input=" + self.input + " grpString=" + self.groups + " iso=" + self.iso + " matrixDesc=" + self.desc + " hmTop=" + self.hmt + " hmPerc=" + self.hmp + " fdr=" + self.dt + " noiseq=" + self.nt + " grpDesc=" + self.groups + " output=" + self.outdir + "  "# rscripts=/shared/sRNAtoolbox/rscripts"
        #     else:
        #         cmd = "java -jar " + self.configuration.path_to_makede + " input=" + self.configuration.media + " grpString=" + self.input + " iso=" + self.iso + " hmTop=" + self.hmt + " hmPerc=" + self.hmp + " fdr=" + self.dt + " noiseq=" + self.nt + " grpDesc=" + self.groups + " output=" + self.outdir + "   diffExpr=true"#rscripts=/shared/sRNAtoolbox/rscripts"
        # else:
        #     cmd = "java -jar " + self.configuration.path_to_makede + " input=" + self.input + " iso=" + self.iso + " hmTop=" + self.hmt + " hmPerc=" + self.hmp + " fdr=" + self.dt + " noiseq=" + self.nt + " matrixDesc=" + self.md.replace(":", ",") + " output=" + self.outdir + "   "#rscripts=/shared/sRNAtoolbox/rscripts"
        #
        # self.set_java_command_line(cmd)
        # print(cmd)
        # os.system(cmd)

        log_msg = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " SUCCESS: Differential Expression Analysis finished"
        self.actualize_pipeline_progress(log_msg)

    def set_out_files(self):
        xls_files = ','.join(glob.glob(os.path.join(self.outdir, "*.xlsx")))
        heatmap = ','.join(glob.glob(os.path.join(self.outdir, "*heatmap*.png")))
        zip_file = os.path.join(self.outdir, "sRNAde_full_Result.zip")
        stats_file = os.path.join(self.outdir, "sequencingStat.txt")
        if not os.path.exists(stats_file):
            stats_file = None

        os.system("cd " + self.outdir + "; zip -r " + zip_file + " " + " *")
        update = {"heatmaps": heatmap, "xls_files": xls_files, "zip_file": zip_file, "stats_file": stats_file}
        self.raw_update(payload=update)
