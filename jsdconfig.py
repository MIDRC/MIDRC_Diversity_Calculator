from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class JSDConfig:
    """
    The JSDConfig class is used to load and store data from a YAML file.

    Attributes:
        filename (str): The name of the YAML file to load. Default is 'jsdconfig.yaml'.
        data (dict): The loaded data from the YAML file.

    Methods:
        __init__(self, filename='jsdconfig.yaml'): Initializes a new instance of the JSDConfig class.
    """
    def __init__(self, filename='jsdconfig.yaml'):
        stream = open(filename, 'r')
        self.data = load(stream, Loader=Loader)

        # print(dump(self.data))
