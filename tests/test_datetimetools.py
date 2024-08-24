import numpy as np
import pandas as pd
from PySide6.QtCore import QDate, QDateTime
import pytest

from datetimetools import convert_date_to_milliseconds, numpy_datetime64_to_qdate, pandas_date_to_qdate


class TestConvertDateToMilliseconds:

    #  The function returns the correct number of milliseconds since epoch for a valid date input.
    def test_valid_date_input(self):
        # Arrange
        date = QDate(2022, 1, 1)

        # Act
        result = convert_date_to_milliseconds(date)

        # Assert
        assert isinstance(result, int)
        assert result == 1640995200000

    #  The function returns the correct number of milliseconds since epoch for the earliest valid date input.
    def test_earliest_valid_date_input(self):
        # Arrange
        date = QDate(1, 1, 1)

        # Act
        result = convert_date_to_milliseconds(date)

        # Assert
        assert isinstance(result, int)
        assert result == -62135596800000

    #  The function returns the correct number of milliseconds since epoch for the latest valid date input.
    def test_latest_valid_date_input(self):
        # Arrange
        date = QDate(9999, 12, 31)

        # Act
        result = convert_date_to_milliseconds(date)

        # Assert
        assert isinstance(result, int)
        assert result == 253402214400000

    #  The function returns the correct number of milliseconds since epoch for a date input with a time component.
    def test_date_input_with_time_component(self):
        # Arrange
        date = QDateTime(2022, 1, 1, 12, 30, 45).date()

        # Act
        result = convert_date_to_milliseconds(date)

        # Assert
        assert isinstance(result, int)
        assert result == 1640995200000

    #  The function raises a TypeError if the input is not a valid date.
    def test_invalid_date_input(self):
        # Arrange
        date = "2022-01-01"

        # Act and Assert
        with pytest.raises(TypeError):
            convert_date_to_milliseconds(date)

    #  The function returns the correct number of milliseconds since epoch for the earliest possible
    #  date input (January 1, 1).
    def test_earliest_possible_date_input(self):
        # Arrange
        date = QDate(1, 1, 1)

        # Act
        result = convert_date_to_milliseconds(date)

        # Assert
        assert isinstance(result, int)
        assert result == -62135596800000

    #  The function returns the correct number of milliseconds since epoch for the latest possible
    #  date input (December 31, 9999).
    def test_latest_possible_date_input(self):
        # Arrange
        date = QDate(9999, 12, 31)

        # Act
        result = convert_date_to_milliseconds(date)

        # Assert
        assert isinstance(result, int)
        assert result == 253402214400000

    #  The function returns the correct number of milliseconds since epoch for a date input with the
    #  maximum allowed year (9999).
    def test_date_input_with_maximum_year(self):
        # Arrange
        date = QDate(9999, 1, 1)

        # Act
        result = convert_date_to_milliseconds(date)

        # Assert
        assert isinstance(result, int)
        assert result == 253370764800000


class TestPandasDateToQdate:

    #  Should convert a pandas Timestamp object to a QDate object with the same year, month, and day
    def test_convert_timestamp_to_qdate(self):
        # Arrange
        timestamp = pd.Timestamp('2022-01-01')

        # Act
        result = pandas_date_to_qdate(timestamp)

        # Assert
        assert result.year() == 2022
        assert result.month() == 1
        assert result.day() == 1

    #  Should convert a pandas datetime object to a QDate object with the same year, month, and day
    def test_convert_datetime_to_qdate(self):
        # Arrange
        datetime = pd.to_datetime('2022-01-01')

        # Act
        result = pandas_date_to_qdate(datetime)

        # Assert
        assert result.year() == 2022
        assert result.month() == 1
        assert result.day() == 1

    #  Should convert a numpy datetime64 object to a QDate object with the same year, month, and day
    def test_convert_numpy_datetime_to_qdate(self):
        # Arrange
        numpy_datetime = np.datetime64('2022-01-01')

        # Act
        result = pandas_date_to_qdate(numpy_datetime)

        # Assert
        assert result.year() == 2022
        assert result.month() == 1
        assert result.day() == 1

    #  Should return a QDate object for a valid input
    def test_return_qdate_for_valid_input(self):
        # Arrange
        valid_input = pd.Timestamp('2022-01-01')

        # Act
        result = pandas_date_to_qdate(valid_input)

        # Assert
        assert isinstance(result, QDate)

    #  Should handle a pandas Timestamp object with year=1
    def test_handle_timestamp_with_year_1(self):
        # Arrange
        timestamp = pd.Timestamp('0001-01-01')

        # Act
        result = pandas_date_to_qdate(timestamp)

        # Assert
        assert result.year() == 1
        assert result.month() == 1
        assert result.day() == 1

    #  Should handle a pandas Timestamp object with year=9999
    def test_handle_timestamp_with_year_9999(self):
        # Arrange
        timestamp = pd.Timestamp('9999-01-01')

        # Act
        result = pandas_date_to_qdate(timestamp)

        # Assert
        assert result.year() == 9999
        assert result.month() == 1
        assert result.day() == 1

    #  Should handle a pandas datetime object with minimum pd.Timestamp
    def test_handle_datetime_at_min(self):
        # Arrange
        datetime = pd.Timestamp.min

        # Act
        result = pandas_date_to_qdate(datetime)

        # Assert
        assert result.year() == 1677
        assert result.month() == 9
        assert result.day() == 21

    #  Should handle a pandas datetime object with maximum pd.Timestamp
    def test_handle_datetime_with_year_9999(self):
        # Arrange
        datetime = pd.Timestamp.max

        # Act
        result = pandas_date_to_qdate(datetime)

        # Assert
        assert result.year() == 2262
        assert result.month() == 4
        assert result.day() == 11


class TestNumpyDatetime64ToQdate:

    #  Should convert a numpy datetime64 object to a QDate object
    def test_convert_numpy_datetime_to_qdate(self):
        numpy_datetime = np.datetime64('2022-01-01')
        expected_qdate = QDate(2022, 1, 1)

        result = numpy_datetime64_to_qdate(numpy_datetime)

        assert result == expected_qdate

    #  Should handle numpy datetime64 objects with year 1 correctly
    def test_handle_numpy_datetime_with_year_1(self):
        numpy_datetime = np.datetime64('0001-01-01')
        expected_qdate = QDate(1, 1, 1)

        result = numpy_datetime64_to_qdate(numpy_datetime)

        assert result == expected_qdate

    #  Should handle numpy datetime64 objects with year 9999 correctly
    def test_handle_numpy_datetime_with_year_9999(self):
        numpy_datetime = np.datetime64('9999-01-01')
        expected_qdate = QDate(9999, 1, 1)

        result = numpy_datetime64_to_qdate(numpy_datetime)

        assert result == expected_qdate

    #  Should handle numpy datetime64 objects with month 1 correctly
    def test_handle_numpy_datetime_with_month_1(self):
        numpy_datetime = np.datetime64('2022-01-01')
        expected_qdate = QDate(2022, 1, 1)

        result = numpy_datetime64_to_qdate(numpy_datetime)

        assert result == expected_qdate
