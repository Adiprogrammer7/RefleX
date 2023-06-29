from flask import Flask, render_template, redirect, flash, url_for
from forms import RegistrationForm, LoginForm

app = Flask(__name__)

app.config['SECRET_KEY'] = '8yuf7u8j'

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
		flash(f"Account has been created for '{form.username.data}'!", "success")
		return redirect(url_for('home'))
	return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		if form.username.data == 'admin' and form.password.data == 'pass':
			flash('You have been logged in!', 'success')
			return redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check username and password', 'danger')
	return render_template('login.html', form=form)


if __name__ == '__main__':
	app.run(debug=True)