__author__ = 'antonior'

import os




class General():
    def __init__(self, *args):
        self.input_header=[*args]
    # def __init__(self, **kwargs):
    #     for attr in kwargs.keys():
    #         if kwargs.get(attr) is not None:
    #             self.__dict__[attr] = kwargs[attr]


    def get_sorted_attr(self):
        return self.input_header

