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
This module contains the JsdViewIPython class, which serves as a Jupyter Notebook view for JSD.
"""

from IPython.display import display
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PySide6.QtCore import QDate, Signal
import seaborn as sns

from midrc_react.core.jsdmodel import JSDTableModel
from midrc_react.gui.common.jsdview_base import JsdViewBase
from midrc_react.gui.common.plot_utils import create_stacked_area_figure, prepare_area_chart_data
from midrc_react.gui.ipython.dataselectiongroupbox import DataSelectionGroupBox


class JsdViewIPython(JsdViewBase):
    """Class: JsdViewIPython

    This class represents a Jupyter Notebook view for JSD. It provides functionality for creating a Jupyter Notebook
    app and handling file uploads. The class has methods for setting up the layout, updating the category combo box,
    and initializing the widget.
    """
    jsd_timeline_plot_update = Signal(JSDTableModel)

    def __init__(self, jsd_model):
        """
        Initialize the JsdViewIPython.

        This method sets up the data selection group box, the JSD timeline plot, and the area chart.

        Args:
            jsd_model (JSDTableModel): The JSDTableModel object.
        """
        super().__init__()
        self.update_view_on_controller_initialization = False

        self.plot_method = 'interactive_plotly'

        self.jsd_model = jsd_model
        self.output_timeline = widgets.Output()
        self.output_area_chart = widgets.Output()
        self._dataselectiongroupbox = DataSelectionGroupBox(jsd_model)

        self._dataselectiongroupbox.excel_file_uploaded.connect(self.open_excel_file)

    def open_excel_file(self, data_source_dict):
        """Open an Excel file and add it as a data source."""
        super().open_excel_file(data_source_dict)
        self.add_data_source.emit(data_source_dict)

    def update_jsd_timeline_plot(self, jsd_model):
        """Update the JSD timeline plot."""
        if self.plot_method == 'interactive_plotly':
            return self.update_jsd_timeline_plot_interactive_plotly(jsd_model)
        if self.plot_method == 'interactive_matlib':
            return self.update_jsd_timeline_plot_interactive(jsd_model)
        # Initialize plot_data to None for proper handling of the first iteration
        plot_data = None

        # Iterate over `column_infos` to get each pair as its own series
        for c, column_info in enumerate(jsd_model.column_infos):
            try:
                # Access every other column, as per your PySide6 logic
                col = c * 2
                date_column = jsd_model.input_data[col]
                value_column = jsd_model.input_data[col + 1]

                # Convert QDate to datetime strings if necessary
                if isinstance(date_column[0], QDate):
                    date_column = [date.toString("yyyy-MM-dd") for date in date_column]

                # Create a temporary DataFrame for the current series
                temp_data = pd.DataFrame({
                    'date': pd.to_datetime(date_column, format='%Y-%m-%d', errors='coerce'),
                    'value': value_column,
                    'label': f"{column_info['file1']} vs {column_info['file2']} {column_info['category']} JSD",
                })

                # Filter out rows with invalid date values (if any date failed to convert)
                temp_data.dropna(subset=['date'], inplace=True)

                # Handle the first iteration by directly assigning temp_data to plot_data
                if plot_data is None:
                    plot_data = temp_data
                else:
                    # Concatenate subsequent series
                    plot_data = pd.concat([plot_data, temp_data], ignore_index=True)

            except Exception as e:  # pylint: disable=W0718
                print(f"An error occurred while processing column info {column_info}: {e}")
                return None

        # Check if we have any data to plot
        if plot_data is None or plot_data.empty:
            print("No data available for plotting.")
            return None

        # Plotting using Seaborn
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=plot_data, x='date', y='value', hue='label', marker='o')
        plt.xlabel('Date')
        plt.ylabel('JSD Value')
        plt.title('JSD Timeline Chart')
        plt.grid(True)
        plt.legend(title='Data Sources', loc='upper right')

        # Set Y-axis limits
        plt.ylim(0.0, 1.0)

        # Display the plot in the Jupyter notebook
        with self.output_timeline:
            self.output_timeline.clear_output(wait=True)
            plt.show()
            plt.close()

        return None

    def update_jsd_timeline_plot_interactive(self, jsd_model):
        """Update the JSD timeline plot using interactive plotting."""
        print("Plotting interactive timeline chart using Matplotlib with ipympl...")

        # Initialize plot_data to None for proper handling of the first iteration
        plot_data = None

        # Iterate over `column_infos` to get each pair as its own series
        for c, column_info in enumerate(jsd_model.column_infos):
            try:
                # Access every other column, as per your PySide6 logic
                col = c * 2
                date_column = jsd_model.input_data[col]
                value_column = jsd_model.input_data[col + 1]

                # Convert QDate to datetime strings if necessary
                if isinstance(date_column[0], QDate):
                    date_column = [date.toString("yyyy-MM-dd") for date in date_column]

                # Create a temporary DataFrame for the current series
                temp_data = pd.DataFrame({
                    'date': pd.to_datetime(date_column, format='%Y-%m-%d', errors='coerce'),
                    'value': value_column,
                    'label': f"{column_info['file1']} vs {column_info['file2']} {column_info['category']} JSD",
                })

                # Filter out rows with invalid date values (if any date failed to convert)
                temp_data.dropna(subset=['date'], inplace=True)

                # Handle the first iteration by directly assigning temp_data to plot_data
                if plot_data is None:
                    plot_data = temp_data
                else:
                    # Concatenate subsequent series
                    plot_data = pd.concat([plot_data, temp_data], ignore_index=True)

            except Exception as e:  # pylint: disable=W0718
                print(f"An error occurred while processing column info {column_info}: {e}")
                return

        # Check if we have any data to plot
        if plot_data is None or plot_data.empty:
            print("No data available for plotting.")
            return

        # Create the interactive figure using ipympl
        with self.output_timeline:
            self.output_timeline.clear_output(wait=True)

            # Use the widget backend for interactive plotting
            _fig, ax = plt.subplots(figsize=(10, 6))

            # Plotting using Seaborn
            sns.lineplot(data=plot_data, x='date', y='value', hue='label', marker='o', ax=ax)

            # Set labels and title
            ax.set_xlabel('Date')
            ax.set_ylabel('JSD Value')
            ax.set_title('JSD Timeline Chart')

            # Set the y-axis limits as specified
            ax.set_ylim(0.0, 1.0)

            # Enable grid and legend
            ax.grid(True)
            ax.legend(title='Data Sources', loc='upper right')

            # Display the interactive figure
            plt.show()

        print("Interactive plotting complete.")

    def update_jsd_timeline_plot_interactive_plotly(self, jsd_model):
        """Update the JSD timeline plot using interactive plotting with Plotly."""
        # Initialize plot_data to None for proper handling of the first iteration
        plot_data = None
        plot_title_suffix = ""

        # Iterate over `column_infos` to get each pair as its own series
        for c, column_info in enumerate(jsd_model.column_infos):
            try:
                # Access every other column, as per your PySide6 logic
                col = c * 2
                date_column = jsd_model.input_data[col]
                value_column = jsd_model.input_data[col + 1]

                # Convert QDate to datetime strings if necessary
                if isinstance(date_column[0], QDate):
                    date_column = [date.toString("yyyy-MM-dd") for date in date_column]

                # Create a temporary DataFrame for the current series
                temp_data = pd.DataFrame({
                    'date': pd.to_datetime(date_column, format='%Y-%m-%d', errors='coerce'),
                    'value': value_column,
                    'label': f"{column_info['file1']} vs {column_info['file2']}",
                })

                # Set the plot title suffix to include category (same for all series)
                if not plot_title_suffix:
                    plot_title_suffix = f"{column_info['category']} JSD"

                # Filter out rows with invalid date values (if any date failed to convert)
                temp_data.dropna(subset=['date'], inplace=True)

                # Handle the first iteration by directly assigning temp_data to plot_data
                if plot_data is None:
                    plot_data = temp_data
                else:
                    # Concatenate subsequent series
                    plot_data = pd.concat([plot_data, temp_data], ignore_index=True)

            except Exception as e:  # pylint: disable=W0718
                print(f"An error occurred while processing column info {column_info}: {e}")
                return

        # Check if we have any data to plot
        if plot_data is None or plot_data.empty:
            print("No data available for plotting.")
            return

        # Plotting using Plotly Express for interactivity
        title = f"JSD Timeline Chart - {plot_title_suffix}"
        fig = px.line(
            plot_data,
            x='date',
            y='value',
            color='label',
            title=title,
            labels={'date': 'Date', 'value': 'JSD Value', 'label': 'Data Sources'},
            # height=600  # Set the height to make the plot taller
        )

        # Set Y-axis limits to 0.0 and 1.0
        fig.update_yaxes(range=[0.0, 1.0])

        fig_widget = go.FigureWidget(fig)
        vbox = widgets.VBox([fig_widget])

        # Clear previous output and display the plot inside `self.output_timeline`
        with self.output_timeline:
            self.output_timeline.clear_output(wait=True)
            display(vbox)

    def update_area_chart(self, category):
        """
        Update the area chart. This method is called when the area chart is clicked.

        Args:
            category (dict): A dictionary of index keys and sheets.

        """
        if self.plot_method == 'interactive_plotly':
            return self.update_area_chart_interactive_plotly(category)

        category = self.dataselectiongroupbox.get_category_info()['current_text']

        # Set up the figure with multiple subplots
        _fig, axes = plt.subplots(len(category), 1, figsize=(10, 6 * len(category)), sharex=True)

        if len(category) == 1:
            axes = [axes]  # Ensure axes is always iterable

        # Find the global maximum date
        global_max_date = max(sheets[category].df['date'].max() for sheets in category.values())

        # Loop through each sheet in the provided dictionary
        for ax, (index, sheets) in zip(axes, category.items()):
            # Extract dataframe and columns to use for plotting
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns

            # Add a data point with the global maximum date if necessary
            df, cumulative_percents = prepare_area_chart_data(df, cols_to_use, global_max_date)

            # Plotting area chart using cumulative percentages
            lower_values = np.zeros(len(df))

            for col in cols_to_use:
                if df[col].iloc[-1] == 0:  # Skip columns with no data
                    continue

                upper_values = cumulative_percents[col]

                # Fill between lower and upper values to create stacked area effect
                ax.fill_between(df['date'], lower_values, upper_values, label=col, alpha=0.5)

                # Update the lower boundary for the next stacked layer
                lower_values = upper_values

            # Final plot settings for each subplot
            ax.set_xlabel('Date')
            ax.set_ylabel(f'{category} Distribution Over Time')
            source_id = self.dataselectiongroupbox.file_infos[index]['source_id']
            ax.set_title(f"{source_id} {category} Distribution Over Time")
            ax.grid(True)
            ax.legend()

        plt.tight_layout()  # Adjust layout to prevent label overlap
        with self.output_area_chart:
            self.output_area_chart.clear_output(wait=True)
            plt.show()
            plt.close()

        return None

    def update_area_chart_interactive_plotly(self, category):
        """Update the area chart using interactive plotting with Plotly."""
        category = self.dataselectiongroupbox.get_category_info()['current_text']

        # Find the global minimum and maximum date
        global_min_date = min(sheets[category].df['date'].min() for sheets in category.values())
        global_max_date = max(sheets[category].df['date'].max() for sheets in category.values())

        # Create a list to hold each plotly figure as widgets
        fig_widgets = []

        # Loop through each sheet in the provided dictionary
        for index, sheets in category.items():
            # Extract dataframe and columns to use for plotting
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns

            # Add a data point with the global maximum date if necessary
            df, cumulative_percents = prepare_area_chart_data(df, cols_to_use, global_max_date)
            individual_percents = df[cols_to_use].div(df[cols_to_use].sum(axis=1), axis=0) * 100

            # Create a new Plotly figure for each dataset
            fig = create_stacked_area_figure(df, cols_to_use, cumulative_percents, individual_percents)

            # Update the layout for each individual figure
            fig.update_layout(
                title=f"{self.dataselectiongroupbox.file_infos[index]['source_id']} {category} Distribution Over Time",
                xaxis_title="Date",
                yaxis_title="Percentage (%)",
                height=400,
                showlegend=True,
                xaxis={range: [global_min_date, global_max_date]},  # Set the x-axis range for consistency
            )

            # Convert the Plotly figure into an interactive widget
            fig_widget = go.FigureWidget(fig)
            fig_widgets.append(fig_widget)

        # Create a VBox to stack all figures vertically
        vbox = widgets.VBox(fig_widgets)

        # Clear previous output and display the VBox inside `self.output_area_chart`
        with self.output_area_chart:
            self.output_area_chart.clear_output(wait=True)
            display(vbox)
