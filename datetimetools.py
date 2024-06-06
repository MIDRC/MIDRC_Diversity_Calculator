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

from PySide6.QtCore import QDateTime, QTime, QDate, QTimeZone
import pandas as pd
import numpy as np


def convert_date_to_milliseconds(date):
    """
    Converts a date to milliseconds since epoch.
    """
    if date is None:
        return None
    return QDateTime(date, QTime(), QTimeZone.utc()).toMSecsSinceEpoch()


def pandas_date_to_qdate(pandas_date):
    """
    Convert a pandas Timestamp or datetime object to a PySide2 QDate object.

    Parameters:
        pandas_date (pd.Timestamp or datetime64): Pandas Timestamp or datetime object.

    Returns:
        QDate: PySide2 QDate object representing the same date.
    """
    if isinstance(pandas_date, pd.Timestamp):
        return QDate(pandas_date.year, pandas_date.month, pandas_date.day)
    elif isinstance(pandas_date, np.datetime64):
        return numpy_datetime64_to_qdate(pandas_date)
    else:
        raise ValueError("Input must be a Pandas Timestamp or datetime object")


def numpy_datetime64_to_qdate(numpy_datetime):
    """
    Convert a NumPy datetime64 object to a PySide2 QDate object.

    Parameters:
        numpy_datetime (numpy.datetime64): NumPy datetime64 object.

    Returns:
        QDate: PySide2 QDate object representing the same date.
    """
    # Extract year, month, and day from numpy datetime64
    # year = np.datetime64(numpy_datetime, 'Y').astype(int)
    # month = np.datetime64(numpy_datetime, 'M').astype(int)
    # day = np.datetime64(numpy_datetime, 'D').astype(int)

    # Convert numpy datetime64 to Python datetime
    python_datetime = np.datetime64(numpy_datetime).astype('M8[D]').astype('O')

    # Extract year, month, and day from Python datetime
    year = python_datetime.year
    month = python_datetime.month
    day = python_datetime.day

    return QDate(year, month, day)
