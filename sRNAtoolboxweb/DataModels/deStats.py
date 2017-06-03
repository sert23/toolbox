__author__ = 'antonior'


class DeStats():
    def __init__(self, sample, raw_reads, adapter_cleaned, reads_in_analysis, unique_reads_in_analysis,
                 genome_mapped_reads, unique_reads_mapped_to_genome):
        self.unique_reads_in_analysis = unique_reads_in_analysis
        self.unique_reads_mapped_to_genome = unique_reads_mapped_to_genome
        self.genome_mapped_reads = genome_mapped_reads
        self.reads_in_analysis = reads_in_analysis
        self.adapter_cleaned = adapter_cleaned
        self.raw_reads = raw_reads
        self.sample = sample

    def get_sorted_attr(self):
        return ["sample", "raw_reads", "adapter_cleaned", "reads_in_analysis", "unique_reads_in_analysis",
                 "genome_mapped_reads", "unique_reads_mapped_to_genome"]

