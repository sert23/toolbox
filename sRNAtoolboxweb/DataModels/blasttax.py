__author__ = 'antonior'


class BlastTax:
    def __init__(self, tax, rc, prc,):
        self.Percentage_Read_Count = prc
        self.Read_count = rc
        self.Taxonomy = tax

    def get_sorted_attr(self):
        return ["Taxonomy", "Read_count", "Percentage_Read_Count"]





