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
This module contains a function to create a stacked area chart using Plotly.
"""

import pandas as pd
import plotly.graph_objects as go


def create_stacked_area_figure(df, cols_to_use, cumulative_percents, individual_percents):
    """
    Create a stacked area chart by adding two traces per column:
    one for the filled area and one invisible trace for hover data.

    Args:
        df (DataFrame): Data frame containing a 'date' column.
        cols_to_use (list): List of column names to process.
        cumulative_percents (dict): Mapping of column names to cumulative percentage values.
        individual_percents (dict): Mapping of column names to actual percentage values.

    Returns:
        go.Figure: The stacked area chart.
    """
    fig = go.Figure()

    for col in cols_to_use:
        if df[col].iloc[-1] == 0:
            continue

        upper_values = cumulative_percents[col]

        # Trace for the stacked area effect.
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=upper_values,
                fill='tonexty',
                name=col,
                mode='lines',
                line={'width': 0.5},
                opacity=0.5,
                hoverinfo='none',
            )
        )

        # Trace for hover information with actual percentages.
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=upper_values,
                text=individual_percents[col],
                name=col,
                mode='lines',
                line={'width': 0.5, 'color': 'rgba(0,0,0,0)'},
                hovertemplate='%{text:.2f}%',
                showlegend=False,
            )
        )

    # Update the layout. Customize as needed.
    fig.update_layout(
        title='Stacked Area Chart',
        xaxis_title='Date',
        yaxis_title='Percentage',
    )
    return fig


def prepare_area_chart_data(df, cols_to_use, global_max_date):
    """
    Prepares data for an area chart.

    - If the maximum date in the dataframe is less than the global maximum date,
      appends a new row with the global maximum date.
    - Calculates cumulative percentages for the given columns.

    Args:
        df (DataFrame): Input data frame that must contain a 'date' column.
        cols_to_use (list): List of column names to use for calculations.
        global_max_date: The global maximum date to compare with.

    Returns:
        tuple: A tuple containing the updated DataFrame and the cumulative percentages.
    """
    if df['date'].max() < global_max_date:
        last_row = df.iloc[-1].copy()
        last_row['date'] = global_max_date
        df = pd.concat([df, pd.DataFrame([last_row])], ignore_index=True)

    total_counts = df[cols_to_use].sum(axis=1)
    cumulative_percents = 100.0 * df[cols_to_use].cumsum(axis=1).div(total_counts, axis=0)

    return df, cumulative_percents
