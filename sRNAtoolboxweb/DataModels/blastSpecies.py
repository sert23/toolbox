__author__ = 'antonior'


class BlastSpecies:
    def __init__(self, specie, rc, prc,):
        self.Percentage_Read_Count = prc
        self.Read_count = rc
        self.specie = specie

    def get_sorted_attr(self):
        return ["specie", "Read_count", "Percentage_Read_Count"]





