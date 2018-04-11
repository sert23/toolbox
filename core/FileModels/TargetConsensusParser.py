from DataModels.targetconsensus import TargetConsensus
from FileModels.Parser import Parser

__author__ = 'antonior'


class TargetConsensusParser(Parser):

    def parse(self):
        fd = open(self.ipath)

        for line in fd:
            aline = line.replace("\n", "").split("\t")
            new_cons = TargetConsensus(*aline)
            yield new_cons

    def get_by_n(self, n):

        for new_cons in self.parse():
            if int(new_cons.Number_of_Programs) >= n:
                yield new_cons
            else:
                break
