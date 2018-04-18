import requests
import json
import dateutil.parser
import csv
from datetime import timedelta, datetime, timezone
import pickle
import time
# import copy

def get_issues(sprint, search=None):
    # """
    # TODO -  Check data retrival at edge cases. Total == Max Results

    # """

    url = 'https://fullprofile.atlassian.net/rest/api/2/search'

    if search == "stories":
        querystring = {
            "jql": "project = ADS AND sprint = " + str(sprint) + " AND type in standardIssueTypes()",
            # "jql": "project = ADS AND type in standardIssueTypes()",
            "maxResults": "100",
            "startAt": 0,
            "fields": "status, subtasks, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate, customfield_10016, assignee, created, timespent, timeoriginalestimate, timeestimate, resolutiondate, fixVersions",
            "expand": "changelog",
        }
    elif search == "subtasks":
        querystring = {
            "jql": "project = ADS AND sprint = " + str(sprint) + " AND type in subtaskIssueTypes()",
            # "jql": "project = ADS AND type in subtaskIssueTypes()",
            "maxResults": "100",
            "startAt": 0,
            "fields": "status, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate, customfield_10016, assignee, created, timespent, timeoriginalestimate, timeestimate, customfield_11222, resolutiondate, fixVersions",
            "expand": "changelog",
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

    response = requests.request(
        "GET", url, headers=headers, params=querystring)

    parsed = response.json()

    print("Recieved", len(parsed['issues']), "issues starting at",
          parsed['startAt'], "from a total of", parsed['total'])

    # Check to see if all issues were received, if not repeat request to retrieve all issues and append to original parsed response
    # maxResults is the number of issues received per request. total is the total number of issues within the query on Jira.
    if parsed['total'] > parsed['maxResults']:

        remaining_calls = parsed['total'] // parsed['maxResults']

        for i in range(remaining_calls):

            querystring['startAt'] = (i + 1) * parsed['maxResults']
            response = requests.request(
                "GET", url, headers=headers, params=querystring).json()
            print("Recieved", len(response['issues']), "issues starting at",
                  response['startAt'], "from a total of", response['total'])

            for issue in response['issues']:
                parsed['issues'].append(issue)

    print("Received", len(parsed['issues']), "issues in total")
    #print(json.dumps(parsed, indent = 4))

    return parsed['issues']


def get_all_sprints():

    url = 'https://fullprofile.atlassian.net/rest/agile/1.0/board/12/sprint/'
    headers = {
        'Authorization': "Basic dGltLnZhbi5lbGxlbWVldDpBZ3JpZGlnaXRhbDEhamlyYQ==",
        'Cache-Control': "no-cache",
        'Postman-Token': "9514aa40-4142-43df-bf5e-361c551463f2"
    }

    querystring = {
        'startAt': 0,
    }

    print("-" * 10)
    print("Getting sprints meta")
    # print("Requesting jql query: ", querystring['jql'])
    # print("Filtering for fields: ", querystring['fields'])

    response = requests.request("GET", url, headers=headers, params=querystring)
    parsed = response.json()
    sprints = parsed['values']
    print("Recieved", len(sprints), 'sprints', 'starting at', querystring['startAt'])

    i = 1
    while not parsed['isLast']:

        querystring['startAt'] = i * parsed['maxResults']
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        print("Recieved", len(response['values']), 'sprints', 'starting at', querystring['startAt'])

        sprints.extend(response['values'])
        parsed['isLast'] = response['isLast']
        i += 1

    print("Received", len(sprints), "sprints in total")

    sprints.sort(key = lambda e: e['name'], reverse = True)

    return sprints


def get_sprint(sprint_id, all_sprints):

    temp_list = [item for item in all_sprints if item['id'] == sprint_id]

    temp = temp_list[0]

    temp["startDate_rendered"] = dateutil.parser.parse(temp['startDate']).strftime("%a %d %b")
    temp["endDate_rendered"] = dateutil.parser.parse(temp['endDate']).strftime("%a %d %b")
    temp["days_remaining"] = (dateutil.parser.parse(temp['endDate']) - dateutil.parser.parse(temp['startDate'])).days
    temp["weekdays_remaining"] = calc_weekdays_remaining(dateutil.parser.parse(temp['endDate']))

    this_sprint = temp

    return temp


# ------------------ FORMAT ISSUES ------------------ #

def format_data(stories, subtasks, sprint_id):
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
        "iconUrl": "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10304&avatarType=issuetype",
        "count": 0,
        "timespent": 0,
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
        print('AGG ::', 'OE:', issue['fields']['aggregatetimeoriginalestimate'], 'TE:', issue['fields']
              ['aggregatetimeestimate'], 'TS:', issue['fields']['aggregatetimespent'])
        print('OE:', issue['fields']['timeoriginalestimate'], 'TE:', issue['fields']
              ['timeestimate'], 'TS:', issue['fields']['timespent'])

        # Filter out support tasks
        if issue['fields']['issuetype']['name'] == "Support ":
            supportIssues['count'] += 1
            if isinstance(issue['fields']['aggregatetimespent'], int):
                supportIssues['timespent'] += issue['fields']['aggregatetimespent']
            # continue

        # WHAT TO DO WITH BUGS -- TREAT AS STORY OR SUPPORT
        # if issue['fields']['issuetype']['name'] == "Bug":
        # 	bugIssues['count'] += 1
        # 	if isinstance(issue['fields']['aggregatetimespent'], int):
        # 		bugIssues['timespent'] += issue['fields']['aggregatetimespent']
        # 	continue

        newStory = {
            "id": issue['id'],
            "key": issue['key'],
            "summary": issue['fields']['summary'],
            "self": "https://fullprofile.atlassian.net/browse/" + issue['key'],
            "created": dateutil.parser.parse(issue['fields']['created']),
            "isSubtask" : False,
            "status": issue['fields']['status']['name'],
            "issuetype": issue['fields']['issuetype']['name'],
            "issuetypeIcon": issue['fields']['issuetype']['iconUrl'],

            "fixVersions" :issue['fields']['fixVersions'],

            "resolutiondate": dateutil.parser.parse(issue['fields']['resolutiondate']) if issue['fields']['resolutiondate'] else None,
            
            "timespent": issue['fields']['timespent'],
            "timeoriginalestimate": issue['fields']['timeoriginalestimate'],
            "timeestimate": issue['fields']['timeestimate'],
            
            "aggregatetimespent": issue['fields']['aggregatetimespent'] if issue['fields']['aggregatetimespent'] else 0,
            "aggregatetimeoriginalestimate": issue['fields']['aggregatetimeoriginalestimate'] if issue['fields']['aggregatetimeoriginalestimate'] else 0,
            "aggregatetimeestimate": issue['fields']['aggregatetimeestimate'] if issue['fields']['aggregatetimeestimate'] else 0,
            "aggregatetimespent_str": format_time(issue['fields']['aggregatetimespent']),
            "aggregatetimeoriginalestimate_str": format_time(issue['fields']['aggregatetimeoriginalestimate']),
            "aggregatetimeestimate_str": format_time(issue['fields']['aggregatetimeestimate']),
            
            "sprints": format_sprints(issue['fields']['customfield_10016']),
            "assignee": format_assignee(issue['fields']['assignee']),
            "changelog": format_changelog(issue['changelog']),

            "progress": calc_progress(issue['fields']['aggregatetimeoriginalestimate'], issue['fields']['aggregatetimeestimate']),
            "TSvsOE": timespent_vs_originalestimate(issue['fields']['aggregatetimeoriginalestimate'], issue['fields']['aggregatetimespent'], issue['fields']['status']['name']),

            "subtasks": [],
            "subtask_status_count": {
                "To Do": 0,
                "Dev In Progress": 0,
                "Dev Review": 0,
                "Awaiting UAT": 0,
                "Done": 0,
                "Reopened": 0,
            },

            "subtask_rootcauses": {},
            "subtask_rootcauses_timespent": 0,
            "subtask_rootcauses_timespent_in_this_sprint": 0,            
        }

        print('DateCreated:', newStory['created'])
        print('Sprints:', [i['id'] for i in newStory['sprints']])
        # print('SPRINTS:', json.dumps(newStory['sprints'], indent = 4))

        # print(format_sprints(issue['fields']['customfield_10016']))

        
        newStory["timespent_in_this_sprint"] = calc_timespent_this_sprint_on_issue(newStory['changelog'], sprint_id, newStory['sprints'])
        newStory["timespent_in_this_sprint_rendered"] = format_time(newStory["timespent_in_this_sprint"])
        newStory["aggregatetimespent_in_this_sprint"] = newStory["timespent_in_this_sprint"]

        for subtask in issue['fields']['subtasks']:
            for s in subtasks:
                if s['id'] == subtask['id']:

                    print("-" * 4)
                    print("Subtask key", subtask['key'])
                    print("Subtask type:", s['fields']['issuetype']['name'])
                    print('OE:', s['fields']['aggregatetimeoriginalestimate'], 'TE:', s['fields']['aggregatetimeestimate'], 'TS:', s['fields']['aggregatetimespent'])


                    newSubtask = {
                        "id": s['id'],
                        "key": s['key'],
                        "summary": s['fields']['summary'],
                        "self": "https://fullprofile.atlassian.net/browse/" + s['key'],
                        "created": dateutil.parser.parse(s['fields']['created']),
                        "isSubtask" : True,
                        "status": s['fields']['status']['name'],
                        
                        "issuetype": s['fields']['issuetype']['name'],
                        "issuetypeIcon": s['fields']['issuetype']['iconUrl'],

                        "fixVersions" :s['fields']['fixVersions'],

                        "resolutiondate": dateutil.parser.parse(s['fields']['resolutiondate']) if s['fields']['resolutiondate'] else None,
                        
                        "timespent": s['fields']['timespent'],
                        "timeoriginalestimate": s['fields']['timeoriginalestimate'],
                        "timeestimate": s['fields']['timeestimate'],
                        "timespent_rendered": format_time(s['fields']['timespent']),
                        "timeoriginalestimate_rendered": format_time(s['fields']['timeoriginalestimate']),
                        "timeestimate_rendered": format_time(s['fields']['timeestimate']),

                        "aggregatetimespent": s['fields']['aggregatetimespent'],
                        "aggregatetimeoriginalestimate": s['fields']['aggregatetimeoriginalestimate'],
                        "aggregatetimeestimate": s['fields']['aggregatetimeestimate'],
                        "aggregatetimespent_str": format_time(s['fields']['aggregatetimespent']),
                        "aggregatetimeoriginalestimate_str": format_time(s['fields']['aggregatetimeoriginalestimate']),
                        "aggregatetimeestimate_str": format_time(s['fields']['aggregatetimeestimate']),

                        "sprints": format_sprints(s['fields']['customfield_10016']),
                        "assignee": format_assignee(s['fields']['assignee']),
                        "changelog": format_changelog(s['changelog']),

                        "devteam": None,

                        "progress": calc_progress(s['fields']['timeoriginalestimate'], s['fields']['timeestimate']),
                        "TSvsOE": timespent_vs_originalestimate(s['fields']['timeoriginalestimate'], s['fields']['timespent'], s['fields']['status']['name']),

                        "rootcause": s['fields']['customfield_11222']['value'] if s['fields']['customfield_11222'] else None,

                        "sprint_completed_in": None,

                    }

                    print("Root cause:", newSubtask['rootcause'])

                    # SANITY CHECK
                    if s['fields']['aggregatetimeestimate'] != s['fields']['timeestimate']:
                        print("ERROR: SANITY CHECK [format_data] aggregatetimeestimate != timeestimate")
                    if s['fields']['aggregatetimespent'] != s['fields']['timespent']:
                        print("ERROR: [format_data] aggregatetimespent != timespent")
                    if s['fields']['aggregatetimeoriginalestimate'] != s['fields']['timeoriginalestimate']:
                        print("ERROR: [format_data] aggregatetimeoriginalestimate != timeoriginalestimate")


                    # For each subtask associate the devteam from the subtask summary
                    if newSubtask['summary'].upper().startswith(("BACK", "API", "PERI"), 1):
                        newSubtask['devteam'] = "Backend"
                    elif newSubtask['summary'].upper().startswith("FRONT", 1):
                        newSubtask['devteam'] = "Front End"
                    elif newSubtask['summary'].upper().startswith("TEST", 1):
                        newSubtask['devteam'] = "Test"
                    elif newSubtask['summary'].upper().startswith("OPS", 1):
                        newSubtask['devteam'] = "Ops"
                    else:
                        print("Error: subtask",
                              newSubtask['key'], "not set to team")

                    print('DateCreated:', dateutil.parser.parse(issue['fields']['created']))
                    print('In Sprints:', [i['id'] for i in newSubtask['sprints']])

                    newSubtask["completed_in_sprint"] = issue_completed_in_sprint_number(newSubtask['resolutiondate'], newSubtask['sprints'])

                    newSubtask["timespent_in_this_sprint"] = calc_timespent_this_sprint_on_issue(newSubtask['changelog'], sprint_id, newSubtask['sprints'])
                    newSubtask["timespent_in_this_sprint_rendered"] = format_time(newSubtask["timespent_in_this_sprint"])
                    newStory["aggregatetimespent_in_this_sprint"] += calc_timespent_this_sprint_on_issue(newSubtask['changelog'], sprint_id, newSubtask['sprints'])

                    newStory['subtasks'].append(newSubtask)

                    # Increase count for subtask status in the story
                    s_status = s['fields']['status']['name']
                    newStory['subtask_status_count'][s_status] += 1



                    # If subtask has rootcause increase count of rootcause in the story & and aggreate timespent on rootcauses
                    if s['fields']['issuetype']['name'] == 'Defect':

                        # Specify rootcause name
                        if s['fields']['customfield_11222']:
                            rootcause = s['fields']['customfield_11222']['value']
                        else:
                            rootcause = 'Rootcause not specified'
                       
                       # If rootcause
                        if rootcause in newStory['subtask_rootcauses']:
                            newStory['subtask_rootcauses'][rootcause]['count'] += 1
                        else:
                            newStory['subtask_rootcauses'][rootcause] = {
                                'count': 1,
                                'timespent': 0,
                                'timespent_in_this_sprint': 0,
                            }

                        if newSubtask['timespent']:
                            newStory['subtask_rootcauses'][rootcause]['timespent'] += newSubtask['timespent']
                            newStory['subtask_rootcauses_timespent'] += newSubtask['timespent']

                        if newSubtask['timespent_in_this_sprint']:
                            newStory['subtask_rootcauses'][rootcause]['timespent_in_this_sprint'] += newSubtask['timespent_in_this_sprint']
                            newStory['subtask_rootcauses_timespent_in_this_sprint'] += newSubtask['timespent_in_this_sprint']
                        


        newStory["aggregatetimespent_in_this_sprint_rendered"] = format_time(newStory["aggregatetimespent_in_this_sprint"])

        storiesFormated.append(newStory)
        
        if DEBUG['defects']: print(newStory['key'], "Story Rootcauses:", json.dumps(newStory['subtask_rootcauses'], indent = 4))


    supportIssues['timespent_rendered'] = format_time(supportIssues['timespent'])

    data = {
        "stories": storiesFormated,
        "support": supportIssues,
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

    if time == 0:
        return "0d"

    if not isinstance(time, int):
        print("Error [format_time] - time is not int, time is:", time)
        return ""



    time = abs(time)

    days_per_week = 5
    hours_per_day = 8

    weeks = time // (days_per_week * hours_per_day * 60 * 60)
    days = (time // (hours_per_day * 60 * 60)) % days_per_week
    hours = (time // (60 * 60)) % hours_per_day
    minutes = (time // 60) % 60

    units = ['w', 'd', 'h', 'm']
    values = [weeks, days, hours, minutes]

    lst = [str(x) + units[i] for i, x in enumerate(values) if x > 0]

    rendered_time = (" ".join(lst))

    return rendered_time


def format_sprints(sprints):

    #current = True

    # sprints are stacked on the end of the list, last member of the
    sprintsFormatted = []

    for s in sprints:

        temp = {}

        for i in s.split('[')[1].split(','):
            key = i.split('=')[0]
            value = i.split('=')[1]
            temp[key] = value

        sprintsFormatted.append({
            "current": "",
            "id": int(temp['id']),
            "state": temp['state'],
            "name": temp['name'],
            "startDate": dateutil.parser.parse(temp['startDate']),
            "startDate_rendered": dateutil.parser.parse(temp['startDate']).strftime("%a %m %b"),
            "endDate": dateutil.parser.parse(temp['endDate']),
            "endDate_rendered": dateutil.parser.parse(temp['endDate']).strftime("%a %m %b"),
            "completeDate": temp['completeDate'],
            "weekdays_remaining": calc_weekdays_remaining(dateutil.parser.parse(temp['endDate']))
        })

    return sprintsFormatted


def calc_weekdays_remaining(endDate):

    today = datetime.now(timezone.utc)
    days_remaining = 0    
    i = 1

    if today > endDate:
        return days_remaining

    while (datetime.date(today + timedelta(days=i)) <= datetime.date(endDate)):

        if (today + timedelta(days=i)).weekday() not in [5,6]:
            days_remaining += 1
        
        i += 1

    return days_remaining

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
        print("Error: changelog pagination required, only",
              changelog['maxResults'], "of", changelog['total'], "received")

    changelogFormatted = []

    # Sort current changelog in descending order - created first is now top
    histories = changelog['histories'][::-1]

    for i_change, change in enumerate(histories):
        for item in change['items']:

            # Filter changelog for fields
            # if item['field']:
            # if item['field'] in ['timespent', 'timeestimate', 'timeoriginalestimate', 'status', 'WorklogId', 'WorklogTimeSpent', 'resolution', 'resolutiondate', 'Sprint']:
            # if item['field'] in ['timespent', 'timeestimate', 'timeoriginalestimate', 'status']:
            if item['field'] not in ['description', 'Attachment', 'assignee', 'Parent', 'Fix Version', 'summary']:

                # Check current item in change against all items in previous change for duplicates, if duplicate contiune onto the next item not appending a newItem
                if i_change > 0:
                    if (is_item_in_prev_change(item, histories[i_change - 1]['items'])):
                        #print("Duplicate changelog item detected", item['field'])
                        continue

                # store new formatted item in formatted changelog
                newItem = {
                    'author': change['author']['displayName'],
                    'created': dateutil.parser.parse(change['created']),
                    'field': item['field'],
                    'from': item['fromString'],
                    'to': item['toString'],
                }

                changelogFormatted.append(newItem)

                if DEBUG['changelog']:
                    if item['field'] in ['timespent', 'timeestimate', 'timeoriginalestimate', ]:
                        print(str(i_change).ljust(3), str(newItem['author']).ljust(20), str(newItem['created']).ljust(32), str(newItem['field']).rjust(
                            20), str(newItem['from']).rjust(15), '->', str(newItem['to']).ljust(6), '=', str(calc_dif(newItem['to'], newItem['from'])).rjust(6))
                    else:
                        print(str(i_change).ljust(3), str(newItem['author']).ljust(20), str(newItem['created']).ljust(
                            32), str(newItem['field']).rjust(20), str(newItem['from']).rjust(15), '->', str(newItem['to']))

            # Global variable SPRINT_LOG used to track count of instances of changelog items acorss the sprint
            if item['field'] not in SPRINT_LOG:
                SPRINT_LOG[item['field']] = 1
            else:
                SPRINT_LOG[item['field']] += 1

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


def calc_progress(originalestimate, timeestimate):
    """
    Calcluate the percentage diffrence between originalestimate and timeesstimate

    If either inputs are None return None. If originalestimate == 0 return None

    """

    if isinstance(originalestimate, int) and isinstance(timeestimate, int):
        
        if originalestimate == 0:
            print("ERROR: [calc_progress] - ZeroError, originalestimate == 0")
            return None
        else:
            progess = round(((originalestimate - timeestimate) / originalestimate) * 100)
            return progess

    else:
        print("ERROR: [calc_progress] - Time not int [OE:", originalestimate, ", TE:", timeestimate, "]")
        return None


def timespent_vs_originalestimate(originalestimate, timespent, status):
    """
    Calcluate the difference between originalestimate and actual timespent. 

    If either inputs are None return None.

    """

    if isinstance(originalestimate, int) and isinstance(timespent, int):
        difference = originalestimate - timespent
        percentage = calc_progress(originalestimate, timespent)

        if percentage is not None:
            percentage = -1 * percentage

    else:
        print("ERROR: [timespent_vs_originalestimate] - Time not int [OE:", originalestimate, ", TS:", timespent, "]")
        difference = None
        percentage = None

    return {'value': difference, 'rendered': format_time(difference), 'percentage': percentage, 'traffic_light': traffic_light(percentage, status)}


def traffic_light(percentage, status):


    if percentage == None:
        return ''
    else:
        
        if status == 'Done':
            if  percentage < 0:
                return 'info'
            elif percentage <= 10:
                return 'success'
            elif percentage <= 50:
                return 'warning'
            else:
                return 'danger'

        elif percentage >= 10:
            return 'overruning'
        else:
            return 'dark'


def calc_dif(to, _from):

    if to is None:
        to = 0
    if _from is None:
        _from = 0

    dif = int(to) - int(_from)

    return dif


def issue_completed_in_sprint_number(resolutiondate, sprints):

    if resolutiondate != None:
        
        sprints.sort(key=lambda e: e['startDate'])

        for sprint in sprints:
            if resolutiondate <= sprint['endDate']:
                # print("Issue completed in sprint:", sprint['id'])
                # print(type(sprint['id']))
                # print((sprint['id']))
                return sprint['id']
        else:
            print("ERROR: [issue_completed_in_sprint_number] - resolutiondate not in sprints, resolutiondate:", str(resolutiondate))
            return None
    else:
        print("Issue completed in sprint: Still in progress")
        return None
        # resolutiondate


def calc_timespent_this_sprint_on_issue(changelog, sprint, sprints):
    
    total = 0

    for change in changelog:

        if change['field'] == 'timespent':

            if sprint == issue_completed_in_sprint_number(change['created'], sprints):

                dif = calc_dif(change['to'], change['from'])

                if dif == None:
                    print("ERROR: [calc_timespent_this_sprint_on_issue] - dif:", dif)
                else:
                    total += dif

    return total
        


# ------------------ TABLE SORT ------------------ #

def sort_table(stories, sort_col, direction):

    if direction == 'descending':
        reverse = True
    else:
        reverse = False


    stories.sort(key=lambda e: e[sort_col], reverse=reverse)

    return stories

# ------------------ BURNDOWN ------------------ #


def append_cumulative_total(dataset):

    new_dataset = []
    total = 0

    for i in dataset:
        new_item = i[:]
        new_item.append(total)
        new_dataset.append(new_item)
        # print(new_item)
        
        total += i[3]
        new_item = i[:]
        new_item.append(total)
        new_dataset.append(new_item)
        # print(new_item)

    # print("DATASET")
    # print(new_dataset)


    return new_dataset


def get_burndown(stories, this_sprint):
    """

    """

    raw_data = get_burndown_raw(stories, this_sprint)
    # sort raw_data by date
    raw_data.sort(key=lambda e: e[0])
    burndown_data = []
    # burndown_data = raw_data


    for line in raw_data:
        # print(str(line[0]).ljust(32), str(line[1]).rjust(7))
        # print(line)
        # print([total])
        burndown_data.append(line)
        # total += line[3]
        # burndown_data.append(line.extend([total]))


    # print()
    # print('Hours at burndown end:', sum([i[1] for i in raw_data])/(60*60))

    # with open('data.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     for line in burndown_data:
    #         writer.writerow(line)


    return burndown_data


def get_burndown_raw(stories, this_sprint):
    raw_data = []

    for story in stories:
        issue_burndown = get_issue_burndown(story, this_sprint)
        raw_data.extend(issue_burndown)

        for subtask in story['subtasks']:
            issue_burndown = get_issue_burndown(subtask, this_sprint)
            raw_data.extend(issue_burndown)

    return raw_data


def get_issue_burndown(issue, this_sprint):

    if 'devteam' in issue:
        devteam = issue['devteam']
    else:
        devteam = "" 

    if DEBUG['burndown']: 
        print()
        print("Issue key:", issue['key'])
        print("Devteam:", issue['devteam']) if 'devteam' in issue else print("Devteam: n/a")
        print("Issue created:", issue['created'])
        print('Issue', 'OE:', issue['timeoriginalestimate'], 'TE:', issue['timeestimate'], 'TS:', issue['timespent'])

        # print issue changelog
        print("-- changelog --")
        for change in issue['changelog']:
            print(str(change['created']).ljust(32), change['field'].ljust(20), str(change['from']).rjust(6), '->', str(change['to']).ljust(6))
    
    # get list of burndown items [date, int], each item is the change in value of the field at the change instance
    issue_burndown = collect_changes_and_dates(issue['changelog'], issue['created'], 'timeestimate', issue['timeoriginalestimate'])
    
    # sum items in burndown where item date is less than given start date
    issue_burndown = adjust_burndown_startdate(issue_burndown, this_sprint['startDate'], this_sprint['id'])

    new_list = []
    for item in issue_burndown:
        new_list.append([item[0], issue['key'], devteam, item[1]])

    return new_list


def collect_changes_and_dates(changelog, issue_created, field, subtask_originalestimate):
    """
    important case - if first timeestimate chang e['from'] in changelog is not None, then fist item in burndown data should be from 0 to change['from']
    with timestamp = issue['created'] timestamp

    """
    issue_burndown = []
    first = True

    if DEBUG['burndown']: print('--', 'Filtered changelog items', '--')

    for change in changelog:
        
        if change['field'] == field:
            
            if first:
                if change['from'] is not None:
                    issue_burndown.append([issue_created, int(change['from'])])
                    if DEBUG['burndown']: print(str(issue_created).ljust(32), str(change['from']).rjust(25))
                first = False

            issue_burndown.append([change['created'], calc_dif(change['to'], change['from'])])
            if DEBUG['burndown']: print(str(change['created']).ljust(32), str(change['from']).rjust(6), '->', str(change['to']).ljust(6), '=', str(calc_dif(change['to'], change['from'])).rjust(6))

    if len(issue_burndown) == 0 and subtask_originalestimate is not None:
        issue_burndown.append([issue_created, subtask_originalestimate])
        if DEBUG['burndown']: print(str(issue_created).ljust(32), subtask_originalestimate)

    if DEBUG['burndown']:
        print('--', 'Items in issue burndown', '--')
        for line in issue_burndown:
            print(str(line[0]).ljust(32), str(line[1]).rjust(7))

    return issue_burndown


def adjust_burndown_startdate(subtask_raw_data, sprint_start, sprint_id):

    total = 0
    subtask_burndown =[]

    sprint_start = dateutil.parser.parse(sprint_start)

    if DEBUG['burndown']: print("--", "Adjusting burndown to align with sprint", "|", "Sprint", str(sprint_id), "start:", str(sprint_start), "--")

    if DEBUG['burndown']:
        print('-burndown before-')
        for line in subtask_raw_data:
            print(str(line[0]).ljust(32), str(line[1]).rjust(7))   




    for i, point in enumerate(subtask_raw_data):
        
        if sprint_start > point[0]:
            total += point[1]

            if i == (len(subtask_raw_data)-1):
                new_point = [sprint_start, total]
                subtask_burndown.append(new_point)

        
        else:
            if total > 0:
                if DEBUG['burndown']: print('summmed total to sprint_start:', total)
                new_point = [sprint_start, total]
                subtask_burndown.append(new_point)
                total = 0

            new_point = [point[0], point[1]]
            subtask_burndown.append(new_point)



    if DEBUG['burndown']:
        print('-burndown after-')
        for line in subtask_burndown:
            print(str(line[0]).ljust(32), str(line[1]).rjust(7))


    total_re_before = sum([x[1] for x in subtask_raw_data])
    total_re_after = sum([x[1] for x in subtask_burndown])

    if total_re_after != total_re_before:
        print('ERROR - [adjust_burndown_startdate] Sum of changelog before:', total_re_before, 'not equal to after:', total_re_after, )

    return subtask_burndown


def get_startdate(story, issue):
    """
    The startDate of an Issue burndown should be:
        1) If the story has been moved mid sprint; the date that the sprint was moved
        2) If the issue was created after the sprint start or after 1) then it should be the created date
        3) Else it should be the start date of the sprint
    """
    pass


def data_checking(stories, subtasks):

    # all_issues = [subtask for story in stories for subtask in story['subtasks']]

    all_issues = []
    total = 0
    count_issues = 0
    issues_timeestimate_none = []

    # for story in stories:
    #     all_issues.append(story)
    #     if story['subtasks']:
    #         for subtask in story['subtasks']:
    #             all_issues.append(subtask)


    all_issues.extend(stories)
    all_issues.extend(subtasks)

    filtered_issues = [[item['key'], item['fields']['timeestimate'], format_time(item['fields']['timeestimate'])] for item in all_issues]

    for issue in all_issues:
        try:
            total += issue['fields']['timeestimate']
            count_issues += 1
        except:
            total += 0
            issues_timeestimate_none.append(issue['key'])
            count_issues += 1

    total = total / (60 * 60)

    return filtered_issues, total, count_issues, issues_timeestimate_none

# ------------------ RETRO ------------------ #

def get_defects(stories):
    """
    
    """
    stories_with_defects = []
    defects_total_count = {}

    for story in stories:
        if story['subtask_rootcauses']:
            
            timespent_on_defects = sum([story['subtask_rootcauses'][x]['timespent'] for x in story['subtask_rootcauses']])
            timespent_in_this_sprint_on_defects = sum([story['subtask_rootcauses'][x]['timespent_in_this_sprint'] for x in story['subtask_rootcauses']])

            story_with_defect = {
                'key': story['key'],
                'self': story['self'],
                'issuetypeIcon' :story['issuetypeIcon'],
                'subtask_rootcauses': story['subtask_rootcauses'],
                'total_count': sum([story['subtask_rootcauses'][x]['count'] for x in story['subtask_rootcauses']]),
                'timespent_on_defects': timespent_on_defects,
                'timespent_on_defects_rendered': format_time(timespent_on_defects),
                'timespent_in_this_sprint_on_defects': timespent_in_this_sprint_on_defects,
                'timespent_in_this_sprint_on_defects_rendered': format_time(timespent_in_this_sprint_on_defects),
            }

            stories_with_defects.append(story_with_defect)

            for key, value in story['subtask_rootcauses'].items():

                # print("HERE: ", key, value)

                if key in defects_total_count:
                    defects_total_count[key]['count'] += value['count']
                    defects_total_count[key]['timespent'] += value['timespent']
                    defects_total_count[key]['timespent_in_this_sprint'] += value['timespent_in_this_sprint']
                else:
                    defects_total_count[key] = {
                        'count': value['count'],
                        'timespent': value['timespent'],
                        'timespent_in_this_sprint': value['timespent_in_this_sprint'],
                    }

    # render the total time spent on each defect_type into w/d/h/m and store
    for defect_type in defects_total_count:
        defects_total_count[defect_type]['timespent_rendered'] = format_time(defects_total_count[defect_type]['timespent'])
        defects_total_count[defect_type]['timespent_in_this_sprint_rendered'] = format_time(defects_total_count[defect_type]['timespent_in_this_sprint'])


    defects_total_count['Total'] = {
        'count': sum([defects_total_count[x]['count'] for x in defects_total_count]),
        'timespent': sum([defects_total_count[x]['timespent'] for x in defects_total_count]),
        'timespent_rendered': format_time(sum([defects_total_count[x]['timespent'] for x in defects_total_count])),
        'timespent_in_this_sprint': sum([defects_total_count[x]['timespent_in_this_sprint'] for x in defects_total_count]),
        'timespent_in_this_sprint_rendered': format_time(sum([defects_total_count[x]['timespent_in_this_sprint'] for x in defects_total_count])),
    }

    if DEBUG['defects']:
        print("----- DEFECTS -----")
        print(json.dumps(defects_total_count, indent = 4))

        print("----- STORY DEFECT -----")
        print(json.dumps(stories_with_defects, indent = 4))
    

    return {'stories_with_defects': stories_with_defects, 'defects_total_count': defects_total_count}


def summarise_sprint(stories):

    sprint_summary = {
        'subtask_count': 0,
        'story_count': 0,
        'aggregatetimespent': 0,
        'aggregatetimespent_in_this_sprint': 0,
        'aggregatetimeestimate': 0,
        'aggregatetimeoriginalestimate': 0,
        'progress': 0,
        'subtask_status': {
            'To Do': 0,
            'Dev In Progress': 0,
            'Dev Review': 0,
            'Awaiting UAT': 0,
            'Done': 0,
            'Reopened': 0
        },
        'TSvsOE': {},
        'accuracy' : {
            'over_estimates': {
                'count': 0,
                'TSvsOE': 0,
                'TSvsOE_rendered': "",
            },
            'under_estimates': {
                'count': 0,
                'TSvsOE': 0,
                'TSvsOE_rendered': "",
            },
            'on_estimates': {
                'count': 0
            },
        },
        'issuetype': {
            'Story': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/images/icons/issuetypes/story.svg",
            },
            'Bug': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10303&avatarType=issuetype",
            },
            'Task': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10318&avatarType=issuetype",
            },
            'Tech-debt': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10308&avatarType=issuetype",
            },
            'Defect': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10303&avatarType=issuetype",
            },
            'Sub-task [Backend]': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10316&avatarType=issuetype",
            },
            'Sub-task [Front End]': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10316&avatarType=issuetype",
            },
            'Sub-task [Test]': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10313&avatarType=issuetype",
            },
            'Sub-task [Ops]': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10316&avatarType=issuetype",
            },
            'Support ': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "https://fullprofile.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10304&avatarType=issuetype",
            },
            'Other': {
                'count': 0,
                'timeoriginalestimate': 0,
                'timespent': 0,
                'timespent_in_this_sprint': 0,
                'timeestimate': 0,
                'originalestimate_rendered': "",
                'timespent_rendered': "",
                'timespent_in_this_sprint_rendered': "",
                'timeestimate_rendered': "",
                'iconUrl': "",
            },
        },
        'sprints_carried_over': []
    }

    sprint_summary['sprints_carried_over'] = list(set([sprint['id'] for story in stories for sprint in story['sprints']]))

    for story in stories:

        sprint_summary['story_count'] += 1

        if story['aggregatetimespent']:
            sprint_summary['aggregatetimespent'] += story['aggregatetimespent']
        if story['aggregatetimespent_in_this_sprint']:
            sprint_summary['aggregatetimespent_in_this_sprint'] += story['aggregatetimespent_in_this_sprint']
        if story['aggregatetimeestimate']:
            sprint_summary['aggregatetimeestimate'] += story['aggregatetimeestimate']
        if story['aggregatetimeoriginalestimate']:
            sprint_summary['aggregatetimeoriginalestimate'] += story['aggregatetimeoriginalestimate']
        
        if story['timeoriginalestimate']:
            sprint_summary['issuetype'][story['issuetype']]['timeoriginalestimate'] += story['timeoriginalestimate']
        if story['timespent']:
            sprint_summary['issuetype'][story['issuetype']]['timespent'] += story['timespent']
        if story['timespent_in_this_sprint']:
            sprint_summary['issuetype'][story['issuetype']]['timespent_in_this_sprint'] += story['timespent_in_this_sprint']
        if story['timeestimate']:
            sprint_summary['issuetype'][story['issuetype']]['timeestimate'] += story['timeestimate']

        # sprint_summary['subtask_status'][story['status']] += 1 ## WORTH ADDING TO INCREASE BY STATUS OF STORY?
        sprint_summary['subtask_status']['To Do'] += story['subtask_status_count']['To Do']
        sprint_summary['subtask_status']['Dev In Progress'] += story['subtask_status_count']['Dev In Progress']
        sprint_summary['subtask_status']['Dev Review'] += story['subtask_status_count']['Dev Review']
        sprint_summary['subtask_status']['Awaiting UAT'] += story['subtask_status_count']['Awaiting UAT']
        sprint_summary['subtask_status']['Done'] += story['subtask_status_count']['Done']
        sprint_summary['subtask_status']['Reopened'] += story['subtask_status_count']['Reopened']

        sprint_summary['issuetype'][story['issuetype']]['count'] += 1


        for subtask in story['subtasks']:

            sprint_summary['subtask_count'] += 1

            if subtask['issuetype'] == 'Testing task':
                key = 'Sub-task [Test]'
            elif subtask['issuetype'] == 'Sub-task':
                if subtask['devteam'] != None:
                    key = 'Sub-task [' + subtask['devteam'] + ']'
                else:
                    key = 'Other'
            else:
                try:
                    key = subtask['issuetype']
                except:
                    key = 'Other'

            sprint_summary['issuetype'][key]['count'] += 1
            if subtask['timeoriginalestimate']:
                sprint_summary['issuetype'][key]['timeoriginalestimate'] += subtask['timeoriginalestimate']
            if subtask['timespent']:
                sprint_summary['issuetype'][key]['timespent'] += subtask['timespent']
            if subtask['timespent_in_this_sprint']:
                sprint_summary['issuetype'][key]['timespent_in_this_sprint'] += subtask['timespent_in_this_sprint']
            if subtask['timeestimate']:
                sprint_summary['issuetype'][key]['timeestimate'] += subtask['timeestimate']


            if subtask['status'] == 'Done' and subtask['TSvsOE']['value'] != None:
                
                if subtask['TSvsOE']['value'] > 0:
                    sprint_summary['accuracy']['over_estimates']['count'] += 1
                    sprint_summary['accuracy']['over_estimates']['TSvsOE'] += subtask['TSvsOE']['value']

                if subtask['TSvsOE']['value'] < 0:
                    sprint_summary['accuracy']['under_estimates']['count'] += 1
                    sprint_summary['accuracy']['under_estimates']['TSvsOE'] += subtask['TSvsOE']['value']
                    
                if subtask['TSvsOE']['value'] == 0:
                    sprint_summary['accuracy']['on_estimates']['count'] += 1

    sprint_summary['progress'] = calc_progress(sprint_summary['aggregatetimeoriginalestimate'], sprint_summary['aggregatetimeestimate'])
    sprint_summary['TSvsOE'] = timespent_vs_originalestimate(sprint_summary['aggregatetimeoriginalestimate'], sprint_summary['aggregatetimespent'], '')

    sprint_summary['aggregatetimespent_rendered'] = format_time(sprint_summary['aggregatetimespent'])
    sprint_summary['aggregatetimespent_in_this_sprint_rendered'] = format_time(sprint_summary['aggregatetimespent_in_this_sprint'])
    sprint_summary['aggregatetimeestimate_rendered'] = format_time(sprint_summary['aggregatetimeestimate'])
    sprint_summary['aggregatetimeoriginalestimate_rendered'] = format_time(sprint_summary['aggregatetimeoriginalestimate'])

    sprint_summary['accuracy']['over_estimates']['TSvsOE_rendered'] = format_time(sprint_summary['accuracy']['over_estimates']['TSvsOE'])
    sprint_summary['accuracy']['under_estimates']['TSvsOE_rendered'] = format_time(sprint_summary['accuracy']['under_estimates']['TSvsOE'])

    for key in sprint_summary['issuetype']:
        sprint_summary['issuetype'][key]['timeoriginalestimate_rendered'] = format_time(sprint_summary['issuetype'][key]['timeoriginalestimate'])
        sprint_summary['issuetype'][key]['timespent_rendered'] = format_time(sprint_summary['issuetype'][key]['timespent'])
        sprint_summary['issuetype'][key]['timespent_in_this_sprint_rendered'] = format_time(sprint_summary['issuetype'][key]['timespent_in_this_sprint'])
        sprint_summary['issuetype'][key]['timeestimate_rendered'] = format_time(sprint_summary['issuetype'][key]['timeestimate'])

    if DEBUG['sprint_summary']: print("Sprint Summary:", json.dumps(sprint_summary, indent = 4))

    return sprint_summary


