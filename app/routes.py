from flask import render_template
from app import app
import requests, json
from . import apiRequests

@app.route('/sprint/<int:sprint_id>')
def index(sprint_id):

	data = apiRequests.start(sprint_id)
	return render_template('index.html', stories = data['stories'])







#--------------------- TEST ---------------------#

"""
	IDEAS
		- webscrape search query to check numbers
		

"""

