__author__ = 'antonior'

import os




class General():
    def __init__(self, input_header):
        self.input_header=input_header
    # def __init__(self, **kwargs):
    #     for attr in kwargs.keys():
    #         if kwargs.get(attr) is not None:
    #             self.__dict__[attr] = kwargs[attr]


    def get_sorted_attr(self):
        return [self.input_header]

