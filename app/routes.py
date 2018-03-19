from flask import render_template
from app import app
import requests, json
from . import apiRequests

@app.route('/')
def index():

	sprint = 78

	data = apiRequests.start(sprint)
	return render_template('index.html', stories = data['stories'])







#--------------------- TEST ---------------------#

"""
	IDEAS
		- webscrape search query to check numbers
		

"""

