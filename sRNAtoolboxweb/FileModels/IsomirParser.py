from DataModels.Isomir import Isomir
from FileModels.Parser import Parser

__author__ = 'antonior'

class IsomirParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield Isomir(*aline)
        fd.close()