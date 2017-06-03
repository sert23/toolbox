__author__ = 'antonior'

class BenchSummary():
    def __init__(self, ifile):
        self.ifile = ifile
        self.libraries = ""
        self.pre = ""
        self.hairpin = ""
        self.matures = ""
        self.mapped = ""
        self.read_in_analysis = ""
        self.clean_input_reads = ""
        self.input_reads = ""
        self.load()

    def load(self):
        fd = file(self.ifile)

        fd.readline()
        self.input_reads = fd.readline().rstrip("\n").split(": ")[1]
        self.clean_input_reads = fd.readline().rstrip("\n").split(": ")[1].split(" ")[0]
        self.read_in_analysis = fd.readline().rstrip("\n").split(": ")[1].split(" ")[0]
        fd.readline()
        fd.readline()
        self.mapped = fd.readline().rstrip("\n").split(" ")[1]
        fd.readline()
        self.matures = fd.readline().rstrip("\n").split(" ")[1]
        self.hairpin = fd.readline().rstrip("\n").split(" ")[1]
        self.hairpin = fd.readline().rstrip("\n").split(" ")[1]
        self.pre = fd.readline().rstrip("\n").split(" ")[1]
        fd.readline()
        self.libraries = {}
        key = ""
        for line in fd:
            if line.startswith("Library"):
                key = line.rstrip("\n").split(":")[1]
                self.libraries[key] = {}
            else:
                self.libraries[key][line.rstrip("\n").split(":")[0]] = line.rstrip("\n").split(":")[1].split(" ")[0]




