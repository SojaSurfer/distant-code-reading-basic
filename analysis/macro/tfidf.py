import pandas as pd
from sklearn.feature_extraction.text import TfidfTransformer


def create_tfidf(dtm:pd.DataFrame) -> pd.DataFrame:
    transformer = TfidfTransformer()

    X = dtm.iloc[:, 3:].to_numpy()  # extract the matrix values
    tfidf_sparse = transformer.fit_transform(X)

    # Convert back to DataFrame with original index and column names
    tfidf = pd.DataFrame(
        tfidf_sparse.toarray(),
        columns=dtm.columns[3:],
        index=dtm.index,
    )
    tfidf = pd.concat([dtm.iloc[:, :3], tfidf], axis=1)

    return tfidf


if __name__ == "__main__":

    path = "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/relative_frequencies/command_tokens/clustering/4/document_term_matrix/DTM_merged.xlsx"
    dtm = pd.read_excel(path)

    tfidf = create_tfidf(dtm)
    print(tfidf)

    tfidf.to_excel("C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/relative_frequencies/command_tokens/clustering/4/tf_idf/tf_idf.xlsx", index=False)

    print("All done!")


