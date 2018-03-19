from flask import render_template
from app import app
import requests, json

@app.route('/')
def index():

	sprint = 77
	stories = get_stories(sprint)
	subtasks = get_subtasks(sprint)

	return render_template('index.html', stories = stories, subtasks = subtasks)







#--------------------- TEST ---------------------#

"""
	IDEAS
		- webscrape search query to check numbers
		

"""

#--------------------- REQUEST FUNCTIONS ---------------------#

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
		"fields" : "status, subtasks, issuetype, summary"
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
