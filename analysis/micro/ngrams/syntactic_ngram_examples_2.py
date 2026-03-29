"""The script shows examples of lexical abstraction for generalized n-gram modeling."""

from typing import Any
import pandas as pd

from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder
from nltk.metrics import BigramAssocMeasures, TrigramAssocMeasures


def calculate_ngrams(
    token_sentences: list[list[str]],
    syntax_sentences: list[list[str]],
) -> list[tuple[str, str, float]]:
    """Calculate bigrams where the first syntax element starts with 'C'."""
    all_tokens = [t for sentence in token_sentences for t in sentence]
    all_syntax = [s for sentence in syntax_sentences for s in sentence]

    finder = BigramCollocationFinder.from_words(all_tokens)
    scored = finder.score_ngrams(BigramAssocMeasures.pmi)

    filtered = [
        (w1, w2, score)
        for (w1, w2), score in scored
        if any(
            w1 == tok1 and w2 == tok2 and syn1.startswith("C")
            for (tok1, tok2), (syn1, _) in zip(zip(all_tokens, all_tokens[1:]), zip(all_syntax, all_syntax[1:]))
        )
    ]
    return filtered


def calculate_trigrams(
    token_sentences: list[list[str]],
    syntax_sentences: list[list[str]],
) -> list[tuple[str, str, str, float]]:
    """Trigrams: token_1 = command, token_2/3 = syntax tags."""
    all_tokens = [t for sentence in token_sentences for t in sentence]
    all_syntax = [s for sentence in syntax_sentences for s in sentence]

    finder = TrigramCollocationFinder.from_words(all_tokens)
    scored = finder.score_ngrams(TrigramAssocMeasures.pmi)

    filtered = []
    for (w1, w2, w3), score in scored:
        for (tok1, tok2, tok3), (syn1, syn2, syn3) in zip(
            zip(all_tokens, all_tokens[1:], all_tokens[2:]),
            zip(all_syntax, all_syntax[1:], all_syntax[2:])
        ):
            if (w1, w2, w3) == (tok1, tok2, tok3) and syn1.startswith("C") and syn2[0] in "NSV":
                filtered.append((
                    tok1,  # keep original command
                    syn2,  # abstracted
                    syn3,  # abstracted
                    score
                ))
                break
    return filtered



def sentence_split(df: pd.DataFrame) -> list[list[str]]:
    """Create a nested list of tokens grouped by file and line."""

    sentences = []
    sentence = []
    previous_line = -1

    files = df["file_id"].unique()
    for file in files:
        file_df = df[df["file_id"] == file]
        for _, row in file_df.iterrows():
            if previous_line != row["line"]:
                if sentence:
                    sentences.append(sentence)
                    sentence = []
                previous_line = row["line"]

            sentence.append(row["token"])
            if row["token"] == ":":
                sentences.append(sentence)
                sentence = []

        if sentence:
            sentences.append(sentence)

    return sentences


def is_command(syntax: pd.Series) -> pd.Series:
    return syntax.str.startswith("C")


def is_not_number(syntax: pd.Series) -> pd.Series:
    return ~syntax.str.startswith("N")


if __name__ == "__main__":
    path = r"C:\Users\eric_\Desktop\Schule\BASIC Projektarbeit\tokenized_dataset.parquet"
    df = pd.read_parquet(path)

    # Abstract: keep token where syntax does not start with "C"
    df["ngram_tokens"] = df["syntax"].mask(is_command, df["token"])

    print(df[["token", "syntax", "ngram_tokens"]])

    # Get token-based sentence list
    df["token"] = df["ngram_tokens"]
    token_sentences = sentence_split(df)

    # Get syntax-based sentence list for filtering
    df["token"] = df["syntax"]
    syntax_sentences = sentence_split(df)

    # Bigram processing
    results = calculate_ngrams(token_sentences, syntax_sentences)
    print(results)
    ngram_df = pd.DataFrame(results, columns=["token_1", "token_2", "pmi_score"])
    ngram_df.to_csv(
        r"C:\Users\eric_\Desktop\Schule\BASIC Projektarbeit\ngrams_output.csv", index=False
    )

    # Trigram processing
    trigram_results = calculate_trigrams(token_sentences, syntax_sentences)
    trigram_df = pd.DataFrame(
        trigram_results, columns=["token_1", "token_2", "token_3", "pmi_score"]
    )
    trigram_df.to_csv(
        r"C:\Users\eric_\Desktop\Schule\BASIC Projektarbeit\trigrams_output.csv", index=False
    )

    """ N-gram classes:
    - gensim.models.Phrases
    - nltk.collocations. (whole module for collocations)
    - textacy.extract.ngrams()
    """
