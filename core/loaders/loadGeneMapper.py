__author__ = 'antonior'

#from GbpaCommonLibs.FileModels.gene_info import GeneNcbi
import optparse
import os
import sys


def main():
#    ################################################

    #### Options and arguments #####################

    ################################################

    usage=""" python loadGeneMapper.py  --gene2refseqURL [url] --gene2ensemblURL [url] --refseq2uniprotURL [url] -o [json file] -t [tmp dir]"""
    parser = optparse.OptionParser(usage)

    #Example:

    parser.add_option("--gene2refseqURL", dest="gene2refseqURL", help="""Requiered. gene2refseq URL""")
    parser.add_option("--gene2ensemblURL", dest="gene2ensemblURL", help="""Requiered. gene2ensembl URL""")
    parser.add_option("--refseq2uniprotURL", dest="refseq2uniprotURL", help="""Requiered. refseq2uniprot URL""")
    parser.add_option("-o", dest="output", help="""Requiered. Output file""")
    parser.add_option("-t", dest="tmp", default="/tmp/", help="""Optional. temporal directory""")


    (options, args) = parser.parse_args(sys.argv)


    gene2refseq_sorted = os.path.join(options.tmp, "gene2refseq.sorted.txt")
    gene2ensembl_sorted = os.path.join(options.tmp, "gene2ensembl.sorted.txt")
    refseq2uniprot = os.path.join(options.tmp, "refseq2uniprot.txt")

    raw_gene2refseq = os.path.join(options.tmp, "gene2refseq.gz")
    raw_gene2ensembl = os.path.join(options.tmp, "gene2ensembl.gz")
    raw_refseq2uniprot = os.path.join(options.tmp, "refseq2uniprot.gz")


    os.system("wget -O "+raw_gene2refseq+" "+options.gene2refseqURL)
    os.system("gzip -d -c "+raw_gene2refseq+" | grep -v '#' | cut -f 1,2,4,5,6,7,16 | sort -k1,1n -k2,2n > "+gene2refseq_sorted)

    os.system("wget -O "+raw_gene2ensembl+" "+options.gene2ensemblURL)
    os.system("gzip -d -c "+raw_gene2ensembl+" | grep -v '#' | sort -k1,1n -k2,2n > "+gene2ensembl_sorted)

    os.system("wget -O "+raw_refseq2uniprot+" "+options.refseq2uniprotURL)
    os.system("gzip -d -c "+raw_refseq2uniprot+" | grep -v '#'  > "+refseq2uniprot)

    new_import=GeneNcbi(gene2refseq_sorted,gene2ensembl_sorted,refseq2uniprot)
    new_import.integrate(options.output)

    os.system("mongoimport -d geneInfo -c accesions < "+options.output)


if __name__ == '__main__':
    main()





