import difflib
import struct
import sys
from pathlib import Path
from typing import Any, Generator, Literal, Self

import pandas as pd
from rich import print, traceback

from commodore64BASIC import ASCII_CODES, ASSEMBLY_CHARS, BYTE_TO_CMD, BYTE_TO_CTRL
from tagset import TAGSET1

traceback.install()
""" Current problems:
- number -1 is split into "-" and "1"
- misclassified variables, like "umwandler", "tauchen"
- make variables uppercase
- inv-mc is excluded
"""


def showFileDiffs(file1:str, file2:str) -> None:
    
    with open(file1, 'r') as file:
        tokenized = [line.lower() for line in file.readlines()]

    with open(file2, 'r') as file:
        groundTruth = [line.lower() for line in file.readlines()]


    for file in (tokenized, groundTruth):
        for i, line in enumerate(file):
            while ' ' in line:
                line = line.replace(' ', '')

            file[i] = line


    diff = difflib.unified_diff(groundTruth, tokenized)
    for line in diff:
        print(line)
    
    return None


    

class BASICToken():

    def __init__(self, value:int, lineno:int, **kwargs) -> None:
        self.value = value
        self.lineno = lineno

        self._byte = kwargs.get('byte', bytearray([value]))
        self.byteRepr = kwargs.get('byteRepr', f'0x{value:02x}')
        self.syntax = kwargs.get('syntax', None)
        self.token = kwargs.get('token', '')
        self.language = kwargs.get('language', 'BASIC')
        return None
    
    @property
    def byte(self) -> bytes:
        return bytes(self._byte)
        
    def __str__(self) -> str:
        return f'{self.__class__.__qualname__}({self.value}, {self.byte}, {self.byteRepr}, {self.token}, {self.syntax})'

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}(value={self.value!r}, byte={self.byte!r}, byteRepr={self.byteRepr!r}, token={self.token!r}, syntax={self.syntax!r})'
    
    def __len__(self) -> int:
        return len(self.byte)
    
    def __add__(self, other:Self) -> Self:
        if not isinstance(other, self.__class__):
            raise TypeError('Can only add two BASICToken objects together')
        if not self.lineno == other.lineno:
            raise ValueError(f'Self and other must be in the same line number to be added together, found {self.lineno} and {other.lineno}')
        elif not self.language == other.language:
            raise ValueError(f'Self and other must be in the same language to be added together, found {self.language} and {other.language}')

        value = self.value  # hmm..
        byte = self.byte + other.byte
        byteRepr = self.byteRepr + other.byteRepr
        token = self.token + ' ' + other.token

        return BASICToken(value, self.lineno, byte=byte, byteRepr=byteRepr, token=token)

    def __iadd__(self, other:Self) -> Self:
        if not isinstance(other, self.__class__):
            raise TypeError('Can only add two BASICToken objects together')
        if not self.lineno == other.lineno:
            raise ValueError(f'Self and other must be in the same line number to be added together, found {self.lineno} and {other.lineno}')
        elif not self.language == other.language:
            raise ValueError(f'Self and other must be in the same language to be added together, found {self.language} and {other.language}')

        self.value = other.value  # hmm..
        self._byte = self.byte + other.byte
        self.byteRepr = self.byteRepr + ' ' + other.byteRepr
        self.token = self.token + other.token

        return self
    
    def isWhitespace(self) -> bool:
        return self.byte == b' '
    
    def isDigit(self) -> bool:
        return self.value in ASCII_CODES['number']
    
    def isLetter(self) -> bool:
        return self.value in ASCII_CODES['letter']
    
    def isPunctuation(self) -> bool:
        return self.value in ASCII_CODES['punctuation']
    
    

