from DataModels.Novel import Novel
from FileModels.Parser import Parser

__author__ = 'antonior'

class NovelParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")[:13]
            yield Novel(*aline)
        fd.close()