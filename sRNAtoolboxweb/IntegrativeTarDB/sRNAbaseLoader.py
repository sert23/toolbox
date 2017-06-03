__author__ = 'antonior'


from utils.mongoDB import mongoDB

class Loader():

    def __init__(self,con,table):
        if isinstance(con, mongoDB):
            self.con=con
            self.table=table
        else:
            print "con must be a conector object"
            return None

    def insert(self,miRNAtargetObj):
        self.con.insert_doc(self.table,miRNAtargetObj.write_json())

    def update(self,miRNAtargetObj):

        #This fisrt query, this query could be slow if miRNA is new,
        # if you are sure this miRNA is not on DB use insert instead.
        data=miRNAtargetObj
        result=self.con.findOne(self.table,{"miRNAname":data.miRNAname})

        #If miRNA does not exist in DB, insert it
        if result is None:
            self.insert(data)

        #If miRNA exists but not with this target push it into the array target

        else:
            for target in data.targets:
                if target.uniprot not in [targets["uniprot"] for targets in result["targets"]]:
                    self.con.update(self.table, {"miRNAname": data.miRNAname}, target.write_json("UpdateGene"))

                #If miRNA exists with this target update source specific fields
                else:
                    self.con.update(self.table, {"miRNAname": data.miRNAname, "targets.uniprot": target.uniprot}, target.write_json("UpdateInfo"))





