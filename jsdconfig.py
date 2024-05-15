from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class JSDConfig:
    def __init__(self, filename='jsdconfig.yaml'):
        stream = open(filename, 'r')
        self.data = load(stream, Loader=Loader)

        # print(dump(self.data))
