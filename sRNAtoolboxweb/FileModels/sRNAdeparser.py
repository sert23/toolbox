from DataModels.deConsensus import DeConsensus

__author__ = 'antonior'
import xlrd
from FileModels.Parser import Parser
from DataModels.noiseqTable import NOISeq
from DataModels.deSeq import DeSeq
from DataModels.edgeR import EdegeR

class SRNAdeParser(Parser):

    def __init__(self, ipath, sheet):
        super(SRNAdeParser, self).__init__(ipath)
        self.sheet_name = sheet

    def parse(self):
        workbook = xlrd.open_workbook(self.ipath)
        sheet = workbook.sheet_by_name(self.sheet_name)
        header = [sheet.cell_value(0, col) for col in range(sheet.ncols)]

        for row in range(sheet.nrows-1):
            if "NOISeq" in self.sheet_name:
                row_values = sheet.row_values(row+1, 0, None)
                samples = {header[i+1]: value for i, value in enumerate(row_values[1:-3])}

                new_noiseq = NOISeq(row_values[0], row_values[-3], row_values[-2], row_values[-1])
                yield new_noiseq

            elif "deSeq" in self.sheet_name:
                row_values = sheet.row_values(row+1, 0, None)
                samples = {header[i+1]: value for i, value in enumerate(row_values[1:-4])}

                new_DeSeq = DeSeq(row_values[0], row_values[-4], row_values[-3], row_values[-2], row_values[-1])
                yield new_DeSeq

            elif "edgeR" in self.sheet_name:
                row_values = sheet.row_values(row+1, 0, None)
                samples = {header[i+1]: value for i, value in enumerate(row_values[1:-4])}

                new_edgeR = EdegeR(row_values[0], row_values[-4], row_values[-3], row_values[-2], row_values[-1])
                yield new_edgeR


    def get_consensus(self, *sheets):
        integration = {}
        for sheet in sheets:
            self.sheet_name = sheet
            for obj in self.parse():
                if obj.miRNA_Name in integration:
                    if "NOISeq" in self.sheet_name:
                        integration[obj.miRNA_Name].NOISeq_Probability = obj.prob
                    elif "edgeR" in self.sheet_name:
                        integration[obj.miRNA_Name].edegeR_FDR = obj.FDR
                    elif "deSeq" in self.sheet_name:
                        integration[obj.miRNA_Name].deSeq_padj = obj.padj
                else:
                    if "NOISeq" in self.sheet_name:
                        integration[obj.miRNA_Name] = DeConsensus(obj.miRNA_Name, NOISeq_Probability=obj.prob)
                    elif "edgeR" in self.sheet_name:
                        integration[obj.miRNA_Name] = DeConsensus(obj.miRNA_Name, edegeR_FDR=obj.FDR)
                    elif "deSeq" in self.sheet_name:
                        integration[obj.miRNA_Name] = DeConsensus(obj.miRNA_Name, deSeq_padj=obj.padj)

        for consensus in integration.values():
            consensus.setNumber()
            yield consensus



