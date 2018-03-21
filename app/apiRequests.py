import requests
import json

def get_issues(sprint, search = None):
	"""
	TODO -  Check data retrival at edge cases. Total == Max Results
	
	"""
		
	url = 'https://fullprofile.atlassian.net/rest/api/2/search'

	if search == "stories":
		querystring = {
			"jql" : "project = ADS AND sprint = " + str(sprint) + " AND type in standardIssueTypes()",
			"maxResults" : "100",
			"startAt" : 0,
			"fields" : "status, subtasks, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate"
		}
	elif search == "subtasks":
		querystring = {
			"jql" : "project = ADS AND sprint = " + str(sprint) + " AND type in subtaskIssueTypes()",
			"maxResults" : "100",
			"startAt" : 0,
			"fields" : "status, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate"
		}
	else:
		print("Error: invalid search criteria, only search for stories or subtasks")
		return

	headers = {
	    'Authorization': "Basic dGltLnZhbi5lbGxlbWVldDpBZ3JpZGlnaXRhbDEhamlyYQ==",
	    'Cache-Control': "no-cache",
	    'Postman-Token': "9514aa40-4142-43df-bf5e-361c551463f2"
	    }

	print("-" * 10)
	print("Getting", search)
	print("Requesting jql query: ", querystring['jql'])
	print("Filtering for fields: ", querystring['fields'])
	
	response = requests.request("GET", url, headers=headers, params=querystring)
	
	parsed = response.json()

	print("Recieved", len(parsed['issues']), "issues starting at", parsed['startAt'], "from a total of", parsed['total'])

	# Check to see if all issues were received, if not repeat request to retrieve all issues and append to original parsed response
	# maxResults is the number of issues received per request. total is the total number of issues within the query on Jira. 
	if parsed['total'] > parsed['maxResults']:

		remaining_calls = parsed['total'] // parsed['maxResults']

		for i in range(remaining_calls):

			querystring['startAt'] = (i + 1) * parsed['maxResults']
			response = requests.request("GET", url, headers=headers, params=querystring).json()
			print("Recieved", len(response['issues']), "issues starting at", response['startAt'], "from a total of", response['total'])

			for issue in response['issues']:
				parsed['issues'].append(issue)


	print("Received", len(parsed['issues']), "issues in total")
	#print(json.dumps(parsed, indent = 4))
	
	return parsed['issues']


