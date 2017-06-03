__author__ = 'antonior'


class DeConsensus:
    def __init__(self, miRNAname, deSeq_padj="", edegeR_FDR="", NOISeq_Probability=""):

        self.deSeq_padj = deSeq_padj
        self.edegeR_FDR = edegeR_FDR
        self.NOISeq_Probability = NOISeq_Probability
        self.miRNA_Name = miRNAname
        self.Detected_by = 0
        self.setNumber()

    def get_sorted_attr(self):
        return ["miRNA_Name", "deSeq_padj", "edegeR_FDR", "NOISeq_Probability", "Detected_by"]


    def setNumber(self):
        values = [self.deSeq_padj, self.edegeR_FDR, self.NOISeq_Probability]
        n = 0
        for v in values:
            if v != "":
                n += 1

        self.Detected_by = n




