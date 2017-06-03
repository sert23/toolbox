__author__ = 'antonior'


class DeSeq():

    def __init__(self, miRNAname, foldChange, log2FoldChange, pval, padj, **samples):

        self.padj = padj
        self.pval = pval
        self.log2FoldChange = log2FoldChange
        self.foldChange = foldChange
        self.miRNA_Name = miRNAname

        for key in samples:
            setattr(self, key, samples[key])

    def __str__(self):
        return "\t".join([str(attr) for attr in self.__dict__.values()])

    def get_sorted_attr(self):
        return ["miRNA_Name", "foldChange", "log2FoldChange", "pval", "padj"]



