
from DataModels.srnacons import sRNAcons_sRNA2Species,sRNAcons_species2sRNA
from FileModels.Parser import Parser


class sRNAconsParser(Parser):
    #def __init__(self, ipath, file_type, limit=1):
    def __init__(self, ipath, file_type, limit=None):
        super(sRNAconsParser, self).__init__(ipath)
        self.file_type = file_type
        self.limit = limit

    def parse(self):
        fd = open(self.ipath)
        header = fd.readline()

        for i, line in enumerate(fd):
            aline = line.replace("\n", "").split("\t")

            if i < self.limit or self.limit is None:
                obj = None
                if self.file_type =="srna2species":
                    obj = sRNAcons_sRNA2Species(*aline)
                elif self.file_type =="species2srna":
                    obj = sRNAcons_species2sRNA(*aline)
                yield obj

            else:
                break








