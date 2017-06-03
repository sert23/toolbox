__author__ = 'antonior'


class ParamsBench():
    def __init__(self, ifile):
        self.ifile = ifile
        self.params = self.load()

    def load(self):
        fd = file(self.ifile)
        values = {}
        for line in fd:
            [key, value] = line.rstrip("\n").split("=")
            if key == "libs" or key == "desc":
                if key in values:
                    values[key].append(value)
                else:
                    values[key] = [value]
            else:
                values[key] = value
        return values



