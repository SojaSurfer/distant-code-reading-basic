import pandas as pd
from collections import Counter, OrderedDict

TAGSET = OrderedDict({
    "system": {
        "time": {
            "tag": "YT",
            "values": ["ti", "ti$"],
        },
        "IO": {
            "tag": "YI",
            "values": ["st"],
        },
    },
    "commands": {
        "arithmetic": {
            "tag": "CA",
            "values": ["ABS", "INT", "LOG", "RND", "SGN", "SQR", "VAL", "SIN", "COS", "TAN", "ATN", "EXP"],
        },
        "string": {
            "tag": "CS",
            "values": ["ASC", "CHR$", "LEFT$", "LEN", "MID$", "RIGHT$", "STR$"],
        },
        "IO": {
            "tag": "CI",
            "values": ["CLOSE", "CMD", "GET", "INPUT", "INPUT#", "OPEN", "PRINT", "PRINT#", "?", "SPC(", "TAB("],
        },
        "variables": {
            "tag": "CV",
            "values": ["CLR", "DATA", "DIM", "LET", "READ", "RESTORE"],
        },
        "functions": {
            "tag": "CD",
            "values": ["DEF"],
        },
        "control": {
            "tag": "CC",
            "values": ["RUN", "STOP", "END"],
        },
        "program": {
            "tag": "CP",
            "values": ["FN", "FOR", "GOSUB", "GOTO", "IF", "NEXT", "ON", "REM", "RETURN", "STEP", "THEN", "TO"],
        },
        "editor": {
            "tag": "CE",
            "values": ["LOAD", "SAVE"],
        },
        "memory": {
            "tag": "CM",
            "values": ["NEW"],
        },
        "system": {
            "tag": "CR",
            "values": ["PEEK", "POKE", "SYS", "USR", "WAIT"],
        },
    },
    "operators": {
        "arithmetic": {
            "tag": "OA",
            "values": ["+", "-", "*", "/", "^"],
        },
        "relational": {
            "tag": "OR",
            "values": ["<", ">", "<=", ">=", "=<", "=>", "<>", "="],
        },
        "logical": {
            "tag": "OL",
            "values": ["AND", "OR", "NOT"],
        },
        "assignment": {
            "tag": "OS",
            "values": ["="],
        },
        "unary": {
            "tag": "OU",
            "values": ["+", "-"],
        },
    },
    "constants": {
        "arithmetic": {
            "tag": "TA",
            "values": ["PI"],
        },
    },
    "variables": {
        "real": {
            "tag": "VR",
            "values": [None],
        },
        "integer": {
            "tag": "VI",
            "values": [None],
        },
        "string": {
            "tag": "VS",
            "values": [None],
        },
        "array_real": {
            "tag": "VAR",
            "values": [None],
        },
        "array_integer": {
            "tag": "VAI",
            "values": [None],
        },
        "array_string": {
            "tag": "VAS",
            "values": [None],
        },
    },
    "numbers": {
        "real": {
            "tag": "NR",
            "values": [None],
        },
        "integer": {
            "tag": "NI",
            "values": [0,1,2,3,4,5,6,7,8,9],
        },
    },
    "punctuations": {
        "colon": {
            "tag": "PC",
            "values": [":"],
        },
        "parenthesis": {
            "tag": "PP",
            "values": ["(", ")"],
        },
        "type": {
            "tag": "PT",
            "values": ["$", "%"],
        },
        "bool": {
            "tag": "PB",
            "values": ["."],
        },
        "separator": {
            "tag": "PS",
            "values": [",", ";"],
        },
        "other": {
            "tag": "PO",
            "values": ["-", "@", "<", "#", "~", "*", "|"],  # also type chars if not used as sigils
        },
    },
    "strings": {
        "comment": {
            "tag": "SC",
            "values": [None],
        },
        "string": {
            "tag": "SL",
            "values": [None],
        },
    },
    "data": {
        "tag": "D",  # opcode-mnemonic table with DATA statement, like in assembler.bas line 10_000
        "values": [None],
    },
})

# Flatten the TAGSET to map value -> tag
value_to_tag = {}
tag_to_name = {}  # optional, for nicer CSVs

def flatten_tagset(tagset):
    for category, subcats in tagset.items():
        if isinstance(subcats, dict):
            flatten_tagset(subcats)
        elif isinstance(subcats, list):
            # terminal case: should not happen in your TAGSET
            pass
        elif 'tag' in subcats and 'values' in subcats:
            tag = subcats['tag']
            for val in subcats['values']:
                if val is not None:
                    value_to_tag[val] = tag
            tag_to_name[tag] = category

flatten_tagset(TAGSET)

# Read the parquet file
df = pd.read_parquet(r"C:\Users\eric_\Desktop\Desktop Folders\Schule\BASIC Projektarbeit\distant-code-reading-basic\analysis\micro\ngrams\tokenized_dataset.parquet")

# Assuming the tokens are in a column named "token"
tokens = df['token'].tolist()

# Count token occurrences
token_counter = Counter(tokens)

# Count tag occurrences
tag_counter = Counter()
for tok in tokens:
    tag = value_to_tag.get(tok)
    if tag:
        tag_counter[tag] += 1
    else:
        tag_counter['UNKNOWN'] += 1  # for tokens not in TAGSET

# Save token counts CSV
pd.DataFrame(token_counter.items(), columns=['token', 'count']) \
    .sort_values(by='count', ascending=False) \
    .to_csv(r"C:\Users\eric_\Desktop\Desktop Folders\Schule\BASIC Projektarbeit\distant-code-reading-basic\analysis\micro\ngrams\token_counts.csv", index=False)

# Save tag counts CSV
pd.DataFrame(tag_counter.items(), columns=['tag', 'count']) \
    .sort_values(by='count', ascending=False) \
    .to_csv(r"C:\Users\eric_\Desktop\Desktop Folders\Schule\BASIC Projektarbeit\distant-code-reading-basic\analysis\micro\ngrams\tag_counts.csv", index=False)

print("Done! token_counts.csv and tag_counts.csv generated.")