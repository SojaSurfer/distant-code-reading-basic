import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go




if False:
    metadata_path = Path("corpus/metadata.xlsx")

    parquet = pd.read_parquet("corpus/dataset/dataset.parquet")
    df["name"] = df["name"].astype(str)
    parquet["name"] = parquet["name"].astype(str)
    print(df.columns)
    df.drop(["disk", "date"], inplace=True, axis=1)


    joined = pd.merge(df, parquet, how="left", on="name")
    joined = joined.set_index("file_id")
    joined["game_id"] = joined["game_id"].astype("uint32")
    print()
    print(joined.info())

    joined.to_parquet("corpus/dataset/dataset_new.parquet")

    joined.drop(columns=["length", "code"], inplace=True)
    joined = joined[["game_id", "disk", "date", "category", "name", "target_platform", "author"]]


    joined["date"] = joined["date"].dt.date
    joined.to_excel("corpus/metadata_new.xlsx")


df = pd.read_parquet("corpus/dataset/dataset.parquet")
df = df.infer_objects()

files = len(df)



def first(series:pd.Series) -> Any:
    if series.empty:
        return None
    return series.iloc[0]


df = df.groupby("game_id").agg(
    {"name": first,
     "target_platform": first,
     "author": first,
     "category": first,
     "disk": first,
     "date": first,
     "length": "sum"})

print(df.info())

dateDF = df[["date", "name"]].groupby("date").count()

fig = px.box(
    df,
    y="length",  # Use 'length' for the boxplot
    title="Länge der Spiele in Zeilen",  # Update the title
    labels={"length": "Anzahl Zeilen"},
    range_y=(0, None),
)

# Update layout for additional customization
fig.update_layout(
    title={
        "text": "Länge der Spiele in Zeilen",  # Title text
        "font": {"size": 24},  # Increase title font size
    },
    yaxis_title="Anzahl Zeilen",  # Set y-axis label
    xaxis_title="Spiele",  # Set x-axis label
    font=dict(
        size=18,  # Increase font size for all text elements
    ),
)

fig.show()