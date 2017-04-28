__author__ = 'antonior'

def valid_mat_file_group(mat, groups):
    fd = file(mat)
    if len(fd.readline().split("\t"))-1 == len(groups):
        return True
    else:
        return "ERROR: Number of columns in matrix file and number of group description given are different. Please provided one group name per sample in matrix file"

