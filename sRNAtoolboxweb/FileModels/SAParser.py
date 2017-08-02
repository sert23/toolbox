from DataModels.SA import SA
from FileModels.Parser import Parser

__author__ = 'antonior'

class SAParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield SA(*aline)
        fd.close()