import pandas as pd
import statistics

# read tf-idf excel file
df = pd.read_excel('C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/relative_frequencies/command_tokens/tf_idf/tf_idf.xlsx')

# select column
commands = ['POKE']

for entry in commands:
    value = df[entry].apply(lambda x: float(str(x).replace(',', '.'))).tolist()
    sorted_asc = sorted(value)
    sorted_desc = sorted(value, reverse=True)

    print(f'{entry}:'
          f'\nMax: {max(value)}'
          f'\nMin: {min(value)}'
          f'\nMedian: {statistics.median(value)}'
          f'\nArithmetisches Mittel: {statistics.mean(value)}'
          f'\nSpannweite: {max(value) - min(value)}'
          f'\nStandardabweichung: {statistics.stdev(value)}'
          f'\nSortiert aufst.: {sorted_asc[:5]}'
          f'\nSortiert abst.: {sorted_desc[:5]}'
          f'\n')
