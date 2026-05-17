from flask import Flask,render_template,redirect,url_for,request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired
import requests
app = Flask(__name__)

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy()
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()

# ---------------- DEFAULT MOVIE ---------------- #
with app.app_context():
    if not db.session.execute(db.select(Movie).filter_by(title="poda dei")).scalar():
        movie_entry = Movie(
            title="poda dei",
            year=2002,
            description="Sample description",
            rating=7.3,
            ranking=10,
            review="Sample review",
            img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
        )
        db.session.add(movie_entry)
        db.session.commit()

# ---------------- FORMS ---------------- #
class Login(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

# ---------------- HOME ---------------- #
@app.route("/")
def home():
    result = db.session.execute(
        db.select(Movie).order_by(Movie.rating.desc())
    )
    movies = result.scalars().all()

    for i in range(len(movies)):
        movies[i].ranking = i + 1

    db.session.commit()

    return render_template("index.html", movies=movies)

# ---------------- EDIT ---------------- #
@app.route("/edit", methods=["GET", "POST"])
def movierate():
    form = Login()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)

    if form.validate_on_submit():
        try:
            movie.rating = float(form.rating.data)
        except:
            movie.rating = None

        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", movie=movie, form=form)

# ---------------- DELETE ---------------- #
@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)

    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for("home"))

# ---------------- ADD MOVIE ---------------- #
TMDB_API_KEY = "YOUR_API_KEY"

@app.route("/add_movie", methods=["GET", "POST"])
def new_movie():
    form = AddMovie()

    if form.validate_on_submit():
        movie_title = form.title.data

        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": movie_title
            }
        )

        data = response.json()

        if len(data["results"]) == 0:
            return "No movie found"

        movie_data = data["results"][0]

        # Handle missing poster
        img_url = "https://via.placeholder.com/500x750?text=No+Image"
        if movie_data["poster_path"]:
            img_url = f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"

        movie_entry = Movie(
            title=movie_data["title"],
            year=int(movie_data["release_date"].split("-")[0]),
            description=movie_data["overview"],
            img_url=img_url
        )

        db.session.add(movie_entry)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("add.html", form=form)

# ---------------- RUN ---------------- #
if __name__ == '__main__':
    app.run(debug=True)