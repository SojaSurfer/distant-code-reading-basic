from pathlib import Path
import sys

from tokenizers import Tokenizer
from transformers import AutoTokenizer
from tqdm import tqdm


ROOT = Path(__file__).parent
MODEL_PATH = ROOT.parent.parent / 'models'

# each entry is "R;G;B"
colors_list = ['102;194;165','252;141;098','141;160;203','231;138;195','166;216;084','255;217;047',]


def showTokens(sentence, tokenizer) -> None:
    # get token IDs and their textual tokens
    toks = tokenizer(sentence)
    token_ids = toks["input_ids"]
    tokens    = tokenizer.convert_ids_to_tokens(token_ids)

    for idx, tok in enumerate(tokens):
        # pick a color and split it into r,g,b ints
        r, g, b = map(int, colors_list[idx % len(colors_list)].split(';'))

        # build ANSI escapes: 48;2;R;G;B = background true‐color
        bg = f'\x1b[48;2;{r};{g};{b}m'
        # optional: set foreground to black (30) or white (97) for contrast
        fg = '\x1b[30m'
        reset = '\x1b[0m'

        print(f'{bg}{fg}{tok}{reset}', end=' ')
    print()
    return None


def save_tokens_html(sentences: list[str], tokenizerNames:list[str], out_path: Path) -> None:

    body = ''
    tokenizerList = [None] * len(tokenizerNames)

    # preload tokenizers
    tokenizerList = [AutoTokenizer.from_pretrained(name, cache_dir=MODEL_PATH, batched=True)
                        for name in tokenizerNames]


    for sentence in tqdm(sentences, ncols=80, desc='Visualize'):
        body += '<div class="sentence-block">\n'
        # body += '  <h2 class="sentence-heading">Code Line</h2>\n'
        body += f'  <pre class="sentence-text">{sentence}</pre>\n\n'

        for i, tokenizer in enumerate(tokenizerList):
            token_ids = tokenizer(sentence)["input_ids"]
            tokens = tokenizer.convert_ids_to_tokens(token_ids)

            body += create_html_body(tokens, tokenizer.__class__.__qualname__)
        
        body += "</div>\n\n"


    # 4) write a minimal HTML page
        html = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>Token Visualization</title>
        <style>
            .sentence-block {{
            background-color: #f0f0f0;
            padding: 12px;
            margin-bottom: 24px;
            border-radius: 6px;
            }}
            .sentence-heading {{
            font-size: 24px;
            margin: 0 0 8px;
            font-family: sans-serif;
            }}
            .sentence-text {{
            font-family: monospace;
            font-size: 14px;
            line-height: 1.3;
            background: none;
            padding: 0;
            margin: 0 0 12px;
            }}
            .tokenizer-visualization {{
            margin-bottom: 16px;
            }}
            .tokenizer-name {{
            font-size: 18px;
            margin: 4px 0;
            font-family: sans-serif;
            font-weight: bold;
            }}
            .tokenizer-visualization pre {{
            font-family: monospace;
            font-size: 14px;
            line-height: 1.3;
            background: none;
            padding: 0;
            margin: 4px 0 0;
            }}
            .tokenizer-visualization span {{
            display: inline-block;
            }}
        </style>
        </head>
        <body>
        {body}
        </body>
        </html>
        """

    out_path.write_text(html, encoding="utf-8")
    return None


def create_html_body(tokens:list, tokenizerName:str) -> str:
    spans = []
    for idx, tok in enumerate(tokens):
        # pick & parse an R;G;B string
        r, g, b = map(int, colors_list[idx % len(colors_list)].split(";"))
        # inline-CSS style for each token
        style = (f"background-color: rgb({r},{g},{b});"
                " color: black;"
                " padding: 2px 4px;"
                " margin: 0 2px;"
                " border-radius: 3px;"
                " font-family: monospace;"
        )
        spans.append(f'<span style="{style}">{tok}</span>')

    # wrap in a div so we can style per‐tokenizer
    html = '  <div class="tokenizer-visualization">\n'
    html += f'    <div class="tokenizer-name">{tokenizerName}</div>\n'
    html += '    <pre>' + " ".join(spans) + "</pre>\n"
    html += "  </div>\n\n"
    return html



if __name__ == '__main__':

    randomCodeExamples = [
        '  520 ifi-1thena$(lc)=left$(l$,i-1):a(lc)=pc:lc=lc+1',
        '   20 print"{down}{down}load"chr$(34)"demon2"chr$(34)","peek(186)"{home}";',
        '  510 ifpeek(861)>aithengosub550',
        '10110 fori=256to511:pokef+i,peek(c+i):next:forz=0to31step8',
        '    0 print"{clr}{down}{down}poke44,28:poke7168,0:new"',
        '   40 print"{down}this is only the first part of the programm load second part later"',
        '   59 data46,104,172,40,46,0,0,0',
    ]

    modelNames = ['google-bert/bert-base-uncased', 'FacebookAI/xlm-roberta-base', 'google-t5/t5-base', 'Xenova/gpt-4']
    
    save_tokens_html(randomCodeExamples, modelNames, ROOT / 'tokenizer_visualization.html')



