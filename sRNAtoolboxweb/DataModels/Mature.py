__author__ = 'antonior'

class Mature():
    def __init__(self, name, unique_reads,	read_count, read_count_mult_map_adj_, RPM_lib, RPM_total,
                 chromosomeString="", *args, **kwargs):
        self.chromosomeString = chromosomeString
        self.RPM_total = round(float(RPM_total), 2)
        self.RPM_lib = round(float(RPM_lib), 2)
        self.read_count_mult_map_adj_ = round(float(read_count_mult_map_adj_), 2)
        self.read_count = read_count
        self.unique_reads = unique_reads
        self.name = name

    def get_sorted_attr(self):
        return ["name", "unique_reads", "read_count", "read_count_mult_map_adj_", "RPM_lib", "RPM_total", "chromosomeString"]