# Book Review
Able to use the application on Heroku - https://edxcs50w-project1.herokuapp.com/

Users are able to register, then log in using their email address and password.
Once log in, the will be able to search for books, leave reviews for individual
and see reviews made by other people.

## API
Using Third-party API by Goodreads, another book review website, to pull in
ratings from broader audience. Users will be able to query book details using
`isbn` number and book reviews.

`/api/<isbn>`
- Return a JSON response containing the book's title, author, publication date,
ISBN number, review count, and average score.

### Sample
`GET` request: `api/<isbn>`

Response:
```json
{
  "author": "Jodi Picoult",
  "average_score": "3.60",
  "isbn": "0140230270",
  "review_count": 44569,
  "title": "Harvesting the Heart",
  "year": 1993
}
```

## Setup
```
# install dependencies
$ pip install -r requirements.txt

# set ENV variables
$ export FLASK_APP = application.py
$ export DATABASE_URL = Heroku Postgres DB URI
$ export GOODREADS_API_KEY = Goodreads API key

# run application
$ flask run
```

## Requirements
- Flask
- Flask-Session
- psycopg2-binary
- SQLAlchemy
- gunicorn
- requests
- Werkzeug==0.16.0
