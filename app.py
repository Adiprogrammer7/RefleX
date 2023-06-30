from flask import Flask, render_template, redirect, flash, url_for
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
from forms import RegistrationForm, LoginForm

# Load environment variables from .env file and access them
load_dotenv() 
mongodb_uri = os.getenv('MONGODB_URI')
secret_key = os.getenv('SECRET_KEY')

# app configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
bcrypt = Bcrypt(app)

# MongoDB stuff
client = MongoClient(mongodb_uri)
db = client['reflex_db']


@app.route("/")
def home():
	return render_template('index.html')

@app.route("/new_entry")
def new_entry():
	return render_template('text_editor.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
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
	form = LoginForm()
	if form.validate_on_submit():
		current_user = db.user.find_one({'username': form.username.data})
		if current_user and bcrypt.check_password_hash(current_user['password'], form.password.data):
			flash('You have been logged in!', 'success')
			return redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check username and password', 'danger')
	return render_template('login.html', form=form)

if __name__ == '__main__':
	app.run(debug=True)