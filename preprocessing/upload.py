import os
from pathlib import Path
import sys

from huggingface_hub import HfApi, CommitInfo
import numpy as np
import pandas as pd 
from rich import traceback, print
traceback.install()


REPO_ID = 'SojaSurfer/homecomp-BASIC-1983-86'


def uploadData(path:str) -> CommitInfo:

    path: Path = Path(path)
    api = HfApi(token=os.getenv("HF_TOKEN"))

    if path.is_file():
        commitInfo = api.upload_file(path_or_fileobj=str(path),
                                     path_in_repo=path.name,
                                     repo_id=REPO_ID,
                                     repo_type="dataset",)
        
    elif path.is_dir():
        commitInfo = api.upload_folder(folder_path=str(path),
                                       repo_id=REPO_ID,
                                       repo_type="dataset",)
        
    else:
        raise FileNotFoundError(str(path))

    return commitInfo


def createDataset(corpus_dir:Path) -> str:

    df = pd.read_excel(corpus_dir / 'metadata.xlsx', dtype={'date': str})
    df['length'] = 0
    df['code'] = ''
    df.index.name = 'index'

    df['date'] = pd.to_datetime(df['date'], format='%m.%Y')
    df['length'] = df['length'].astype(np.uint16)
    # df['disk'] = df['disk'].astype('category')


    filepaths = [file for file in corpus_dir.rglob('*.bas')]
    filepaths.sort()

    for file in filepaths:
        idx = df[df['name'] == file.stem].index

        code, length = loadCodeFile(file)

        df.loc[idx, 'code'] = code
        df.loc[idx, 'length'] = length


    savepath = corpus_dir / 'dataset' / 'dataset.parquet'
    df.to_parquet(savepath)

    return savepath


def loadCodeFile(filepath:Path) -> tuple[str, int]:
    with open(filepath, 'r') as file:
        raw = file.readlines()
    
    raw = [line for line in raw if not line.strip() == '\n'] 
    length = len(raw)

    return (''.join(raw), length)







if __name__ == '__main__':

    corpus_dir = Path('corpus')
    
    parquet_path = createDataset(corpus_dir)
    # parquet_path = 'corpus/dataset/dataset.parquet'

    commitInfo = uploadData(parquet_path)
    print(commitInfo)