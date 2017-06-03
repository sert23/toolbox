__author__ = 'antonior'


class TargetConsensus():
    def __init__(self, microRNA, mRNA, Number_of_Program, Detected_by):


        self.Detected_by = Detected_by
        self.Number_of_Programs = Number_of_Program
        self.mRNA = mRNA
        self.microRNA = microRNA

    def get_sorted_attr(self):
        return ["microRNA", "mRNA", "Number_of_Programs", "Detected_by"]