import csv

INPUT = r"C:\Users\eric_\Desktop\Desktop Folders\Schule\BASIC Projektarbeit\trigrams_output_plot.csv"
OUTPUT = r"C:\Users\eric_\Desktop\Desktop Folders\Schule\BASIC Projektarbeit\trigrams_output_plot_reduced.csv"

allowed = ("REM", "PEEK", "POKE", "PRINT")

with open(INPUT, newline="", encoding="utf-8") as infile, \
     open(OUTPUT, "w", newline="", encoding="utf-8") as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for row in reader:
        if not row:
            continue
        first_cell = row[0]
        if any(first_cell.upper().startswith(k) for k in allowed):
            writer.writerow(row)
