import pandas as pd
import statistics

# read excel file
df = pd.read_excel('C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/tokens_per_line/test/global_line_counts_table_merged.xlsx')

# setup line count
lines_total = 0
lines_listed = []

# deselect columns 'game_id' and 'name'
tokens = df.iloc[:, 2:]

for i in range(0, 57):
    tokens['total_tokens'] = tokens.sum(axis=1)
    print(f'row {i}: {tokens['total_tokens'][i]}')

    lines_total += int(tokens['total_tokens'][i])
    lines_listed.append(int(tokens['total_tokens'][i]))

    tokens['total_tokens'] = 0

print(lines_listed)
print(lines_total)
#print(tokens)

sorted_asc = sorted(lines_listed)
sorted_desc = sorted(lines_listed, reverse=True)

print(f'{lines_listed}:'
      f'\nMax: {max(lines_listed)}'
      f'\nMin: {min(lines_listed)}'
      f'\nMedian: {statistics.median(lines_listed)}'
      f'\nArithmetisches Mittel: {statistics.mean(lines_listed)}'
      f'\nSpannweite: {max(lines_listed) - min(lines_listed)}'
      f'\nStandardabweichung: {statistics.stdev(lines_listed)}'
      f'\nSortiert aufst.: {sorted_asc[:5]}'
      f'\nSortiert abst.: {sorted_desc[:5]}'
      f'\nAnzahl Lines: {lines_total}')
