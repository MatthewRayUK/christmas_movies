from flask import Flask, render_template, redirect, url_for, request, flash, abort
import requests
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, TimeField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, text
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap(app)
Base = declarative_base()

api_key = "b6f038e5338cf8fbc1f28e2caf556c96"

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///christmas_movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)



# Create a User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    # Relationship
    watchlist = relationship("Watchlist", back_populates="user")


# Movie DB
class Movie(db.Model):
    __tablename__ = "movies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    watchlist = relationship("Watchlist", back_populates="movie")


class Watchlist(db.Model):
    __tablename__ = "watchlist"
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    user_rating: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relationships to User and Movie
    user = relationship("User", back_populates="watchlist")
    movie = relationship("Movie", back_populates="watchlist")

with app.app_context():
    db.create_all()



class builder_search(FlaskForm):
    search = StringField('Type the name of a movie', validators=[DataRequired()])
    submit = SubmitField('Submit')

class pack_builder_search(FlaskForm):
    search = StringField('Type the name of a movie', validators=[DataRequired()])
    category = SelectField('Category', choices=[('', 'Click here to select a category'), ('starter', 'Starter'), ('90s', '90s')])
    submit = SubmitField('Submit')

@app.route('/', methods=["GET", "POST"])
def home():
    form = builder_search()
    if current_user.is_authenticated:
        user = current_user  # Get the currently logged-in user
        movies = db.session.query(Watchlist.movie_id, Watchlist.image_url, Watchlist.title).filter(
            Watchlist.user_id == current_user.id).all()
        movie_data = [{"movie_id": movie_id, "image_url": image_url, "title": title} for movie_id, image_url, title in
                      movies]
        count= len(movie_data)
        return render_template("index.html", form=form, user=user, database=movie_data, count=count)
    else:
        user = None  # No user is logged in
    # add_title_column()
    return render_template("index.html", form=form, user=user)

@app.route('/about', methods=["GET", "POST"])
def about():
    return render_template('about.html')
@app.route('/starter')
def starter():

    movies = db.session.query(Watchlist.movie_id, Watchlist.image_url, Watchlist.title).filter(
            Watchlist.category == 'starter').all()
    user_watchlist = db.session.query(Watchlist.movie_id, Watchlist.image_url, Watchlist.title).filter(
            Watchlist.user_id == current_user.id).all()
    user_watchlist_ids = [movie.movie_id for movie in user_watchlist]

    movie_data = [{"movie_id": movie_id, "image_url": image_url, "title": title} for movie_id, image_url, title in movies]
    return render_template("starter.html", database=movie_data, user_watchlist=user_watchlist_ids)



@app.route ('/user_search',methods=["GET", "POST"])
def user_search():
    form = builder_search()
    if form.validate_on_submit():
        results = form.search.data
        print(results)
        return redirect(url_for("user_search_results", data=results))
    return render_template('user_search.html', form=form)


@app.route ('/user_search_results',methods=["GET", "POST"])
def user_search_results():
    search = request.args.get('data')
    url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()

    return render_template('user_search_results.html', data=data)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=8)

        try:
            result = db.session.execute(db.select(User).where(User.email == email))
            user = result.scalar()


            new_user = User(
                email=email,
                password=password,
                name=name
            )

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)


            return redirect(url_for('home'))
        except:
            flash("Sorry, email already registered")

    return render_template("register.html", logged_in=current_user.is_authenticated)

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')


        try:
            result = db.session.execute(db.select(User).where(User.email == email))
            user = result.scalar()

            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Password incorrect, please try again")
        except:
            flash("Sorry, email not recognised")

    return render_template("login.html", logged_in=current_user.is_authenticated)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add_movie/<int:movie_id>')
def add_movie(movie_id):
    print(movie_id)
    add_to_watchlist(current_user.id, movie_id)
    return redirect(url_for('home'))

@app.route('/packbuilder', methods=["GET", "POST"])
def packbuilder():
    form = pack_builder_search()
    if form.validate_on_submit():
        results = form.search.data
        category = form.category.data
        return redirect(url_for("pack_builder_results", data=results, category=category))
    return render_template("packbuilder.html", form=form)


# Pack builder - admins
@app.route('/pack_builder_results', methods=["GET", "POST"])
def pack_builder_results():
    search = request.args.get('data')
    category = request.args.get('category')

    url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()


    return render_template('packbuilder_results.html', data=data, category=category)

@app.route('/admin_add/<int:movie_id>')
def admin_add(movie_id):
    user_id = current_user.id  # or use your method of getting the current user's ID
    add_to_watchlist(user_id, movie_id)

    return redirect(url_for('packbuilder'))

def add_to_watchlist(user_id, movie_id, *category):

    if user_id == 1:
        category = 'starter'
    else:
        category = 'user'

    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}', params={'api_key': api_key})
    title = response.json().get('original_title')
    image_url = response.json().get('poster_path')

    watchlist_entry = Watchlist(user_id=user_id, movie_id=movie_id, category=category, image_url = image_url, title=title, user_rating=0)
    db.session.add(watchlist_entry)
    db.session.commit()

# def add_title_column():
#     with app.app_context():  # Ensures you're within the app context when modifying the DB
#         # Execute raw SQL to add the 'title' column
#         db.session.execute(text('ALTER TABLE watchlist ADD COLUMN user_rating INTEGER;'))
#         db.session.commit()

if __name__ == "__main__":
    app.run(debug=True, port=5001)