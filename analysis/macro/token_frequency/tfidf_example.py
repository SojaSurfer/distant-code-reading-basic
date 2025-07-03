import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer




def create_tfidf(dtm:pd.DataFrame) -> pd.DataFrame:
    transformer = TfidfTransformer()

    X = dtm.iloc[:, 2:].to_numpy()  # extract the matrix values
    tfidf_sparse = transformer.fit_transform(X)

    # Convert back to DataFrame with original index and column names
    tfidf = pd.DataFrame(
        tfidf_sparse.toarray(), 
        columns=dtm.columns[2:],
        index=dtm.index ,
    )
    tfidf = pd.concat([dtm.iloc[:, :2], tfidf], axis=1)

    return tfidf




if __name__ == "__main__":
    
    path = "analysis/macro/token_frequency/absolute_frequencies/command_tokens/document_term_matrix/DTM_merged.xlsx"
    dtm = pd.read_excel(path)

    tfidf = create_tfidf(dtm)
    print(tfidf)
    # tfidf.to_excel("analysis/macro/token_frequency/absolute_frequencies/command_tokens/document_term_matrix/TFIDF_merged.xlsx", 
    #                index=False)