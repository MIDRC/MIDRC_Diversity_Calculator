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
This module contains a function to process file uploads in a GUI application.
"""


def process_file_upload(view, data_source_dict):
    """
    Process a file upload by printing debug information,
    opening the file via the view and updating the layout.

    Args:
        view: An instance that implements open_excel_file and holds a
              data_selection_group_box attribute.
        data_source_dict (dict): Contains the uploaded file information.
    """
    print(f"handle_excel_file_uploaded() triggered with file: {data_source_dict['name']}")
    view.open_excel_file(data_source_dict)
    print("Excel file loaded, try to update layout")
    if hasattr(view, 'data_selection_group_box'):
        view.data_selection_group_box.update_filebox_layout(
            view.data_selection_group_box.num_fileboxes
        )
