__author__ = 'antonior'


class JBrowserBed():
    def __init__(self, chrom, chromStart, chromEnd, name, score, strand, url):
        self.url = url
        self.strand = strand
        self.score = score
        self.name = name
        self.chromEnd = chromEnd
        self.chromStart = chromStart
        self.chrom = chrom

    def get_sorted_attr(self):
        return ["chrom", "chromStart", "chromEnd", "name", "score", "strand", "url"]