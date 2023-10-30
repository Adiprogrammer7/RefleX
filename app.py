from flask import Flask, render_template, redirect, flash, url_for, request
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os
from forms import RegistrationForm, LoginForm
from recommender import Recommender
from utils import *

# Load environment variables from .env file and access them
load_dotenv() 
mongodb_uri = os.getenv('MONGODB_URI')
secret_key = os.getenv('SECRET_KEY')

# app configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# MongoDB stuff
client = MongoClient(mongodb_uri)
db = client['reflex_db']

# User class that satisfies the requirements of Flask-Login. The User class should inherit from UserMixin, which provides default implementations for the required methods.
class User(UserMixin):
	def __init__(self, user_id, username, email):
		self.id = user_id
		self.username = username
		self.email = email

	# This method is required by Flask-Login's UserMixin class. It returns the string representation of the user's ID, which is used for user authentication and session management.
	def get_id(self):
		return str(self.id)

#  user loader function that Flask-Login will use to load the user from the database based on the user ID
@login_manager.user_loader
def load_user(user_id):
	# Query the database to find the user by ID
	user = db.user.find_one({'_id': ObjectId(user_id)})
	# Return the user object
	return User(user['_id'], user['username'], user['email'])


@app.route("/", methods=['GET', 'POST'])
@login_required
def home():
	user_id = ObjectId(current_user.get_id())
	tags = db.diary.distinct("diary_tag", {"author_id": user_id})
	emotions = db.diary.distinct("emotion", {"author_id": user_id})

	if request.method == 'POST':
		filter_type = request.form.get('filter_type')
		filter_value = request.form.get(filter_type)			
		if filter_type == 'tag':
			entries = db.diary.find({'diary_tag': filter_value})
		elif filter_type == 'emotion':
			entries = db.diary.find({'emotion': filter_value})
		
	elif request.method == 'GET':
		# Handle search form submissions
		search_keyword = request.args.get('search_keyword')
		if search_keyword:
			entries = search_entries_by_keyword(db, search_keyword)
		else:
			entries = db.diary.find({'author_id': user_id})

	return render_template('index.html', entries=entries, tags=tags, emotions=emotions)


@app.route("/write")
@login_required
def write():
	user_id = ObjectId(current_user.get_id())
	tags = db.diary.distinct("diary_tag", {"author_id": user_id})
	return render_template('text_editor.html', tags=tags)

@app.route('/books', methods=['GET'])
@app.route('/books/<book_id>', methods=['GET'])
@login_required
def books(book_id=None):
	if book_id:
		book = db.books.find_one({'_id': ObjectId(book_id)})
		return render_template('book_details.html', book=book)
	else:
		user_id = ObjectId(current_user.get_id())
		books = db.books.find({'author_id': user_id})
		return render_template('books.html', books=books)
	

@app.route('/movies', methods=['GET'])
@app.route('/movies/<movie_id>', methods=['GET'])
@login_required
def movies(movie_id=None):
	if movie_id:
		movie = db.movies.find_one({'_id': ObjectId(movie_id)})
		return render_template('movie_details.html', movie=movie)
	else:
		user_id = ObjectId(current_user.get_id())
		movies = db.movies.find({'author_id': user_id})
		return render_template('movies.html', movies=movies)


@app.route("/entry/<entry_id>")
@login_required
def view_entry(entry_id):
	# Retrieve the diary entry from the database based on the entry_id
	entry = db.diary.find_one({'_id': ObjectId(entry_id)})

	if entry:
		# Render the template to display the entry content
		return render_template('view_entry.html', entry=entry)
	else:
		flash("Diary entry not found.", "danger")
		return redirect(url_for('home'))


@app.route("/delete_entry/<entry_id>")
@login_required
def delete_entry(entry_id):
	entry = db.diary.find_one({"_id": ObjectId(entry_id)})
	print(type(entry))
	if not entry:
		flash("Diary entry not found!", "danger")
		return redirect(url_for("home"))
	
	 # Delete the entry from the database
	db.diary.delete_one({"_id": ObjectId(entry['_id'])})
	flash(f"Diary entry named '{entry['diary_title']}' deleted successfully", "success")
	return redirect(url_for("home"))

