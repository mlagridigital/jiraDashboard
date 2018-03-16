from flask import render_template
from app import app

@app.route('/')
def index():
	data = {'story' : 'hey we got a story'}
	return render_template('index.html', data = data)