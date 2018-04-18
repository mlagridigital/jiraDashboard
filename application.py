from flask import Flask, render_template, jsonify, redirect, url_for, request, Response
from functools import wraps
# from application import application
import requests, json
import apiRequests
# from flask.ext.cache import Cache

# cache = Cache(application, config={'CACHE_TYPE': 'simple'})

application = Flask(__name__)
application.debug = True

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'agridigitaldashboard001'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@application.route('/')
@requires_auth
def index():

	all_sprints = apiRequests.get_all_sprints()
	return render_template('index.html', all_sprints = all_sprints)

@application.route('/sprint/<int:sprint_id>')
@requires_auth
def sprint_dashboard(sprint_id, sort_field="issuetype", sort_direction="ascending"):

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

	stories = apiRequests.sort_table(stories, sort_field, sort_direction)

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


@application.route('/sprint/<int:sprint_id>/data')
@requires_auth
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

	return jsonify(
		stories = (data['stories']),
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

	# return jsonify (data = data['stories'])


if __name__ == "__main__":
	application.debug = True
	application.run()

#--------------------- TEST ---------------------#

"""
	IDEAS
		- webscrape search query to check numbers
		

"""

