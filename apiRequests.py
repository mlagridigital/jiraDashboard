import requests
import json

def get_stories(sprint):
	"""
	TODO - get/request code is currently duplicated and can be reduced


	"jql" : "project = ADS AND sprint = 'A-Team' AND sprint IN openSprints() AND sprint NOT IN futureSprints() AND type in standardIssueTypes()",

	"""

	url = 'https://fullprofile.atlassian.net/rest/api/2/search'
				# '?jql=\
				# project=ADS\
				# +AND+sprint="A-Team"\
				# +AND+sprint+IN+openSprints()\
				# +AND+sprint+NOT+IN+futureSprints()\
				# +AND+type+IN+standardIssueTypes()\
				# '


	querystring = {
		"jql" : "project = ADS AND sprint = " + str(sprint) + " AND type in standardIssueTypes()",
		"maxResults" : "100",
		"fields" : "status, subtasks, issuetype"
	}

	headers = {
	    'Authorization': "Basic dGltLnZhbi5lbGxlbWVldDpBZ3JpZGlnaXRhbDEhamlyYQ==",
	    'Cache-Control': "no-cache",
	    'Postman-Token': "9514aa40-4142-43df-bf5e-361c551463f2"
	    }

	response = requests.request("GET", url, headers=headers, params=querystring)

	parsed = response.json()
	#print(json.dumps(parsed['issues'][0], indent = 4))
	
	print("Requesting stories in sprint:", sprint)
	print("Recieved:", len(parsed['issues']), "/", parsed['total'] ,"stories")


	return parsed


def get_subtasks(sprint):
	"""
	TODO -  request does not capture all the results, limited by maxResults. only maxResults = 100.
			Explore pagination of results, or perform multiple requests starting at n * maxResults
	
	"""
	
	url = 'https://fullprofile.atlassian.net/rest/api/2/search'

	querystring = {
		"jql" : "project = ADS AND sprint = " + str(sprint) + " AND type in subtaskIssueTypes()",
		"maxResults" : "200",
		"fields" : "status, issuetype"
	}

	headers = {
	    'Authorization': "Basic dGltLnZhbi5lbGxlbWVldDpBZ3JpZGlnaXRhbDEhamlyYQ==",
	    'Cache-Control': "no-cache",
	    'Postman-Token': "9514aa40-4142-43df-bf5e-361c551463f2"
	    }

	response = requests.request("GET", url, headers=headers, params=querystring)

	parsed = response.json()
	#print(json.dumps(parsed, indent = 4))

	print("Requesting subtasks in sprint:", sprint)
	print("Recieved:", len(parsed['issues']), "/", parsed['total'] ,"subtasks")

	return parsed



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




if __name__ == "__main__":

	sprint = 76

	stories = get_stories(sprint)
	subtask = get_subtasks(sprint)
	lookup = create_lookup(stories)
	






