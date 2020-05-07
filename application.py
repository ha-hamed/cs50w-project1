import requests
import os

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

GOODREADS_API_KEY = os.getenv("GOODREADS_API_KEY")
if not GOODREADS_API_KEY:
    raise RuntimeError("GOODREADS_API_KEY is not set")


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    user_id = session.get("user_id", None)
    return render_template("index.html", user_id = user_id)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a user """

    if request.method == "GET":
        return render_template("register.html")

    # Get form information
    email = request.form.get("email")
    password = request.form.get("password")

    # Insert user to the database
    db.execute("INSERT INTO users (email, password) \
        VALUES(:email, :password)",
        {"email": email, "password": generate_password_hash(password)})
    try:
        db.commit()
    except:
        return render_template("error.html",
            message = "An error occured saving the user to the database.")
    return render_template("success.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """ Login a user """
    return render_template("login.html")


@app.route("/validatelogin", methods=["POST"])
def validate_login():
    try:
        _email = request.form.get("email")
        _password = request.form.get("password")

        user = db.execute("SELECT * from users where email = :email",
            {"email": _email}).fetchone()
        if user is not None:
            if check_password_hash(user[2], _password):
                session["user_id"] = user[0]
                return redirect('/')
            else:
                return render_template("error.html", message = "Wrong email address or password.")
        else:
            return render_template("error.html", message = "Wrong email address or password.")
    except Exception as e:
        return render_template("error.html", message = str(e))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route("/books", methods = ["POST"])
def books():

    isbn = request.form.get("isbn")
    title = request.form.get("title")
    author = request.form.get("author")

    books = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn AND title LIKE :title AND author LIKE :author",
        {"isbn": "%{}%".format(isbn), "title": "%{}%".format(title), "author": "%{}%".format(author)}).fetchall()

    return render_template("books.html", books=books)


@app.route("/book/<int:book_id>", methods = ["GET", "POST"])
def book(book_id):
    """Lists details about a single book."""

    # Persist review
    if request.method == "POST":
        rating = request.form.get("rating")
        opinon = request.form.get("rating_opinon")

        if db.execute("SELECT * FROM reviews WHERE user_id = :user_id and book_id = :book_id", {"user_id": session["user_id"], "book_id": book_id}).rowcount != 0:
            review_exist = True
            return render_template("error.html", message = "Already submitted review for the book. Multiple reviews are not allowed for the same book!")

        db.execute("INSERT INTO reviews (user_id, book_id, rating, message) VALUES(:user_id, :book_id, :rating, :message)",
            {"user_id": session["user_id"], "book_id": book_id, "rating": rating, "message": opinon})
        try:
            db.commit()
        except:
            return render_template("error.html",
                message = "An error occured saving the user to the database.")
        print("commit to the database")

    # make sure book exists
    book = db.execute("SELECT * from books where id = :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message = "No book found.")

    # get all reviews
    reviews = db.execute("SELECT rating, message FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()

    # get goodreads review data
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": book.isbn}).json()
    goodreads = { "average_rating": res["books"][0]["average_rating"], "ratings_count": res["books"][0]["work_ratings_count"] }

    return render_template("book.html", book = book, reviews = reviews, goodreads = goodreads)

@app.route("/api/<string:isbn_number>")
def book_api(isbn_number):
    """ Return details about a single book."""

    # make sure book exists
    book = db.execute("SELECT * from books where isbn = :isbn", {"isbn": isbn_number}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid isbn_number"})

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GOODREADS_API_KEY, "isbns": isbn_number}).json()
    goodreads = { "average_rating": res["books"][0]["average_rating"], "ratings_count": res["books"][0]["work_ratings_count"] }
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": goodreads['ratings_count'],
        "average_score": goodreads['average_rating']
    })
