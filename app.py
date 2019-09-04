from flask import Flask, render_template, flash, request, url_for, redirect
from flask import session
from pymongo import MongoClient
import ml
import requests
import os
from flask.ext.bcrypt import Bcrypt
from datetime import timedelta
app = Flask(__name__)
app.secret_key = 'some_secret' # Required for running flash
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=30)
bcrypt = Bcrypt(app)
db = MongoClient("localhost", 27017).movrec


@app.route("/")
def hello():
    try:
        if "user" in session:
            res = list(db.Users.find({"_id": session["user"]}))[0]
            recommended = []
            similarities = []
            liked = []
            details = []
            k = 5
            user_ratings = res["ratings"]
            for movie, rating in res["ratings"].items():
                if int(rating) >= 3:
                    liked.append(movie)
            user_rated_movies = dict()
            for movie_id in liked:
                count = 0
                isContent = False
                ratings_list = list(db.MovieRatings.find({"movie_id":movie_id}))
                user_rated_movies[movie_id] = list(db.Movies.find({"movie_id":movie_id}))[0]

                if ratings_list:
                    sim, indices = ml.findKSimilarMovies(int(movie_id), k)
                    indices = indices.flatten()+1
                    for i in indices:
                        if i == int(movie_id):
                            continue;
                        res =  list(db.Movies.find({"movie_id":str(i)}))
                        if res:
                            recommended.append(res[0])
                            similarities.append(sim)
                else:
                    sim, indices = ml.kContent(int(movie_id), k)
                    isContent = True
                    for i in indices:
                        if i == int(movie_id):
                            continue;
                        res =  list(db.Movies.find({"movie_id":str(i)}))
                        if res:
                            recommended.append(res[0])
                            similarities.append(sim)

            # print(user_rated_movies)

            return render_template("profile.html", user = list(db.Users.find({"_id": session["user"]}))[0], recommendations = recommended[:k], user_ratings = user_ratings, user_rated_movies = user_rated_movies)
        else:
            return render_template("login.html")
    except:
        return redirect(url_for("hello"))


@app.route("/content/<string:movie_id>")
def contentRecommend(movie_id):
    try:
        movie = list(db.Movies.find({"movie_id":str(movie_id)}))[0]
        _, indices = ml.kContent(int(movie_id), 5)
        similar_movies = []
        for i in indices:
            if i == int(movie_id):
                continue;
            res =  list(db.Movies.find({"movie_id":str(i)}))
            # print(res)
            if res:
                similar_movies.append(res[0])

        movie["imdb_id"] = "0"*(7 - len(str(movie["imdb_id"]))) + str(movie["imdb_id"])
        details_url = "http://www.omdbapi.com/?i=tt" + movie["imdb_id"] + "&apikey=801a08fe"
        details = requests.get(details_url).json()
        return render_template("movie.html", movie = movie, similar_movies = similar_movies, content=True, details=details)
    except:
        return redirect(url_for("hello"))


@app.route("/movie/<string:movie_id>")
def displayMovie(movie_id):
    try:
        movie = list(db.Movies.find({"movie_id":movie_id}))[0]
        average_rating = 0
        count = 0
        isContent = False
        ratings_list = list(db.MovieRatings.find({"movie_id":movie_id}))
        user_rating = None
        if "user" in session:
            res = list(db.Users.find({"_id":session["user"]}))[0]
            # print(res)
            if movie_id in res["ratings"]:
                user_rating = res["ratings"][movie_id]
                # print(user_rating)

        if ratings_list:
            # Trying Collaborative Filtering Recommendations
            _, indices = ml.findKSimilarMovies(int(movie_id), 5)
            indices = indices.flatten()+1
            similar_movies = []
            for i in indices:
                if i == int(movie_id):
                    continue;
                res =  list(db.Movies.find({"movie_id":str(i)}))
                if res:
                    similar_movies.append(res[0])
        else:
            # Ratings not Found
            # Content Based Recommendations
            # print("Trying content based")
            _, indices = ml.kContent(int(movie_id), 5)
            similar_movies = []
            isContent = True
            for i in indices:
                if i == int(movie_id):
                    continue;
                res =  list(db.Movies.find({"movie_id":str(i)}))
                if res:
                    similar_movies.append(res[0])

        movie["imdb_id"] = "0"*(7 - len(str(movie["imdb_id"]))) + str(movie["imdb_id"])
        details_url = "http://www.omdbapi.com/?i=tt" + movie["imdb_id"] + "&apikey=801a08fe"
        details = requests.get(details_url).json()
        # print(details)
        return render_template("movie.html", movie = movie, similar_movies = similar_movies, content=isContent, details = details, user_rating = user_rating)
    except Exception as e:
        print(e)
        return "404: Page Not Found"


