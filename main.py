from flask import Flask, render_template, redirect, url_for, request, flash, abort
import requests
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, TimeField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, text, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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
    is_netflix: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    is_disney: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    is_prime: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    is_nowtv: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    is_apple: Mapped[int] = mapped_column(Integer, nullable=True, default=0)


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


        movies = db.session.query(Watchlist.movie_id, Watchlist.image_url, Watchlist.title, Watchlist.user_rating, Watchlist.is_netflix, Watchlist.is_apple, Watchlist.is_nowtv, Watchlist.is_prime, Watchlist.is_disney).filter(
            Watchlist.user_id == current_user.id).all()

        movie_data = [{"movie_id": movie_id, "image_url": image_url, "title": title, "rating": user_rating, "is_netflix": is_netflix, "is_apple": is_apple, "is_nowtv": is_nowtv, "is_prime": is_prime, "is_disney": is_disney} for movie_id, image_url, title, user_rating, is_netflix, is_apple, is_nowtv, is_prime, is_disney in
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


@app.route('/update_rating', methods=['POST'])
def update_rating():
    movie_id = request.form.get('movie_id')
    new_rating = request.form.get('rating')
    print(f"M:{movie_id}  NR:{new_rating}")

    if movie_id and new_rating:
        print("part 1")
        # Find the existing Watchlist entry for the current user and movie
        watchlist_entry = Watchlist.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()

        if watchlist_entry:
            print("part 2")
            # Update the user rating for the movie
            watchlist_entry.user_rating = int(new_rating)  # Set the new rating here

            # Commit the changes to the database
            db.session.commit()

            # Flash a success message
            flash(f"Your rating for the movie was updated to {new_rating} stars.", "success")
        else:
            flash("Could not find the movie in your watchlist.", "danger")

    return redirect(request.referrer or url_for('home'))


@app.route('/starter')
def starter():
    movies = db.session.query(Watchlist.movie_id, Watchlist.image_url, Watchlist.title, Watchlist.user_rating, Watchlist.is_netflix, Watchlist.is_apple, Watchlist.is_nowtv, Watchlist.is_prime, Watchlist.is_disney).filter(
            Watchlist.category == 'starter').all()
    user_watchlist = db.session.query(Watchlist.movie_id, Watchlist.image_url, Watchlist.title).filter(
            Watchlist.user_id == current_user.id).all()
    user_watchlist_ids = [movie.movie_id for movie in user_watchlist]

    movie_data = [{"movie_id": movie_id, "image_url": image_url, "title": title, "rating": user_rating, "is_netflix": is_netflix, "is_apple": is_apple, "is_nowtv": is_nowtv, "is_prime": is_prime, "is_disney": is_disney} for movie_id, image_url, title, user_rating, is_netflix, is_apple, is_nowtv, is_prime, is_disney in movies]
    return render_template("starter.html", database=movie_data, user_watchlist=user_watchlist_ids)

@app.route('/remove_movie', methods=["POST"])
def remove_movie():
    movie_id = request.form['movie_id']
    user_id = current_user.id
    print(movie_id, user_id)
    watchlist_entry = Watchlist.query.filter_by(movie_id=movie_id, user_id=user_id).first()

    if watchlist_entry:
        db.session.delete(watchlist_entry)  # Delete the record
        db.session.commit()  # Commit the transaction
    return redirect(url_for('home'))

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
    # url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={api_key}"
    # response = requests.get(url)
    # data = response.json()

    data = api_movie(search)
    user_watchlist = db.session.query(Watchlist.movie_id, Watchlist.image_url, Watchlist.title).filter(
        Watchlist.user_id == current_user.id).all()
    user_watchlist_ids = [movie.movie_id for movie in user_watchlist]

    return render_template('user_search_results.html', data=data, user_watchlist = user_watchlist_ids)

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



def api_movie(search):
    url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()
    movie_list = data['results']
    movie_details = []

    provider_details = []
    for movie in movie_list:
            movie_id = movie['id']
            title = movie['original_title']
            img_url = movie['poster_path']




            # Providers
            providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}"
            providers_response = requests.get(providers_url)
            providers_data = providers_response.json()

            if 'GB' in providers_data['results']:
                providers = providers_data['results']['GB']

                print(providers)
                if 'flatrate' in providers:
                    print('start')
                    is_netflix = 0
                    is_disney = 0
                    is_prime = 0
                    is_apple = 0
                    is_nowtv = 0
                    for provider in providers['flatrate']:
                        provider_name = provider.get('provider_name', '').lower()
                        if 'netflix' in provider_name:
                            is_netflix = 1
                        elif 'disney' in provider_name:
                            is_disney = 1
                        elif 'prime' in provider_name:
                            is_prime = 1
                        elif 'apple' in provider_name:
                            is_apple = 1
                        elif 'now' in provider_name:
                            is_nowtv = 1

                    print(movie_id, title, is_netflix)
                    movie_details.append ({
                        'movie_id': movie_id,
                        'title': title,
                        'img_url': img_url,
                        'is_netflix': is_netflix,
                        'is_disney': is_disney,
                        'is_prime': is_prime,
                        'is_apple': is_apple,
                        'is_now': is_nowtv,
                    })
                else:
                    movie_details.append({
                        'movie_id': movie_id,
                        'title': title,
                        'img_url': img_url,
                        'is_netflix': 0,
                        'is_disney': 0,
                        'is_prime': 0,
                        'is_apple': 0,
                        'is_now': 0,
                    })

    return movie_details



