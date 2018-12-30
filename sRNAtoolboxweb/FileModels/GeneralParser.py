from DataModels.generalTable import General
from FileModels.Parser import Parser

__author__ = 'antonior'


def is_numeric(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class GeneralParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            aline = [round(float(x),2) if is_numeric(x) else x for x in aline]
            yield General(header, *aline)
        fd.close()
