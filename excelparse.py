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

import pandas as pd


def excelparse(filename, sheet_name):
    """
    Parse a spreadsheet using the filename and sheet name specified and return a pandas dataframe

    :param string filename: filename to open
    :param string sheet_name: sheet name to parse
    :return: pandas dataframe
    """

    # This opens the file and creates a list of sheet names, along with necessary readers
    xls = pd.ExcelFile(filename)

    # This reads all Excel sheets, probably not worth it
    # df_map = pd.read_excel(xls)

    # This reads in the specified worksheet
    df = xls.parse(sheet_name=sheet_name, usecols=lambda x: '(%)' not in str(x), engine='openpyxl')

    # Find the columns that are percentages of the total distribution
    # pct_cols = [col for col in df.columns if '(%)' in col]

    # return df[['date'] + pct_cols]
    return df
