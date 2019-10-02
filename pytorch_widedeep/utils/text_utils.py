import numpy as np
import pandas as pd
import html
import re

from pathlib import PosixPath
from typing import List
from gensim.utils import tokenize
from fastai.text import Tokenizer
from fastai.text.transform import Vocab

from ..wdtypes import *


def prepare_text(df:pd.DataFrame, text_col:str, max_vocab:int, min_freq:int, maxlen:int,
	word_vectors_path:Optional[str]=None, verbose:int=1):
	texts = df[text_col].tolist()
	tokens = get_texts(texts)
	vocab = Vocab.create(tokens, max_vocab=max_vocab, min_freq=min_freq)
	sequences = [vocab.numericalize(t) for t in tokens]
	padded_seq = np.array([pad_sequences(s, maxlen=maxlen) for s in sequences])
	if verbose:
	    print("The vocabulary contains {} words".format(len(vocab.stoi)))
	if word_vectors_path is not None:
	    embedding_matrix = build_embeddings_matrix(vocab, word_vectors_path)
	else:
		embedding_matrix = None
	return padded_seq, embedding_matrix, vocab


def simple_preprocess(doc:str, lower:bool=False, deacc:bool=False, min_len:int=2,
	max_len:int=15) -> List[str]:
    tokens = [
        token for token in tokenize(doc, lower=False, deacc=deacc, errors='ignore')
        if min_len <= len(token) <= max_len and not token.startswith('_')
    ]
    return tokens


def get_texts(texts:List[str]) -> List[List[str]]:
    processed_textx = [' '.join(simple_preprocess(t)) for t in texts]
    tok = Tokenizer().process_all(processed_textx)
    return tok


def pad_sequences(seq:List[int], maxlen:int=190, pad_first:bool=True, pad_idx:int=1) -> List[List[int]]:
    if len(seq) >= maxlen:
        res = np.array(seq[-maxlen:]).astype('int32')
        return res
    else:
        res = np.zeros(maxlen, dtype='int32') + pad_idx
        if pad_first: res[-len(seq):] = seq
        else:         res[:len(seq):] = seq
        return res


def build_embeddings_matrix(vocab:Vocab, word_vectors_path:PosixPath, verbose:int=1) -> np.ndarray:

	if verbose: print('Indexing word vectors...')

	embeddings_index = {}
	f = open(str(word_vectors_path))
	for line in f:
	    values = line.split()
	    word = values[0]
	    coefs = np.asarray(values[1:], dtype='float32')
	    embeddings_index[word] = coefs
	f.close()

	if verbose:
		print('Loaded {} word vectors'.format(len(embeddings_index)))
		print('Preparing embeddings matrix...')

	mean_word_vector = np.mean(list(embeddings_index.values()), axis=0)
	embedding_dim = len(list(embeddings_index.values())[0])
	num_words = len(vocab.itos)
	embedding_matrix = np.zeros((num_words, embedding_dim))
	found_words=0
	for i,word in enumerate(vocab.itos):
	    embedding_vector = embeddings_index.get(word)
	    if embedding_vector is not None:
	        embedding_matrix[i] = embedding_vector
	        found_words+=1
	    else:
	        embedding_matrix[i] = mean_word_vector

	if verbose:
		print('{} words in the vocabulary had {} vectors and appear more than the min frequency'.format(found_words, word_vectors_path))

	return embedding_matrix
