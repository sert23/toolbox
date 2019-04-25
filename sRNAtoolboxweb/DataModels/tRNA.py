__author__ = 'antonior'

class TRNA():
    def __init__(self, antiCodon, unique_reads,	read_count, read_adjusted, RPM_lib, RPM_all):
        self.RPM_all = round(float(RPM_all), 2)
        self.RPM_lib = round(float(RPM_lib), 2)
        self.read_adjusted = read_adjusted
        self.read_count = round(float(read_count), 2)
        self.unique_reads = round(float(unique_reads), 2)
        self.tRNA_gene = antiCodon

    def get_sorted_attr(self):
        return ["tRNA_gene", "unique_reads", "read_count", "read_adjusted", "RPM_lib", "RPM_all"]