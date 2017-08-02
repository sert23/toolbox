from DataModels.deStats import DeStats
from FileModels.Parser import Parser

__author__ = 'antonior'

class DeStatsParser(Parser):

    def parse(self):
        fd = open(self.ipath)
        header = fd.readline()

        for line in fd:
            aline = line.replace("\n", "").split("\t")
            new_stats = DeStats(*aline[0:7])
            yield new_stats
