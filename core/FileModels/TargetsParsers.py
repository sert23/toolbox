import json
import os
import sys
from DataModels.targetPrediction import TargetPrediction
from FileModels.Parser import Parser
import xlrd
from DataModels.miRNAtargets import MirnaTarget, Target
from IntegrativeTarDB.sRNAbaseLoader import Loader
from utils.mongoDB import mongoDB
import progressbar

__author__ = 'antonior'


class ParseMirTarBase(Parser):
    def parse(self):

        fdw = open(os.path.basename(self.ipath)+"_MirTarBase.txt", "w")

        workbook = xlrd.open_workbook(self.ipath)
        if "miRTarBase" in workbook.sheet_names():
            sheet = workbook.sheet_by_name("miRTarBase")

        else:
            return "Don't found miRTarBase, please check sheets names"

        header = [sheet.cell_value(0, col) for col in range(sheet.ncols)]

        new_conDB = mongoDB("localhost", "Targets")
        new_loader = Loader(new_conDB, "test")

        conDB_mapping = mongoDB("localhost", "geneInfo")


        widgets = ["processing file: " + self.ipath, progressbar.Percentage(), ' ',
                   progressbar.Bar(marker=progressbar.RotatingMarker()), ' ', progressbar.ETA(), ' ',
                   progressbar.FileTransferSpeed()]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=sheet.nrows - 1).start()

        for row in range(sheet.nrows - 1):
            pbar.update(row)
            mirnaname = sheet.cell_value(row + 1, header.index("miRNA"))

            geneID = sheet.cell_value(row + 1, header.index("Target Gene (Entrez Gene ID)"))
            if geneID != "":
                query = {"gene_id": int(geneID), "protein.uniprot_id": {"$exists": "true"}}
                results = conDB_mapping.find("accesions", query, {"protein.uniprot_id": 1})
                for uniprots in [r["protein"] for r in results]:
                    for record in uniprots:
                        uniprot = record["uniprot_id"]
                        source = "MirTarBase"
                        # validation_status = sheet.cell_value(row+1, header.index("Support Type"))
                        validation_status = "Experimental"
                        bib = "PubmedID: " + str(int(sheet.cell_value(row + 1, header.index("References (PMID)"))))
                        validation_experiments = sheet.cell_value(row + 1, header.index("Experiments")).split("//")

                        new_target = Target(source, validation_experiments, validation_status, uniprot, bib)
                        newobj = MirnaTarget(mirnaname, new_target)
                        #print "load element:" + str(row) + ", " + newobj.miRNAname + "-->" + new_target.uniprot
                        fdw.write(json.dumps(newobj.write_json()) + "\n")
                        #new_loader.insert(newobj)
        pbar.finish()
        fdw.close()


class ParserMiranda(Parser):
    def parse(self):

        fd = open(self.ipath)
        lines = 0
        for line in fd:
            lines += 1
        fd.close()

        fd = open(self.ipath)

        fdw = open(os.path.basename(self.ipath)+"_not_founds_miranda.txt", "w")
        fdw1 = open(os.path.basename(self.ipath)+"_miranda.json", "w")


        # Connectors
        conDB_mapping = mongoDB("localhost", "Uniprots")

        widgets = ["processing file: " + fd.name, progressbar.Percentage(), ' ',
                   progressbar.Bar(marker=progressbar.RotatingMarker()), ' ', progressbar.ETA(), ' ',
                   progressbar.FileTransferSpeed()]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=lines).start()

        for i, line in enumerate(fd):
            aline = line.replace(" ", "").replace("\n", "").split("\t")
            aline[0] = aline[0].lower()

            pbar.update(i + 1)
            new_target_predicted = TargetPrediction(*aline)
            query = {"xrefs": new_target_predicted.mRNA, "protein.uniprot_id": {"$exists": "true"}}
            results = conDB_mapping.findOne("accesions", query, {"protein": 1})

            if results is not None:
                proteinList = results["protein"]

                uniprots = []
                for prot in proteinList:
                    if new_target_predicted.mRNA in prot["transcripts_ids"]:
                        uniprots = [prot["uniprot_id"]]

                if uniprots == []:
                    uniprots = [prot["uniprot_id"] for prot in proteinList]

                for uniprot in uniprots:
                    source = "MIRANDA"
                    validation_status = "Prediction"
                    bib = []
                    validation_experiments = ["Computational Prediction"]
                    new_target = Target(source, validation_experiments, validation_status, uniprot, bib)
                    newobj = MirnaTarget(new_target_predicted.microRNA, new_target)
                    fdw1.write(json.dumps(newobj.write_json()) + "\n")

            else:
                fdw.write(new_target_predicted.mRNA + "\n")

        pbar.finish()
        fd.close()
        fdw.close()
        fdw1.close()



class ParserTargetScan(Parser):
    def parse(self):

        fd = open(self.ipath)
        lines = 0
        for line in fd:
            lines += 1
        fd.close()

        fd = open(self.ipath)

        fdw = open("not_founds.txt", "w")
        fdw1 = open("ts.json", "w")


        # Connectors
        new_conDB = mongoDB("localhost", "Targets")
        new_loader = Loader(new_conDB, "IntegrateTargetDB")
        conDB_mapping = mongoDB("localhost", "geneInfo")

        widgets = ["processing file: " + fd.name, progressbar.Percentage(), ' ',
                   progressbar.Bar(marker=progressbar.RotatingMarker()), ' ', progressbar.ETA(), ' ',
                   progressbar.FileTransferSpeed()]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=lines).start()

        for i, line in enumerate(fd):
            aline = line.replace(" ", "").replace("\n", "").split("\t")
            aline[0] = aline[0].lower()

            pbar.update(i + 1)
            new_target_predicted = TargetPrediction(*aline)
            query = {"xrefs": new_target_predicted.mRNA, "protein.uniprot_id": {"$exists": "true"}}
            results = conDB_mapping.findOne("accesions", query, {"protein": 1})
            if results is not None:
                proteinList = results["protein"]

                uniprots = []
                for prot in proteinList:
                    if new_target_predicted.mRNA in prot["transcripts_ids"]:
                        uniprots = [prot["uniprot_id"]]

                if uniprots == []:
                    uniprots = [prot["uniprot_id"] for prot in proteinList]

                for uniprot in uniprots:
                    source = "TS"
                    validation_status = "Prediction"
                    bib = []
                    validation_experiments = ["Computational Prediction"]
                    new_target = Target(source, validation_experiments, validation_status, uniprot, bib)
                    newobj = MirnaTarget(new_target_predicted.microRNA, new_target)
                    fdw1.write(json.dumps(newobj.write_json()) + "\n")

            else:
                fdw.write(new_target_predicted.mRNA + "\n")

        pbar.finish()
        fd.close()
        fdw.close()
        fdw1.close()



inputfile = sys.argv[1]
ParseMirTarBase(inputfile).parse()







