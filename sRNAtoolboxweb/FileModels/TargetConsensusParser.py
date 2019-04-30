from DataModels.targetconsensus import TargetConsensus
from FileModels.Parser import Parser

__author__ = 'antonior'


class TargetConsensusParser(Parser):
    def __init__(self, ipath, limit=5000):
        super(TargetConsensusParser, self).__init__(ipath)
        self.limit = limit
    def parse(self):
        fd = open(self.ipath)

        for i, line in enumerate(fd):
            if i < self.limit or self.limit is None:

                aline = line.replace("\n", "").split("\t")
                new_cons = TargetConsensus(*aline)
                yield new_cons

    def get_by_n(self, n):

        for new_cons in self.parse():
            if int(new_cons.Number_of_Programs) >= n:
                yield new_cons
            else:
                break
