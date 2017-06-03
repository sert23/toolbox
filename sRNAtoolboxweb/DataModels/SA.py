__author__ = 'antonior'

class SA():
    def __init__(self, name, unique_reads,	read_count_MA, read_count_SA, RPM_lib, RPM_total, chromosomeString="--"):
        self.chromosomeString = chromosomeString
        self.RPM_total = round(float(RPM_total), 2)
        self.RPM_lib = round(float(RPM_lib), 2)
        self.read_count_MA = read_count_MA
        self.read_count_SA = read_count_SA
        self.unique_reads = unique_reads
        self.name = name

    def get_sorted_attr(self):
        return ["name", "unique_reads", "read_count_MA", "read_count_SA", "RPM_lib", "RPM_total", "chromosomeString"]