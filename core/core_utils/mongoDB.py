'''
Created on 11/04/2014

@author: antonior
'''

import json
import os
import pymongo
import progressbar


class mongoDB ():
    '''
    Class to manage mysql Ontology DBs
    '''


    def __init__(self, _host,db,port=27017):
        '''
        Constructor
        '''
        self.host=_host
        self.port=port
        self.client=pymongo.MongoClient(_host,port)
        self.db=self.client[db]
        self.dbname=db
        
    
    def insert_doc(self, table, doc):

        self.db[table].insert(doc)

    def ensure_index(self, table,doc_index):
        self.db[table].ensure_index(doc_index)
        
        
    def insert_table(self, _filename, tmp_jsonfile, table, columns_index,strict_str=None, header=None, sep='\t'):
        
        fd=open(_filename)
        line_count=len(fd.readlines())
        print(line_count)
        widgets = ["processing file: "+_filename, progressbar.Percentage(), ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=line_count).start()      
        
        fd=open(_filename)
        if header==None:
            header=fd.readline().replace("\n",'').split(sep) 

        
        i=0
        batch=fd.readlines(2097152)
        while batch!=[]:
            fdw=open(tmp_jsonfile,'w')
            batch_array=[]
            for line in batch:
                pbar.update(i+1)
                i=i+1
                aline=line.replace("\n",'').split(sep)
                reg={}
                for i,field in enumerate(aline):
                    if i+1 in columns_index:
                            
                        if i+1 in strict_str:
                            reg[header[i]]=field
                        else:
                            try:
                                reg[header[i]]=int(field)
                            except:
                                try:
                                    reg[header[i]]=float(field)
                                except:
                                    reg[header[i]]=field
                batch_array.append(reg)
            json.dump(batch_array, fdw)
            fdw.close()
            self.insert_doc(table,tmp_jsonfile)
            batch=fd.readlines(2097152)
        pbar.finish()
        
    
    def find(self, table, doc="", include=None):
        if include==None:
            for row in self.db[table].find(doc):
                yield row
        else:
            for row in self.db[table].find(doc, include):
                yield row
            
    
    def agregate(self, table, doc=""):
        
        cursor=self.db[table].aggregate(doc)
        return cursor
                
    
    def update(self, table, query, doc,multi=False, upsert=False):
        self.db[table].update(query,doc,multi=multi,upsert=upsert)

    def findOne(self, table, query, include=None):
        if include == None:
            return self.db[table].find_one(query)
        else:
            return self.db[table].find_one(query, include)



