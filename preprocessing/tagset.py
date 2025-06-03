

TAGSET0 = {
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

TAGSET1 = {
    "command": "C",
    "operators": {
        "relational operators": "O",
        "arithmetic operators": "O",
        "logical operators": "O",
        "assignment operators": "O",
    },
    "variables": {
        "numerical variable": "V",
        "string variable": "V",
        "array variable": "V",
    },
    "numbers": {
        "integer": "N",
        "float": "N",
        "nan": "N",
    },
    "punctuations": {
        "punctuation": "P",
        "semicolon": "P",
    },
    "string": {
        "print string": "S",
        "comment string": "SC",
        "string": "S",
    },
    "data": "D",  # opcode-mnemonic table with DATA statement, like in assembler.bas line 10_000
}

TAGSET2 = {
    "command": "C",
    "operators": "O",
    "variables": "V",
    "numbers": "N",
    "punctuations": "P",
    "string": "S",
}