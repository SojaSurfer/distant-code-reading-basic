import pandas as pd


# Create the data structure from your markdown
data = []

# 1 Commands
commands = [
    ("CA", "arithmetische Commands", "ABS, SQR"),
    ("CS", "String-basierte Commands", "ASC, LEFT$"),
    ("CI", "I/O-basierte Commands", "CLOSE, INPUT"),
    ("CV", "spezifische Variablendeklaration", "CLR, DATA"),
    ("CD", "Funktionsdeklaration", "DEF"),
    ("CC", "File-Run Control", "RUN, STOP"),
    ("CP", "Program Control", "GOTO, FOR"),
    ("CE", "Editor", "LOAD, SAVE"),
    ("CM", "Memory", "NEW"),
    ("CR", "System", "PEEK, POKE"),
]

for tag, explanation, example in commands:
    data.append({"Kategorie": "Commands", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 2 Operatoren
operators = [
    ("OA", "arithmetische Operatoren", "+, *"),
    ("OR", "relationale Operatoren", "<=, ="),
    ("OL", "logische Operatoren", "AND, OR"),
    ("OS", "Zuweisungsoperator", "="),
    ("OU", "Unäre Operatoren", "-, +"),
]

for tag, explanation, example in operators:
    data.append({"Kategorie": "Operatoren", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 3 Konstanten
constants = [("TA", "arithmetische Konstanten", "PI")]

for tag, explanation, example in constants:
    data.append({"Kategorie": "Konstanten", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 4 Systemvariablen
system_vars = [("YT", "Zeit-basierte Systemvariablen", "ti, ti$"), ("YI", "I/O-basierte Systemvariablen", "st")]

for tag, explanation, example in system_vars:
    data.append({"Kategorie": "Systemvariablen", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 5 Variablen
variables = [
    ("VR", "Variable mit Type reele Zahl", "i, a"),
    ("VI", "Variable mit Type integer Zahl", "i%, a%"),
    ("VS", "Variable mit Type String", "s$, h$"),
    ("VAR", "Variable mit reelen Zahlen Array", "i(4), a(7)"),
    ("VAI", "Variable mit integer Zahlen Array", "i%(4), a%(7)"),
    ("VAS", "Variable mit String Array", "s$(4), a$(7)"),
]

for tag, explanation, example in variables:
    data.append({"Kategorie": "Variablen", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 6 Zahlen
numbers = [("NR", "reele Zahl", "3.512, .7"), ("NI", "integer Zahl", "3, 0")]

for tag, explanation, example in numbers:
    data.append({"Kategorie": "Zahlen", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 7 Strings
strings = [("SC", "Kommentar", "Copyright by"), ("SL", "String", '"Hallo"')]

for tag, explanation, example in strings:
    data.append({"Kategorie": "Strings", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 8 Interpunktion
punctuation = [
    ("PC", "Doppelpunkt, Statement Trenner", ":"),
    ("PP", "Klammern", "(, )"),
    ("PT", "Variabeltyp, Sigil", "$, %"),
    ("PB", "Punkt/Boolean", "."),
    ("PS", "Separatoren", ", ;"),
    ("PO", "Andere Interpunktionen", "-, @, #"),
]

for tag, explanation, example in punctuation:
    data.append({"Kategorie": "Interpunktion", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# 9 Data
data_section = [("D", "opcode-mnemonische Tabelle", "a,!,r")]

for tag, explanation, example in data_section:
    data.append({"Kategorie": "Data", "Tag": tag, "Erklärung": explanation, "Beispiel": example})

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel with formatting
with pd.ExcelWriter("tagset.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Tagset", index=False)

    # Get the workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets["Tagset"]

    # Auto-adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width

print("Excel file 'tagset.xlsx' created successfully!")
print(f"Total entries: {len(df)}")
print("\nEntries per category:")
print(df["Kategorie"].value_counts())
