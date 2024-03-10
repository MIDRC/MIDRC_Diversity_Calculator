import excelparse
import jsdview
import jsdmodel
from PySide6.QtCore import Qt, QObject
from dateutil.rrule import *
from datetime import date
import numpy as np
from scipy.spatial import distance


class JSDController(QObject):
    def __init__(self, jsd_view, jsd_model):
        super().__init__()
        self.jsd_view = jsd_view
        self.jsd_model = jsd_model
        self.fileChanged()

    def fileChanged(self):
        cbox0 = self.jsd_view.groupbox.file_comboboxes[0]
        categorylist = list(self.jsd_model.raw_data[cbox0.currentData()].sheets.keys())

        for cbox2 in self.jsd_view.groupbox.file_comboboxes[1:]:
            categorylist2 = self.jsd_model.raw_data[cbox2.currentData()].sheets.keys()
            categorylist = [value for value in categorylist if value in categorylist2]

        self.jsd_view.groupbox.category_combobox.clear()
        self.jsd_view.groupbox.category_combobox.addItems(categorylist)

        self.categoryChanged()

    def categoryChanged(self):
        cat = self.jsd_view.groupbox.category_combobox.currentText()
        # cbox0 = self.jsd_view.groupbox.file_comboboxes[0]

        # cols = self.jsd_model.raw_data[cbox0.currentData()].sheets[cat].columns.values()
        # We don't really care about the columns themselves, we just need to update the jsd plot
        data_vec = [0] * (2 * len(self.jsd_view.groupbox.file_comboboxes))
        for i in range(0, len(self.jsd_view.groupbox.file_comboboxes)):
            cbox1 = self.jsd_view.groupbox.file_comboboxes[i]
            df1 = self.jsd_model.raw_data[cbox1.currentData()].sheets[cat].df
            for cbox2 in self.jsd_view.groupbox.file_comboboxes[i+1:]:
                df2 = self.jsd_model.raw_data[cbox2.currentData()].sheets[cat].df
                #cols_to_use = df1.columns.intersection(df2.columns.values())
                #cols_to_use = cols_to_use[1:] # First column is date
                date_list = sorted(set(df1.date.values + df2.date.values))
                jsd_list = []
                for calcdate in date_list:
                    jsd = calcjsd(df1, df2, calcdate)
                    jsd_list.append(jsd)

                # TODO: Set the model values for the view


def calcjsd(df1, df2, calcdate):
    # Get the list of data columns for the specified sheet
    cols_to_use = df1.data_columns

    # find the row with the highest date below the date specified above
    df1_row = (np.searchsorted(df1.date.values, calcdate) - 1).clip(0)
    df2_row = (np.searchsorted(df2.date.values, calcdate) - 1).clip(0)

    # get the data for the rows and columns determined above
    df1_data = np.asarray(df1[cols_to_use].iloc[df1_row].values, dtype=float)
    df2_data = np.asarray(df2[cols_to_use].iloc[df2_row].values, dtype=float)

    return distance.jensenshannon(df1_data, df2_data, base=2.0)
