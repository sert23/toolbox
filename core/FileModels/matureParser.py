from DataModels.Mature import Mature
from FileModels.Parser import Parser

__author__ = 'antonior'

class MatureParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield Mature(*aline)
        fd.close()