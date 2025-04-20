import pandas as pd
from arcplot import ArcDiagram
import matplotlib.pyplot as plt



path = 'corpus/dataset/dataset.parquet'
df = pd.read_parquet(path)

row = df.loc[1]
codelines = row['code'].splitlines()
linenos = [int(line.split(maxsplit=1)[0]) for line in codelines]

codeDF = pd.DataFrame(data={'codelines': codelines, 'linenos': linenos})

def getGoto(codeline:str) -> int:
    idx = codeline.find('goto')

    if idx == -1:
        return idx
    else:
        goto = ''
        start_idx = idx + 4
        char = codeline[start_idx]

        while char not in [' ', '\n']:
            try:
                goto += char
                start_idx += 1
                char = codeline[start_idx]
            except IndexError:
                break

    return int(goto)


codeDF['goto'] = codeDF['codelines'].apply(getGoto)

print(row['name'])
print(codeDF.head(30))
print(codeDF['goto'].unique())

nodes = codeDF.index
nodes = list(codeDF['linenos'])

title = f'Code Line Progression in {row["name"]}'

arc_diagram = ArcDiagram(nodes, title)

for idx in codeDF.index[1:]:

    arc_diagram.connect(codeDF['linenos'].loc[idx-1],
                        codeDF['linenos'].loc[idx])

for idx in codeDF.index[1:]:
    if codeDF['goto'].loc[idx] != -1:

        arc_diagram.connect(codeDF['linenos'].loc[idx],
                            codeDF['goto'].loc[idx],
                            arc_position='below')

# ax = plt.gca() 
# ax.set_xticks(ax.get_xticks()[::10])
# plt.tight_layout()
# ax.set_xlim(nodes[0], nodes[-1])

arc_diagram.set_label_rotation_degree(45)

# Draw the diagram
plt.tight_layout()
arc_diagram.show_plot()

# Apply tight layout adjustments