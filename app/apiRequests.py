import requests
import json
import dateutil.parser

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
			"fields" : "status, subtasks, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate, customfield_10016, assignee, created",
			"expand" : "changelog",
		}
	elif search == "subtasks":
		querystring = {
			"jql" : "project = ADS AND sprint = " + str(sprint) + " AND type in subtaskIssueTypes()",
			"maxResults" : "100",
			"startAt" : 0,
			"fields" : "status, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate, customfield_10016, assignee, created",
			"expand" : "changelog",
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
		- How should treat story level tasks?
		- How should I treat bugs - as stories or supports
		- Creating burn downs, should stories be associated to a dev team and the timespent aggregated? 
		- How should I treat TECH-DEBT?
		- How should I treat subtask - OPS, PERI, API
		- Issue status - include Reopened?
		- Check for other issue statuses
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
		
		print("_" * 30)
		print("Issue Key:", issue['key'])
		print("Issue type name:", issue['fields']['issuetype']['name'])

		# Filter out support tasks
		if issue['fields']['issuetype']['name'] == "Support ":
			supportIssues['count'] += 1
			if isinstance(issue['fields']['aggregatetimespent'], int):
				supportIssues['timespent'] += issue['fields']['aggregatetimespent']
			continue

		#WHAT TO DO WITH BUGS -- TREAT AS STORY OR SUPPORT
		# if issue['fields']['issuetype']['name'] == "Bug":
		# 	bugIssues['count'] += 1
		# 	if isinstance(issue['fields']['aggregatetimespent'], int):
		# 		bugIssues['timespent'] += issue['fields']['aggregatetimespent']
		# 	continue

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
			"aggregatetimespent_str" : format_time(issue['fields']['aggregatetimespent']),
			"aggregatetimeoriginalestimate_str" : format_time(issue['fields']['aggregatetimeoriginalestimate']),
			"aggregatetimeestimate_str" : format_time(issue['fields']['aggregatetimeestimate']),
			"progress" : calc_progress(issue['fields']['aggregatetimeoriginalestimate'], issue['fields']['aggregatetimeestimate']),
			"subtasks" : [],
			"subtask_status_count" : {			
				"To Do" : 0,
				"Dev In Progress" : 0,
				"Dev Review" : 0,
				"Awaiting UAT" : 0,
				"Done" : 0,
			},
			"sprints" : format_sprints(issue['fields']['customfield_10016']),
			"assignee" : format_assignee(issue['fields']['assignee']),
			"changelog" : format_changelog(issue['changelog']),
			"created" : dateutil.parser.parse(issue['fields']['created']),
		}

		#print(format_sprints(issue['fields']['customfield_10016']))

		for subtask in issue['fields']['subtasks']:

			for s in subtasks:
				if s['id'] == subtask['id']:
					print("-" * 4)
					print("Subtask key", subtask['key'])
					print("Subtask type:", s['fields']['issuetype']['name'])

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
						"aggregatetimespent_str" : format_time(s['fields']['aggregatetimespent']),
						"aggregatetimeoriginalestimate_str" : format_time(s['fields']['aggregatetimeoriginalestimate']),
						"aggregatetimeestimate_str" : format_time(s['fields']['aggregatetimeestimate']),
						"progress" : calc_progress(s['fields']['aggregatetimeoriginalestimate'], s['fields']['aggregatetimeestimate']),
						"sprints" : format_sprints(s['fields']['customfield_10016']),
						"assignee" : format_assignee(s['fields']['assignee']),
						"changelog" : format_changelog(s['changelog']),
						"created" : dateutil.parser.parse(issue['fields']['created']),
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
		"support" : supportIssues
	}

	return data

	# print(supportIssues)
	# print(json.dumps(storiesFormated, indent = 4))


	# print("_" * 50)
	# print(json.dumps(subtasks, indent = 4))


def format_time(time):
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


def format_sprints(sprints):

	#current = True

	# sprints are stacked on the end of the list, last member of the
	sprintsFormatted = []

	for s in reversed(sprints):

		temp = {}

		for i in s.split('[')[1].split(','):
			key = i.split('=')[0]
			value = i.split('=')[1]
			temp[key] = value
		
		sprintsFormatted.append({
			"current" : "",
			"id" : temp['id'],
			"state" : temp['state'],
			"name" : temp['name'],
			"startDate" : temp['startDate'],
			"endDate" : temp['endDate'],
			"completeDate" : temp['completeDate']
			})

	return sprintsFormatted


def format_assignee(assignee):

	if assignee != None:
		return assignee['displayName']

	return ""


