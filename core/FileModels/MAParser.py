from DataModels.MA import MA
from FileModels.Parser import Parser

__author__ = 'antonior'

class MAParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield MA(*aline)
        fd.close()