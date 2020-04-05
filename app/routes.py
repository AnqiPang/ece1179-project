from flask import render_template
from app import webapp

@webapp.route('/', methods=['GET'])
@webapp.route('/index', methods=['GET'])
def index():
    return render_template("index.html", title="Home")
