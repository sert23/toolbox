

from DataModels.jBrowserBed import JBrowserBed
from FileModels.Parser import Parser
import mmap
import os
__author__ = 'antonior'

class JBrowserParser(Parser):

    def parse(self):
        fd = open(self.ipath)

        for line in fd:
            aline = line.replace("\n", "").split("\t")
            print (aline)
            new_bed = JBrowserBed(*aline)
            yield new_bed

    def get_firsts(self, n):

        fd = open(self.ipath)

        for i, line in enumerate(fd):
            aline = line.replace("\n", "").split("\t")
            new_bed = JBrowserBed(*aline)
            if i < n:
                yield new_bed
            else:
                break

    def get_tail(self, n):
        """Returns last n lines from the filename. No exception handling"""
        size = os.path.getsize(self.ipath)
        with open(self.ipath, "rb") as f:
            # for Windows the mmap parameters are different
            fm = mmap.mmap(f.fileno(), 0, mmap.MAP_SHARED, mmap.PROT_READ)
            try:
                for i in xrange(size - 1, -1, -1):
                    if fm[i] == '\n':
                        n -= 1
                        if n == -1:
                            break
                for line in fm[i + 1 if i else 0:].splitlines():
                    aline = line.replace("\n", "").split("\t")
                    new_bed = JBrowserBed(*aline)
                    yield new_bed

            finally:
                fm.close()
