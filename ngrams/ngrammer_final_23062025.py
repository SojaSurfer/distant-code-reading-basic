import pandas as pd
import sys
import os
from tagset import TAGSET3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_all_command_tokens():
    commands = TAGSET3.get("command", {})
    tokens = []
    for category in commands.values():
        tokens.extend(category.get("values", []))
    return [t for t in tokens if t is not None]

def get_command_category(token):
    for group_name, group in TAGSET3.get("command", {}).items():
        if token in group.get("values", []):
            return group["tag"]
    return "UNKNOWN"

def get_all_punctuation_tags():
    punctuations = TAGSET3.get("punctuations", {})
    return [info["tag"] for info in punctuations.values()]

def get_placeholder_tags():
    # Placeholder tokens (variable, string, integer tags)
    variable_tags = [v["tag"] for v in TAGSET3.get("variable", {}).values() if v["tag"] is not None]
    string_tags = [v["tag"] for v in TAGSET3.get("string", {}).values() if v["tag"] is not None]
    integer_tags = [v["tag"] for v in TAGSET3.get("integer", {}).values() if v["tag"] is not None]
    return variable_tags + string_tags + integer_tags

def extract_adjacent_command_string_ngrams(df, command_token='PRINT'):
    string_tags = [v["tag"] for v in TAGSET3.get("string", {}).values() if v["tag"] is not None]
    results = []
    for i in range(len(df) - 1):
        curr, next_tok = df.iloc[i], df.iloc[i + 1]
        if curr['token'].upper() == command_token and next_tok['syntax'] in string_tags and curr['line'] == next_tok['line']:
            results.append({
                'command': curr['token'],
                'string_value': next_tok['token'],
                'ngram': [curr['token'], next_tok['token']],
                'matched_token': curr['token'],
                'matched_category': 'command-string-adjacent',
                'line': curr['line'],
                'name': curr.get('name', None),
                'game_id': curr.get('game_id', None)
            })
    return results

def extract_ngrams_generic(
    df,
    main_tag='command',
    placeholder_tags=None,
    window_size=3,
    include_center=True,
    category_name=None,
    category_fn=None,
    ngram_key='ngram',
    extra_fields_fn=None,
    max_depth=3,
    iterative=False,
    command_tokens=None
):
    if placeholder_tags is None:
        placeholder_tags = []
    if category_fn is None:
        category_fn = lambda x: "UNKNOWN"
    results = []

    if iterative and command_tokens is not None:
        filtered_df = df[df['token'].isin(command_tokens)]
        for i, row in filtered_df.iterrows():
            line_df = df[df['line'] == row['line']].reset_index()
            index_in_line = line_df.index[line_df['index'] == i].tolist()
            if not index_in_line:
                continue
            pos = index_in_line[0]

            # Build ngrams incrementally, only including placeholders behind the command token
            for depth in range(1, max_depth + 1):
                start = max(0, pos - depth)
                seq_tokens = line_df.loc[start:pos, ['token', 'syntax']].to_dict('records')

                # Reverse tokens so command token is first, then placeholders behind
                seq_tokens = [seq_tokens[-1]] + seq_tokens[:-1]

                # Validate: first token must be command token, rest placeholders
                valid_seq = True
                if seq_tokens[0]['token'] != row['token']:
                    valid_seq = False
                for t in seq_tokens[1:]:
                    if t['syntax'] not in placeholder_tags:
                        valid_seq = False
                        break

                if not valid_seq:
                    continue

                ngram_tokens = [t['token'] for t in seq_tokens]
                results.append({
                    'depth': depth,
                    ngram_key: ngram_tokens,
                    'matched_token': row['token'],
                    'matched_category': category_fn(row['token']),
                    'line': row['line'],
                    'name': row.get('name', None),
                    'game_id': row.get('game_id', None)
                })

    else:
        # Standard ngram or skipgram extraction
        filtered_df = df[df['syntax'].isin(placeholder_tags if placeholder_tags else placeholder_tags)]
        for i, row in filtered_df.iterrows():
            line_df = df[df['line'] == row['line']].reset_index()
            index_in_line = line_df.index[line_df['index'] == i].tolist()
            if not index_in_line:
                continue
            pos = index_in_line[0]

            start = max(0, pos - window_size)
            end = min(len(line_df), pos + window_size + 1)
            tokens_window = line_df.loc[start:end, ['token', 'syntax']].to_dict('records')

            if include_center:
                ngram_tokens = [t['token'] for t in tokens_window]
            else:
                # exclude the center token, replace with '_'
                ngram_tokens = []
                for idx, t in enumerate(tokens_window):
                    if start + idx == pos:
                        ngram_tokens.append('_')
                    else:
                        ngram_tokens.append(t['token'])

            res = {
                ngram_key: ngram_tokens,
                'matched_token': row['token'],
                'matched_category': category_name or category_fn(row['token']),
                'line': row['line'],
                'name': row.get('name', None),
                'game_id': row.get('game_id', None)
            }
            if extra_fields_fn:
                res.update(extra_fields_fn(row, line_df, pos))

            results.append(res)

    return results


