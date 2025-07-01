import datasets

ds_path = 'corpus/dataset/dataset.parquet'
ds = datasets.Dataset.from_parquet(ds_path)

dsdict = ds.train_test_split(test_size=0.2)

print(dsdict)dfdf

def func(arg) -> None:
    """_summary_

    Parameters
    ----------
    arg : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """    
    return None