# def timespent_per_developer(stories):

#     data = [item for story in stories for item in story['changelog'] if item['field'] == 'timespent']


#     # for story in stories:
#     #     for item in story['changelog']:
#     #         if item['field'] == 'timespent':
#     #             data.extend([item])
    
#     # timespent_changes = [d for d in data if d['']]

#     return data

# ------------------ SETUP ------------------ #

def start(sprint):

    global SPRINT_LOG
    SPRINT_LOG = {}

    global DEBUG
    DEBUG = {
        'changelog': False,
        'burndown': False,
        'defects': False,
        'sprint_summary': False,
    }

    OFFLINE_MODE = False

    if OFFLINE_MODE:
        with open('stories.pkl', 'rb') as f:
            stories = pickle.load(f)
        with open('subtasks.pkl', 'rb') as f:
            subtasks = pickle.load(f)
        with open('all_sprints.pkl', 'rb') as f:
            all_sprints = pickle.load(f)

        print('-'*20)
        print()
        print('!! OFFLINE MODE !!')
        print()
        print('-'*20)

    else:
        stories = get_issues(sprint, search="stories")
        subtasks = get_issues(sprint, search="subtasks")
        all_sprints = get_all_sprints()

        print("Stories received:", len(stories))
        print("Subtasks received:", len(subtasks))
        print("Sprints received:", len(all_sprints))

        with open('stories.pkl', 'wb') as f:
            pickle.dump(stories, f)
        with open('subtasks.pkl', 'wb') as f:
            pickle.dump(subtasks, f)
        with open('all_sprints.pkl', 'wb') as f:
            pickle.dump(all_sprints, f)

    data = format_data(stories, subtasks, sprint)
    data_check = data_checking(stories, subtasks)

    if DEBUG['changelog']: print('SPRINT_LOG:', json.dumps(SPRINT_LOG, indent = 4))

    return (data, all_sprints, data_check)


if __name__ == "__main__":

    sprint = 77

    stories = get_issues(sprint, search="stories")
    subtasks = get_issues(sprint, search="subtasks")
    data = format_data(stories, subtasks, sprint)
