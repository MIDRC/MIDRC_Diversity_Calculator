from PySide6.QtCore import Signal, QObject
import matplotlib.pyplot as plt
import seaborn as sns
import ipywidgets as widgets
from IPython.display import display
from ipywidgets import VBox, HBox, Label
import numpy as np

from jsdview_base import JsdViewBase
from jsdmodel import JSDTableModel



# Define the data selection group box
class DataSelectionGroupBox(QObject):
    category_changed = Signal(str)
    file_selection_changed = Signal()

    def __init__(self, jsd_model):
        super().__init__()
        self.jsd_model = jsd_model
        self.file_comboboxes = []
        self.category_combobox = widgets.Dropdown(
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
        self.category_combobox.observe(self.on_category_changed, names='value')
        for combobox in self.file_comboboxes:
            combobox.observe(self.on_file_selection_changed, names='value')

    def _setup_layout(self):
        self.layout.children = [self.category_combobox]

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
            self.update_category_combobox()

    def update_file_comboboxes(self):
        # Update file comboboxes based on data sources
        data_sources = self.jsd_model.data_sources
        for combobox in self.file_comboboxes:
            combobox.options = list(data_sources.keys())
        if self.num_fileboxes > len(self.file_comboboxes):
            self._initialize_data_sources()

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
                combobox_to_remove = self.file_comboboxes.pop()
                self.layout.children = tuple(child for child in self.layout.children if child != combobox_to_remove)

    def update_category_combobox(self):
        # Update category combobox based on selected data sources
        selected_sheets = [combobox.value for combobox in self.file_comboboxes]
        common_categories = set.intersection(*[set(self.jsd_model.data_sources[combobox.value].sheets.keys()) for combobox in self.file_comboboxes])
        self.category_combobox.options = list(common_categories)
        self.category_combobox.disabled = False

    def on_category_changed(self, change):
        self.category_changed.emit(change['new'])

    def on_file_selection_changed(self, change):
        self.file_selection_changed.emit()
        self.update_category_combobox()

    def display(self):
        return self.layout

# Create instance of DataSelectionGroupBox

class JsdViewIPython(JsdViewBase):
    jsd_timeline_plot_update = Signal(JSDTableModel)

    def __init__(self, jsd_model):
        super().__init__()
        self.jsd_model = jsd_model
        self.data_selection_groupbox = DataSelectionGroupBox(jsd_model)

    def open_excel_file(self, data_source_dict):
        super().open_excel_file(data_source_dict)
        self.jsd_model.add_data_source(data_source_dict)

    def update_jsd_timeline_plot(self, jsd_model):
        print("Plotting timeline chart...")
        plt.figure(figsize=(10, 6))
        category = self.data_selection_groupbox.category_combobox.value
        for combobox in self.data_selection_groupbox.file_comboboxes:
            if combobox.value:
                try:
                    print(f"Processing: {combobox.value}")
                    file_data = self.jsd_model.data_sources[combobox.value].sheets[category].df
                    print(file_data.head())  # Debug to see if file_data is accessible
                    if file_data.empty:
                        print(f"No data available for {combobox.value} and category {category}. Skipping.")
                        continue  # Skip empty data
                    sns.lineplot(data=file_data, x='date', y=file_data.columns[1],
                                 label=f'{combobox.value}: {category} ({file_data.columns[1]})')
                except Exception as e:
                    print(f"An error occurred while processing {combobox.value}: {e}")
        print('done with this step')
        plt.xlabel('Date')
        plt.ylabel(f'JSD for Category: {category}')
        plt.title('JSD Timeline Chart')
        plt.grid(True)
        plt.legend()
        plt.show()
        plt.close()

    def update_area_chart(self, sheet_dict):
        print("Plotting area charts...")

        category = self.data_selection_groupbox.category_combobox.value

        # Set up the figure with multiple subplots
        fig, axes = plt.subplots(len(sheet_dict), 1, figsize=(10, 6 * len(sheet_dict)), sharex=True)

        if len(sheet_dict) == 1:
            axes = [axes]  # Ensure axes is always iterable

        # Loop through each sheet in the provided dictionary
        for ax, (index, sheets) in zip(axes, sheet_dict.items()):
            # Extract dataframe and columns to use for plotting
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns

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
            ax.set_title(
                f'{self.dataselectiongroupbox.file_infos[index]} {category} Distribution Over Time')
            ax.grid(True)
            ax.legend()

        plt.tight_layout()  # Adjust layout to prevent label overlap
        plt.show()
        plt.close()

        print('done with this step')