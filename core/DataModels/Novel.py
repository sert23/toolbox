__author__ = 'antonior'


class Novel():
    def __init__(self, aling, name2, chrom, chromStart, chromEnd, strand, RC_hairpin, _5pSeq, _5pRC, _3pSeq, _3pRC, type,
                 _hairpin):
        self.align_ = aling
        self._hairpin = _hairpin
        self.type = type
        self._3pRC = _3pRC
        self._3pSeq = _3pSeq
        self._5pRC = _5pRC
        self._5pSeq = _5pSeq
        self.RC_hairpin = RC_hairpin
        self.strand = strand
        self.chromEnd = chromEnd
        self.chromStart = chromStart
        self.chrom = chrom
        self.name2 = name2


    def get_sorted_attr(self):
        return ["name2", "chrom", "chromStart", "chromEnd", "strand", "RC_hairpin", "_5pSeq", "_5pRC", "_3pSeq",
                "_3pRC", "type", "_hairpin", "align_"]