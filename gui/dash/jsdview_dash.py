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

import os

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from core.jsdconfig import JSDConfig
from core.jsdmodel import JSDTableModel
from core.jsdcontroller import JSDController
from gui.jsdview_base import JsdViewBase
from gui.dash.dataselectiongroupbox import DataSelectionGroupBox

class JSDViewDash(JsdViewBase):
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
        self.app.layout = html.Div([
            self.data_selection_group_box.display(),
            dcc.Graph(id='timeline-chart'),
            html.Div(id='area-chart-container')
        ])

        @self.app.callback(
            Output('timeline-chart', 'figure'),
            Input(self.data_selection_group_box.category_combobox.id, 'value')
        )
        def update_timeline_chart(selected_category):
            return self.update_timeline_chart(selected_category)

        @self.app.callback(
            Output('area-chart-container', 'children'),
            Input(self.data_selection_group_box.category_combobox.id, 'value')
        )
        def update_area_chart(selected_category):
            return self.update_area_chart(selected_category)

    def get_categories(self):
        return self.controller.get_categories()

    def update_timeline_chart(self, category):
        plot_data = self.controller.get_timeline_data(category)

        if plot_data is None or plot_data.empty:
            return px.line(title="No data available for plotting.")

        if 'label' not in plot_data.columns:
            print("The 'label' column is missing in the plot data.")
            return

        fig = go.Figure()

        for label, df in plot_data.groupby('label'):
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['value'],
                mode='lines',
                name=label
            ))

        fig.update_layout(
            title=f"JSD Timeline Chart - {category}",
            xaxis_title="Date",
            yaxis_title="JSD Value",
            yaxis=dict(range=[0.0, 1.0]),
            height=600
        )

        return fig

    def update_area_chart(self, category):
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
            if df['date'].max() < global_max_date:
                last_row = df.iloc[-1].copy()
                last_row['date'] = global_max_date
                df = pd.concat([df, pd.DataFrame([last_row])], ignore_index=True)

            # Prepare cumulative percentages for area plot
            total_counts = df[cols_to_use].sum(axis=1)
            cumulative_percents = 100.0 * df[cols_to_use].cumsum(axis=1).div(total_counts, axis=0)
            individual_percents = 100.0 * df[cols_to_use].div(total_counts, axis=0)

            # Create a new Plotly figure for each dataset
            fig = go.Figure()

            # Plotting area chart using cumulative percentages
            lower_values = np.zeros(len(df))

            for col in cols_to_use:
                if df[col].iloc[-1] == 0:  # Skip columns with no data
                    continue

                upper_values = cumulative_percents[col]

                # Add a trace for the stacked area effect
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=upper_values,
                        fill='tonexty',
                        name=col,
                        mode='lines',
                        line=dict(width=0.5),
                        opacity=0.5,
                        hoverinfo='none'  # Prevent default cumulative percentage from being shown
                    )
                )

                # Add a separate trace for hover information with actual column percentages
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=upper_values,
                        text=individual_percents[col],
                        name=col,
                        mode='lines',
                        line=dict(width=0.5, color='rgba(0,0,0,0)'),  # Invisible line
                        hovertemplate='%{text:.2f}%',
                        showlegend=False  # Hide these hover traces from the legend
                    )
                )

            # Update the layout for each individual figure
            fig.update_layout(
                title=f"{data_source.name} {category} Distribution Over Time",
                xaxis_title="Date",
                yaxis_title="Percentage (%)",
                height=400,
                showlegend=True,
                xaxis=dict(range=[global_min_date, global_max_date])  # Set the x-axis range for consistency
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
        print(f"handle_excel_file_uploaded() triggered with file: {data_source_dict['name']}")  # Debugging print
        self.open_excel_file(data_source_dict)
        print("Excel file loaded, try to update layout")
        self.data_selection_group_box.update_filebox_layout(self.data_selection_group_box.num_fileboxes)

    def run(self):
        self.app.run_server(debug=True)
        # Remove threading if we want to use Qt Signals and Slots
        # self.app.run_server(debug=False, threaded=False)

# Example usage:
config = JSDConfig()
data_source_list = config.data['data sources']
jsd_model = JSDTableModel(data_source_list, config.data.get('custom age ranges', None))
view = JSDViewDash(jsd_model, config)

# Load data sources
for data_source in data_source_list:
    print(f"Loading: {data_source['description']}...")
    view.open_excel_file(data_source)

print("Done Loading Files")

view.run()