def add_to_watchlist(user_id, movie_id, *category):

    if user_id == 1:
        category = 'starter'
    else:
        category = 'user'

    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}', params={'api_key': api_key})
    title = response.json().get('original_title')
    image_url = response.json().get('poster_path')

    """
    START Platform search
    """
    region = 'GB'  # Replace with the desired region code (e.g., US for the United States)

    url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}&region=GB"

    headers = {
        "accept": "application/json",
        "Authorization": "b6f038e5338cf8fbc1f28e2caf556c96"  # Replace with your valid API key
    }

    response = requests.get(url, headers=headers)

    data = response.json()

    if 'results' in data:
        providers = data['results']['GB']

        is_netflix = 0
        is_disney = 0
        is_prime = 0
        is_apple = 0
        is_sky = 0
        is_nowtv = 0

        if 'flatrate' in providers:
            for provider in providers['flatrate']:
                provider_name = provider.get('provider_name', '').lower()
                if 'netflix' in provider_name:
                    is_netflix = 1
                elif 'disney' in provider_name:
                    is_disney = 1
                elif 'prime' in provider_name:
                    is_prime = 1
                elif 'apple' in provider_name:
                    is_apple = 1
                elif 'sky' in provider_name:
                    is_sky = 1
                elif 'now' in provider_name:
                    is_nowtv = 1
            print(is_netflix, is_disney, is_prime, is_apple, is_sky, is_nowtv)

    """
    END Platform search
    """
    watchlist_entry = Watchlist(user_id=user_id, movie_id=movie_id, category=category, image_url = image_url, title=title, user_rating=0, is_netflix=is_netflix, is_apple=is_apple, is_disney=is_disney,is_nowtv=is_nowtv, is_prime=is_prime)
    db.session.add(watchlist_entry)
    db.session.commit()

# def add_title_column():
#     with app.app_context():  # Ensures you're within the app context when modifying the DB
#         # Execute raw SQL to add the 'title' column
#         db.session.execute(text('ALTER TABLE watchlist ADD COLUMN user_rating INTEGER;'))
#         db.session.commit()


def update_streaming_platforms():
    # Ensure we're within the Flask app context
    with app.app_context():
        # Iterate over each movie in the watchlist
        watchlist_entries = Watchlist.query.all()

        for entry in watchlist_entries:
            movie_id = entry.movie_id  # Get the movie_id from the watchlist
            # Fetch streaming providers from Movie DB API
            url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}"

            headers = {
                "accept": "application/json",
                "Authorization": "b6f038e5338cf8fbc1f28e2caf556c96"  # Replace with your valid API key
            }

            response = requests.get(url, headers=headers)
            data = response.json()

            # Print the full API response to inspect it
            print(f"API Response for movie_id {movie_id}: {data}")

            # Check for streaming platforms in the response
            if 'results' in data:
                if 'GB' in data['results']:
                    providers = data['results']['GB']
                    print(f"Providers for movie_id {movie_id}: {providers}")

                    # Initialize flags as 0
                    entry.is_netflix = 0
                    entry.is_disney = 0
                    entry.is_prime = 0
                    entry.is_apple = 0
                    entry.is_sky = 0
                    entry.is_nowtv = 0

                    # Check only 'flatrate' providers
                    if 'flatrate' in providers:
                        for provider in providers['flatrate']:
                            provider_name = provider.get('provider_name', '').lower()
                            if 'netflix' in provider_name:
                                entry.is_netflix = 1
                            elif 'disney' in provider_name:
                                entry.is_disney = 1
                            elif 'prime' in provider_name:
                                entry.is_prime = 1
                            elif 'apple' in provider_name:
                                entry.is_apple = 1
                            elif 'sky' in provider_name:
                                entry.is_sky = 1
                            elif 'now' in provider_name:
                                entry.is_nowtv = 1

                    # Commit the changes to the database
                    db.session.commit()
                else:
                    print(f"No data found for 'GB' in the response for movie_id {movie_id}")
            else:
                print(f"No 'results' key in API response for movie_id {movie_id}")





if __name__ == "__main__":
    app.run(debug=True)