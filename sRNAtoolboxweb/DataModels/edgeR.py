__author__ = 'antonior'


class EdegeR():

    def __init__(self, miRNAname, logFC, logCPM, pval, FDR, **samples):

        self.FDR = FDR
        self.logCPM = logCPM
        self.logFC = logFC
        self.pval = pval
        self.miRNA_Name = miRNAname

        for key in samples:
            setattr(self, key, samples[key])

    def __str__(self):
        return "\t".join([str(attr) for attr in self.__dict__.values()])


    def get_sorted_attr(self):
        return ["miRNA_Name", "logFC", "logCPM", "pval", "FDR"]
