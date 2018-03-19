import requests
import json

def get_issues(sprint, search = None):
	"""
	TODO -  
	
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

	print("Recieved", len(parsed['issues']), "issues starting at", parsed['startAt'], "of a total of", parsed['total'])

	# CHECK FOR CASE WHERE NUMBER OF TOTAL == MAXRESULTS
	# SENSE CHECK DATA - COMPARE AGAINST
	if parsed['total'] > parsed['maxResults']:

		remaining_calls = parsed['total'] // parsed['maxResults']

		for i in range(remaining_calls):

			querystring['startAt'] = (i + 1) * parsed['maxResults']
			response = requests.request("GET", url, headers=headers, params=querystring).json()
			print("Recieved", len(response['issues']), "issues starting at", response['startAt'], "of a total of", response['total'])

			for issue in response['issues']:
				parsed['issues'].append(issue)


	print("Received", len(parsed['issues']), "issues in total")
	#print(json.dumps(parsed, indent = 4))
	
	return parsed['issues']



# def create_lookup(parsed):
# 	"""
# 	Lookup that creates dict with key = issue_id and values = list of the issue's subtask_ids
# 	"""

# 	# print(parsed['total'])
# 	# print(len(parsed['issues']))

# 	count = 0
# 	subtask_keys = {}
# 	for i, issue in enumerate(parsed['issues']):
# 		# print('issue: ', i, ' has: ', len(issue['fields']['subtasks']), ' subtasks')
# 		count += 1 + len(issue['fields']['subtasks'])

# 		subtask_keys[issue['id']] = []
# 		for subtask in issue['fields']['subtasks']:
# 			subtask_keys[issue['id']].append(subtask['id'])

# 	# 	print("Issue id: ", issue['id'], " with key: ", issue['key'])
# 	# 	print("Has ", count, " subtasks: ", subtask_keys[issue['id']])
	
# 	print('Created lookup for issues: ', count)
# 	#print(subtask_keys)
# 	return(subtask_keys)


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
	
		- Add status to issues


	# QUESTIONS 
		- Include Priorities?? 
		- For Defects, Bugs and Subtasks include ROOT CAUSE
		- How should I treat bugs - as stories or supports
		- Creating burn downs, should stories be associated to a dev team and the timespent aggregated? 
		- How should I treat TECH-DEBT?
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

	print("_" * 50)
	#print(json.dumps(subtasks, indent = 4))

	for i, issue in enumerate(stories):
		
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
			"self" : "",
			"status" : issue['fields']['status']['name'],
			"issuetype" : issue['fields']['issuetype']['name'],
			"issuetypeIcon" :"",
			"aggregatetimespent" : issue['fields']['aggregatetimespent'],
			"aggregatetimeoriginalestimate" : issue['fields']['aggregatetimeoriginalestimate'],
			"aggregatetimeestimate" : issue['fields']['aggregatetimeestimate'],
			"subtasks" : []
		}


		for subtask in issue['fields']['subtasks']:
			print("	Has subtasks:",subtask['key'])

			for s in subtasks:
				if s['id'] == subtask['id']:
					print("	subtask match", s['id'], subtask['id'])

					newSubtask = {
						"id" : s['id'],
						"key" : s['key'],
						"summary" : s['fields']['summary'],
						"self" : "",
						"status" : s['fields']['status']['name'],
						"devteam" : "",
						"issuetype" : s['fields']['issuetype']['name'],
						"issuetypeIcon" :"",
						"aggregatetimespent" : s['fields']['aggregatetimespent'],
						"aggregatetimeoriginalestimate" : s['fields']['aggregatetimeoriginalestimate'],
						"aggregatetimeestimate" : s['fields']['aggregatetimeestimate'],
					}

					if newSubtask['summary'].upper().startswith(("BACK", "API", "PERI"), 1) :
						newSubtask['devteam'] = "backend"
					elif newSubtask['summary'].upper().startswith("FRONT", 1):
						newSubtask['devteam'] = "frontend"
					elif newSubtask['summary'].upper().startswith("TEST", 1):
						newSubtask['devteam'] = "test"
					else:
						print("Error: subtask", newSubtask['id'], "not set to team")


					# print(json.dumps(newSubtask, indent = 4))
					newStory['subtasks'].append(newSubtask)

			
		storiesFormated.append(newStory)
		# print(json.dumps(newStory, indent = 4))



	data = {
		"stories" : storiesFormated,
		"supoort" : supportIssues
	}

	return data

	# print(supportIssues)
	# print(json.dumps(storiesFormated, indent = 4))


	# print("_" * 50)
	# print(json.dumps(subtasks, indent = 4))




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

	






