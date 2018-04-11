from DataModels.MatureSa import MatureSA
from FileModels.Parser import Parser

__author__ = 'antonior'

class MatureParserSA(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield MatureSA(*aline)
        fd.close()