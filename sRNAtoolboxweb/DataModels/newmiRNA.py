__author__ = 'antonior'


class NewMiRNA():
    def __init__(self, name, homolog, _5p_pos, _3p_pos, homologSeq, pattern):
        self.matures = []
        self.pattern = pattern
        self.homologSeq = homologSeq
        self._3p_pos = _3p_pos
        self._5p_pos = _5p_pos
        self.homolog = homolog
        self.name = name

        for i, char in enumerate(self.homologSeq):
            if i % 60 == 0:

                self.homologSeq = self.homologSeq[:i] + " " + self.homologSeq[i:]

        self.homologSeq = self.homologSeq

    def get_sorted_attr(self):
        return ["name", "homolog", "_5p_pos", "_3p_pos", "homologSeq", "pattern"]


class MatureMiRNA():
    def __init__(self, name, unique_reads, read_count, canonical_read_count, RPM_lib, RPM_total):
        self.RPM_total = RPM_total
        self.RPM_lib = RPM_lib
        self.canonical_read_count = canonical_read_count
        self.read_count = read_count
        self.unique_reads = unique_reads
        self.name = name

    def get_sorted_attr(self):
        return ["name", "unique_reads", "read_count", "canonical_read_count", "RPM_lib", "RPM_total"]