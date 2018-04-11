from DataModels.mirbaseMain import MirBaseMain
from FileModels.Parser import Parser

__author__ = 'antonior'

class MirBaseParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            yield MirBaseMain(*aline)
        fd.close()