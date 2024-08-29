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

from dataclasses import dataclass, field

from yaml import dump, load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


@dataclass
class JSDConfig:
    """
    The JSDConfig class loads and stores data from a YAML file.

    Attributes:
        filename (str): The name of the YAML file to load. Default is 'jsdconfig.yaml'.
        data (dict): The loaded data from the YAML file.

    Methods:
        __init__(self, filename='jsdconfig.yaml'): Initializes a new instance of JSDConfig.
        __post_init__(self): Loads the YAML data from the current filename.
        set_filename(self, new_filename: str): Sets a new filename and reloads the data.
    """
    filename: str = 'jsdconfig.yaml'
    data: dict = field(init=False)

    def __post_init__(self):
        self._load_data()

    def _load_data(self):
        """Load the YAML data from the current filename."""
        with open(self.filename, 'r', encoding='utf-8') as stream:
            self.data = load(stream, Loader=Loader)
        # print(dump(self.data))

    def set_filename(self, new_filename: str):
        """Set a new filename and reload the data."""
        self.filename = new_filename
        self._load_data()
