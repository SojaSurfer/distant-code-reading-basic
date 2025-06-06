import difflib
import struct
import sys
from pathlib import Path
from typing import Any, Generator, Literal, Self

import pandas as pd
from rich import print, traceback
from tagset import TAGSET1, TAGSET3

from preprocessing.basics import BASICFile, BASICToken
from preprocessing.characterSet import (
    ASCII_CODES,
    ASSEMBLY_CHARS,
    BYTE_TO_CMD,
    BYTE_TO_CTRL,
)
from preprocessing.parser import Parser




traceback.install()
""" Current problems:
- number -.1 is split into "-" and ".1"
- misclassified variables, like "umwandler", "tauchen"
- make variables uppercase
- inv-mc is excluded
- pingi2 line 6030ff:  <6030 "{rvs_on}" rvs ON>
- roulette line 10ff:    <10 * * * * * * * * * * * * * * * * * *>
    skip non-valid BASIC statemtents? -> line-number not followed by a keyword or quoted string
- pingi2 l. 100ff.: . and * are meant as boolean false and true!? . is definitive 0, but * gets Syntax error

"""


def show_file_diffs(file1: str, file2: str) -> None:
    with open(file1, "r") as file:
        tokenized = [line.lower() for line in file.readlines()]

    with open(file2, "r") as file:
        ground_truth = [line.lower() for line in file.readlines()]

    for file in (tokenized, ground_truth):
        for i, line in enumerate(file):
            while " " in line:
                line = line.replace(" ", "")

            file[i] = line

    diff = difflib.unified_diff(ground_truth, tokenized)
    for line in diff:
        print(line)

    return None



