import json

__author__ = 'antonior'
import sys

fd = file(sys.argv[1])
fdw = file(sys.argv[2], "w")

for line in fd:
    aline = line.rstrip("\n").split("\t")
    fdw.write(json.dumps({"uniprot": aline[0], "_id": aline[2]}) + "\n")

fd.close()


