import requests
import json

# def get_stories(sprint):
# 	"""
# 	TODO - get/request code is currently duplicated and can be reduced


# 	"jql" : "project = ADS AND sprint = 'A-Team' AND sprint IN openSprints() AND sprint NOT IN futureSprints() AND type in standardIssueTypes()",

# 	"""

# 	url = 'https://fullprofile.atlassian.net/rest/api/2/search'
# 				# '?jql=\
# 				# project=ADS\
# 				# +AND+sprint="A-Team"\
# 				# +AND+sprint+IN+openSprints()\
# 				# +AND+sprint+NOT+IN+futureSprints()\
# 				# +AND+type+IN+standardIssueTypes()\
# 				# '


# 	querystring = {
# 		"jql" : "project = ADS AND sprint = " + str(sprint) + " AND type in standardIssueTypes()",
# 		"maxResults" : "100",
# 		"fields" : "status, subtasks, issuetype, summary, timespent"
# 	}

# 	headers = {
# 	    'Authorization': "Basic dGltLnZhbi5lbGxlbWVldDpBZ3JpZGlnaXRhbDEhamlyYQ==",
# 	    'Cache-Control': "no-cache",
# 	    'Postman-Token': "9514aa40-4142-43df-bf5e-361c551463f2"
# 	    }

# 	response = requests.request("GET", url, headers=headers, params=querystring)

# 	parsed = response.json()
# 	#print(json.dumps(parsed['issues'][0], indent = 4))
	
# 	print("Requesting jql query: ", querystring['jql'])
# 	print("Filtering for fields: ", querystring['fields'])
# 	print("Recieved:", len(parsed['issues']), "/", parsed['total'] ,"stories")


# 	return parsed['issues']


def get_issues(sprint, search = None):
	"""
	TODO -  request does not capture all the results, limited by maxResults. only maxResults = 100.
			Explore pagination of results, or perform multiple requests starting at n * maxResults
	
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
			"fields" : "status, issuetype"
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



def create_lookup(parsed):
	"""
	Lookup that creates dict with key = issue_id and values = list of the issue's subtask_ids
	"""

	# print(parsed['total'])
	# print(len(parsed['issues']))

	count = 0
	subtask_keys = {}
	for i, issue in enumerate(parsed['issues']):
		# print('issue: ', i, ' has: ', len(issue['fields']['subtasks']), ' subtasks')
		count += 1 + len(issue['fields']['subtasks'])

		subtask_keys[issue['id']] = []
		for subtask in issue['fields']['subtasks']:
			subtask_keys[issue['id']].append(subtask['id'])

	# 	print("Issue id: ", issue['id'], " with key: ", issue['key'])
	# 	print("Has ", count, " subtasks: ", subtask_keys[issue['id']])
	
	print('Created lookup for issues: ', count)
	#print(subtask_keys)
	return(subtask_keys)


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
	"""

	subtasksFormated = [{
		"id" : int,
		"key" : "",
		"self" : "",
		"issuetype" : "",
		"issuetypeIcon" :"",
		"timeestimate" : int,
		"remainingEstimate" : int,
		"timespent" : int,
	}]

	storiesFormated = []


	# Support Issues are filtered, total support issues are counted and timespent is summed
	supportIssues = {
		"count" : 0,
		"timespent" : 0,
	}


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

		# WHAT TO DO WITH TECH-DEBT?

		# FORMAT self to url

		newStory = {
			"id" : issue['id'],
			"key" : issue['key'],
			"self" : "",
			"issuetype" : issue['fields']['issuetype']['name'],
			"issuetypeIcon" :"",
			"aggregatetimespent" : issue['fields']['aggregatetimespent'],
			"aggregatetimeoriginalestimate" : issue['fields']['aggregatetimeoriginalestimate'],
			"aggregatetimeestimate" : issue['fields']['aggregatetimeestimate'],
			"subtasks" : []
		}

		storiesFormated.append(newStory)

		for subtask in issue['fields']['subtasks']:
			print("	Has subtasks:",subtask['key'])
			subtasks.index

	print(supportIssues)
	print(json.dumps(storiesFormated, indent = 4))


	print("_" * 50)
	print(json.dumps(subtasks, indent = 4))




	


if __name__ == "__main__":

	sprint = 77

	#stories = get_stories(sprint)
	#subtasks = get_subtasks(sprint)

	stories = get_issues(sprint, search = "stories")
	subtasks = get_issues(sprint, search = "subtasks")
	data = format_data(stories, subtasks)
	#lookup = create_lookup(stories)
	






