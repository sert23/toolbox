from DataModels.generalTable import General
from FileModels.Parser import Parser

__author__ = 'antonior'


class GeneralParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            numbers = aline[1:]
            numbers = [float(x) for x in numbers]
            aline = [aline[0]] + [round(x, 2) for x in numbers]
            yield General(header, *aline)
        fd.close()
