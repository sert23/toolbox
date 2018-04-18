__author__ = 'antonior'

from FileModels.Parser import Parser
from DataModels.blastSpecies import BlastSpecies
from DataModels.blast import Blast
from DataModels.blasttax import BlastTax


class BlastParser(Parser):
    #def __init__(self, ipath, file_type, limit=1):
    def __init__(self, ipath, file_type, limit=None):
        super(BlastParser, self).__init__(ipath)
        self.file_type = file_type
        self.limit = limit
        print(limit)
        print("this is the limit")
        print(self.limit)
        print(type(limit))
        print(type(self.limit))

    def parse(self):
        print("Aquí está el Blast")
        print(self.limit)
        print(self.ipath)
        fd = open(self.ipath)
        header = fd.readline()

        for i, line in enumerate(fd):
            aline = line.replace("\n", "").split("\t")

            if i < self.limit or self.limit is None:
                obj = None
                if self.file_type =="blast":
                    obj = Blast(*aline)
                elif self.file_type =="species":
                    obj = BlastSpecies(*aline)
                elif self.file_type =="tax":
                    obj = BlastTax(*aline)

                yield obj

            else:
                break

    def sort_blast_by_rc(self, out):
        fd = file(self.ipath)
        fdw = file(out, "w")

        header = fd.readline()
        fdw.write(header)
        all_blast = []

        for i, line in enumerate(fd):
            aline = line.replace("\n", "").split("\t")

            if self.file_type =="blast":
                obj = Blast(*aline)
                all_blast.append(obj)


        blast_sorted = sorted(all_blast, key=lambda x: x.Read_Count, reverse=True)

        for blast in blast_sorted:
            fdw.write(str(blast) + "\n")







