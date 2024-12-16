import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from jsdconfig import JSDConfig
from jsdmodel import JSDTableModel

class JSDViewDash:
    def __init__(self, jsd_model):
        self.jsd_model = jsd_model
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
            dcc.Graph(id='area-chart')
        ])

        @self.app.callback(
            Output('timeline-chart', 'figure'),
            Input('category-dropdown', 'value')
        )
        def update_timeline_chart(selected_category):
            return self.update_timeline_chart(selected_category)

        @self.app.callback(
            Output('area-chart', 'figure'),
            Input('category-dropdown', 'value')
        )
        def update_area_chart(selected_category):
            return self.update_area_chart(selected_category)

    def get_categories(self):
        # Assuming categories are the same across all data sources
        return list(list(self.jsd_model.data_sources.values())[0].sheets.keys())

    def update_timeline_chart(self, category):
        plot_data = None
        for sheets in self.jsd_model.data_sources.values():
            temp_data = sheets[category].df
            if plot_data is None:
                plot_data = temp_data
            else:
                plot_data = pd.concat([plot_data, temp_data], ignore_index=True)

        if plot_data is None or plot_data.empty:
            return px.line(title="No data available for plotting.")

        fig = px.line(
            plot_data,
            x='date',
            y='value',
            color='label',
            title=f"JSD Timeline Chart - {category}",
            labels={'date': 'Date', 'value': 'JSD Value', 'label': 'Data Sources'},
            height=600
        )
        fig.update_yaxes(range=[0.0, 1.0])
        return fig

    def update_area_chart(self, category):
        global_max_date = max(sheets[category].df['date'].max() for sheets in self.jsd_model.data_sources.values())
        fig = go.Figure()

        for sheets in self.jsd_model.data_sources.values():
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns

            if df['date'].max() < global_max_date:
                last_row = df.iloc[-1].copy()
                last_row['date'] = global_max_date
                df = pd.concat([df, pd.DataFrame([last_row])], ignore_index=True)

            total_counts = df[cols_to_use].sum(axis=1)
            cumulative_percents = 100.0 * df[cols_to_use].cumsum(axis=1).div(total_counts, axis=0)

            lower_values = np.zeros(len(df))
            for col in cols_to_use:
                if df[col].iloc[-1] == 0:
                    continue
                upper_values = cumulative_percents[col]
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=upper_values,
                        fill='tonexty',
                        name=col,
                        mode='lines',
                        line=dict(width=0.5),
                        opacity=0.5,
                        hoverinfo='none'
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=upper_values,
                        text=100.0 * df[col].div(total_counts, axis=0),
                        name=col,
                        mode='lines',
                        line=dict(width=0.5, color='rgba(0,0,0,0)'),
                        hovertemplate='%{text:.2f}%',
                        showlegend=False
                    )
                )
                lower_values = upper_values

        fig.update_layout(
            title=f"{category} Distribution Over Time",
            xaxis_title="Date",
            yaxis_title="Percentage (%)",
            height=400,
            showlegend=True
        )
        return fig

    def run(self):
        self.app.run_server(debug=True)

# Example usage:
config = JSDConfig()
data_source_list = config.data['data sources']
jsd_model = JSDTableModel(data_source_list, config.data.get('custom age ranges', None))
view = JSDViewDash(jsd_model)
view.run()
