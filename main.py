from flask import Flask, render_template, redirect, url_for, request, flash, abort
import requests
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, TimeField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy import Column, Integer, Float, String, Text
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash


from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user


# from datetime import date
# from flask_bootstrap import Bootstrap5
# from flask_ckeditor import CKEditor
# from flask_gravatar import Gravatar
# from flask_sqlalchemy import SQLAlchemy

# from sqlalchemy import Integer, String, Text
# from functools import wraps
# from sqlalchemy.orm import relationship

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


# Movie DB
class Movie(db.Model):
    __tablename__ = "movies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Text, nullable=False)

# Need a watchilst table


with app.app_context():
    db.create_all()



class builder_search(FlaskForm):
    search = StringField('Type the name of a movie', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods=["GET", "POST"])
def home():
    form = builder_search()
    if current_user.is_authenticated:
        user = current_user  # Get the currently logged-in user
    else:
        user = None  # No user is logged in
    return render_template("index.html", form=form, user=user)

@app.route ('/builder',methods=["GET", "POST"])
def builder():
    form = builder_search()
    if form.validate_on_submit():
        results = form.search.data
        return redirect(url_for("builder_results", data=results))
    return render_template('builder.html', form=form)


@app.route ('/builder_results',methods=["GET", "POST"])
def builder_results():
    search = request.args.get('data')
    url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()


    # ids = [x['id'] for x in data['results']]
    # titles = [x['original_title'] for x in data['results']]
    # image_urls = [f"https://image.tmdb.org/t/p/original/{x['poster_path']}" for x in data['results']]

    #
    #
    # image_path = data['results'][0]['poster_path']
    # id = data['results'][0]['id']
    # title = data['results'][0]['original_title']
    # image_url = f"https://image.tmdb.org/t/p/original/{image_path}"

    return render_template('builder_results.html', data=data)

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
            return render_template("index.html")
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


@app.route('/add_movie')
def add_movie():
    pass

if __name__ == "__main__":
    app.run(debug=True, port=5001)