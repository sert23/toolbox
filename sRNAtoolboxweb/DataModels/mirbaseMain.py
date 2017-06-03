__author__ = 'antonior'

import os

class MirBaseMain():
    def __init__(self, Name, UR, RC, RC_adj, UR5p, RC5p, RC5p_adj, name_5p, UR3p, RC3p, RC3p_adj, name_3p, coordinates,
                 _5pcanonical, _3pcanonical):
        self.Name = Name
        self._3pcanonical = _3pcanonical
        self._5pcanonical = _5pcanonical
        self.coordinates = coordinates
        self.name_3p = name_3p
        self.RC3p_adj = RC3p_adj
        self.RC3p = RC3p
        self.UR3p = UR3p
        self.name_5p = name_5p
        self.RC5p_adj = round(float(RC5p_adj), 2)
        self.RC5p = RC5p
        self.UR5p = UR5p
        self.RC_adj = round(float(RC_adj), 2)
        self.RC = RC
        self.UR = UR
        self.align = Name + "_" + "_".join(coordinates.split("#")[:2])

    def get_sorted_attr(self):
        return ["Name", "UR", "RC", "RC_adj", "UR5p", "RC5p", "RC5p_adj", "name_5p", "UR3p", "RC3p", "RC3p_adj", "name_3p", "coordinates",
                "_5pcanonical", "_3pcanonical", "align"]