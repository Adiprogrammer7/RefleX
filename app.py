from flask import Flask, render_template, redirect, flash, url_for, request
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os
from forms import RegistrationForm, LoginForm
from recommender import BookRecommender
from utils import extract_plaintext, save_books

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


@app.route("/")
@login_required
def home():
	user_id = ObjectId(current_user.get_id())
	entries = db.diary.find({'author_id': user_id})
	return render_template('index.html', entries=entries)

@app.route("/write")
@login_required
def write():
	return render_template('text_editor.html')

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
	if not entry:
		flash("Diary entry not found!", "danger")
		return redirect(url_for("home"))
	# render 'text_editor.html' with entry contents
	return render_template('text_editor.html', entry=entry)


@app.route("/save_diary/", defaults={'entry_id': None}, methods=['POST'])
@app.route("/save_diary/<entry_id>", methods=['POST'])
@login_required
def save_diary(entry_id):
	title = request.form.get('diary_title')
	tag = request.form.get('diary_tag')
	content = request.form.get('diary_content')
	create_date = datetime.now()
	author_id = current_user.get_id()

	# generate book recommendations and save in db
	plaintext = extract_plaintext(content)
	book_recommender = BookRecommender(plaintext)
	book_recommender.fetch_results()
	save_books(db, book_recommender.books, author_id)

	# Update existing entry
	if entry_id:
		diary_modified = datetime.now()
		db.diary.update_one({'_id': ObjectId(entry_id)}, {'$set': {'diary_title': title, 'diary_tag': tag, 'diary_content': content, 'diary_modified': diary_modified}})
		flash("Diary entry has been updated!", "success")
	
	# Create new entry
	else:
		new_entry = {
			'diary_title': title,
			'diary_tag': tag,
			'diary_content': content,
			'diary_created': create_date,
			'author_id': ObjectId(author_id)
		}
		db.diary.insert_one(new_entry)
		flash("Diary entry has been saved!", "success")
	
	return redirect(url_for('home'))


@app.route("/register", methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm(db) # Passing the db object to the form
	if form.validate_on_submit():
		# encrypting the password
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		print(hashed_password)
		# to insert the user
		new_user = {
			'email': form.email.data,
			'username': form.username.data,
			'password': hashed_password
		}
		db.user.insert_one(new_user) #inserting in 'user' collection

		flash(f"Account has been created for '{form.username.data}'!", "success")
		return redirect(url_for('home'))
	return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = db.user.find_one({'username': form.username.data})
		if user and bcrypt.check_password_hash(user['password'], form.password.data):
			# Create a User object from the retrieved data
			user_obj = User(user['_id'], user['username'], user['email'])
			login_user(user_obj, remember=form.remember.data)  # Login the user
			flash('You have been logged in!', 'success')
			return redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check username and password', 'danger')
	return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
	logout_user()  
	flash('You have been logged out!', 'success')
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.run(debug=True)