class BASICLexer:
    """A class to decode a Commodore BASIC binary file."""

    def __init__(self, tagset:dict) -> None:
        self.parser = Parser(tagset)
        self.tagset = tagset

        self.filename = None
        self.asciiCodes = {char: key for key, value in ASCII_CODES.items() for char in value}

    def detokenize_basic_file(self, filename: str|Path) -> BASICFile:
        """Detokenizes a BASIC file from the given filename.

        This method reads a tokenized BASIC file, processes each line within a specified range,
        detokenizes the content, and adds the detokenized lines to a new BASICFile object.

        Args:
            filename (str | Path): The path to the tokenized BASIC file to be detokenized.

        Returns:
            BASICFile: An object containing the detokenized lines of the BASIC file.
        """

        self.filename = filename

        bfile = BASICFile()
        lines_inbetween = (0, 99_999)

        for ln, txt in self.split_basic_line():
            if lines_inbetween[0] <= ln <= lines_inbetween[1]:
                detokenized_line = self._decode_line(ln, txt)
                bfile.add_line(detokenized_line, ln)

                # bfile.printLine()

            if ln >= lines_inbetween[1]:
                break

        return bfile

    def split_basic_line(self) -> Generator[tuple[int, bytes], None, None]:
        """Parse a tokenized Commodore-BASIC source file into (lineno, content bytes) tuples.

        Assumption:
        - first 2 bytes are header (skip)
        - each line: 2-byte little-endian line number,
                    two-byte pointer to next line?
                    tokenized text ending in 0x00,
        """

        with open(self.filename, "rb") as f:
            data = f.read()

        pos = 2  # skip header
        end = len(data)
        while pos < end - 4:
            # pointer
            (ptr,) = struct.unpack_from("<H", data, pos)
            pos += 2

            # read line number
            (lineno,) = struct.unpack_from("<H", data, pos)
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

    def _decode_line(self, lineno: int, line: bytes) -> list[BASICToken]:
        if len(line) == 1:
            hexbytes: list[int] = [line[0]]
        else:
            hexbytes: list[int] = list(line)  # [x for x in line]

        self.comment_cmd = False
        self.print_cmd = False
        self.string_decl = False
        self.is_data_block = False
        self.parenthesis = 0
        self.last_char: BASICToken = None
        self.append_btoken = True
        self.decoded_tokens: list[BASICToken] = []

        for value in hexbytes:
            btoken = BASICToken(value, lineno)

            if btoken.is_whitespace() and not self._within_string_like_expression():
                continue

            if self.string_decl:
                self._decode_string(btoken)

            elif self.comment_cmd:
                self._decode_comment_statement(btoken)

            elif value < 0x20:
                # ASCII control char outside of print statement, unclear why
                btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
                btoken.syntax = self.parser.parse_string(btoken)

                if self.string_decl:
                    self.append_btoken = False

            elif 0x20 <= value <= 0x7F:
                # value is an ASCII printable character
                self._decode_ascii(btoken)

            elif value >= 0x80:
                # BASIC command statement
                self._decode_cmd(btoken)

            else:
                btoken.token = btoken.byte
                btoken.syntax = "?_unknown"
                self.append_btoken = True

            if self.append_btoken:
                self.decoded_tokens.append(btoken)
            else:
                if self.decoded_tokens:
                    self.decoded_tokens[-1] += btoken
                else:
                    self.decoded_tokens.append(btoken)

            self.last_char = btoken

        self._check_line_language()

        return self.decoded_tokens
    
    def _decode_cmd(self, btoken: BASICToken) -> None:
        self.append_btoken = True
        
        if (btoken.value in (0xB1, 0xB2, 0xB3) and self.last_char.value in (0xB1, 0xB2, 0xB3)
            and btoken.value != self.last_char.value):
            # 2-byte relational operator like <=, >=, <>, =>, =<
            self.append_btoken = False

        elif btoken.value == 0x83 and not self.decoded_tokens:
            self.is_data_block = True


        self.print_cmd = btoken.value in (0x98, 0x99) if not self.print_cmd else self.print_cmd  # PRINT & PRINT#
        self.comment_cmd = btoken.value in (0x8F,)  # REM

        if self.string_decl:
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
            btoken.syntax = self.parser.parse_string(btoken)
            self.append_btoken = False
        else:
            btoken.token = BYTE_TO_CMD[btoken.byte]
            btoken.syntax = self.parser.parse_command(btoken, self.decoded_tokens)

            # disambiguate equal sign
            if btoken.value == 0xB2 and self.decoded_tokens:
                btoken.syntax = self.tagset["operators"]["assignment"]["tag"]

                for prior_token in self.decoded_tokens[::-1]:
                    if prior_token.token == "IF":
                        # relational equal sign
                        btoken.syntax = self.parser.parse_command(btoken, self.decoded_tokens)
                        break
                    elif prior_token.token in (":", ";", "THEN"):
                        # end of command span, since "IF" was not found it is an assignment
                        break

        return None

    def _decode_string(self, btoken: BASICToken) -> None:
        # BASIC commands are not available in a string
        if btoken.byte == b'"':
            # first ", start of print statement
            self.parenthesis += 1
            btoken.token = '"'
            self.append_btoken = True

            if self.parenthesis == 2:
                # second ", end of print statement
                self.parenthesis = 0
                self.append_btoken = False
                self.string_decl = False

        elif self.parenthesis == 0:
            # no <"> after PRINT, expect variable or command
            self.append_btoken = True

            if btoken.value < 0x20:
                # ASCII control char outside of print statement, unclear why
                btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
                btoken.syntax = self.parser.parse_string(btoken)


            elif 0x20 <= btoken.value <= 0x7F:
                # btoken.value is an ASCII printable character
                self._decode_ascii(btoken)

            elif btoken.value >= 0x80:
                # BASIC command statement
                self._decode_cmd(btoken)

            else:
                btoken.token = btoken.byte
                btoken.syntax = "?_unknown"

        else:
            # anything in between "" in the print statement
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte.decode("ascii", errors="replace").lower())
            if btoken.value > 0x80 and btoken.byte not in BYTE_TO_CTRL:
                # add those to the BYTE_TO_CTRL dict
                print(btoken, btoken.lineno, [b.token for b in self.decoded_tokens])
            self.append_btoken = False

            btoken.syntax = self.tagset["string"]["string"]["tag"]
        return None


    def _decode_comment_statement(self, btoken: BASICToken) -> None:
        btoken.syntax = self.tagset["string"]["comment"]["tag"]
        if btoken.value < 0x20:
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
        elif btoken.value < 0x80:
            btoken.token = btoken.byte.decode("ascii", errors="replace").lower()
        else:
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte.decode("ascii", errors="replace"))

        if self.last_char.value not in (0x8F,):
            # a comment where at least one char was placed already
            self.append_btoken = False

        return None

    def _decode_ascii(self, btoken: BASICToken) -> None:
        btoken.token = chr(btoken.value).lower()

        btoken.syntax = self.parser.parse_ascii(btoken, self.decoded_tokens)

        if self._belongs_to_previous_byte(btoken):
            # assumption: either multi-char var name or multi-digit number
            self.append_btoken = False

        else:
            self.append_btoken = True

        if btoken.byte == b'"':
            self.parenthesis += 1
            self.string_decl = True

            if self.parenthesis == 2:
                self.string_decl = False
                self.parenthesis = 0

        if self.string_decl:
            btoken.syntax = self.parser.parse_string(btoken)
        elif btoken.is_digit() or btoken.token == ".":
            self._disambiguate_dot(btoken)

        elif btoken.syntax.startswith("V") or btoken.syntax == "PB" or btoken.is_digit():
            self._disambiguate_minus_sign()

        elif btoken.is_sigil():
            if self.decoded_tokens and self.decoded_tokens[-1].is_letter():
                if btoken.token == "$":
                    self.decoded_tokens[-1].syntax = self.tagset["variables"]["string"]["tag"]
                else:
                    self.decoded_tokens[-1].syntax = self.tagset["variables"]["integer"]["tag"]
            else:
                btoken.syntax = self.tagset["punctuations"]["other"]["tag"]

        elif btoken.token == "(" and self.decoded_tokens and self.decoded_tokens[-1].syntax.startswith("V"):
            # disambiguate parenthesis, could hint at an array variable
            self.decoded_tokens[-1].syntax = f"VA{self.decoded_tokens[-1].syntax[-1]}"

        if self.is_data_block and btoken.is_letter():
            btoken.syntax = self.tagset["data"]["tag"]
        return None

    def _belongs_to_previous_byte(self, btoken: BASICToken) -> bool:
        if self.last_char is None:
            return False
        elif (
            (btoken.is_letter() and self.last_char.is_letter())               # v, a -> va  (variable)
            or (btoken.is_digit() and self.last_char.is_digit())              # 1, 2 -> 12  (number)
            or (btoken.is_digit() and self.last_char.is_letter())             # v, 1 -> v2  (variable)
            or self.string_decl                                               # "hell, o -> "hello (string literal)
            or (btoken.is_sigil() and self.last_char.syntax.startswith("V"))  # v, $ -> v$  (variable)
        ):
            return True

        return False

    def _within_string_like_expression(self) -> bool:
        return any([self.print_cmd, self.comment_cmd, self.string_decl])

    def _check_line_language(self) -> None:
        tokenized_line = [b.token for b in self.decoded_tokens]
        if tokenized_line and tokenized_line[0].lower() == "data" and all(
            (char in ASSEMBLY_CHARS for token in tokenized_line[1:] for char in token),
        ):
            for b in self.decoded_tokens:
                b.language = "ASSEMBLY"

        return None

    def _disambiguate_minus_sign(self) -> None:
        if (self.last_char is not None
            and self.last_char.token == "-"
            and len(self.decoded_tokens) > 1
            and self.decoded_tokens[-2].syntax
            and self.decoded_tokens[-2].syntax.startswith("O")):

                # sign belongs to digit
                self.decoded_tokens[-1].syntax = "digit"
                self.append_btoken = False

        return None

    def _disambiguate_dot(self, btoken:BASICToken) -> None:
        """Add the current token to the previous token if the current token is a dot and
        the previous token was a digit or the current token is a digit and the previous token was a dot.
        """

        if (self.last_char is not None
            and (btoken.token == "." and self.last_char.is_digit()) 
            or self.last_char.token == "."):

                self.decoded_tokens[-1].syntax = self.tagset["numbers"]["real"]["tag"]
                btoken.syntax = self.tagset["numbers"]["real"]["tag"]
                self.append_btoken = False   

        return None




