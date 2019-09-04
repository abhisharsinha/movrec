import numpy as np
import pandas as pd
import os
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient

# Connection to mongo database
db = MongoClient("localhost", 27017).movrec

# Collaborative Filtering Recommender
matrix = pd.read_csv("Data/rating_matrix.csv")
model_knn = NearestNeighbors(metric = "cosine", algorithm = 'brute')
model_knn.fit(csr_matrix(matrix))

def findKSimilarMovies(movie_id, k=5):
    similarities=[]
    indices=[]

    distances, indices = model_knn.kneighbors(matrix.iloc[movie_id-1, :].values.reshape(1, -1), n_neighbors = k+1)
    similarities = 1-distances.flatten()

    return similarities, indices

# Content Based Recommender
def find_sim_matrix():
    movies = list(db.Movies.find())
    movies = pd.DataFrame(movies)
    movies.drop(labels=["_id"], axis=1, inplace=True)
    movies.index = movies.movie_id.apply(int)
    movies.dropna(axis=0, inplace=True)
    movies = movies.loc[:, ["title", "genres", "year"]]
    movies["tags"] = movies.title + " " + movies.year.apply(str) + " " + movies.genres.apply(lambda x: " ".join(x))
    tf_idf = TfidfVectorizer()
    X = tf_idf.fit_transform(movies.tags)
    sim_mat = cosine_similarity(X, X)
    # New code to fix indexing
    sim_mat = pd.DataFrame(sim_mat)
    sim_mat.index = movies.index
    return sim_mat, movies
    
sim_mat, movies = find_sim_matrix()

def kContent(index, k = 10):
    indices = []
    score_series = pd.Series(sim_mat.ix[index]).sort_values(ascending = False)
    similarities = list(score_series.iloc[1:k+1])
    top_k_indexes = list(score_series.iloc[1:k+1].index)
    # print(top_k_indexes)

    for i in top_k_indexes:
        indices.append(list(movies.index)[i])
    # print("Content generated")
    return similarities, indices


if __name__ == "__main__":
    kContent(101)
