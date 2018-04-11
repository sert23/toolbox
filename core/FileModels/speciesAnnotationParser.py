from FileModels.Parser import Parser

__author__ = 'antonior'


class SpeciesAnnotationParser(Parser):

    def __init__(self, ipath):
        super(SpeciesAnnotationParser, self).__init__(ipath)
        self.speciesAnnotation = {}

    def parse(self):
        fd = open(self.ipath)

        for line in fd:
            if not (line.startswith("#")) and line != "\n":
                print(line)
                (sp, values) = line.replace("\n", "").replace("\r", "").split(":")
                (tag, value) = values.split("=")

                if sp in self.speciesAnnotation:
                    if tag in self.speciesAnnotation[sp]:
                        self.speciesAnnotation[sp][tag].append(value)
                    else:
                        self.speciesAnnotation[sp][tag] = [value]
                else:
                    self.speciesAnnotation[sp] = {}
                    self.speciesAnnotation[sp][tag] = [value]

        return self.speciesAnnotation