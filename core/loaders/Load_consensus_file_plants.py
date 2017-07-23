import json
from core_utils.mongoDB import mongoDB

__author__ = 'antonior'

import sys

fd = open(sys.argv[1])
sp = sys.argv[2]
cds_utr = sys.argv[3]
fdw = open(sys.argv[4], "w")

db_uniprot = mongoDB("localhost", "Uniprots")

for line in fd:
    aline = line.rstrip("\n").split("\t")
    sources = aline[3].replace("[", "").replace("]", "").replace(" ","").split(",")
    gene = aline[1]

    

    query = {"_id": gene}
    results = db_uniprot.findOne("Uniprot_mapping", query)
    if results is not None:
        uniprot = results["uniprot"]
        fdw.write(json.dumps({"miRNAname": aline[0], "sources": sources, "transcripts": uniprot, "number": int(aline[2]), "species": sp, "mode": cds_utr}) + "\n")
    else:
        query = {"_id": ".".join(gene.split(".")[:-1])}
        results = db_uniprot.findOne("Uniprot_mapping", query)
        if results is not None:
            uniprot = results["uniprot"]
            fdw.write(json.dumps({"miRNAname": aline[0], "sources": sources, "transcripts": uniprot, "number": int(aline[2]), "species": sp, "mode": cds_utr}) + "\n")


