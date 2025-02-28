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
This module contains the JSDViewDash class, which represents a Dash view for JSD.
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

from midrc_react.core.jsdconfig import JSDConfig
from midrc_react.core.jsdcontroller import JSDController
from midrc_react.core.jsdmodel import JSDTableModel
from midrc_react.gui.common.file_upload import process_file_upload
from midrc_react.gui.common.jsdview_base import JsdViewBase
from midrc_react.gui.common.plot_utils import create_stacked_area_figure, prepare_area_chart_data
from midrc_react.gui.dash.dataselectiongroupbox import DataSelectionGroupBox


class JSDViewDash(JsdViewBase):
    """
    Class: JSDViewDash
    This class represents a Dash view for JSD. It provides functionality for creating a Dash app and handling file
    uploads. The class has methods for setting up the layout, updating the category combo box, and initializing the
    widget.
    """
    def __init__(self, jsd_model, config):
        super().__init__()
        self.jsd_model = jsd_model
        self.controller = JSDController(self, jsd_model, config)
        self.app = dash.Dash(__name__)
        self.data_selection_group_box = DataSelectionGroupBox(jsd_model, self.app)
        self.setup_layout()

        # Connect the signal to the slot
        # if not self.data_selection_group_box.excel_file_uploaded.connect(self.handle_excel_file_uploaded):
        #     print("⚠️ Failed to connect excel_file_uploaded signal!")
        # else:
        #     print("✅ Successfully connected excel_file_uploaded signal to handle_excel_file_uploaded")

    def setup_layout(self):
        """
        Sets up the layout of the Dash app.
        """
        self.app.layout = html.Div([
            self.data_selection_group_box.display(),
            dcc.Graph(id='timeline-chart'),
            html.Div(id='area-chart-container'),
        ])

        @self.app.callback(
            Output('timeline-chart', 'figure'),
            Input(self.data_selection_group_box.category_combobox.id, 'value'),  # pylint: disable=no-member
        )
        def update_timeline_chart(selected_category):
            return self.update_timeline_chart(selected_category)

        @self.app.callback(
            Output('area-chart-container', 'children'),
            Input(self.data_selection_group_box.category_combobox.id, 'value'),  # pylint: disable=no-member
        )
        def update_area_chart(selected_category):
            return self.update_area_chart(selected_category)

    def get_categories(self):
        """
        Get the categories from the controller.

        Returns:
            list: A list of categories.
        """
        return self.controller.get_categories()

    def update_timeline_chart(self, category):
        """
        Updates the timeline chart with the specified category.

        Args:
            category (str): The category to update the chart with.

        Returns:
            bool: True if the chart was updated, False if there was no data to update.
        """
        plot_data = self.controller.get_timeline_data(category)

        if plot_data is None or plot_data.empty:
            return px.line(title="No data available for plotting.")

        if 'label' not in plot_data.columns:
            # print("The 'label' column is missing in the plot data.")
            return px.line(title="The 'label' column is missing in the plot data.")

        fig = go.Figure()

        for label, df in plot_data.groupby('label'):
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['value'],
                mode='lines',
                name=label,
            ))

        fig.update_layout(
            title=f"JSD Timeline Chart - {category}",
            xaxis_title="Date",
            yaxis_title="JSD Value",
            yaxis={'range': [0.0, 1.0]},
            height=600,
        )

        return fig

    def update_area_chart(self, category):
        """
        Updates the area chart with the specified category.

        Args:
            category (str): The category to update the chart with.

        Returns:
            bool: True if the chart was updated, False if there was no data to update.
        """
        data_sources = [ds for ds in self.jsd_model.data_sources.values() if category in ds.sheets]

        if not data_sources:
            return html.Div("No data available for the selected category.")

        # Find the global minimum and maximum date
        global_min_date = min(ds.sheets[category].df['date'].min() for ds in data_sources)
        global_max_date = max(ds.sheets[category].df['date'].max() for ds in data_sources)

        # Create a list to hold each plotly figure
        figures = []

        # Loop through each data source
        for data_source in data_sources:
            df = data_source.sheets[category].df.copy()
            cols_to_use = data_source.sheets[category].data_columns

            # Add a data point with the global maximum date if necessary
            df, cumulative_percents = prepare_area_chart_data(df, cols_to_use, global_max_date)
            individual_percents = df[cols_to_use].div(df[cols_to_use].sum(axis=1), axis=0) * 100

            fig = create_stacked_area_figure(df, cols_to_use, cumulative_percents, individual_percents)

            # Update the layout for each individual figure
            fig.update_layout(
                title=f"{data_source.name} {category} Distribution Over Time",
                xaxis_title="Date",
                yaxis_title="Percentage (%)",
                height=400,
                showlegend=True,
                xaxis={'range': [global_min_date, global_max_date]},  # Set the x-axis range for consistency
            )

            # Append the figure as a dcc.Graph component
            figures.append(dcc.Graph(figure=fig))

        # Arrange figures in a grid layout with two figures per row
        rows = []
        for i in range(0, len(figures), 2):
            row = html.Div(figures[i:i + 2], style={'display': 'flex', 'justify-content': 'space-around'})
            rows.append(row)

        return rows

    def handle_excel_file_uploaded(self, data_source_dict):
        """
        Handles the file upload.

        Args:
            data_source_dict (dict): The data source dictionary.
        """
        process_file_upload(self, data_source_dict)

    def run(self):
        """
        Runs the Dash app.
        """
        self.app.run_server(debug=True)
        # Remove threading if we want to use Qt Signals and Slots
        # self.app.run_server(debug=False, threaded=False)


if __name__ == '__main__':
    # Example usage:
    my_config = JSDConfig()
    my_data_source_list = my_config.data['data sources']
    my_jsd_model = JSDTableModel(my_data_source_list, my_config.data.get('custom age ranges', None))
    dash_view = JSDViewDash(my_jsd_model, my_config)

    # Load data sources
    for my_data_source in my_data_source_list:
        print(f"Loading: {my_data_source['description']}...")
        dash_view.open_excel_file(my_data_source)

    print("Done Loading Files")

    dash_view.run()
