import json
from DataModels.FuncAnnot import FuncAnnotModule, FuncAnnot

__author__ = 'antonior'



class EdaFile():
    def __init__(self, filename, type):
        self.filename = filename
        self.type = type

    def parse(self):

        fd = open(self.filename)

        fd.readline()
        for line in fd:

            aline = line.replace("\n","").split("\t")

            proteins = aline[8].replace(" ","").replace("[","").split(",")
            go_info = aline[0].split("#")

            if self.type == "module":
                newobj = FuncAnnotModule(go_info[0], go_info[1], aline[1], aline[2], aline[3], aline[4], aline[5], aline[6], aline[7], proteins, aline[9])
            elif self.type == "all":
                newobj = FuncAnnot(go_info[0], go_info[1], aline[1], aline[2], aline[3], aline[4], aline[5], aline[6], aline[7], proteins)
            else:
                newobj = FuncAnnot(go_info[0], go_info[1], aline[1], aline[2], aline[3], aline[4], aline[5], aline[6], aline[7], proteins)

            yield newobj






