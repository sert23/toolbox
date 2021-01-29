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
                try:
                    if '=' in line:
                        args = line.rstrip("\n").split("=")
                        key = args.pop(0)
                        value = "=".join(args)
                        if key == "libs" or key == "desc":
                            if key in values:
                                values[key].append(value)
                            else:
                                values[key] = [value]
                        else:
                            values[key] = value
                except:
                    pass

        return values



