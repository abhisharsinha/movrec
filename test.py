import ml

_, indices = ml.findKSimilarMovies(44)
print(indices)

# from pymongo import MongoClient
# db = MongoClient("localhost", 27017).movrec
# movie = list(db.Movies.find({"movie_id":"111"}))[0]
# print(movie)
# ratings = list(db.MovieRatings.find({"movie_id":"111"}))[0]["ratings"]
# print(ratings[:5])
#
# indices = indices.flatten()+1
# similar_movies = []
# for i in indices:
#     res =  list(db.Movies.find({"movie_id":str(i)}))
#     print(res)
#     if res:
#         similar_movies.append(res[0])
# print(similar_movies)
# print(indices)
