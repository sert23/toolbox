from DataModels.generalTable import General
from FileModels.Parser import Parser
import os
from django.core.urlresolvers import reverse_lazy

__author__ = 'antonior'


def is_dec(s):
    try:
        c = float(s)
        if c.is_integer():
            return False
        else:
            return True
    except ValueError:
        return False

class LinksParser(Parser):
    def parse(self):
        fd = open(self.ipath)
        header = fd.readline().replace("\n", "").split("\t")
        header = header[0:-1] + ["link"]
        #header = header[0:-1] + ["Link to results"]
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            rel_path = aline[-1].split("/")
            link = os.path.join(reverse_lazy('de_method'), rel_path[-1], rel_path[-3])
            aline = aline[:-1] + [link]
            # aline = aline[:-1] + ['<a href="'+link+'" class="btn btn-primary btn-sm" role="button" aria-pressed="true">Go to results</a>']
            yield General(header, *aline)
        fd.close()

class BWParser(Parser):
    def parse(self, MEDIA_ROOT, MEDIA_URL):
        fd = open(self.ipath)
        header = ["description","link"]
        #header = header[0:-1] + ["Link to results"]
        for line in fd:
            aline = line.replace("\n", "").split("\t")
            media_path = aline[-1].replace(MEDIA_ROOT,MEDIA_URL)
            link = media_path
            aline = aline[:-1] + [link]
            # aline = aline[:-1] + ['<a href="'+link+'" class="btn btn-primary btn-sm" role="button" aria-pressed="true">Go to results</a>']
            yield General(header, *aline)
        fd.close()