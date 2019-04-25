__author__ = 'antonior'


class Novel():
    def __init__(self, name, seqName, start, end, strand, totalRC, _5pname, _5pseq, _5pRC, _3pname, _3pseq, _3pRC,
                 duplexType, isHairpin, hasHomolog, hairpinSeq, duplexQuality, detectionType, mature5pFluctuation,
                 InClusterRatioSense, Dominant2AllRatioMature, matureBindings, top2ClusterAreGuideAndStar, noClusters,
                 outOf6Fulfilled):
        self.align_ = name
        self.name = name
        self.seqName = seqName
        self.start = start
        self.end = end
        self.strand = strand
        self.totalRC = totalRC
        self._5pname = _5pname
        self._5pseq = _5pseq
        self._5pRC = _5pRC
        self._3pname = _3pname
        self._3pseq = _3pseq
        self._3pRC = _3pRC

        # self.align_ = aling
        # self._hairpin = _hairpin
        # self.type = type
        # self._3pRC = _3pRC
        # self._3pSeq = _3pSeq
        # self._5pRC = _5pRC
        # self._5pSeq = _5pSeq
        # self.RC_hairpin = RC_hairpin
        # self.strand = strand
        # self.chromEnd = chromEnd
        # self.chromStart = chromStart
        # self.chrom = chrom
        # self.name2 = name2

    def get_sorted_attr(self):
        return ["name", "seqName", "start", "end", "strand",
                "totalRC", "_5pname", "_5pseq", "_5pRC", "_3pname", "_3pseq", "_3pRC", "align_"]
