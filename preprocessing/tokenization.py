import difflib
import struct
import sys
from pathlib import Path
from typing import Any, Generator, Literal, Self

import pandas as pd
from rich import print, traceback
from tagset import TAGSET1

from preprocessing.characterSet import (
    ASCII_CODES,
    ASSEMBLY_CHARS,
    BYTE_TO_CMD,
    BYTE_TO_CTRL,
)




traceback.install()
""" Current problems:
- number -1 is split into "-" and "1"
- misclassified variables, like "umwandler", "tauchen"
- make variables uppercase
- inv-mc is excluded
- pingi2 line 6030ff:  <6030 "{rvs_on}" rvs ON>
- roulette line 10ff:    <10 * * * * * * * * * * * * * * * * * *>
    skip non-valid BASIC statemtents? -> line-number not followed by a keyword or quoted string
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


class BASICToken:
    """A class that represents one token in the Commodore BASIC programming language."""

    def __init__(self, value: int, lineno: int, **kwargs) -> None:
        self.value = value
        self.lineno = lineno

        self._byte = kwargs.get("byte", bytearray([value]))
        self.byte_repr = kwargs.get("byteRepr", f"0x{value:02x}")
        self.syntax = kwargs.get("syntax")
        self.token = kwargs.get("token", "")
        self.language = kwargs.get("language", "BASIC")

    @property
    def byte(self) -> bytes:
        """The bytes representation of the token."""
        return bytes(self._byte)

    def __str__(self) -> str:
        return (
            f"{self.__class__.__qualname__}({self.value}, {self.byte}, {self.byte_repr}, {self.token}, {self.syntax})"
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(value={self.value!r}, byte={self.byte!r}, byteRepr={self.byte_repr!r}, token={self.token!r}, syntax={self.syntax!r})"

    def __len__(self) -> int:
        return len(self.byte)

    def __add__(self, other: Self) -> Self:
        self._add_check_other(other)

        value = self.value  # hmm..
        byte = self.byte + other.byte
        byte_repr = self.byte_repr + other.byte_repr
        token = self.token + " " + other.token

        return self.__class__(value, self.lineno, byte=byte, byteRepr=byte_repr, token=token)

    def __iadd__(self, other: Self) -> Self:
        self._add_check_other(other)

        self.value = other.value  # hmm..
        self._byte = self.byte + other.byte
        self.byte_repr = self.byte_repr + " " + other.byte_repr
        self.token = self.token + other.token

        return self

    def _add_check_other(self, other: Any) -> None:
        if not isinstance(other, self.__class__):
            msg = "Can only add two BASICToken objects together"
            raise TypeError(msg)

        if self.lineno != other.lineno:
            msg = f"Self and other must be in the same line number to be added together, found {self.lineno} and {other.lineno}"
            raise ValueError(msg)
        elif self.language != other.language:
            msg = f"Self and other must be in the same language to be added together, found {self.language} and {other.language}"
            raise ValueError(msg)
        return None

    def is_whitespace(self) -> bool:
        """Check if token contains only an empty space."""
        return self.byte == b" "

    def is_digit(self) -> bool:
        """Check if token is an ASCII digit."""
        return self.value in ASCII_CODES["number"]

    def is_letter(self) -> bool:
        """Check if token is an ASCII letter."""
        return self.value in ASCII_CODES["letter"]

    def is_punctuation(self) -> bool:
        """Check if token is an ASCII punctuation but not a sigil."""
        return self.value in ASCII_CODES["punctuation"]

    def is_sigil(self) -> bool:
        """Check if token is an BASIC sigil."""
        return self.value in ASCII_CODES["sigil"]


class BASICFile:
    """A class that represents a Commodore BASIC file containing a dict with BASICToken elements."""

    def __init__(self) -> None:
        self.file: dict[int, list[BASICToken]] = {}

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}()"

    def __getitem__(self, index) -> list[BASICToken]:
        return self.file[index]

    def print_line(self, index: int = -1) -> None:
        if index == -1:
            index = max(self.file.keys())

        token_line = " ".join([btoken.token for btoken in self.file[index]])
        print(f"{index:>5d} {token_line}")
        return None

    def add_line(self, tokens: list[BASICToken], lineno: int) -> None:
        self.file[lineno] = tokens
        return None

    def save_file(self, path: str|Path) -> None:
        """Save the BASIC file as an text file."""
        data = []
        for lineno, tokens in self.file.items():
            line = f"{lineno:>5d} {' '.join([tk.token for tk in tokens])}"

            data.append(line)

        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(data))
        return None

    def save_table(self, path: str|Path) -> pd.DataFrame:
        """Save the BASIC file as an Excel file."""

        df = pd.DataFrame(columns=["line", "token_id", "bytes", "token", "syntax", "language"])

        for lineno, btokens in self.file.items():
            for idx, btoken in enumerate(btokens):
                df.loc[len(df)] = [lineno, idx, btoken.byte_repr, btoken.token, btoken.syntax, btoken.language]

        df.to_excel(path)
        return df


class BASICDecoder:
    """A class to decode a Commodore BASIC binary file."""

    def __init__(self) -> None:
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
        self.last_char: BASICToken
        self.append_btoken = True
        self.decoded_tokens: list[BASICToken] = []

        for value in hexbytes:
            btoken = BASICToken(value, lineno)

            if btoken.is_whitespace() and not self._within_string_like_expression():
                continue

            if self.print_cmd:
                self._decode_print_statement(btoken)

            elif self.comment_cmd:
                self._decode_comment_statement(btoken)

            elif value < 0x20:
                # ASCII control char outside of print statement, unclear why
                btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
                if btoken.token == btoken.byte:
                    btoken.syntax = "?_ascii_control_char"
                else:
                    btoken.syntax = TAGSET1["string"]["print string"]
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

        # other operators: O -> unequal, T, exponent
        if btoken.value in (0xAA, 0xAB, 0xAC, 0xAD, 0xAE):
            syntax = TAGSET1["operators"]["arithmetic operators"]

        elif btoken.value in (0xB1, 0xB2, 0xB3):
            syntax = TAGSET1["operators"]["relational operators"]
            if self.last_char.value in (0xB1, 0xB3):
                # 2-byte relational operator like <=, >=, <>
                self.append_btoken = False

        elif btoken.value in (0xA8, 0xAF, 0xB0):
            syntax = TAGSET1["operators"]["logical operators"]

        elif btoken.value == 0x83 and not self.decoded_tokens:
            # first command of line is DATA
            self.is_data_block = True
            syntax = TAGSET1["command"]

        elif False:
            # TODO: implement strategy for identifying assignment operators
            syntax = TAGSET1["operators"]["assignment operators"]

        else:
            syntax = TAGSET1["command"]
            self.print_cmd = btoken.value in (0x98, 0x99) if not self.print_cmd else self.print_cmd  # PRINT & PRINT#
            self.comment_cmd = btoken.value in (0x8F,)  # REM

        if self.string_decl:
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte)
            btoken.syntax = TAGSET1["string"]["print string"]
            self.append_btoken = False
        else:
            btoken.token = BYTE_TO_CMD[btoken.byte]
            btoken.syntax = syntax
        return None

    def _decode_print_statement(self, btoken: BASICToken) -> None:
        # BASIC commands are not available in a string
        if btoken.byte == b'"':
            # first ", start of print statement
            self.parenthesis += 1
            btoken.token = '"'
            self.append_btoken = True

            if self.parenthesis == 2:
                # second ", end of print statement
                self.print_cmd = False
                self.parenthesis = 0
                self.append_btoken = False

        elif self.parenthesis == 0:
            # no " after PRINT detected, check for command
            if btoken.value < 0x80:
                # print(f'Warning: expected <"> as start of string print but found a non-CMD char: {btoken}')
                btoken.token = btoken.byte.decode("ascii", errors="replace").lower()
            else:
                self._decode_cmd(btoken)

            self.print_cmd = True

        else:
            # anything in between "" in the print statement
            btoken.token = BYTE_TO_CTRL.get(btoken.byte, btoken.byte.decode("ascii", errors="replace").lower())
            if btoken.value > 0x80 and btoken.byte not in BYTE_TO_CTRL:
                print(btoken, btoken.lineno, [b.token for b in self.decoded_tokens])
            self.append_btoken = False
        btoken.syntax = TAGSET1["string"]["print string"]
        return None

    def _decode_comment_statement(self, btoken: BASICToken) -> None:
        btoken.syntax = TAGSET1["string"]["comment string"]
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
        ascii_type = self.asciiCodes.get(btoken.value, "unknown")

        if ascii_type == "letter":
            btoken.syntax = TAGSET1["variables"]["numerical variable"]
        elif ascii_type == "number":
            btoken.syntax = TAGSET1["numbers"]["integer"]
        elif ascii_type in ("punctuation", "sigil"):
            btoken.syntax = TAGSET1["punctuations"]["punctuation"]
        else:
            btoken.syntax = "?_" + ascii_type

        if btoken.is_letter() and not self._within_string_like_expression():
            # assumtion: variable
            btoken.syntax = TAGSET1["variables"]["numerical variable"]

        if self._belongs_to_previous_byte(btoken):
            # assumption: either multi-char var name or multi-digit number
            self.append_btoken = False

        else:
            self.append_btoken = True

        if btoken.byte == b'"':
            self.parenthesis += 1
            self.string_decl = True
            btoken.syntax = TAGSET1["string"]["string"]
            if self.parenthesis == 2:
                self.string_decl = False
                self.parenthesis = 0

        if self.string_decl:
            btoken.syntax = TAGSET1["string"]["string"]
        elif btoken.is_digit():
            self._disambiguate_minus_sign()

        if self.is_data_block and btoken.is_letter():
            btoken.syntax = TAGSET1["data"]
        return None

    def _belongs_to_previous_byte(self, btoken: BASICToken) -> bool:
        if self.last_char is None:
            return False
        elif (
            (btoken.is_letter() and self.last_char.is_letter())
            or (btoken.is_digit() and self.last_char.is_digit())
            or self.string_decl
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



if __name__ == "__main__":
    corpus_path = Path(__file__).resolve().parents[2] / "corpus"
    source_path = corpus_path / "encoded"
    petcat_path = corpus_path / "decoded" / "petcat"
    dest_path = corpus_path / "decoded" / "tokenizer"
    table_path = corpus_path / "dataset"

    # erronous files: inv-mc

    STRING = "maschinen"

    df = pd.DataFrame()
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

            detokenizer = BASICDecoder()
            bfile = detokenizer.detokenize_basic_file(source_file)

            bfile.save_file(dest_file)
            table = bfile.save_table(table_file)

            table.insert(0, "game", source_file.name)
            df = table if df.empty else pd.concat((df, table), axis=0)


    print(df)
    df.to_parquet(table_path / "tokenized_dataset.parquet")

    # print()
    # showFileDiffs(petcatFile, destFile)
