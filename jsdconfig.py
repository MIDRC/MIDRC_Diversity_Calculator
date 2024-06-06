#  Copyright (c) 2024 Medical Imaging and Data Resource Center (MIDRC).
#
#      Licensed under the Apache License, Version 2.0 (the "License");
#      you may not use this file except in compliance with the License.
#      You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#      Unless required by applicable law or agreed to in writing, software
#      distributed under the License is distributed on an "AS IS" BASIS,
#      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#      See the License for the specific language governing permissions and
#      limitations under the License.
#

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
