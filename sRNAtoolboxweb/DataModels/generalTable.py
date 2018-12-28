__author__ = 'antonior'


class General(object):
    def __init__(self, input_header, *args):
        self.input_header = input_header
        for name, arg in zip(self.input_header, args):
            self.__dict__[name] = arg

    def get_sorted_attr(self):
        return self.input_header

