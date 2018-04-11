from DataModels.species import Species
from FileModels.Parser import Parser

__author__ = 'antonior'


class SpeciesParser(Parser):

    def parse(self):
        fd = open(self.ipath)
        # header = fd.readline().replace("\n", "").split(",")
        species_array = []
        for line in fd:
            aline = line.replace("\n", "").split(",")
            new_species = Species(*aline)
            species_array.append(new_species)
        fd.close()

        return species_array