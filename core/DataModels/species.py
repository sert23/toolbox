__author__ = 'antonior'


class Species():
    def __init__(self, sp_class, specie, shortName, db, db_ver, scientific, taxID, full=False, hasTargetSequencesAndGO=False):
        if hasTargetSequencesAndGO == "true":
            self.hasTargetSequencesAndGO = True
        else:
            self.hasTargetSequencesAndGO = False

        if full == "true":
            self.full = True
        else:
            self.full = False

        self.db_ver = db_ver
        self.taxID = taxID
        self.scientific = scientific
        self.db = db
        self.shortName = shortName
        self.specie = specie
        self.sp_class = sp_class

    def __str__(self):
        return self.specie + "(" + self.db + ")"
        #return self.specie + "(" + self.db + "), " +self.scientific