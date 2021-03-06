from __future__ import division
import os
import string


__author__ = 'antonior'

def make_dir(path):
    'It creates a directory if it does not exist'
    if not os.path.exists(path):
            os.makedirs(path)
    return


def istext(filename):
    s=open(filename).read(512)
    text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
    _null_trans = string.maketrans("", "")
    if not s:
        # Empty files are considered text
        return True
    if "\0" in s:
        # Files with null bytes are likely binary
        return False
    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = s.translate(_null_trans, text_characters)
    # If more than 30% non-text characters, then
    # this is considered a binary file
    if float(len(t))/float(len(s)) > 0.30:
        return False
    return True

def istabfile(filename):
    fd = open(filename)
    if len(fd.readline().split("\t")) > 1:
        return True
    else:
        return False