def format_data(stories, subtasks):
	"""
	# FOR BURNDOWN - datetime is to show timespent on task over time

	# TODO 
		- ADD LOG TIME FIELDS TO STORIES / SUBTASKS; logtime = [developer, timespent, datetime];
			log are split by using ;  split go from end
			using datetime to format datetime fields
			idea for error checking  - function should return correct type
			check jira.tempo to which DEV??; expected none
			check logs include comments; attention these look to have affected .csv

	# QUESTIONS 
		- Include Priorities?? 
		- For Defects, Bugs and Subtasks include ROOT CAUSE
		- How should I treat bugs - as stories or supports
		- Creating burn downs, should stories be associated to a dev team and the timespent aggregated? 
		- How should I treat TECH-DEBT?
		- How should I treat subtask - OPS, PERI, API
	"""

	storiesFormated = []


	# Support Issues are filtered, total support issues are counted and timespent is summed
	supportIssues = {
		"count" : 0,
		"timespent" : 0,
	}

	# bugIssues = {
	# 	"count" : 0,
	# 	"timespent" : 0,
	# }

	#print("_" * 20)
	#print(json.dumps(subtasks, indent = 4))

	for issue in stories:
		
		print("_" * 20)
		print("Issue Key:", issue['key'])
		print("Issue type name:", issue['fields']['issuetype']['name'])


		# Filter out support tasks
		if issue['fields']['issuetype']['name'] == "Support ":
			supportIssues['count'] += 1
			if isinstance(issue['fields']['aggregatetimespent'], int):
				supportIssues['timespent'] += issue['fields']['aggregatetimespent']
			continue

		# FILTER OUT 'TASKS'


		#WHAT TO DO WITH BUGS -- TREAT AS STORY OR SUPPORT
		# if issue['fields']['issuetype']['name'] == "Bug":
		# 	bugIssues['count'] += 1
		# 	if isinstance(issue['fields']['aggregatetimespent'], int):
		# 		bugIssues['timespent'] += issue['fields']['aggregatetimespent']
		# 	continue

		# WHAT TO DO WITH TECH-DEBT?

		# FORMAT self to url

		newStory = {
			"id" : issue['id'],
			"key" : issue['key'],
			"summary" : issue['fields']['summary'],
			"self" : "https://fullprofile.atlassian.net/browse/" + issue['key'],
			"status" : issue['fields']['status']['name'],
			"issuetype" : issue['fields']['issuetype']['name'],
			"issuetypeIcon" : issue['fields']['issuetype']['iconUrl'],
			"aggregatetimespent" : issue['fields']['aggregatetimespent'],
			"aggregatetimeoriginalestimate" : issue['fields']['aggregatetimeoriginalestimate'],
			"aggregatetimeestimate" : issue['fields']['aggregatetimeestimate'],
			"aggregatetimespent_str" : str_time(issue['fields']['aggregatetimespent']),
			"aggregatetimeoriginalestimate_str" : str_time(issue['fields']['aggregatetimeoriginalestimate']),
			"aggregatetimeestimate_str" : str_time(issue['fields']['aggregatetimeestimate']),
			"progress" : calc_progress(issue['fields']['aggregatetimeoriginalestimate'], issue['fields']['aggregatetimeestimate']),
			"subtasks" : [],
			"subtask_status_count" : {
				"Dev In Progress" : 0,
				"To Do" : 0,
				"Done" : 0,
				"Dev Review" : 0,
				"Awaiting UAT" : 0,
			},
		}


		for subtask in issue['fields']['subtasks']:
			#print("  Has subtasks:",subtask['key'])

			for s in subtasks:
				if s['id'] == subtask['id']:
					print(" Has subtask match", s['key'], subtask['key'])

					newSubtask = {
						"id" : s['id'],
						"key" : s['key'],
						"summary" : s['fields']['summary'],
						"self" : "https://fullprofile.atlassian.net/browse/" + s['key'],
						"status" : s['fields']['status']['name'],
						"devteam" : "",
						"issuetype" : s['fields']['issuetype']['name'],
						"issuetypeIcon" : s['fields']['issuetype']['iconUrl'],
						"aggregatetimespent" : s['fields']['aggregatetimespent'],
						"aggregatetimeoriginalestimate" : s['fields']['aggregatetimeoriginalestimate'],
						"aggregatetimeestimate" : s['fields']['aggregatetimeestimate'],
						"aggregatetimespent_str" : str_time(s['fields']['aggregatetimespent']),
						"aggregatetimeoriginalestimate_str" : str_time(s['fields']['aggregatetimeoriginalestimate']),
						"aggregatetimeestimate_str" : str_time(s['fields']['aggregatetimeestimate']),
						"progress" : calc_progress(s['fields']['aggregatetimeoriginalestimate'], s['fields']['aggregatetimeestimate'])
					}

					if newSubtask['summary'].upper().startswith(("BACK", "API", "PERI"), 1) :
						newSubtask['devteam'] = "Backend"
					elif newSubtask['summary'].upper().startswith("FRONT", 1):
						newSubtask['devteam'] = "Front End"
					elif newSubtask['summary'].upper().startswith("TEST", 1):
						newSubtask['devteam'] = "Test"
					else:
						print("Error: subtask", newSubtask['key'], "not set to team")


					# print(json.dumps(newSubtask, indent = 4))
					newStory['subtasks'].append(newSubtask)

					s_status = s['fields']['status']['name']
					newStory['subtask_status_count'][s_status] += 1


			
		storiesFormated.append(newStory)
		#print(json.dumps(newStory, indent = 4))


	data = {
		"stories" : storiesFormated,
		"supoort" : supportIssues
	}

	return data

	# print(supportIssues)
	# print(json.dumps(storiesFormated, indent = 4))


	# print("_" * 50)
	# print(json.dumps(subtasks, indent = 4))


def str_time(time):
	"""
	Given a time in seconds. Return a string "Ww Dd Hh Mm". Where W/D/H/M are the number of weeks, days, hours, minutes in time.
	"""

	if not isinstance(time, int):
		print("Error time is not int, time is:", time)
		return time

	days_per_week = 5
	hours_per_day = 8

	weeks = time // (days_per_week * hours_per_day * 60 * 60)
	days = (time // (hours_per_day * 60 * 60)) % days_per_week
	hours = (time // (60 * 60)) % hours_per_day
	minutes = (time // 60) % 60

	units = ['w', 'd', 'h', 'm']
	values = [weeks, days, hours, minutes]

	lst = [str(x) + units[i] for i, x in enumerate(values) if x > 0]

	return " ".join(lst)


def calc_progress(original_estimate, remaining_time):

	if isinstance(original_estimate, int):
		if isinstance(remaining_time, int):

			if original_estimate == 0:
				print("ZeroError: original_estimate == 0")
				return None

			progess = round(((original_estimate - remaining_time) / original_estimate) * 100)
			#print("Progres:", progess)
			return progess

	else:
		print("Error calculating progress as time not int, time: [OE:", original_estimate, ", RE:", remaining_time, "]")
		return None


def start(sprint):
	stories = get_issues(sprint, search = "stories")
	subtasks = get_issues(sprint, search = "subtasks")
	data = format_data(stories, subtasks)

	return data



if __name__ == "__main__":

	sprint = 77

	stories = get_issues(sprint, search = "stories")
	subtasks = get_issues(sprint, search = "subtasks")
	data = format_data(stories, subtasks)

	






