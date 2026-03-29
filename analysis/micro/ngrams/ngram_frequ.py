"""Lexical abstraction for generalized n-gram modeling with raw frequencies."""

import pandas as pd
from collections import Counter
import os

def sentence_split(df):
    """Convert dataframe to list of token lists grouped by file and line."""
    sentences = []
    sentence = []
    prev_line = -1

    for file_id in df["file_id"].unique():
        file_df = df[df["file_id"] == file_id]
        for _, row in file_df.iterrows():
            if row["line"] != prev_line:
                if sentence:
                    sentences.append(sentence)
                    sentence = []
                prev_line = row["line"]

            sentence.append(row["token"])
            if row["token"] == ":":
                sentences.append(sentence)
                sentence = []

        if sentence:
            sentences.append(sentence)
            sentence = []

    return sentences

def is_command(syntax):
    return syntax.str.startswith("C")

def calculate_bigrams(filtered_tokens, filtered_syntax):
    """Single-pass bigram frequency count after filtering."""
    bigrams = [
        (filtered_tokens[i], filtered_tokens[i+1])
        for i in range(len(filtered_tokens) - 1)
        if filtered_syntax[i].startswith("C")
    ]
    return Counter(bigrams)

def calculate_trigrams(filtered_tokens, filtered_syntax):
    """Single-pass trigram frequency count after filtering."""
    trigrams = [
        (filtered_tokens[i], filtered_syntax[i+1], filtered_syntax[i+2])
        for i in range(len(filtered_tokens) - 2)
        if filtered_syntax[i].startswith("C") and filtered_syntax[i+1][0] in "NSV"
    ]
    return Counter(trigrams)

if __name__ == "__main__":
    # --- Load dataset ---
    path = r"C:\Users\eric_\Desktop\Desktop Folders\Schule\BASIC Projektarbeit\tokenized_dataset.parquet"
    df = pd.read_parquet(path)

    # --- Pre-filter / lexical abstraction ---
    df["ngram_tokens"] = df["syntax"].mask(is_command, df["token"])

    # Flatten tokens and syntax for single-pass processing
    filtered_tokens = [t for t in df["ngram_tokens"]]
    filtered_syntax = [s for s in df["syntax"]]

    # --- Calculate bigrams & trigrams ---
    bigram_freqs = calculate_bigrams(filtered_tokens, filtered_syntax)
    trigram_freqs = calculate_trigrams(filtered_tokens, filtered_syntax)

    # --- Save to CSV ---
    output_folder = os.path.dirname(os.path.abspath(__file__))

    bigram_df = pd.DataFrame(
    [(t1, t2, freq) for (t1, t2), freq in bigram_freqs.items()],
    columns=["token_1", "token_2", "frequency"]
)
    trigram_df = pd.DataFrame(
    [(t1, t2, t3, freq) for (t1, t2, t3), freq in trigram_freqs.items()],
    columns=["token_1", "token_2", "token_3", "frequency"]
)

    bigram_df.to_csv(os.path.join(output_folder, "bigrams_frequ.csv"), index=False)
    trigram_df.to_csv(os.path.join(output_folder, "trigrams_frequ.csv"), index=False)

    print(f"Bigrams saved: {os.path.join(output_folder, 'bigrams_frequ.csv')}")
    print(f"Trigrams saved: {os.path.join(output_folder, 'trigrams_frequ.csv')}")