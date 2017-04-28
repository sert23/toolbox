__author__ = 'antonior'

import pywatch
import time

while True:
    f = file("/home/antonior/hola.txt")
    for line in f.readlines():
        print line
    f.close()
    time.sleep(5)