if __name__ == "__main__":
    corpus_path = Path("/Users/julian/Documents/3 - Bildung/31 - Studium/314 Universität Stuttgart/314.2 Semester 2/Projektarbeit/corpus")
    source_path = corpus_path / "encoded"
    petcat_path = corpus_path / "decoded" / "petcat"
    dest_path = corpus_path / "decoded" / "tokenizer"
    table_path = corpus_path / "dataset"

    
    df = pd.DataFrame()
    detokenizer = BASICLexer(TAGSET3)

    for disk in ("Homecomp1", "Homecomp2", "Homecomp3"):
        for source_file in (source_path / disk).iterdir():
            if source_file.name in (".DS_Store", "inv-mc"):
                continue

            print(source_file.name)

            # sourceFile = sourcePath / 'Homecomp1' / game
            petcat_file = petcat_path / source_file.parent.name / f"{source_file.name}.bas"
            dest_file = dest_path / source_file.parent.name / f"{source_file.name}.bas"
            table_file = table_path / source_file.parent.name / f"{source_file.name}.xlsx"
            dest_file.parent.mkdir(exist_ok=True)
            table_file.parent.mkdir(exist_ok=True)

            
            bfile = detokenizer.detokenize_basic_file(source_file)

            dest_file = dest_path / source_file.parent.name / f"{source_file.name}_1.bas"
            bfile.save_file(dest_file)
            table_file = table_path / source_file.parent.name / f"{source_file.name}_1.xlsx"
            table = bfile.save_table(table_file)

            table.insert(0, "name", source_file.name)
            df = table if df.empty else pd.concat((df, table), axis=0)


    print(df)

    metadata_df = pd.read_excel("/Users/julian/Documents/3 - Bildung/31 - Studium/314 Universität Stuttgart/314.2 Semester 2/Projektarbeit/corpus/metadata.xlsx")

    # Merge file_id and game_id from metadata_df into df based on the 'name' column
    df = df.merge(
        metadata_df[["name", "file_id", "game_id"]],
        on="name",
        how="left",
    )

    df = df[["file_id", "game_id", "name", "line", "token_id", "bytes", "token", "syntax", "language"]]
    df.to_parquet(table_path / "tokenized_dataset.parquet")

    # print()
    # showFileDiffs(petcatFile, destFile)
