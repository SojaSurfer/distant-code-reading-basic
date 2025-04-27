from collections import defaultdict
from pathlib import Path
import sys
import string

import pandas as pd
from arcplot import ArcDiagram
from rich import traceback, print
traceback.install()



ALLOWED_LINECHARS = string.digits + ' \n,'
ctrlTransferStatements_color = {'goto': 'blue', 'gosub': 'green', 'then': 'purple', 'else': 'yellow'}


def getGoto(codeline:str, lineno:int) -> defaultdict[str, list[tuple]]:
    ctrlTransferStatements = {'goto': None, 'gosub': None, 'then': None, 'else': None}
    indices = defaultdict(list)

    for statement in ctrlTransferStatements.keys():
        idx = codeline.find(statement)

        if idx != -1:
            gotoLine = getGotoLine(codeline, idx, statement)

            if gotoLine != -1:
                indices[statement].append((lineno, gotoLine))

    return indices


def getGotoLine(codeline:str, idx:int, statement:str) -> int|tuple[int]:
    if idx == -1:
        return idx
    else:
        gotoLine = ''
        start_idx = idx + len(statement)
        char = codeline[start_idx]

        if not char.isnumeric():
            return -1

        while char in ALLOWED_LINECHARS:
            try:
                gotoLine += char
                start_idx += 1
                char = codeline[start_idx]
            except IndexError:
                break

    if ',' in gotoLine:
        lines = gotoLine.split(',')
        gotoLines = [int(line) for line in lines]
        return tuple(gotoLines)

    return int(gotoLine)


def createArcDiagram(codeDF:pd.DataFrame) -> None:

    def connectArcDiagram(indices:dict):

        # arc_diagram.set_custom_colors(colorList)
        arc_diagram.set_label_rotation_degree(45)

        # Draw the diagram
        arc_diagram.show_plot()

        edgesAdded = 0
        for statement, value in indices.items():
            for valuePair in value:
                arc_diagram.connect(valuePair[0], valuePair[1],
                                    arc_position='below')
                edgesAdded += 1
        return edgesAdded

    nodes = codeDF.index
    nodes = list(codeDF['linenos'])

    title = f'Code Line Progression in {row["name"]}'

    arc_diagram = ArcDiagram(nodes, title)

    for idx in codeDF.index[1:]:

        arc_diagram.connect(codeDF['linenos'].loc[idx-1],
                            codeDF['linenos'].loc[idx])

    colorList = ['red'] * len(codeDF)
    for index, row in codeDF.iterrows():
    
        indices = getGoto(row['codelines'], row['linenos'])
        if indices:
            print(indices)
            edgesAdded = connectArcDiagram(indices)
            colorList.extend([ctrlTransferStatements_color[key] for key in indices.keys()])
    
    return None


def saveNodeEdgesInfo(codelines, linenos) -> None:
    codeDF = pd.DataFrame(data={'codelines': codelines, 'linenos': linenos})

    edgesDF = pd.DataFrame(columns=['from', 'to', 'color'])

    for index, row in codeDF.iterrows():
    
        indices = getGoto(row['codelines'], row['linenos'])
        for statement, value in indices.items():
            for valuePair in value:
                edgesDF.loc[len(edgesDF)] = {'from': valuePair[0], 'to': valuePair[1], 'color': ctrlTransferStatements_color[statement]}

    codeDF = codeDF.rename(columns={'linenos': 'name'})
    codeDF['parent'] = 'root'


    codeDF[['name', 'parent']].to_csv(Path(__file__, 'nodes.csv'), index=False)
    edgesDF.to_csv(Path(__file__, 'edges.csv'), index=False)
    return None



if __name__ == '__main__':

    path = 'corpus/dataset/dataset.parquet'
    df = pd.read_parquet(path)

    row = df.loc[1]
    codelines = row['code'].splitlines()
    linenos = [int(line.split(maxsplit=1)[0]) for line in codelines]
    print(row['name'])

    saveNodeEdgesInfo(codelines, linenos)



