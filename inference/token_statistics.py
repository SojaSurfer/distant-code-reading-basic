import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rich import print, traceback

from preprocessing.tagset import TAGSET1, TAGSET2

traceback.install()


def plotSyntaxDistribution(df:pd.DataFrame, syntaxTag:tuple[str,str]) -> None:
    
    groupedDF = df[df['syntax'] == syntaxTag[1]]
    commands = groupedDF['token'].value_counts()
    groupedDF = pd.DataFrame(commands)
    groupedDF['percentage'] = groupedDF['count'] / groupedDF['count'].sum()

    otherGrouping = groupedDF[groupedDF['percentage'] <= 0.01]
    exclusiveGrouping =groupedDF[groupedDF['percentage'] > 0.01]

    otherRow = pd.DataFrame({'count': [otherGrouping['count'].sum()],
                             'percentage': [otherGrouping['percentage'].sum()]}, index=['other'])
    inclusiveGrouping = pd.concat([exclusiveGrouping, otherRow])


    fig = _plotDistribution(groupedDF, exclusiveGrouping, inclusiveGrouping, syntaxTag[0])

    fig.show()
    fig.write_image(plotPath / f'{syntaxTag[0]}_distribution.svg', width=2000, height=1200)
    return None


# def plotCommandDistr(df:pd.DataFrame) -> None:
    
#     grouped = df[df['syntax'] == 'C']
#     commands = grouped['token'].value_counts()
#     grouped = pd.DataFrame(commands)
#     grouped['percentage'] = grouped['count'] / grouped['count'].sum()

#     others = grouped[grouped['percentage'] <= 0.01]
#     grouped_ = grouped[grouped['percentage'] > 0.01]

#     fig = _plotDistribution(grouped, grouped_, others)

#     fig.show()
#     fig.write_image(plotPath / 'command_distribution.svg', width=2000, height=1200)
#     return None


def _plotDistribution(groupedDF:pd.DataFrame, exclusiveGrouping:pd.DataFrame, inclusiveGrouping:pd.DataFrame, syntax:str) -> go.Figure:
    
    xaxis_tickangle = 0 if any([x in syntax.lower() for x in ['operator', 'punctuation']]) else 90

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("", ""),
        specs=[[{"type": "bar"}], [{"type": "pie"}]],
        vertical_spacing=0.15,
    )
    
    # Bar chart (top)
    fig.add_trace(go.Bar(
        y=groupedDF['percentage'],
        x=groupedDF.index,
        orientation='v',
        showlegend=False
    ), row=1, col=1)

    # Pie chart (bottom)
    fig.add_trace(
        go.Pie(
            labels=inclusiveGrouping.index,
            values=inclusiveGrouping['percentage'],
            sort=False,
            direction='counterclockwise',
            rotation=0,
            textposition='outside',
            textinfo='label+percent',
        ),
        row=2, col=1
    )

    fig.update_layout(
        title_text=f"{syntax.capitalize()} Statement Distribution",
        xaxis_title=syntax,
        yaxis_title="Percentage",
        yaxis_tickformat=".0%",
        xaxis_tickangle=xaxis_tickangle,
        xaxis_tickformat=".0%",
        bargap=0.2,
        legend=dict(
            x=0.75,   # Move legend to the right
            y=0.1,
            xanchor='left',
            yanchor='bottom'
        ),
    )
    return fig




if __name__ == '__main__':
    corpusPath = Path(__file__).resolve().parents[2] / 'corpus'
    plotPath = Path(__file__).parent / 'plots'

    df = pd.read_parquet(corpusPath / 'dataset' / 'tokenized_dataset.parquet')

    # plotCommandDistr(df)

    for syntax, tagset in TAGSET2.items():
        plotSyntaxDistribution(df, (syntax, tagset))