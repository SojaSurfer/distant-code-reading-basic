import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rich import traceback

from preprocessing.tagset import TAGSET2




traceback.install()


def plot_syntax_distribution(df: pd.DataFrame, syntax_tag: tuple[str, str]) -> None:
    grouped_df = df[df["syntax"] == syntax_tag[1]]
    commands = grouped_df["token"].value_counts()
    grouped_df = pd.DataFrame(commands)
    grouped_df["percentage"] = grouped_df["count"] / grouped_df["count"].sum()

    other_grouping = grouped_df[grouped_df["percentage"] <= 0.01]
    exclusive_grouping = grouped_df[grouped_df["percentage"] > 0.01]

    other_row = pd.DataFrame(
        {
            "count": [other_grouping["count"].sum()],
            "percentage": [other_grouping["percentage"].sum()],
        },
        index=["other"],
    )
    inclusive_grouping = pd.concat([exclusive_grouping, other_row])

    fig = _plot_distribution(grouped_df, inclusive_grouping, syntax_tag[0])

    fig.show()
    fig.write_image(plot_path / f"{syntax_tag[0]}_distribution.svg", width=2000, height=1200)
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


def _plot_distribution(
    grouped_df: pd.DataFrame,
    inclusive_grouping: pd.DataFrame,
    syntax: str,
) -> go.Figure:
    xaxis_tickangle = 0 if any(x in syntax.lower() for x in ["operator", "punctuation"]) else 90

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("", ""),
        specs=[[{"type": "bar"}], [{"type": "pie"}]],
        vertical_spacing=0.15,
    )

    # Bar chart (top)
    fig.add_trace(
        go.Bar(
            y=grouped_df["percentage"],
            x=grouped_df.index,
            orientation="v",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # Pie chart (bottom)
    fig.add_trace(
        go.Pie(
            labels=inclusive_grouping.index,
            values=inclusive_grouping["percentage"],
            sort=False,
            direction="counterclockwise",
            rotation=0,
            textposition="outside",
            textinfo="label+percent",
        ),
        row=2,
        col=1,
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
            x=0.75,  # Move legend to the right
            y=0.1,
            xanchor="left",
            yanchor="bottom",
        ),
    )
    return fig


if __name__ == "__main__":
    corpus_path = Path(__file__).resolve().parents[2] / "corpus"
    plot_path = Path(__file__).parent / "plots"

    df = pd.read_parquet(corpus_path / "dataset" / "tokenized_dataset.parquet")

    # plotCommandDistr(df)

    for syntax, tagset in TAGSET2.items():
        plot_syntax_distribution(df, (syntax, tagset))
