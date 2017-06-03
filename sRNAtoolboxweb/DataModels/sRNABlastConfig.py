import json

__author__ = 'antonior'


class SRNABlastConfig():
    def __init__(self, blastDB, blastn, output, dbPath, input, minRC, maxReads, minEvalue, adapter=None, recursiveAdapterTrimming="false",
                 adapterMinLength=None, adapterMM=None, guessAdapter=False, local=False):

        self.minEvalue = minEvalue
        self.maxReads = maxReads
        self.input = input
        self.blastn = blastn
        self.blastDB = blastDB
        self.recursiveAdapterTrimming = recursiveAdapterTrimming
        self.guessAdapter = guessAdapter
        self.dbPath = dbPath
        self.output = output
        self.adapterMinLength = adapterMinLength
        self.adapterMM = adapterMM
        self.minRC = minRC

        if guessAdapter == "true":
            self.guessAdapter = guessAdapter
        else:
            self.adapter = adapter

        if local == "true":
            self.local = local


    def write_conf_file(self, config_file_name):

        fdw = file(config_file_name, "w")

        none_atr = [key for key in self.__dict__.keys() if self.__dict__[key] is None]
        for atr in none_atr:
            delattr(self, atr)

        for attr in self.__dict__:
            if attr == "species" or attr == "assembly":
                fdw.write(attr + "=" + ":".join(self.__dict__[attr]) + "\n")
            elif attr != "libs" and attr != "desc":
                fdw.write(attr + "=" + self.__dict__[attr] + "\n")
            else:
                for value in self.__dict__[attr]:
                    fdw.write(attr + "=" + value + "\n")

        fdw.close()