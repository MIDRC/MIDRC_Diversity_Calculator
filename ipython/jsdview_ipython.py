from PySide6.QtCore import Signal, QDate
import matplotlib.pyplot as plt
import seaborn as sns
import ipywidgets as widgets
import numpy as np
import pandas as pd

from jsdview_base import JsdViewBase
from jsdmodel import JSDTableModel
from ipython.dataselectiongroupbox import DataSelectionGroupBox


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

    def update_area_chart(self, sheet_dict):
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
