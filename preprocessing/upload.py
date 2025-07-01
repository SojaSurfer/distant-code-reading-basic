"""The script provides functions to upload the corpus to HuggingFace Datasets."""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from huggingface_hub import CommitInfo, HfApi
from rich import print, traceback




traceback.install()

REPO_ID = "SojaSurfer/homecomp-BASIC-1983-86"


def upload_data(path:Path) -> CommitInfo:

    path = Path(path)
    api = HfApi(token=os.getenv("HF_TOKEN"))

    if path.is_file():
        commit_info = api.upload_file(path_or_fileobj=str(path),
                                     path_in_repo=path.name,
                                     repo_id=REPO_ID,
                                     repo_type="dataset")
        
    elif path.is_dir():
        commit_info = api.upload_folder(folder_path=str(path),
                                       repo_id=REPO_ID,
                                       repo_type="dataset")
        
    else:
        raise FileNotFoundError(str(path))

    return commit_info


def create_dataset(corpus_dir:Path) -> Path:

    df = pd.read_excel(corpus_dir / "metadata.xlsx", dtype={"date": str})
    df["length"] = 0
    df["code"] = ""
    df.index.name = "index"

    df["date"] = pd.to_datetime(df["date"], format="%m.%Y")
    df["length"] = df["length"].astype(np.uint16)
    # df['disk'] = df['disk'].astype('category')

    filepaths = list(corpus_dir.rglob("*.bas"))
    filepaths.sort()

    for file in filepaths:
        idx = df[df["name"] == file.stem].index

        code, length = load_code_file(file)

        df.loc[idx, "code"] = code
        df.loc[idx, "length"] = length


    savepath = corpus_dir / "dataset" / "dataset.parquet"
    df.to_parquet(savepath)

    return savepath


def load_code_file(filepath:Path) -> tuple[str, int]:
    with open(filepath, "r") as file:
        raw = file.readlines()
    
    raw = [line for line in raw if line.strip() != "\n"] 
    length = len(raw)

    return ("".join(raw), length)




if __name__ == "__main__":

    corpus_dir = Path("corpus")
    
    parquet_path = create_dataset(corpus_dir)
    # parquet_path = 'corpus/dataset/dataset.parquet'

    commit_info = upload_data(parquet_path)
    print(commit_info)