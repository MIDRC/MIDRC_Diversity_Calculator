#  Copyright (c) 2025 Medical Imaging and Data Resource Center (MIDRC).
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

"""
This module contains utility functions for file handling and data processing.
"""


def create_file_info(data_source, index):
    """
    Create a file info dictionary from a data source.

    Args:
        data_source (dict): Dictionary containing file info.
        index (int): The index to assign.

    Returns:
        dict: A dictionary with description, source_id, index and checked flag.
    """
    return {
        'description': data_source.get('description'),
        'source_id': data_source.get('name'),
        'index': index,
        'checked': True,
    }


def get_common_categories(file_infos, jsd_model):
    """
    Extract common categories from file information.

    Args:
        file_infos (list): List of file information dictionaries.
        jsd_model: Model containing data_sources.

    Returns:
        list: A list of common category keys.
    """
    if not file_infos:
        return []

    # Get the initial set of categories from the first file info.
    cbox0 = file_infos[0]
    common_categories = list(jsd_model.data_sources[cbox0['source_id']].sheets.keys())

    # Intersect with the categories from subsequent file infos.
    for cbox in file_infos[1:]:
        categorylist = jsd_model.data_sources[cbox['source_id']].sheets.keys()
        common_categories = [value for value in common_categories if value in categorylist]

    return common_categories


def create_data_source_dict(filename, file_content, data_type='content', content_type=None):
    """
    Create a data source dictionary.

    Args:
        filename (str): The file name.
        file_content (BytesIO): The file content.
        data_type (str, optional): The data type label. Defaults to 'content'.
        content_type (str, optional): The content type. Defaults to None.

    Returns:
        dict: A dictionary with file details.
    """
    return {
        'description': filename,
        'name': filename,
        'content': file_content,
        'data type': data_type,
        'content type': content_type,
    }
