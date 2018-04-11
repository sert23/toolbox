from DataModels.tRNA import TRNA
from FileModels.Parser import Parser

__author__ = 'antonior'

class TRNAParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield TRNA(*aline)
        fd.close()