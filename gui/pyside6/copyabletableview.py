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
This module contains a custom QTableView subclass that allows copying selected data to the clipboard.
"""

import csv
import io
from typing import List

from PySide6.QtCore import QDate, QEvent, QObject, Qt
from PySide6.QtGui import QGuiApplication, QKeySequence
from PySide6.QtWidgets import QTableView


class CopyableTableView(QTableView):
    """
    Custom QTableView subclass that allows copying selected data to the clipboard.
    """
    def __init__(self) -> None:
        """
        Initialize the CopyableTableView and install its event filter.
        """
        super().__init__()
        self.installEventFilter(self)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """
        Filter events to handle key presses for copying selection.

        Args:
            source (QObject): The source object.
            event (QEvent): The event to filter.

        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if event.type() == QEvent.KeyPress:
            if event == QKeySequence.Copy:
                self.copy_selection()
                return True
        return super().eventFilter(source, event)

    def copy_selection(self) -> None:
        """
        Copy the currently selected table data to the clipboard in a tab-delimited format.

        Returns:
            None
        """
        selection = self.selectedIndexes()
        if selection:
            rows: List[int] = sorted(index.row() for index in selection)
            columns: List[int] = sorted(index.column() for index in selection)
            rowcount: int = rows[-1] - rows[0] + 1
            colcount: int = columns[-1] - columns[0] + 1
            table: List[List[str]] = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                index_data = index.data()
                if isinstance(index_data, QDate):
                    index_data = index_data.toString(format=Qt.ISODate)
                table[row][column] = str(index_data)
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            QGuiApplication.clipboard().setText(stream.getvalue())
