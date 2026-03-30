import pandas as pd
import statistics

# read excel file
df = pd.read_excel('C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/length_in_tokens/test/document_term_matrix/DTM_merged.xlsx')

# setup token count
tokens_total = 0
tokens_listed = []

# deselect columns 'game_id' and 'name'
tokens = df.iloc[:, 2:]

for i in range(0, 57):
    tokens['total_tokens'] = tokens.sum(axis=1)
    print(f'row {i}: {tokens['total_tokens'][i]}')

    tokens_total += int(tokens['total_tokens'][i])
    tokens_listed.append(int(tokens['total_tokens'][i]))

    tokens['total_tokens'] = 0

print(tokens_listed)
print(tokens_total)
#print(tokens)

sorted_asc = sorted(tokens_listed)
sorted_desc = sorted(tokens_listed, reverse=True)

print(f'{tokens_listed}:'
      f'\nMax: {max(tokens_listed)}'
      f'\nMin: {min(tokens_listed)}'
      f'\nMedian: {statistics.median(tokens_listed)}'
      f'\nArithmetisches Mittel: {statistics.mean(tokens_listed)}'
      f'\nSpannweite: {max(tokens_listed) - min(tokens_listed)}'
      f'\nStandardabweichung: {statistics.stdev(tokens_listed)}'
      f'\nSortiert aufst.: {sorted_asc[:5]}'
      f'\nSortiert abst.: {sorted_desc[:5]}'
      f'\nAnzahl Tokens: {tokens_total}')
