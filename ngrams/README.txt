ngrammer

Requires:
- tokenized_dataset.parquet
- tagset.py including TAGSET3

Running it will create the following files:

- command_string_ngrams
	Contains ngrams of print + a skipgram of the following string

- iterative_command_ngrams_depth1, 2 and 3
	Contain ngrams of command + any token, command + variable tokens, command + integer + variable tokens respectively

- punctuation_ngrams
	Contains ngrams of punctuations in a window of 2 in each direction

- skipgram_ngrams
	Contains skipgrams of variables, strings and integers