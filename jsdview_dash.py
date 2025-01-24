import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from jsdconfig import JSDConfig
from jsdmodel import JSDTableModel
from jsdcontroller import JSDController
from jsdview_base import JsdViewBase

class JSDViewDash(JsdViewBase):
    def __init__(self, jsd_model, config):
        super().__init__()
        self.jsd_model = jsd_model
        self.controller = JSDController(self, jsd_model, config)
        self.app = dash.Dash(__name__)
        self.setup_layout()

    def setup_layout(self):
        self.app.layout = html.Div([
            dcc.Dropdown(
                id='category-dropdown',
                options=[{'label': cat, 'value': cat} for cat in self.get_categories()],
                value=self.get_categories()[0]
            ),
            dcc.Graph(id='timeline-chart'),
            html.Div(id='area-chart-container')
        ])

        @self.app.callback(
            Output('timeline-chart', 'figure'),
            Input('category-dropdown', 'value')
        )
        def update_timeline_chart(selected_category):
            return self.update_timeline_chart(selected_category)

        @self.app.callback(
            Output('area-chart-container', 'children'),
            Input('category-dropdown', 'value')
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
        data_sources = list(self.jsd_model.data_sources.values())

        # Find the global minimum and maximum date
        global_min_date = min(data_source.sheets[category].df['date'].min() for data_source in data_sources if
                              category in data_source.sheets)
        global_max_date = max(data_source.sheets[category].df['date'].max() for data_source in data_sources if
                              category in data_source.sheets)

        # Create a list to hold each plotly figure
        figures = []

        # Loop through each data source
        for data_source in data_sources:
            if category in data_source.sheets:
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

    def run(self):
        self.app.run_server(debug=True)

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
