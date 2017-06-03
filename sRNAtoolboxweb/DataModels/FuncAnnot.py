__author__ = 'antonior'


class FuncAnnot():

    def __init__(self, go_id, go_term, f1, number_protein, f3, pvalue, pvalue_adj, f6, f7, proteins):

        self.go_id = go_id
        self.go_term = go_term
        self.Proteins_inBackGround = int(f1)
        self.number_protein = int(number_protein)
        self.notInGeneList = int(f3)
        self.pvalue = round(float(pvalue),5)
        self.FDR = round(float(pvalue_adj),5)
        self.RE = round(float(f6),5)
        self.type = f7
        self.proteins = proteins


class FuncAnnotModule(FuncAnnot):

    def __init__(self, go_id, go_term, f1, number_protein, f3, pvalue, pvalue_adj, f6, f7, proteins, module):

        FuncAnnot.__init__(self, go_id, go_term, f1, number_protein, f3, pvalue, pvalue_adj, f6, f7, proteins)
        self.module = module


