__author__ = 'antonior'


class TargetPrediction():
    def __init__(self, microRNA, mRNA, energy, targetStart, targetEnd, score):

        self.score = score
        self.targetEnd = targetEnd
        self.targetStart = targetStart
        self.energy = energy
        self.mRNA = mRNA
        self.microRNA = microRNA

    def get_sorted_attr(self):
        return ["microRNA", "mRNA", "energy", "targetStart", "targetEnd", "score"]