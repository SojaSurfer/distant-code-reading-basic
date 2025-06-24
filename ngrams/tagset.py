from collections import OrderedDict




TAGSET1 = {
    "command": "C",
    "operators": {
        "relational operators": "OR",
        "arithmetic operators": "OM",
        "logical operators": "OL",
        "assignment operators": "OA",
    },
    "variables": {
        "numerical variable": "VN",
        "string variable": "VS",
        "array variable": "VA",
    },
    "numbers": {
        "integer": "NI",
        "float": "NF",
        "nan": "NA",
    },
    "punctuations": {
        "semicolon": "PS",
    },
    "string": {
        "print string": "SP",
        "comment string": "SC",
        "string": "SD",
    },
    "data": "D",  # opcode-mnemonic table with DATA statement, like in assembler.bas line 10_000
}



# opcode-mnemonic table with DATA statement, like in assembler.bas line 10_000
TAGSET2 = {
    "command": "C",
    "operators": "O",
    "variables": "V",
    "numbers": "N",
    "punctuations": "P",
    "string": "S",
}

TAGSET3 = OrderedDict({
    "command": {
        "arithmetic": {
            "tag": "CA",
            "values": ["ABS", "INT", "LOG", "RND", "SGN", "SQR", "VAL"],
        },
        "string": {
            "tag": "CS",
            "values": ["ASC", "CHR$", "LEFT$", "LEN", "MID$", "RIGHT$", "STR$"],
        },
        "IO": {
            "tag": "CI",
            "values": ["CLOSE", "CMD", "GET", "INPUT", "INPUT#", "OPEN", "PRINT", "PRINT#", "SPC(", "TAB("],
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
        "other": {
            "tag": "CO",
            "values": ["PI"],
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
        "nan": {
            "tag": "NA",
            "values": [None],
        },
    },
    "punctuations": {
        "semicolon": {
            "tag": "PS",
            "values": [";"],
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
        "other": {
            "tag": "PO",
            "values": [",", ":", "-", "@", "<", "#", "~", "*", "|"],  # also type chars if not used as sigils
        },
    },
    "string": {
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