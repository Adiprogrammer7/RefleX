from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
	return "<p>Hello, World!</p>"

@app.route("/new_entry")
def new_entry():
	return render_template('text_editor.html')

if __name__ == '__main__':
	app.run(debug=True)