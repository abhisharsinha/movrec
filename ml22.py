import numpy as np
import pandas as pd
import os
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Collaborative Filtering Recommender
matrix = pd.read_csv("Data/rating_matrix.csv")
model_knn = NearestNeighbors(metric = "cosine", algorithm = 'brute')
model_knn.fit(csr_matrix(matrix))

def findKSimilarMovies(movie_id, k=5):
    similarities=[]
    indices=[]

    distances, indices = model_knn.kneighbors(matrix.iloc[movie_id-1, :].values.reshape(1, -1), n_neighbors = k+1)
    similarities = 1-distances.flatten()
    print('{0} most similar items for item {1}:\n'.format(k,movie_id))
    for i in range(0, len(indices.flatten())):
        if indices.flatten()[i]+1 == movie_id:
            continue;
        else:
            print('{0}: Item {1} , with similarity of {2}'.format(i,indices.flatten()[i]+1, similarities.flatten()[i]))

    return similarities, indices

# Content Based Recommender
movies = pd.read_csv("Data/movies.dat", sep=";", index_col=0)
movies = movies.loc[:, ["title", "genre", "year"]]
movies["tags"] = movies.title + " " + movies.year.apply(str) + " " + movies.genre.apply(lambda x: x.replace("|", " "))
tf_idf = TfidfVectorizer()
X = tf_idf.fit_transform(movies.tags)
sim_mat = cosine_similarity(X, X)

def kContent(index, k = 10):
    indices = []
    score_series = pd.Series(sim_mat[index-1]).sort_values(ascending = False)
    similarities = list(score_series.iloc[1:k+1])
    top_k_indexes = list(score_series.iloc[1:k+1].index)
    print(top_k_indexes)

    for i in top_k_indexes:
        indices.append(list(movies.index)[i])
    return similarities, indices


if __name__ == "__main__":
    findKSimilarMovies(111)
