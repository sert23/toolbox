from DataModels.organism_mirbase import Organims
from FileModels.Parser import Parser

__author__ = 'antonior'


class OrganimsParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        fd.readline()

        for line in fd:
            aline = line.replace("\n", "").split("\t")
            new_organims = Organims(*aline)
            yield new_organims

    def get_organims_from_name(self, name):

        for organims in self.parse():
            if organims.name.lower() in name.lower():
                return organims.organism
            elif organims.organism.lower() in name.split(":"):
                return organims.organism










