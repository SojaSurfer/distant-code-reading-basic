import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from tagset import TAGSET


cmd_to_subcat = {}
subcat_order = []

for category, subcats in TAGSET.items():
    if isinstance(subcats, dict):
        for subcat, entry in subcats.items():
            if "values" in entry and entry["values"]:
                for cmd in entry["values"]:
                    if cmd is not None:
                        cmd_to_subcat[cmd] = subcat
                if subcat not in subcat_order:
                    subcat_order.append(subcat)


df = pd.read_csv(r"C:\Users\eric_\Desktop\Desktop Folders\Schule\BASIC Projektarbeit\trigrams_output_plot.csv")

cmd_col = df.columns[0]
df["__subcat__"] = df[cmd_col].map(cmd_to_subcat)


df["__subcat__"] = pd.Categorical(df["__subcat__"], categories=subcat_order, ordered=True)
df = df.sort_values("__subcat__").reset_index(drop=True)


color_values = df["__subcat__"].cat.codes


plot_df = df.iloc[:, :-3]


code_df = pd.DataFrame()
label_maps = {}

for i, col in enumerate(plot_df.columns):
    if i == 0:
        unique_vals = []
        for subcat in subcat_order:
            subset = df[df["__subcat__"] == subcat][col].dropna().unique()
            unique_vals.extend(sorted(subset, reverse=True)) 
        unique_vals = list(dict.fromkeys(unique_vals)) 
    elif i in [1, 2]:
        unique_vals = sorted(plot_df[col].dropna().unique(), reverse=True) 
    else:
        unique_vals = plot_df[col].dropna().unique().tolist()

    cat_col = pd.Categorical(plot_df[col], categories=unique_vals, ordered=True)
    code_df[col] = cat_col.codes
    label_maps[col] = dict(enumerate(unique_vals))

dimensions = []
for col in plot_df.columns:
    codes = code_df[col]
    labels = label_maps[col]
    dimensions.append(dict(
        label=col,
        values=codes,
        tickvals=list(labels.keys()),
        ticktext=list(labels.values())
    ))



fig = go.Figure(
    data=go.Parcoords(
        line=dict(
            color=color_values,
            colorscale=px.colors.qualitative.Dark2,
            showscale=True
        ),
        dimensions=dimensions
    )
)

fig.update_layout(
    template="ggplot2",
    font=dict(family="sans-serif", size=16),
    width=900,
    height=900
)

fig.show()