@app.route("/search", methods=["GET", "POST"])
def search():
    error = None
    try:
        if request.method == "POST":
            query = request.form["query"]
            if query == " ":
                error = "Empty query!"
                flash(error)
            results = list(db.Movies.find({"$text":{"$search": query}}))
            return render_template("results.html", results=results, query=query, error = error)
    except:
        return redirect(url_for("hello"))


@app.route("/rate/<string:movie_id>", methods=["GET", "POST"])
def rate(movie_id):
    try:
        if "user" in session and request.method == "POST":
            # print("Rating")
            # print(request.form)
            rating = request.form["stars"]
            db.Users.update({"_id":session["user"]}, {"$set":{"ratings."+movie_id:rating}})
            return redirect("/movie/"+movie_id)
        else:
            return redirect(url_for("hello"))
    except:
        flash("Something went wrong!")
        return redirect(url_for("hello"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    try:
        if "admin" in session:
            return redirect(url_for("admin"))
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            res = list(db.Admin.find({"username":username}))
            if len(res) == 0:
                error = "Username does not exist"
                flash(error)
                return render_template("admin_login.html", error = error)
            elif res[0]["password"] == password:
                session["admin"] = username
                return redirect(url_for("admin"))
            else:
                error = "Username does not exist"
                flash(error)
                return render_template("admin_login.html", error = error)
        else:
            return render_template("admin_login.html")
    except:
        return redirect(url_for("hello"))


def recalculate_ml():
    import imp
    imp.reload(ml)

import threading

@app.route("/admin", methods=["GET", "POST"])
def admin():
    try:
        if "admin" not in session:
            return render_template("admin_login.html")

        if request.method == "POST":
            try:
                imdb_id = "0"*(7 - len(str(request.form["imdb_id"]))) + str(request.form["imdb_id"])
                details_url = "http://www.omdbapi.com/?i=tt" + imdb_id + "&apikey=801a08fe"
                # print(details_url)
                details = requests.get(details_url).json()

                movie_id = list(db.Counts.find())[0]["movies"]
                # print(type(movie_id), movie_id)
                db.Counts.update({"_id":1}, {"$set":{"movies":movie_id+1}})

                db.Movies.insert({"movie_id":str(int(movie_id)), "genres":str(request.form["genres"]).split(","), "imdb_id":str(request.form["imdb_id"]), "title":str(request.form["title"]), "year":str(request.form["year"])})
                t = threading.Thread(target=recalculate_ml)
                t.start()
                return redirect(url_for("admin"))
            except Exception as e:
                print(e)
                flash("Enter correct details")
                return redirect(url_for("admin"))
        else:
            return render_template("admin.html")
    except:
        return redirect(url_for("hello"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    try:
        if "user" in session:
            return redirect(url_for("hello"))
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            # print(username)
            res = list(db.Users.find({"username":username}))
            # print(res)
            if len(res) == 1 and bcrypt.check_password_hash(res[0]["password"], password):
                session["user"] = res[0]["_id"]
                # print(session["user"])
                return redirect(url_for("hello"))
            else:
                error = "Username/password incorrect"
                flash(error)
                return redirect(url_for("login"))
        else:
            return render_template("login.html")
    except:
        return redirect(url_for("hello"))


@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        if "user" in session:
            return redirect(url_for("hello"))
        if request.method == "POST":
            username = str(request.form["username"])
            if len(username.split()) == 0:
                flash("Username cannot be empty")
                return redirect(url_for("register"))
            password = str(request.form["password"])
            if len(password.split()) == 0:
                flash("Password cannot be empty")
                return redirect(url_for("register"))
            name = str(request.form["name"])
            if len(name.split()) == 0:
                flash("Name cannot be empty")
                return redirect(url_for("register"))
            res = list(db.Users.find({"username":username}))
            if len(res) == 0:
                user_id = list(db.Counts.find({"_id":1}))[0]["users"]
                user_id = int(user_id)
                # print(user_id)
                db.Counts.update({"_id":1}, {"$set":{"users":user_id+1}})
                # print("Updated")
                user_id = str(int(user_id))
                password = bcrypt.generate_password_hash(password)
                db.Users.insert({"_id":user_id, "username":username, "name":name, "password":password, "ratings":{}})
                # print("Inserted")
                session["user"] = user_id
                return redirect(url_for("hello"))
            else:
                flash("User already exists!")
                return redirect(url_for("login"))

        else:
            flash("Something went wrong!")
            return redirect(url_for("login"))
    except:
        return redirect(url_for("hello"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("hello"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


# Patch for favicon error
from flask import send_from_directory
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True)
