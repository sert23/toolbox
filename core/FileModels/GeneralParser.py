from DataModels.generalTable import General
from FileModels.Parser import Parser

__author__ = 'antonior'

class GeneralParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield General(aline)
        fd.close()