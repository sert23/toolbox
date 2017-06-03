__author__ = 'antonior'


class Blast():
    def __init__(self, qseqid, sseqid, sgi, sstart, send, evalue, bitscore, pident, mismatch, sscinames, sskingdoms,
                 stitle):
        self.specie_title = stitle
        self.specie_kingdom = sskingdoms
        self.specie_name = sscinames
        self.mismatches = mismatch
        self.p_identity = pident
        self.bitScore = bitscore
        self.evalue = evalue
        self.subject_end = send
        self.subject_start = sstart
        self.subject_gi = sgi
        self.subject_id = sseqid
        self.query_id = qseqid.split("#")[0]
        self.Read_Count = int(qseqid.split("#")[1])

    def __str__(self):
        return "\t".join([self.query_id + "#" + str(self.Read_Count), self.subject_id, self.subject_gi,
                          self.subject_start, self.subject_end, self.evalue, self.bitScore, self.p_identity,
                          self.mismatches, self.specie_name, self.specie_kingdom, self.specie_title])

    def get_sorted_attr(self):
        return ["query_id", "Read_Count", "subject_id", "evalue", "p_identity", "specie_name", "specie_title"]

