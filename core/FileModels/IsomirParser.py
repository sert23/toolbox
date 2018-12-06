from DataModels.Isomir import Isomir
from FileModels.Parser import Parser

__author__ = 'antonior'

class IsomirParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        header = header + ["Draw"]
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            aline = aline + [aline[0]]
            yield Isomir(*aline)
        fd.close()