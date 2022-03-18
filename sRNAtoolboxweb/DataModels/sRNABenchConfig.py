import json

__author__ = 'antonior'

class SRNABenchConfig():
    def __init__(self, annot_dic, dbPath, output, ifile, iszip="true", bedGraph="true",
                 writeGenomeDist="true", predict=None,  graphics="true", species=None, assembly=None, short_names=(), adapter=None,
                 recursiveAdapterTrimming = "false", libmode=False, nolib=False, microRNA=None, removeBarcode=None, adapterMinLength=None, adapterMM=None,
                 seed=None, noMM=None, alignType=None, minRC=None, solid=None, guessAdapter=False, highconf=False, mirDB=False,
                 homolog=None, user_files=None, minReadLength="15", mBowtie="10", **kwargs):
        for attr in kwargs.keys():
            if kwargs.get(attr) is not None:
                self.__dict__[attr] = kwargs[attr]

        self.mBowtie = mBowtie
        self.minReadLength = minReadLength
        self.recursiveAdapterTrimming = recursiveAdapterTrimming
        self.guessAdapter = guessAdapter
        self.zip = iszip
        #self.RNAfold = RNAfold
        self.dbPath = dbPath
        self.output = output
        self.input = ifile
        self.bedGraph = bedGraph
        self.writeGenomeDist = writeGenomeDist
        if predict == "true":
            self.predict = predict
        self.graphics = graphics
        self.maintainOrig = "true"
        self.species = species
        self.microRNA = microRNA
        self.removeBarcode = removeBarcode
        self.adapterMinLength = adapterMinLength
        self.adapterMM = adapterMM
        self.seed = seed
        self.noMM = noMM
        self.alignType = alignType
        self.minRC = minRC
        self.homolog = homolog


        self.libs = []

        if user_files:
            self.libs += user_files

        self.libsStringTypes = "mature#sense;hairpin#sense"
        self.libsStringNames = "microRNA_sense"
        if assembly is not None:
            self.assembly = assembly

            if libmode:
                annotation_keys = short_names
            else:
                annotation_keys = self.assembly

            for assemb in annotation_keys:
                if assemb in annot_dic:
                    if "libs" in annot_dic[assemb]:
                        self.libs = annot_dic[assemb]["libs"]
                        #print(annot_dic[assemb]["libs"])
                    if "desc" in annot_dic[assemb]:
                        self.desc = annot_dic[assemb]["desc"]
                    if "libsStringTypes" in annot_dic[assemb]:
                        self.libsStringTypes = annot_dic[assemb]["libsStringTypes"][0]
                    if "libsStringNames" in annot_dic[assemb]:
                        self.libsStringNames = annot_dic[assemb]["libsStringNames"][0]
                    if "kingdom" in annot_dic[assemb]:
                        self.kingdom = annot_dic[assemb]["kingdom"][0]
                    if "tRNA" in annot_dic[assemb]:
                        self.tRNA = '{}.fa'.format(annot_dic[assemb]["tRNA"][0])
            if nolib:
                delattr(self, "libs")
            if libmode:
                delattr(self, "species")
                delattr(self, "assembly")
                # delattr(self, "libsStringTypes")
                # delattr(self, "libsStringNames")

        self.solid = solid

        if guessAdapter == "true":
            self.guessAdapter = guessAdapter
        else:
            self.adapter = adapter

        if highconf:
            self.mature = "high_conf_mature.fa"
            self.hairpin = "high_conf_hairpin.fa"
        if mirDB:
            self.mature = "mature_MGDB.fa"
            self.hairpin = "hairpin_MGDB.fa"
            self.microRNA = mirDB

        if self.microRNA and self.microRNA != "":
            self.isoMiR = "true"
            self.plotMiR = "true"

    def write_conf_file(self, config_file_name):

        fdw = open(config_file_name, "w")

        none_atr = [key for key in self.__dict__.keys() if self.__dict__[key] is None]
        for atr in none_atr:
            delattr(self, atr)

        if self.__dict__.get("assembly"):
            delattr(self,"assembly")
        for attr in self.__dict__:
            if attr == "assembly":
                continue
            if attr == "species" :
                if self.__dict__.get(attr):
                    fdw.write("species" + "=" + ":".join(self.__dict__[attr]) + "\n")
            elif attr != "libs" and attr != "desc":
                #print(attr)
                fdw.write(attr + "=" + str(self.__dict__[attr]) + "\n")
            else:
                for value in self.__dict__[attr]:
                    fdw.write(attr + "=" + value + "\n")

        fdw.close()

