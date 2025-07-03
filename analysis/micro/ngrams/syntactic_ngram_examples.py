"""The script shows examples of lexical abstraction for generalized n-gram modeling."""

from typing import Any

import pandas as pd




def calculate_ngrams(tokens:list[str]) -> Any:
    raise NotImplementedError


def sentence_split(df:pd.DataFrame) -> list[list[str]]:
    """Create a nested list of tokens."""

    sentences = [] # structure: [["REM", "Hello"], ["PRINT", "a$"], ...]
    sentence = []
    previous_line = -1

    files = df["file_id"].unique()

    for file in files:
        # iterate over every file to avoid previous line matching with new file
        file_df = df[df["file_id"] == file]

        for idx, row in file_df.iterrows():

            # Start new sentence if line changes
            if previous_line != row["line"]:
                if sentence:  # Save current sentence if it exists
                    sentences.append(sentence)
                    sentence = []
                previous_line = row["line"]
            
            # Add token to current sentence
            sentence.append(row["token"])
            
            # End sentence if token is a colon
            if row["token"] == ":":
                sentences.append(sentence)
                sentence = []

        if sentence:
            # append the last sentence
            sentences.append(sentences)

    return sentences



def is_command(syntax:pd.Series) -> pd.Series:
    return syntax.str.startswith("C")


def is_not_number(syntax:pd.Series) -> pd.Series:
    return ~syntax.str.startswith("N")



if __name__ == "__main__":

    path = "corpus/dataset/tokenized_dataset.parquet"
    path = "/Users/julian/Documents/3 - Bildung/31 - Studium/314 Universität Stuttgart/314.2 Semester 2/Projektarbeit/corpus/dataset/tokenized_dataset.parquet"
    df = pd.read_parquet(path)


    df["ngram_tokens"] = df["syntax"].mask(is_command, df["token"])

    print(df[["token", "syntax", "ngram_tokens"]])

    # sentences = sentence_split(df)

    # calculate_ngrams(sentences)

    """ N-gram classes:
    - gensim.models.Phrases
    - nltk.collocations. (whole module for collocations)
    - textacy.extract.ngrams()
    - ...
    """