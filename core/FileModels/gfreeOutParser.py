from DataModels.newmiRNA import MatureMiRNA, NewMiRNA

__author__ = 'antonior'


class GFreeOutParser():
    def __init__(self, info_file, micro_file):


        self.micro_file = micro_file
        self.info_file = info_file

    def parse(self):
        self.fd_info = open(self.info_file)
        self.fd_micro = open(self.micro_file)
        self.fd_micro.readline()
        self.fd_info.readline()
        all_matures = {}

        for line in self.fd_micro:
            mature = MatureMiRNA(*line.replace("\n", "").split("\t"))
            all_matures[mature.name] = mature

        for line in self.fd_info:

            micro = NewMiRNA(*line.replace("\n", "").split("\t"))
            for mature_name in all_matures:
                if micro.name == mature_name[:-3]:
                    micro.matures.append(all_matures[mature_name])
            yield micro