class BASICFile():

    def __init__(self) -> None:
        self.file: dict[int, list[BASICToken]] = {}
        return None
    
    def __str__(self) -> str:
        return f'{self.__class__.__qualname__}()'
    
    def __getitem__(self, index) -> None:
        return self.file[index]
    

    def printLine(self, index:int = -1) -> None:
        if index == -1:
            index = max(self.file.keys())

        tokenLine = ' '.join([btoken.token for btoken in self.file[index]])
        print(f'{index:>5d} {tokenLine}')
        return None
    
    def addLine(self, tokens:list[BaseException], lineno:int) -> None:
        self.file[lineno] = tokens
        return None
    

    def saveFile(self, path:str) -> None:
        data = []
        for lineno, tokens in self.file.items():
            line = f'{lineno:>5d} {" ".join([tk.token for tk in tokens])}'

            data.append(line)

        with open(path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(data))
        return None
    

    def saveTable(self, path:str) -> pd.DataFrame:
        df = pd.DataFrame(columns=['line', 'token_id', 'bytes', 'token', 'syntax', 'language'])

        for lineno, btokens in self.file.items():
            for idx, btoken in enumerate(btokens):
                    df.loc[len(df)] = [lineno, idx, btoken.byteRepr, btoken.token, btoken.syntax, btoken.language]
        
        df.to_excel(path)
        return df
    
    
    