def format_changelog(changelog):
	"""
		
	Current changelog  => changelog{ histories : [ items[] ] }
	Change log contains a list, histories, where each change in histories is a list of items that were changed at that change instance
	Formatted changelog is a list of change items

		TODO:
			- NEED TO CHANGE TIMESHEET ID TO DISPLAYNAME
	"""

	# Check if all changelog histories have been received
	if changelog['total'] > changelog['maxResults']:
		print("Error: changelog pagination required, only", changelog['maxResults'], "of", changelog['total'], "received")

	
	changelogFormatted = []

	# Sort current changelog in descending order - created first is now top
	histories = changelog['histories'][::-1]

	for i_change, change in enumerate(histories):
		for item in change['items']:

			# Global variable SPRINT_LOG used to track count of instances of changelog items acorss the sprint
			# if item['field'] not in SPRINT_LOG:
			# 	SPRINT_LOG[item['field']] = 1
			# else:
			# 	SPRINT_LOG[item['field']] += 1
			

			# Filter changelog for fields
			if item['field'] in ['timespent', 'timeestimate', 'status', 'WorklogId', 'timeoriginalestimate', 'WorklogTimeSpent', 'resolution', 'resolutiondate']:
			#if item['field'] in ['timeestimate', 'timeoriginalestimate', 'timespent']:
			# if item['field'] not in ['description', 'Attachment', 'assignee', 'Parent', 'Fix Version', 'summary']:

				# Check current item in change against all items in previous change for duplicates, if duplicate contiune onto the next item not appending a newItem
				if i_change > 0:
					if (is_item_in_prev_change(item, histories[i_change - 1]['items'])):
						#print("Duplicate changelog item detected", item['field'])
						continue

				# store new formatted item in formatted changelog
				newItem = {
					'author' : change['author']['displayName'],
					'created' : dateutil.parser.parse(change['created']),
					'field' : item['field'],
					'from' : item['fromString'],
					'to' : item['toString'],
				}

				changelogFormatted.append(newItem)

	
	#print(json.dumps(changelogFormatted, indent = 4))

	return changelogFormatted


def is_item_in_prev_change(item, prev_change):
	"""
	Check current item against all items in previous change, return True if current item is a duplicate item else return False
	"""
	for prev_item in prev_change:
		#print("checking", item, "\nagainst", prev_item)
		if prev_item['field'] == item['field'] and item['from'] == prev_item['from'] and item['to'] == prev_item['to']:
			return True

	return False


def calc_dif(to, _from):

	if to is None:
		to = 0
	if _from is None:
		_from = 0
	
	dif = int(to) - int(_from)

	return dif


def get_burndown(stories, devteam):
	"""
	
	"""

	if devteam not in ['Front End', 'Backend', 'Test']:
		print("Error: get_burndown - devteam not in ['Front End', 'Backend', 'Test']")

	raw_data = []
	burndown_data = []

	for story in stories:
		#print('--', story['key'], story['created'])
		# sort_data(story['changelog'], story['created'], 'timeestimate')

		for subtask in story['subtasks']:
			# print('--', subtask['key'], subtask['created'])
			if subtask['devteam'] == devteam:
				raw_data.extend(collect_changes_and_dates(subtask['changelog'], subtask['created'], 'timeestimate'))
	
	for line in raw_data:
		print(line)
	
	print('-'*20)

	raw_data.sort(key = lambda e: e[0])
	total = 0
	for line in raw_data:
		# print(line)
		total += line[1]
		burndown_data.append([line[0], total])

	for line in burndown_data:
		print(line)

	return burndown_data

def collect_changes_and_dates(changelog, issue_created, field):
	"""
	important case - if first timeestimate chang e['from'] in changelog is not None, then fist item in burndown data should be from 0 to change['from']
	with timestamp = issue['created'] timestamp

	"""
	issue_burndown = []
	first_timestimate = True

	for i, change in enumerate(changelog):
		if change['field'] == field:

			if first_timestimate:
				first_timestimate = False
				if change['from'] is not None:
					issue_burndown.append([issue_created, int(change['from'])])
			
			issue_burndown.append([change['created'], calc_dif(change['to'], change['from'])])

			#print(change['created'], change['from'], '->', change['to'], '=', calc_dif(change['to'], change['from']))

	#print(issue_burndown)
	return issue_burndown



def start(sprint):

	#global SPRINT_LOG
	#SPRINT_LOG = {}

	stories = get_issues(sprint, search = "stories")
	subtasks = get_issues(sprint, search = "subtasks")
	data = format_data(stories, subtasks)

	print("Stories received:", len(stories))
	print("Subtasks received:", len(subtasks))
	#print(SPRINT_LOG)

	return data



if __name__ == "__main__":

	sprint = 77

	stories = get_issues(sprint, search = "stories")
	subtasks = get_issues(sprint, search = "subtasks")
	data = format_data(stories, subtasks)

	