# class SRNABenchConfig():
#     def __init__(self, annot_dic, dbPath, output, ifile, iszip="true", bedGraph="true",
#                  writeGenomeDist="true", predict=None,  graphics="true", species=None, assembly=None, short_names=(), adapter=None,
#                  recursiveAdapterTrimming = "false", libmode=False, nolib=False, microRNA=None, removeBarcode=None, adapterMinLength=None, adapterMM=None,
#                  seed=None, noMM=None, alignType=None, minRC=None, solid=None, guessAdapter=False, highconf=False, mirDB=False,
#                  homolog=None, user_files=None, minReadLength="15", mBowtie="10"):
#
#         self.mBowtie = mBowtie
#         self.minReadLength = minReadLength
#         self.recursiveAdapterTrimming = recursiveAdapterTrimming
#         self.guessAdapter = guessAdapter
#         self.zip = iszip
#         #self.RNAfold = RNAfold
#         self.dbPath = dbPath
#         self.output = output
#         self.input = ifile
#         self.bedGraph = bedGraph
#         self.writeGenomeDist = writeGenomeDist
#         if predict == "true":
#             self.predict = predict
#         self.graphics = graphics
#         self.maintainOrig = "true"
#
#         self.species = species
#         self.microRNA = microRNA
#         self.removeBarcode = removeBarcode
#         self.adapterMinLength = adapterMinLength
#         self.adapterMM = adapterMM
#         self.seed = seed
#         self.noMM = noMM
#         self.alignType = alignType
#         self.minRC = minRC
#         self.homolog = homolog
#
#
#         self.libs = []
#
#         if user_files:
#             self.libs += user_files
#
#         if assembly is not None:
#             self.assembly = assembly
#
#             if libmode:
#                 annotation_keys = short_names
#             else:
#                 annotation_keys = self.assembly
#
#             for assemb in annotation_keys:
#                 if assemb in annot_dic:
#                     if "libs" in annot_dic[assemb]:
#                         self.libs = annot_dic[assemb]["libs"]
#                         #print(annot_dic[assemb]["libs"])
#                     if "desc" in annot_dic[assemb]:
#                         self.desc = annot_dic[assemb]["desc"]
#                     if "libsStringTypes" in annot_dic[assemb]:
#                         self.libsStringTypes = annot_dic[assemb]["libsStringTypes"][0]
#                     if "libsStringNames" in annot_dic[assemb]:
#                         self.libsStringNames = annot_dic[assemb]["libsStringNames"][0]
#                     if "kingdom" in annot_dic[assemb]:
#                         self.kingdom = annot_dic[assemb]["kingdom"][0]
#                     if "tRNA" in annot_dic[assemb]:
#                         self.tRNA = '{}.fa'.format(annot_dic[assemb]["tRNA"][0])
#             if nolib:
#                 delattr(self, "libs")
#             if libmode:
#                 delattr(self, "species")
#                 delattr(self, "assembly")
#                 # delattr(self, "libsStringTypes")
#                 # delattr(self, "libsStringNames")
#
#
#         self.solid = solid
#
#         if guessAdapter == "true":
#             self.guessAdapter = guessAdapter
#         else:
#             self.adapter = adapter
#
#         if highconf:
#             self.mature = "high_conf_mature.fa"
#             self.hairpin = "high_conf_hairpin.fa"
#         if mirDB:
#             self.mature = "mature_MGDB.fa"
#             self.hairpin = "hairpin_MGDB.fa"
#             self.microRNA = mirDB
#
#         if self.microRNA and self.microRNA != "":
#             self.isoMiR = "true"
#             self.plotMiR = "true"
#
#     def write_conf_file(self, config_file_name):
#
#         fdw = open(config_file_name, "w")
#
#         none_atr = [key for key in self.__dict__.keys() if self.__dict__[key] is None]
#         for atr in none_atr:
#             delattr(self, atr)
#
#         if self.__dict__.get("assembly"):
#             delattr(self,"assembly")
#         for attr in self.__dict__:
#             if attr == "assembly":
#                 continue
#             if attr == "species" :
#                 if self.__dict__.get(attr):
#                     fdw.write("species" + "=" + ":".join(self.__dict__[attr]) + "\n")
#             elif attr != "libs" and attr != "desc":
#                 #print(attr)
#                 fdw.write(attr + "=" + self.__dict__[attr] + "\n")
#             else:
#                 for value in self.__dict__[attr]:
#                     fdw.write(attr + "=" + value + "\n")
#
#         fdw.close()