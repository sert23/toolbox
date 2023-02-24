#!/usr/bin/python3

import argparse, os, os.path, time, shutil, csv

parser = argparse.ArgumentParser(description='sRNAtoolbox webdata deleter')
parser.add_argument('--webdata','-w', type=str, metavar='/path/to/webdata', required=True, help='webdata path')
parser.add_argument('--pdirs','-p', type=str, metavar='/path/to/protected.txt', required=True, help='text file containing a list of protected directories')
parser.add_argument('--edays', '-e', type=int, metavar='N' ,default=15, help='delete directories modified N days ago or more')
args = parser.parse_args()

wd = args.webdata
threshold = args.edays
protected = list()

def protectedList(fpath, dlist):
	with open(fpath, 'rt') as r:
		[dlist.append(line.strip()) for line in r if all([line.strip() != '', not line.startswith("#")])]

def log(infoList,logFile):
	if not os.path.exists(logFile):
		with open(logFile,"wt") as outFile:
			writer = csv.writer(outFile, delimiter='\t', quotechar='', quoting=csv.QUOTE_NONE)
			writer.writerow(["#path","size (MB)", "modified date", "date removed"])
			[writer.writerow(data[:-1]) for data in infoList if data[-1]]
	else:
		with open(logFile,"at") as outFile:
			writer = csv.writer(outFile, delimiter='\t', quotechar='', quoting=csv.QUOTE_NONE)
			[writer.writerow(data[:-1]) for data in infoList if data[-1]]

class wdDir():
	def __init__(self,name,mdate,ignore):
		self.name = name
		self.mdate = mdate
		self.edays = int((time.time() - mdate) / 86400)
		self.ignore = ignore
	def getDirSize(self):
		dirsize = 0
		for root,dirs,files in os.walk(self.name):
			for f in files:
				filepath = os.path.join(root,f)
				dirsize += os.path.getsize(filepath)
		dirsize = round(dirsize/1048576.0, 2)
		return dirsize
	def remove(self):
		loginfo = [self.name,self.getDirSize(),time.ctime(self.mdate),time.ctime(time.time()),False]
		if all([not self.ignore, self.edays >= threshold, self.name != wd]):
			shutil.rmtree(self.name, ignore_errors = True)
			loginfo[-1] = True
		else:
			pass
		return loginfo
	def __str__(self):
		return self.name

def main():
	wdDict = dict()
	for root,dirs,files in os.walk(wd):
		for f in files:
			if root != wd:
				name = root.replace(wd,"").split("/")[1]
				path = os.path.join(root,f)
				mdate = os.path.getmtime(path)
				ignore = True
				if not name in protected:
					ignore = False
				else:
					pass
				name = os.path.join(wd,root.replace(wd,"").split("/")[1])
				wdObj = wdDir(name,mdate,ignore)
				if not name in wdDict:
					wdDict[name] = wdObj
				else:
					dstored = wdDict[name].edays
					cdate = wdObj.edays
					if cdate < dstored:
						wdDict[name] = wdObj
					else:
						pass
	infoList = [wdDict[wdObj].remove() for wdObj in wdDict]
	os.system("find {} -empty -type d -delete".format(wd))
	logFile = os.path.join(wd,"log.txt")
	log(infoList,logFile)
	
if __name__ == '__main__':
	protectedList(args.pdirs, protected)
	main()