@app.route("/edit_entry/<entry_id>")
@login_required
def edit_entry(entry_id):
	entry = db.diary.find_one({"_id": ObjectId(entry_id)})
	user_id = ObjectId(current_user.get_id())
	tags = db.diary.distinct("diary_tag", {"author_id": user_id})
	if not entry:
		flash("Diary entry not found!", "danger")
		return redirect(url_for("home"))
	# render 'text_editor.html' with entry contents
	return render_template('text_editor.html', entry=entry, tags=tags)


@app.route("/save_diary/", defaults={'entry_id': None}, methods=['POST'])
@app.route("/save_diary/<entry_id>", methods=['POST'])
@login_required
def save_diary(entry_id):
	title = request.form.get('diary_title')
	tag = request.form.get('diary_tag')
	if not tag:
		tag = "None"
	content = request.form.get('diary_content')
	create_date = datetime.now()
	author_id = current_user.get_id()
	plaintext = extract_plaintext(content)

	# extract emotion from diary text
	emotion = extract_emotion(plaintext)

	# generate book recommendations and save in db
	recommender = Recommender(plaintext, alsoPhrases=True)
	recommender.fetch_results()
	print(recommender.keywords)
	print(recommender.phrases)
	print(recommender.entities)
	save_books(db, recommender.books, author_id)
	save_movies(db, recommender.movies, author_id)


	# Update existing entry
	if entry_id:
		diary_modified = datetime.now()
		db.diary.update_one({'_id': ObjectId(entry_id)}, {'$set': {'diary_title': title, 'diary_tag': tag, 'diary_content': content, 'diary_modified': diary_modified, 'emotion': emotion}})
		flash("Diary entry has been updated!", "success")
	
	# Create new entry
	else:
		new_entry = {
			'diary_title': title,
			'diary_tag': tag,
			'diary_content': content,
			'diary_created': create_date,
			'emotion': emotion,
			'author_id': ObjectId(author_id)
		}
		db.diary.insert_one(new_entry)
		flash("Diary entry has been saved!", "success")
	
	return redirect(url_for('home'))


@app.route("/plot", methods=['GET', 'POST'])
@login_required
def plot():
	if request.method == "POST":
		start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
		end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
		author_id = ObjectId(current_user.get_id())
		counts, emotions = fetch_data(db, author_id, start_date, end_date)
		return render_template('plot.html', counts=counts, emotions=emotions)

	return render_template('plot.html')

@app.route("/register_user", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    registration_form = RegistrationForm(db)  # Passing the database object to the form
    
    if registration_form.validate_on_submit():
        # Encrypting the password
        hashed_pw = bcrypt.generate_password_hash(registration_form.password.data).decode('utf-8')
        
        # Creating a new user entry
        new_user_entry = {
            'email': registration_form.email.data,
            'username': registration_form.username.data,
            'password': hashed_pw
        }
        db.user.insert_one(new_user_entry)  # Inserting into the 'user' collection
        
        flash(f"Account has been created for '{registration_form.username.data}'!", "success")
        return redirect(url_for('home'))
    
    return render_template('register.html', form=registration_form)


@app.route("/login_user", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	login_form = LoginForm()
	if login_form.validate_on_submit():
		user = db.user.find_one({'username': login_form.username.data})
		if user and bcrypt.check_password_hash(user['password'], login_form.password.data):
			# Create a User object from the retrieved data
			user_obj = User(user['_id'], user['username'], user['email'])
			login_user(user_obj, remember=login_form.remember.data)  # Login the user
			flash('You have been logged in!', 'success')
			return redirect(url_for('home'))
		else:
			flash('Login Failed. Please check username and password', 'danger')
	return render_template('login.html', form=login_form)

@app.route("/logout_user")
@login_required
def logout():
	logout_user()  
	flash('Logged out!', 'success')
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.run(debug=True)