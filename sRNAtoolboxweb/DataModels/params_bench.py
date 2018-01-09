__author__ = 'antonior'


class ParamsBench():
    def __init__(self, *ifiles):
        self.ifiles = ifiles
        self.params = self.load()

    def load(self):
        values = {}
        for ifile in self.ifiles:
            fd = open(ifile)
            for line in fd:
                if '=' in line:
                    [key, value] = line.rstrip("\n").split("=")
                    if key == "libs" or key == "desc":
                        if key in values:
                            values[key].append(value)
                        else:
                            values[key] = [value]
                    else:
                        values[key] = value
        return values



