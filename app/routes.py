from flask import render_template, jsonify
from app import app
import requests, json
from . import apiRequests


@app.route('/')
def index():

	all_sprints = apiRequests.get_all_sprints()
	return render_template('index.html', all_sprints = all_sprints)

@app.route('/sprint/<int:sprint_id>')
def sprint_dashboard(sprint_id):

	# all_sprints = apiRequests.get_all_sprints()
	# this_sprint = apiRequests.get_sprint(sprint_id, all_sprints)

	data, all_sprints, data_check = apiRequests.start(sprint_id)

	this_sprint = apiRequests.get_sprint(sprint_id, all_sprints)
	burndown_data = apiRequests.get_burndown(data['stories'], this_sprint)
	sprint_burndown = apiRequests.append_cumulative_total(burndown_data)

	# for line in sprint_burndown:
	# 	print_str = [str(item) for item in line]
	# 	print_str[3] = round(int(print_str[3]) / (60*60), 1) 
	# 	print_str[4] = round(int(print_str[4]) / (60*60), 1) 
	# 	print(print_str)

	# print(burndown_data)
	backend_data = [x for x in burndown_data if x[2] == 'Backend']
	backend_burndown = apiRequests.append_cumulative_total(backend_data)

	frontend_data = [x for x in burndown_data if x[2] == 'Front End']
	frontend_burndown = apiRequests.append_cumulative_total(frontend_data)

	test_data = [x for x in burndown_data if x[2] == 'Test']
	test_burndown = apiRequests.append_cumulative_total(test_data)

	sprint_summary = apiRequests.summarise_sprint(data['stories'])

	stories = data['stories']

	stories = apiRequests.sort_table(stories, 'key', 'ascending')

	# frontend_burndown = backend_burndown
	# test_burndown = backend_burndown
	# frontend_burndown = apiRequests.get_burndown(data['stories'], 'Front End', this_sprint)
	# test_burndown = apiRequests.get_burndown(data['stories'], 'Test', this_sprint)

	defects = apiRequests.get_defects(data['stories'])

	return render_template('sprint_dashboard.html',
		stories = stories,
		sprint_burndown = sprint_burndown,
		backend_burndown = backend_burndown,
		frontend_burndown = frontend_burndown,
		test_burndown = test_burndown,
		defects = defects,
		all_sprints = all_sprints,
		this_sprint = this_sprint,
		sprint_summary = sprint_summary,
		support = (data['support']),
		)

@app.route('/sprint/<int:sprint_id>/data')
def json_data(sprint_id):
	# all_sprints = apiRequests.get_all_sprints()
	# this_sprint = apiRequests.get_sprint(sprint_id, all_sprints)

	data, all_sprints, data_check = apiRequests.start(sprint_id)

	this_sprint = apiRequests.get_sprint(sprint_id, all_sprints)
	burndown_data = apiRequests.get_burndown(data['stories'], this_sprint)
	sprint_burndown = apiRequests.append_cumulative_total(burndown_data)

	# for line in sprint_burndown:
	# 	print_str = [str(item) for item in line]
	# 	print_str[3] = round(int(print_str[3]) / (60*60), 1) 
	# 	print_str[4] = round(int(print_str[4]) / (60*60), 1) 
	# 	print(print_str)

	# print(burndown_data)
	backend_data = [x for x in burndown_data if x[2] == 'Backend']
	backend_burndown = apiRequests.append_cumulative_total(backend_data)

	frontend_data = [x for x in burndown_data if x[2] == 'Front End']
	frontend_burndown = apiRequests.append_cumulative_total(frontend_data)

	test_data = [x for x in burndown_data if x[2] == 'Test']
	test_burndown = apiRequests.append_cumulative_total(test_data)

	sprint_summary = apiRequests.summarise_sprint(data['stories'])

	# frontend_burndown = backend_burndown
	# test_burndown = backend_burndown
	# frontend_burndown = apiRequests.get_burndown(data['stories'], 'Front End', this_sprint)
	# test_burndown = apiRequests.get_burndown(data['stories'], 'Test', this_sprint)

	defects = apiRequests.get_defects(data['stories'])

	# return jsonify(
	# 	stories = (data['stories']),
	# 	sprint_burndown = sprint_burndown,
	# 	backend_burndown = backend_burndown,
	# 	frontend_burndown = frontend_burndown,
	# 	test_burndown = test_burndown,
	# 	defects = defects,
	# 	all_sprints = all_sprints,
	# 	this_sprint = this_sprint,
	# 	sprint_summary = sprint_summary,
	# 	support = (data['support']),
	# 	)

	return jsonify (data = data['stories'])


#--------------------- TEST ---------------------#

"""
	IDEAS
		- webscrape search query to check numbers
		

"""