def main(parquet_file, max_depth=3):
    df = pd.read_parquet(parquet_file)

    # 1. Punctuation ngrams (simple ngrams around punctuation tags)
    punctuation_results = extract_ngrams_generic(
        df,
        placeholder_tags=get_all_punctuation_tags(),
        window_size=max_depth,
        include_center=True,
        category_name='punctuation',
        max_depth=max_depth
    )

    # 2. Skipgram for variable/string/integer tokens, excluding the token from ngram
    placeholder_tags = get_placeholder_tags()
    skipgram_results = extract_ngrams_generic(
        df,
        placeholder_tags=placeholder_tags,
        window_size=max_depth,
        include_center=False,
        category_name='skipgram',
        extra_fields_fn=lambda row, line_df, pos: {
            'skipped_token': row['token'],
            'skip_tag': row['syntax']
        },
        max_depth=max_depth
    )

    # 3. Iterative ngrams starting from command tokens with placeholders behind
    command_tokens = get_all_command_tokens()
    iterative_results = extract_ngrams_generic(
        df,
        main_tag='command',
        placeholder_tags=placeholder_tags,
        max_depth=max_depth,
        iterative=True,
        command_tokens=command_tokens,
        category_fn=get_command_category,
        ngram_key='ngram'
    )

    # 4. Adjacent command-string ngrams (e.g. PRINT + string token)
    command_string_results = extract_adjacent_command_string_ngrams(df, command_token='PRINT')

    # Save as Excel files
    output_dir = SCRIPT_DIR  # Save outputs in same folder as script
    os.makedirs(output_dir, exist_ok=True)

    all_results = {
        'punctuation_ngrams': punctuation_results,
        'skipgram_ngrams': skipgram_results,
        'command_string_ngrams': command_string_results
    }

    # Save standard outputs
    for name, results in all_results.items():
        output_path = os.path.join(output_dir, f"{name}.csv")
        pd.DataFrame(results).to_csv(output_path, index=False)

    # Save iterative command ngrams by depth
    iterative_df = pd.DataFrame(iterative_results)
    if not iterative_df.empty:
        for depth in sorted(iterative_df['depth'].unique()):
            subset = iterative_df[iterative_df['depth'] == depth]
            output_path = os.path.join(output_dir, f"iterative_command_ngrams_depth{depth}.csv")
            subset.to_csv(output_path, index=False)

    print(f"All done. Results saved to {output_dir}")

if __name__ == "__main__":
    default_file = os.path.join(SCRIPT_DIR, 'tokenized_dataset.parquet')
    default_depth = 3

    if len(sys.argv) >= 2:
        parquet_file = sys.argv[1]
        max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else default_depth
    else:
        parquet_file = default_file
        max_depth = default_depth

    main(parquet_file, max_depth)
