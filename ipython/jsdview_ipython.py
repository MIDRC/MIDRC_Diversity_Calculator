from PySide6.QtCore import Signal, QObject, QDate
import matplotlib.pyplot as plt
import seaborn as sns
import ipywidgets as widgets
from IPython.display import display
from ipywidgets import VBox, HBox, Label
import numpy as np
import pandas as pd

from jsdview_base import JsdViewBase, GroupBoxData
from jsdmodel import JSDTableModel



# Define the data selection group box
class DataSelectionGroupBox(QObject, GroupBoxData):
    category_changed = Signal()
    file_selection_changed = Signal(str)

    def __init__(self, jsd_model):
        super().__init__()
        self.jsd_model = jsd_model
        self._file_comboboxes = []
        self._category_combobox = widgets.Dropdown(
            options=[],
            value=None,
            description='Attribute:',
            disabled=True,
        )
        self.layout = VBox()
        self._setup_layout()

        self.num_fileboxes = 2
        self._initialize_data_sources()

        # Connect signals
        self._category_combobox.observe(self.on_category_changed, names='value')
        for combobox in self.file_comboboxes:
            combobox.observe(self.on_file_selection_changed, names='value')

    def _setup_layout(self):
        self.layout.children = [self._category_combobox]

    def _initialize_data_sources(self):
        # Initialize file comboboxes based on data sources from JSDController
        data_sources = self.jsd_model.data_sources
        for index, data_source_key in enumerate(list(data_sources.keys())[len(self.file_comboboxes):self.num_fileboxes]):
            combobox = widgets.Dropdown(
                options=list([ds_key for ds_key in data_sources.keys()]),
                value=data_source_key,
                description=f'Data Source {index + 1}:',
                disabled=False
            )
            self.file_comboboxes.append(combobox)
            self.layout.children += (combobox,)
            combobox.observe(self.on_file_selection_changed, names='value')

        # Initialize category combobox based on the current data selection
        if self.file_comboboxes:
            self.on_file_selection_changed()

    def update_file_comboboxes(self):
        # Update file comboboxes based on data sources
        data_sources = self.jsd_model.data_sources
        for combobox in self._file_comboboxes:
            combobox.options = list(data_sources.keys())
        if self.num_fileboxes > len(self._file_comboboxes):
            self._initialize_data_sources()

    @property
    def file_comboboxes(self):
        return self._file_comboboxes

    def change_number_of_fileboxes(self, num_fileboxes):
        self.num_fileboxes = num_fileboxes

        # Add file comboboxes if num_fileboxes is greater than the current number
        if self.num_fileboxes > len(self.file_comboboxes):
            self.update_file_comboboxes()

        # Remove file comboboxes if num_fileboxes is less than the current number
        elif self.num_fileboxes < len(self.file_comboboxes):
            # Remove excess comboboxes from the layout and list
            excess_comboboxes = len(self.file_comboboxes) - self.num_fileboxes
            for _ in range(excess_comboboxes):
                combobox_to_remove = self._file_comboboxes.pop()
                self.layout.children = tuple(child for child in self.layout.children if child != combobox_to_remove)
            self.on_file_selection_changed()

    def update_category_combobox(self):
        # Update category combobox based on selected data sources
        previous_value = self.get_category_info()['current_text']

        file_infos = self.get_file_infos()
        cbox0 = file_infos[0]
        common_categories = self.jsd_model.data_sources[cbox0['source_id']].sheets.keys()

        for cbox2 in file_infos[1:]:
            categorylist2 = self.jsd_model.data_sources[cbox2['source_id']].sheets.keys()
            common_categories = [value for value in common_categories if value in categorylist2]
        self._category_combobox.options = common_categories
        if previous_value not in common_categories:
            self.update_category_list(common_categories, 0)
            self._category_combobox.index = 0
        else:
            self.update_category_list(common_categories, common_categories.index(previous_value))
            self._category_combobox.value = previous_value
        self._category_combobox.disabled = False

    def on_category_changed(self, change):
        self.update_category_text(change['new'])
        self.category_changed.emit()

    def on_file_selection_changed(self, change=None):
        data_sources = self.jsd_model.data_sources
        file_infos = []
        for index, file_combobox in enumerate(self.file_comboboxes):
            data_source_dict = data_sources[file_combobox.value].data_source
            file_infos.append({
                'description': data_source_dict['description'],
                'source_id': data_source_dict['name'],
                'index': index,
                'checked': True,
            })
        self._file_infos = file_infos
        self.update_category_combobox()
        self.file_selection_changed.emit(change)

    def display(self):
        return self.layout

# Create instance of DataSelectionGroupBox

class JsdViewIPython(JsdViewBase):
    jsd_timeline_plot_update = Signal(JSDTableModel)

    def __init__(self, jsd_model):
        super().__init__()
        self.update_view_on_controller_initialization = False

        self.jsd_model = jsd_model
        self.output_timeline = widgets.Output()
        self.output_area_chart = widgets.Output()
        self._dataselectiongroupbox = DataSelectionGroupBox(jsd_model)

    def open_excel_file(self, data_source_dict):
        super().open_excel_file(data_source_dict)
        self.jsd_model.add_data_source(data_source_dict)

    def update_jsd_timeline_plot(self, jsd_model):
        print("Plotting timeline chart using Seaborn...")

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
                    'label': f"{column_info['file1']} vs {column_info['file2']} {column_info['category']} JSD"
                })

                # Filter out rows with invalid date values (if any date failed to convert)
                temp_data.dropna(subset=['date'], inplace=True)

                # Handle the first iteration by directly assigning temp_data to plot_data
                if plot_data is None:
                    plot_data = temp_data
                else:
                    # Concatenate subsequent series
                    plot_data = pd.concat([plot_data, temp_data], ignore_index=True)

            except Exception as e:
                print(f"An error occurred while processing column info {column_info}: {e}")

        # Check if we have any data to plot
        if plot_data is None or plot_data.empty:
            print("No data available for plotting.")
            return

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

        print("Plotting complete.")

    def update_area_chart(self, sheet_dict):
        print("Plotting area charts...")

        category = self.dataselectiongroupbox.get_category_info()['current_text']

        # Set up the figure with multiple subplots
        fig, axes = plt.subplots(len(sheet_dict), 1, figsize=(10, 6 * len(sheet_dict)), sharex=True)

        if len(sheet_dict) == 1:
            axes = [axes]  # Ensure axes is always iterable

        # Find the global maximum date
        global_max_date = max(sheets[category].df['date'].max() for sheets in sheet_dict.values())

        # Loop through each sheet in the provided dictionary
        for ax, (index, sheets) in zip(axes, sheet_dict.items()):
            # Extract dataframe and columns to use for plotting
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns

            # Add a data point with the global maximum date if necessary
            if df['date'].max() < global_max_date:
                last_row = df.iloc[-1].copy()
                last_row['date'] = global_max_date
                df = pd.concat([df, pd.DataFrame([last_row])], ignore_index=True)

            # Prepare cumulative percentages for area plot
            total_counts = df[cols_to_use].sum(axis=1)
            cumulative_percents = 100.0 * df[cols_to_use].cumsum(axis=1).div(total_counts, axis=0)

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
            ax.set_title(f'{self.dataselectiongroupbox.file_infos[index]['source_id']} {category} Distribution Over Time')
            ax.grid(True)
            ax.legend()

        plt.tight_layout()  # Adjust layout to prevent label overlap
        with self.output_area_chart:
            self.output_area_chart.clear_output(wait=True)
            plt.show()
            plt.close()

        print('done with this step')