__author__ = 'antonior'


class Isomir():
    def __init__(self, name, unique_reads, read_count, RPM_total, RPM_lib, Canonical_RC, NTA_A, NTA_U, NTA_C, NTA_G,
                 NTA_Sum, lv3pE, lv3pT, lv5pE, lv5pT, mv):
        self.mv = mv
        self.lv5pT = lv5pT
        self.lv5pE = lv5pE
        self.lv3pT = lv3pT
        self.lv3pE = lv3pE
        self.NTA_G = NTA_G
        self.NTA_C = NTA_C
        self.NTA_U = NTA_U
        self.NTA_A = NTA_A
        self.NTA_Sum = NTA_Sum
        self.Canonical_RC = Canonical_RC
        self.RPM_lib = round(float(RPM_lib), 2)
        self.RPM_total = round(float(RPM_total), 2)
        self.read_count = read_count
        self.unique_reads = unique_reads
        self.name = name

    def get_sorted_attr(self):
        return ["name", "unique_reads", "read_count", "RPM_lib", "RPM_total", "Canonical_RC", "NTA_A", "NTA_U",
                "NTA_C", "NTA_G", "NTA_Sum", "lv3pE", "lv3pT", "lv5pE", "lv5pT", "mv"]