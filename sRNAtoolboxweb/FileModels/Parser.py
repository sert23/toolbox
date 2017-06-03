from abc import ABCMeta, abstractmethod

__author__ = 'antonior'


class Parser():
    __metaclass__ = ABCMeta


    def __init__(self, ipath):
        self.ipath = ipath


    @abstractmethod
    def parse(self):
        pass