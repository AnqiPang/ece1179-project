from flask import Flask
from flask import render_template

webapp = Flask(__name__)

@webapp.route('/')
def index():
    return render_template("index.html", title="Home")

@webapp.route('/hi')
def say_hi():
    return "Hi!", 200

if __name__ == '__main__':
    webapp.run()
