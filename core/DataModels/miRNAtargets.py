__author__ = 'antonior'
import json
import ast
import copy


class MirnaTarget ():

    def __init__(self, mirna_name, targets):

        self.miRNAname = mirna_name

        if isinstance(targets, Target):
            self.targets = [targets]

        elif type(self.targets) == list:
            self.targets = targets


    def __str__(self):

        miRNAtargets_array=[self.miRNAname,",".join(self.targets.source),",".join(self.targets.source),",".join(self.targets.source),",".join(self.targets.source)]


        return "\t".join(miRNAtargets_array)+"\n"


    def write_json(self):
        """
        :return: Object in jsonFormat
        """
        return ast.literal_eval(json.dumps(self,cls=MirnaTargetEncoded))

class Target ():

    def __init__(self,  source, validation_experiments, validation_status, genename, bibliography=[], comments=[]):

        self.uniprot = genename

        if type(validation_status) == list:
            self.validation_status = validation_status
        else:
            self.validation_status = [validation_status]

        if type(validation_experiments) == list:
            self.validation_experiments = validation_experiments
        else:
            self.validation_experiments = [validation_experiments]

        if type(source) == list:
            self.source = source
        else:
            self.source = [source]

        if type(bibliography) == list:
            self.bibliography = bibliography
        else:
            self.bibliography = [bibliography]

        if type(comments) == list:
            self.comments = comments
        else:
            self.comments = [comments]

    def write_json(self, typeofjson):
        """
        :return: Object in jsonFormat
        """
        if typeofjson == "UpdateGene":
            return ast.literal_eval(json.dumps(self,cls=TargetEncodedUpdateGene))
        if typeofjson == "UpdateInfo":
            return ast.literal_eval(json.dumps(self,cls=TargetEncodedUpdateGeneInfo))





#Accesories function to override json.dump method (used to make update easier)



class MirnaTargetEncoded (json.JSONEncoder):

    def default(self, obj):

        #check correct object Type
        if isinstance(obj, MirnaTarget):
            newObj=copy.deepcopy(obj)
            for i, target in enumerate(newObj.targets):

                if newObj.targets[i].bibliography == []:
                    delattr(newObj.targets[i], "bibliography")

                if newObj.targets[i].comments == []:
                    delattr(newObj.targets[i], "comments")

                newObj.targets[i] = target.__dict__

            return newObj.__dict__

        else:
            return "TypeError: Please provide and object of type MirnaTarget"


class TargetEncodedUpdateGene (json.JSONEncoder):

    def default(self, obj):

        #check correct object Type
        if isinstance(obj, Target):
            return {"$push": {"targets": obj.__dict__}}
        else:
            return "TypeError: Please provide and object of type Target"


class TargetEncodedUpdateGeneInfo(json.JSONEncoder):

    def default(self, obj):

        #check correct object Type
        if isinstance(obj, Target):
            return {"$addToSet": {"targets.$.source": {"$each": obj.source},
                                 "targets.$.validation_status": {"$each": obj.validation_status},
                                 "targets.$.validation_experiments": {"$each": obj.validation_experiments},
                                 "targets.$.bibliography": {"$each": obj.bibliography},
                                 "targets.$.comments": {"$each": obj.comments}}}

        else:
            return "TypeError: Please provide and object of type MirnaTarget"






















