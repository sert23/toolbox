fh = open("annotation.txt","r")
lines = fh.readlines()
detected = {}
for line in lines:
    f = line.split()
    if line in detected:
#        print("duplicated "+line)
        continue
    elif "tRNA" in line:
        detected[line]=""
    else:
        print(line)

