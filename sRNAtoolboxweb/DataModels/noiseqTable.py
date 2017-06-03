__author__ = 'antonior'


class NOISeq():

    def __init__(self, miRNAname, m, d, prob, **samples):

        self.Log2Ratio_M = m
        self.Difference_D = d
        self.prob = prob
        self.miRNA_Name = miRNAname

        for key in samples:
            setattr(self, key, samples[key])

    def __str__(self):
        return "\t".join([str(attr) for attr in self.__dict__.values()])

    def get_sorted_attr(self):
        return ["miRNA_Name", "Difference_D", "Log2Ratio_M", "prob"]



