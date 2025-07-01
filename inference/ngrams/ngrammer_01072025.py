import pandas as pd
import os
from collections import Counter
from tagset import TAGSET  # Assumes TAGSET defines token types and command vocabularies

# Directory containing this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Collect syntax tags from TAGSET
STRING_TAGS = [v["tag"] for v in TAGSET.get("strings", {}).values() if v["tag"]]
VARIABLE_TAGS = [v["tag"] for v in TAGSET.get("variables", {}).values() if v["tag"]]
INTEGER_TAGS = [v["tag"] for v in TAGSET.get("numbers", {}).values() if v["tag"]]
PUNCT_TAGS = [v["tag"] for v in TAGSET.get("punctuations", {}).values() if v["tag"]]

# Flatten list of all possible command tokens
COMMANDS = TAGSET.get("commands", {})
ALL_COMMAND_TOKENS = [val for cat in COMMANDS.values() for val in cat.get("values", []) if val]

# Extract a centered ngram of tokens within a line window
def extract_ngram(df, center_idx, window_size, placeholder_tags=None, skip_center=False, mask_center=False):
    center_line = df.iloc[center_idx]['line']
    start = max(0, center_idx - window_size)
    end = min(len(df), center_idx + window_size + 1)
    window = df.iloc[start:end]

    # Ensure window doesn't cross lines
    if not all(window['line'] == center_line):
        return None

    ngram = []
    for i, row in window.iterrows():
        # Mask or skip the center token if configured
        if mask_center and i == df.index[center_idx]:
            ngram.append("SKIP")
        else:
            ngram.append(row['token'])

    return {
        'name': df.iloc[center_idx].get('name'),
        'game_id': df.iloc[center_idx].get('game_id'),
        'ngram': ngram,
        'matched_token': df.iloc[center_idx]['token'],
        'matched_category': 'generic-ngram',
        'line': center_line
    }

# Extract ngrams centered around any token with matching tag
def ngram_around_tag(df, tags, window_size, mask_center=False):
    results = []
    for i in range(len(df)):
        if df.iloc[i]['syntax'] in tags:
            out = extract_ngram(df, i, window_size, tags, mask_center=mask_center)
            if out:
                out['matched_category'] = 'ngram-around-' + df.iloc[i]['syntax']
                results.append(out)
    return results

# Get [command, token1, token2] where token1 matches accepted_tags
def skipgram_following(df, command_token, accepted_tags):
    results = []
    for i in range(len(df) - 2):
        curr, next1, next2 = df.iloc[i], df.iloc[i + 1], df.iloc[i + 2]
        if (command_token is None or curr['token'].upper() == command_token) and \
           next1['syntax'] in accepted_tags and \
           curr['line'] == next1['line'] == next2['line']:
            results.append({
                'name': curr.get('name'),
                'game_id': curr.get('game_id'),
                'ngram': [curr['token'], next1['token'], next2['token']],
                'matched_token': curr['token'],
                'matched_category': 'command-int-var',
                'line': curr['line']
            })
    return results

# Extract [command, token1] for any known command token
def command_plus_following(df):
    results = []
    for i in range(len(df) - 1):
        curr, next1 = df.iloc[i], df.iloc[i + 1]
        if curr['token'] in ALL_COMMAND_TOKENS and curr['line'] == next1['line']:
            results.append({
                'name': curr.get('name'),
                'game_id': curr.get('game_id'),
                'ngram': [curr['token'], next1['token']],
                'matched_token': curr['token'],
                'matched_category': 'command-plus-1',
                'line': curr['line']
            })
    return results


# Extract [any_command, variable, *] patterns
def command_variable(df):
    return skipgram_following(df, command_token=None, accepted_tags=VARIABLE_TAGS)

# Extract [command, integer, variable] sequences
def command_integer_then_variable(df):
    results = []
    for i in range(len(df) - 2):
        curr, next1, next2 = df.iloc[i], df.iloc[i + 1], df.iloc[i + 2]
        if curr['token'] in ALL_COMMAND_TOKENS and \
           next1['syntax'] in INTEGER_TAGS and \
           next2['syntax'] in VARIABLE_TAGS and \
           curr['line'] == next1['line'] == next2['line']:
            results.append({
                'name': curr.get('name'),
                'game_id': curr.get('game_id'),
                'ngram': [curr['token'], next1['token'], next2['token']],
                'matched_token': curr['token'],
                'matched_category': 'command-int-var',
                'line': curr['line']
            })
    return results

# Count unique ngrams and return with frequency
def count_ngrams(records):
    counter = Counter(tuple(r['ngram']) for r in records)
    return [{'ngram': list(k), 'count': v} for k, v in counter.items()]

# Save raw and counted ngram dataframes
def save_df(name, data, raw_dir, counted_dir):
    df = pd.DataFrame(data)

    # Remove 'command' field for non-command categories
    if not name.startswith("command") and "print" not in name:
        df = df.drop(columns=['command'], errors='ignore')

    df.to_csv(os.path.join(raw_dir, f"{name}_ngrams_raw.csv"), index=False)
    pd.DataFrame(count_ngrams(data)).to_csv(os.path.join(counted_dir, f"{name}_ngram_counts.csv"), index=False)

# Entry point to run all extraction routines and save results
def main(parquet_path):
    df = pd.read_parquet(parquet_path)
    output_dir = SCRIPT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # Define all ngram extraction routines to run
    configs = [
        ("punctuation", ngram_around_tag(df, PUNCT_TAGS, 3)),
        ("string", ngram_around_tag(df, STRING_TAGS, 3, mask_center=True)),
        ("variable", ngram_around_tag(df, VARIABLE_TAGS, 3, mask_center=True)),
        ("integer", ngram_around_tag(df, INTEGER_TAGS, 3, mask_center=True)),
        ("print_followed_by_var_or_str", skipgram_following(df, "PRINT", STRING_TAGS + VARIABLE_TAGS)),
        ("command_plus_1", command_plus_following(df)),
        ("command_followed_by_var", command_variable(df)),
        ("command_int_var", command_integer_then_variable(df))
    ]

    # Ensure output directories exist
    raw_dir = os.path.join(output_dir, "raw")
    counted_dir = os.path.join(output_dir, "counted")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(counted_dir, exist_ok=True)

    # Save outputs for each routine
    for name, data in configs:
        save_df(name, data, raw_dir, counted_dir)

# Run script from CLI or default input path
if __name__ == "__main__":
    import sys
    f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRIPT_DIR, 'tokenized_dataset.parquet')
    main(f)
