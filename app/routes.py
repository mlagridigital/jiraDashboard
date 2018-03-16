from flask import render_template
from app import app
import requests, json

@app.route('/')
def index():
	data = {'story' : 'hey we got a story'}

	sprint = 76
	stories = get_stories(sprint)
	
	return render_template('index.html', data = stories)




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