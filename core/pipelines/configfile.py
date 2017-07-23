__author__ = 'antonior'
import json

# CONF = json.load(file("/shared/sRNAtoolbox/sRNAtoolbox.conf"))

targetAnnot = []
# targetAnnot = file(CONF["targetAnnotation"])
GO = {}
UTR_FILES = {}
for line in targetAnnot:
    aline = line.rstrip("\n").split("\t")
    GO[aline[0]] = aline[4]
    if aline[2] != "-" or aline[2] != "":
        UTR_FILES[aline[0]] = aline[2]
    else:
        UTR_FILES[aline[0]] = aline[1]