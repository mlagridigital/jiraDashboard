from flask import render_template, jsonify
from app import app
import requests, json
from . import apiRequests

@app.route('/sprint/<int:sprint_id>')
def index(sprint_id):

	data = apiRequests.start(sprint_id)
	backend_burndown = apiRequests.get_burndown(data['stories'], 'Backend')
	frontend_burndown = apiRequests.get_burndown(data['stories'], 'Front End')
	return render_template('index.html', stories = (data['stories']), backend_burndown = backend_burndown, frontend_burndown = frontend_burndown)


@app.route('/sprint/<int:sprint_id>/data')
def json_data(sprint_id):
	#burndown_data = apiRequests.start(sprint_id)
	return jsonify(data)





#--------------------- TEST ---------------------#

"""
	IDEAS
		- webscrape search query to check numbers
		

"""