class Detokenizer():

    def __init__(self) -> None:
        self.filename = None

        self.asciiCodes = {char: key for key, value in ASCII_CODES.items() for char in value}
        return None
    

    def detokenizeBasicFile(self, filename:str) -> BASICFile:
        self.filename = filename

        
        bfile = BASICFile()
        lines_inbetween = (0, 99_999)


        for ln, txt in self.splitBasicLine():
            
            if lines_inbetween[0] <= ln <= lines_inbetween[1]:
                detokenizedLine = self._decodeLine(ln, txt)
                bfile.addLine(detokenizedLine, ln)
 
                # bfile.printLine()

            if ln >= lines_inbetween[1]:
                break


        return bfile
    

    def splitBasicLine(self) -> Generator[tuple[int, bytes], None, None]:
        """
        Parse a tokenized Commodore-BASIC source file into (lineno, content bytes) tuples.
        Assumes:
        - first 2 bytes are header (skip)
        - each line: 2-byte little-endian line number,
                    two-byte pointer to next line?
                    tokenized text ending in 0x00,
        """

        with open(self.filename, 'rb') as f:
            data = f.read()

        pos = 2  # skip header
        end = len(data)
        while pos < end-4:
            # pointer
            ptr,  = struct.unpack_from('<H', data, pos)
            pos += 2

            # read line number
            lineno,  = struct.unpack_from('<H', data, pos)
            pos += 2

            if lineno == 0x00:  # EOF
                return None

            # read text until the 0x00 terminator
            try:
                eol = data.index(0x00, pos)
            except ValueError:
                print(f"No EOL 0x00 found after byte {pos}, assuming EOF")
                eol = len(data)
                return None

            text = data[pos:eol]
            pos = eol + 1  # skip the 0x00

            yield (lineno, text)

        return None


    def _decodeLine(self, lineno:int, line:bytes) -> dict[str, list]:

        if len(line) == 1:
            hexbytes: list[int] = [line[0]]
        else:
            hexbytes: list[int] = [x for x in line]
        
        self.commentCMD = False
        self.printCMD = False
        self.stringDecl = False
        self.parenthesis = 0
        self.lastChar = None
        self.appendBtoken = True
        self.detokenizedLine = []

        for value in hexbytes:
            btoken = BASICToken(value, lineno)

            if btoken.isWhitespace() and not self._withinStringLikeExpression():
                continue
            
            if self.printCMD:
                self._decodePrintStatement(btoken)

            elif self.commentCMD:
                self._decodeCommentStatement(btoken)

            elif value < 0x20:
                # ASCII control char outside of print statement, unclear why
                btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
                if btoken.token == btoken.byte:
                    btoken.syntax = '?_ascii_control_char'
                else:
                    btoken.syntax = TAGSET1['string']['print string']
                if self.stringDecl:
                    self.appendBtoken = False

            elif 0x20 <= value <= 0x7F:
                # value is an ASCII printable character
                self._decodeASCII(btoken)

            elif value >= 0x80:
                # BASIC command statement
                self._decodeCMD(btoken)

            else:
                btoken.token = btoken.byte
                btoken.syntax = '?_unknown'
                self.appendBtoken = True
            

            if self.appendBtoken:
                self.detokenizedLine.append(btoken)
            else:
                if self.detokenizedLine:
                    self.detokenizedLine[-1] += btoken
                else:
                    self.detokenizedLine.append(btoken)


            self.lastChar = btoken
        
        self._checkLineLanguage()

        return self.detokenizedLine


    def _decodeCMD(self, btoken:BASICToken) -> None:
        self.appendBtoken = True

        # other operators: O -> unequal, T, exponent
        if btoken.value in (0xAA, 0xAB, 0xAC, 0xAD, 0xAE):
            syntax = TAGSET1['operators']['arithmetic operators']

        elif btoken.value in (0xB1, 0xB2, 0xB3):
            syntax = TAGSET1['operators']['relational operators']
            if self.lastChar.value in (0xB1, 0xB3):
                # 2-byte relational operator like <=, >=, <>
                self.appendBtoken = False

        elif btoken.value in (0xA8, 0xAF, 0xB0):
            syntax = TAGSET1['operators']['logical operators']

        elif False:
            #TODO: implement strategy for identifying assignment operators
            syntax = TAGSET1['operators']['assignment operators']

        else:
            syntax = TAGSET1['command']
            self.printCMD = btoken.value in (0x98, 0x99) if not self.printCMD else self.printCMD  # PRINT & PRINT#
            self.commentCMD = btoken.value in (0x8F,)  # REM
        
        if self.stringDecl:
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
            btoken.syntax = TAGSET1['string']['print string']
            self.appendBtoken = False
        else:
            btoken.token = BYTE_TO_CMD[btoken.byte]
            btoken.syntax = syntax
        return None
    

    def _decodePrintStatement(self, btoken:BASICToken) -> None:
        # BASIC commands are not available in a string
        if btoken.byte == b'"':
            # first ", start of print statement
            self.parenthesis += 1
            btoken.token = '"'
            self.appendBtoken = True
            
            if self.parenthesis == 2:
                # second ", end of print statement
                self.printCMD = False
                self.parenthesis = 0
                self.appendBtoken = False

        elif self.parenthesis == 0:
            # no " after PRINT detected, check for command
            if btoken.value < 0x80:
                # print(f'Warning: expected <"> as start of string print but found a non-CMD char: {btoken}')
                btoken.token = btoken.byte.decode('ascii', errors='replace').lower()
            else:
                self._decodeCMD(btoken)

            self.printCMD = True

        else:
            # anything in between "" in the print statement
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte.decode('ascii', errors='replace').lower())
            if btoken.value > 0x80 and not btoken.byte in BYTE_TO_CTRL:
                print(btoken, btoken.lineno, [b.token for b in self.detokenizedLine])
            self.appendBtoken = False
        btoken.syntax = TAGSET1['string']['print string']
        return None
    

    def _decodeCommentStatement(self, btoken:BASICToken) -> None:

        btoken.syntax = TAGSET1['string']['comment string']
        if btoken.value < 0x20:
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
        elif btoken.value < 0x80:
            btoken.token = btoken.byte.decode('ascii', errors='replace').lower()
        else:
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte.decode('ascii', errors='replace'))

        if not self.lastChar.value in (0x8F,):
            # a comment where at least one char was placed already
            self.appendBtoken = False

        return None


    def _decodeASCII(self, btoken:BASICToken) -> None:

        btoken.token = chr(btoken.value).lower()
        asciiType = self.asciiCodes.get(btoken.value, 'unknown')

        if asciiType == 'letter':
            btoken.syntax = TAGSET1['variables']['numerical variable']
        elif asciiType == 'number':
            btoken.syntax = TAGSET1['numbers']['integer']
        elif asciiType in ('punctuation', 'sigil'):
            btoken.syntax = TAGSET1['punctuations']['punctuation']
        else:
            btoken.syntax = '?_' + asciiType

        if btoken.isLetter() and not self._withinStringLikeExpression():
            # assumtion: variable
            btoken.syntax = TAGSET1['variables']['numerical variable']

        if self._belongsToPreviousByte(btoken):
            # assumption: either multi-char var name or multi-digit number
            self.appendBtoken = False
        
        else:
            self.appendBtoken = True

        if btoken.byte == b'"':
            self.parenthesis += 1
            self.stringDecl = True
            btoken.syntax = TAGSET1['string']['string']
            if self.parenthesis == 2:
                self.stringDecl = False
                self.parenthesis = 0

        if self.stringDecl:
            btoken.syntax = TAGSET1['string']['string']
        elif btoken.isDigit():
            self._disambiguateMinusSign()
        return None
    

    def _belongsToPreviousByte(self, btoken:BASICToken) -> bool:
        if self.lastChar is None:
            return False
        elif (btoken.isLetter() and self.lastChar.isLetter()) or \
             (btoken.isDigit() and self.lastChar.isDigit()) or self.stringDecl:
            return True
        
        return False
    
    def _withinStringLikeExpression(self) -> bool:
        return any([self.printCMD, self.commentCMD, self.stringDecl])
    

    def _checkLineLanguage(self) -> None:
        tokenizedLine = [b.token for b in self.detokenizedLine]
        if tokenizedLine:
            if tokenizedLine[0].lower() == 'data' and all([char in ASSEMBLY_CHARS for token in tokenizedLine[1:] for char in token]):
                for b in self.detokenizedLine:
                    b.language = 'ASSEMBLY'

        return None
    
    def _disambiguateMinusSign(self) -> None:
        if self.lastChar is not None and self.lastChar.token == '-':
            if len(self.detokenizedLine) > 1:
                if self.detokenizedLine[-2].syntax and self.detokenizedLine[-2].syntax.startswith('O'):
                    # sign belongs to digit
                    self.detokenizedLine[-1].syntax = 'digit'
                    self.appendBtoken = False

        return None
    

