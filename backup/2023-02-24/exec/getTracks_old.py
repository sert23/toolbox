import os,sys
import subprocess

def createTrackHub(templateDir,sampleDir):
	###Get genome and page

	dictFile = open(templateDir+"/speciesDict",'r')
	dictSpecies = {}
	for line in dictFile:
		line = line.strip().split(";")
		genome = line[0]
		assembly = line[1]
		page = line[2]
		dictSpecies[genome] = [assembly,page]

	configFile = open(sampleDir+"/conf.txt",'r')

	for line in configFile:
		if "species=" in line:
			line = line.strip().split(":")[0]
			line = line.strip().split("=")
			genome = line[1]
			try:
				[assembly,page] = dictSpecies[genome]
			except:
				assembly = genome
				page = "ensembl"

	##Get sampleName
	sampleName = sampleDir.split("/")[-1]

	###Create BigWigs

	fileBigWig = sampleDir+"/bigwig/"+genome

	filesDef = []
	names = []
	files = subprocess.check_output("ls "+sampleDir+"/bigwig/*bedGraph", shell=True).decode("utf-8").splitlines()
	for file in files:
		file = file.split(".bedGraph")[0]
		if "_F" in file:
			filesDef.append(file)
			name = file.split("/")[-1].split("_F")[0]
			names.append(name)
		elif "_R" in file:
			filesDef.append(file)

	##Sorting

	for file in filesDef:
		os.system("awk '{print \"chr\"$0}' "+file+".bedGraph >"+file+"_UCSC.bedGraph")
		if page == "ucsc":
			os.system("sort -k1,1 -k2,2n "+file+"_UCSC.bedGraph >"+file+"_sorted.bedGraph")
	seqFile = file.split("_mp")[0]+"_mp.seqLen"
	if page == "ucsc":
		seqFile = file.split("_mp")[0]+"_UCSC.seqLen"
		os.system("awk '{print \"chr\"$0}' "+file.split("_mp")[0]+"_mp.seqLen >"+seqFile)

	for file in filesDef:
		os.system(templateDir+"/bedGraphToBigWig "+file+"_sorted.bedGraph "+seqFile+" "+file+".bigWig")

	os.system("rm "+sampleDir+"/bigwig/*UCSC*")
	os.system("rm "+sampleDir+"/bigwig/*sorted*")


	###Create outDir
	os.system("mkdir "+sampleDir+"/bigwig/trackHub")

	###Create hub.txt
	os.system("touch "+sampleDir+"/bigwig/trackHub/hub.txt")
	outHub = open(sampleDir+"/bigwig/trackHub/hub.txt",'a')
	hubFile = open(templateDir+"/hub.txt",'r')
	for line in hubFile:
		line = line.replace("$sName",sampleName)
		outHub.write(line)


	###Create genomes.txt
	genomeFile = open(templateDir+"/genomes.txt",'r')
	os.system("touch "+sampleDir+"/bigwig/trackHub/genomes.txt")
	outGenome = open(sampleDir+"/bigwig/trackHub/genomes.txt",'a')
	for line in genomeFile:
		line = line.replace("$genome", assembly)
		outGenome.write(line)

	####Create trackDB.txt

	os.system("touch "+sampleDir+"/bigwig/trackHub/trackDb.txt")
	outTrack = open(sampleDir+"/bigwig/trackHub/trackDb.txt",'a')
	for name in names:
		nombre = name
		track = nombre.replace("mp_19-23","19-23").replace("mp_0-200","ALL")
		short = track.split("mp_")[-1].split("_")[-1]
		trackFile = open(templateDir+"/trackDb.txt",'r')
		for line in trackFile:
			line = line.replace("$short",short)
			line = line.replace("$track",track)
			line = line.replace("$name",nombre)
			line = line.replace("$sName",sampleName)
			line = line.replace("$genome",genome)
			line = line.replace("$sampleDir",sampleDir)
			outTrack.write(line)

	###Create link

	if page == "ensembl":
		enlace = "http://www.ensembl.org/Trackhub?url=https://alu.ugr.es/srnatoolbox/media/"+sampleName+"/bigwig/trackHub/hub.txt"
	elif page =="ucsc":
		enlace = "https://genome.ucsc.edu/cgi-bin/hgTracks?hubUrl=https://alu.ugr.es/srnatoolbox/media/"+sampleName+"/bigwig/trackHub/hub.txt&genome="+assembly
	print(enlace)

	###Create bed links

	for name in names:
		bedFile = open(sampleDir+"/bigwig/"+name+".bed",'r')
		bedLinks = open(sampleDir+"/bigwig/"+name+"_bedLinks",'a')
		for i in range (0,10):
			linea = bedFile.readline().split("\t")
			chrom = linea[0]
			start = linea[1]
			end = linea[2]
			if chrom.isdigit():
				chrom="chr"+chrom
			else:
				chrom = chrom.replace(".","v")
				chrom="chrUn_"+chrom
			lineaNueva = enlace+"&position="+chrom+"%3A"+start+"-"+end+"\n"
			bedLinks.write(lineaNueva)

createTrackHub(sys.argv[1],sys.argv[2])