if __name__ == '__main__':

    corpusPath = Path(__file__).resolve().parents[2] / 'corpus'
    sourcePath = corpusPath / 'encoded'
    petcatPath = corpusPath / 'decoded' / 'petcat'
    destPath = corpusPath / 'decoded' / 'tokenizer'
    tablePath = corpusPath / 'dataset'


    # erronous files: inv-mc
    df = None
    for disk in ('Homecomp1', 'Homecomp2', 'Homecomp3'):
        for sourceFile in (sourcePath / disk).iterdir():
            if sourceFile.name in ('.DS_Store', 'inv-mc'):
                continue

            print(sourceFile.name)

            # sourceFile = sourcePath / 'Homecomp1' / game
            petcatFile = petcatPath / sourceFile.parent.name / f'{sourceFile.name}.bas'
            destFile = destPath / sourceFile.parent.name / f'{sourceFile.name}.bas'
            tableFile = tablePath / sourceFile.parent.name / f'{sourceFile.name}.xlsx'
            destFile.parent.mkdir(exist_ok=True)
            tableFile.parent.mkdir(exist_ok=True)


            detokenizer = Detokenizer()
            bfile = detokenizer.detokenizeBasicFile(sourceFile)

            bfile.saveFile(destFile)
            table = bfile.saveTable(tableFile)

            table.insert(0, 'game', sourceFile.name)
            if df is None:
                df = table
            else:
                df = pd.concat((df, table), axis=0)

    df.to_parquet(tablePath / 'tokenized_dataset.parquet')

    # print()
    # showFileDiffs(petcatFile, destFile)

    
