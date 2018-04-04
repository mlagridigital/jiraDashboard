import requests
import json
import dateutil.parser
import csv
from datetime import timedelta
import pickle
import time

def get_issues(sprint, search=None):
    # """
    # TODO -  Check data retrival at edge cases. Total == Max Results

    # """

    url = 'https://fullprofile.atlassian.net/rest/api/2/search'

    if search == "stories":
        querystring = {
            "jql": "project = ADS AND sprint = " + str(sprint) + " AND type in standardIssueTypes()",
            "maxResults": "100",
            "startAt": 0,
            "fields": "status, subtasks, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate, customfield_10016, assignee, created, timespent, timeoriginalestimate, timeestimate",
            "expand": "changelog",
        }
    elif search == "subtasks":
        querystring = {
            "jql": "project = ADS AND sprint = " + str(sprint) + " AND type in subtaskIssueTypes()",
            "maxResults": "100",
            "startAt": 0,
            "fields": "status, issuetype, summary, aggregatetimespent, aggregatetimeoriginalestimate, aggregatetimeestimate, customfield_10016, assignee, created, timespent, timeoriginalestimate, timeestimate, customfield_11222",
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


# ------------------ FORMAT ISSUES ------------------ #

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
            continue

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
            
            "timespent": issue['fields']['timespent'],
            "timeoriginalestimate": issue['fields']['timeoriginalestimate'],
            "timeestimate": issue['fields']['timeestimate'],
            
            "aggregatetimespent": issue['fields']['aggregatetimespent'],
            "aggregatetimeoriginalestimate": issue['fields']['aggregatetimeoriginalestimate'],
            "aggregatetimeestimate": issue['fields']['aggregatetimeestimate'],
            "aggregatetimespent_str": format_time(issue['fields']['aggregatetimespent']),
            "aggregatetimeoriginalestimate_str": format_time(issue['fields']['aggregatetimeoriginalestimate']),
            "aggregatetimeestimate_str": format_time(issue['fields']['aggregatetimeestimate']),
            
            "sprints": format_sprints(issue['fields']['customfield_10016']),
            "assignee": format_assignee(issue['fields']['assignee']),
            "changelog": format_changelog(issue['changelog']),

            "progress": calc_progress(issue['fields']['aggregatetimeoriginalestimate'], issue['fields']['aggregatetimeestimate']),
            "TEvsOE": timespent_vs_originalestimate(issue['fields']['aggregatetimeoriginalestimate'], issue['fields']['aggregatetimespent'], issue['fields']['status']['name']),

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
        }

        print('DateCreated:', newStory['created'], '|', 'Sprint', newStory['sprints'][0]['id'], 'start:', newStory['sprints'][0]['startDate'])
        print('Sprints:', [i['id'] for i in newStory['sprints']])
        # print('SPRINTS:', json.dumps(newStory['sprints'], indent = 4))

        # print(format_sprints(issue['fields']['customfield_10016']))

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
                        
                        "timespent": s['fields']['timespent'],
                        "timeoriginalestimate": s['fields']['timeoriginalestimate'],
                        "timeestimate": s['fields']['timeestimate'],

                        "aggregatetimespent": s['fields']['aggregatetimespent'],
                        "aggregatetimeoriginalestimate": s['fields']['aggregatetimeoriginalestimate'],
                        "aggregatetimeestimate": s['fields']['aggregatetimeestimate'],
                        "aggregatetimespent_str": format_time(s['fields']['aggregatetimespent']),
                        "aggregatetimeoriginalestimate_str": format_time(s['fields']['aggregatetimeoriginalestimate']),
                        "aggregatetimeestimate_str": format_time(s['fields']['aggregatetimeestimate']),

                        "sprints": format_sprints(s['fields']['customfield_10016']),
                        "assignee": format_assignee(s['fields']['assignee']),
                        "changelog": format_changelog(s['changelog']),

                        "devteam": "",

                        "progress": calc_progress(s['fields']['timeoriginalestimate'], s['fields']['timeestimate']),
                        "TEvsOE": timespent_vs_originalestimate(s['fields']['timeoriginalestimate'], s['fields']['timespent'], s['fields']['status']['name']),

                        "rootcause": s['fields']['customfield_11222']['value'] if s['fields']['customfield_11222'] else None

                    }

                    print("ROOTCASE:", newSubtask['rootcause'])

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
                    else:
                        print("Error: subtask",
                              newSubtask['key'], "not set to team")

                    print('DateCreated:', dateutil.parser.parse(issue['fields']['created']), '|', 'Sprint', newSubtask['sprints'][0]['id'], 'start:', newSubtask['sprints'][0]['startDate'])
                    print('Sprints:', [i['id'] for i in newSubtask['sprints']])
                                       
                    newStory['subtasks'].append(newSubtask)

                    # Increase count for subtask status in the story
                    s_status = s['fields']['status']['name']
                    newStory['subtask_status_count'][s_status] += 1

                    # If subtask has rootcause increase count of rootcause in the story & and aggreate timespent on rootcauses
                    if s['fields']['customfield_11222']:
                        rootcause = s['fields']['customfield_11222']['value']
                        if rootcause in newStory['subtask_rootcauses']:
                            newStory['subtask_rootcauses'][rootcause] += 1
                        else:
                            newStory['subtask_rootcauses'][rootcause] = 1
                        
                        if newSubtask['timespent']:
                            newStory['subtask_rootcauses_timespent'] += newSubtask['timespent']

        storiesFormated.append(newStory)
        #print(json.dumps(newStory, indent = 4))

    data = {
        "stories": storiesFormated,
        "support": supportIssues
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

    for s in reversed(sprints):

        temp = {}

        for i in s.split('[')[1].split(','):
            key = i.split('=')[0]
            value = i.split('=')[1]
            temp[key] = value

        print(temp['startDate'])

        sprintsFormatted.append({
            "current": "",
            "id": temp['id'],
            "state": temp['state'],
            "name": temp['name'],
            "startDate": dateutil.parser.parse(temp['startDate']),
            "endDate": dateutil.parser.parse(temp['endDate']),
            "completeDate": temp['completeDate']
        })

        print(dateutil.parser.parse(temp['startDate']))


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
        precentage = calc_progress(originalestimate, timespent)

        if precentage is not None:
            precentage = -1 * precentage

    else:
        print("ERROR: [timespent_vs_originalestimate] - Time not int [OE:", originalestimate, ", TE:", timespent, "]")
        difference = None
        precentage = None


    if status == 'Done':
        tl = traffic_light(precentage)
    else:
        tl = 'inProgress'

    return {'value': difference, 'rendered': format_time(difference), 'percentage': precentage, 'traffic_light': tl}


def traffic_light(percentage):

    if percentage == None:
        return None
    elif percentage < 0:
        return 'blue'
    elif percentage <= 10:
        return 'green'
    elif percentage <= 50:
        return 'amber'
    else:
        return 'red'


def calc_dif(to, _from):

    if to is None:
        to = 0
    if _from is None:
        _from = 0

    dif = int(to) - int(_from)

    return dif


# ------------------ BURNDOWN ------------------ #


def filter_burndown(burndown, issueType):

    pass


def get_burndown(stories, devteam):
    """

    """

    # if devteam not in ['Front End', 'Backend', 'Test']:
    #     print("Error: get_burndown - devteam not in ['Front End', 'Backend', 'Test']")

    raw_data = []
    burndown_data = []

    for story in stories:

        # if devteam == "total_burndown":
            # print()
            # print(story['key'])
            # print(story['issuetype'])
            # print(story['created'])
            # print('OE:', story['timeoriginalestimate'], 'TE:', story['timeestimate'], 'TS:', story['timespent'])
            # subtask_burndown = collect_changes_and_dates(story['changelog'], story['created'], 'timeestimate', story['timeoriginalestimate'])
            # subtask_burndown = adjust_burndown_startdate(subtask_burndown, story['sprints'][0]['startDate'], story['sprints'][0]['id'])
            # raw_data.extend(subtask_burndown)

        for subtask in story['subtasks']:
            
            if subtask['devteam'] != devteam:
                continue
                
            print()
            print(subtask['key'])
            print(subtask['devteam'])
            print(subtask['created'])
            print('OE:', subtask['aggregatetimeoriginalestimate'], 'TE:', subtask['aggregatetimeestimate'], 'TS:', subtask['aggregatetimespent'])

            
            subtask_burndown = collect_changes_and_dates(subtask['changelog'], subtask['created'], 'timeestimate', subtask['aggregatetimeoriginalestimate'])
            subtask_burndown = adjust_burndown_startdate(subtask_burndown, subtask['sprints'][0]['startDate'], subtask['sprints'][0]['id'])

            raw_data.extend(subtask_burndown)

    raw_data.sort(key=lambda e: e[0])
    

    total = 0

    for line in raw_data:
        # print(line)
        burndown_data.append([line[0], total])
        total += line[1]
        burndown_data.append([line[0], total])

    
    print(devteam, 'BURNDOWN SUM:', sum([i[1] for i in raw_data])/(60*60))

    with open('data.csv', 'w') as f:
    	writer = csv.writer(f)
    	for line in burndown_data:
    		writer.writerow(line)

    return burndown_data


def collect_changes_and_dates(changelog, issue_created, field, subtask_originalestimate):
    """
    important case - if first timeestimate chang e['from'] in changelog is not None, then fist item in burndown data should be from 0 to change['from']
    with timestamp = issue['created'] timestamp

    """
    issue_burndown = []
    first = True

    print('--', 'Filtered changelog items', '--')

    for i, change in enumerate(changelog):
        
        if change['field'] == field:
            
            if first:
                first = False

                if change['from'] is not None:
                    issue_burndown.append([issue_created, int(change['from'])])
                    print(str(issue_created).ljust(32), str(change['from']).rjust(25))

            issue_burndown.append([change['created'], calc_dif(change['to'], change['from'])])
            print(str(change['created']).ljust(32), str(change['from']).rjust(6), '->', str(change['to']).ljust(6), '=', str(calc_dif(change['to'], change['from'])).rjust(6))


    if len(issue_burndown) == 0 and subtask_originalestimate is not None:
        issue_burndown.append([issue_created, subtask_originalestimate])
        print(str(issue_created).ljust(32), 'no changes', subtask_originalestimate)

    if DEBUG['burndown']:
        print('--', 'Items in issue burndown', '--')
        for line in issue_burndown:
            print(str(line[0]).ljust(32), str(line[1]).rjust(7))

    return issue_burndown


def adjust_burndown_startdate(subtask_raw_data, sprint_start, sprint_id):

    total = 0
    subtask_burndown =[]

    print("--", "Subtask burndown after date adjustment", "|", "Sprint", str(sprint_id), "start:", str(sprint_start), "--")

    print('-before-')

    for line in subtask_raw_data:
        print(str(line[0]), line[1])


    print('-after-')

    for i, point in enumerate(subtask_raw_data):
        
        if sprint_start > point[0]:
            total += point[1]

            if i == (len(subtask_raw_data)-1):
                new_point = [sprint_start, total]
                subtask_burndown.append(new_point)

        
        else:
            if total > 0:
                print('summmed total to sprint_start:', total)
                new_point = [sprint_start, total]
                subtask_burndown.append(new_point)
                total = 0

            new_point = [point[0], point[1]]
            subtask_burndown.append(new_point)


    for line in subtask_burndown:
        print(str(line[0]), line[1])


    total_re_before = sum([x[1] for x in subtask_raw_data])
    total_re_after = sum([x[1] for x in subtask_burndown])

    print('before:', total_re_before, 'after:', total_re_after, total_re_after == total_re_before)

    return subtask_burndown


def get_startdate(story, issue):
    """
    The startDate of an Issue burndown should be:
        1) If the story has been moved mid sprint; the date that the sprint was moved
        2) If the issue was created after the sprint start or after 1) then it should be the created date
        3) Else it should be the start date of the sprint
    """
    pass


def get_burndown_axes(stories):

    start_date = stories[0]['sprints'][0]['startDate']
    end_date = stories[0]['sprints'][0]['endDate']
    pass


# ------------------ RETRO ------------------ #

def get_defects(stories):

    stories_with_defects = []
    defects_total_count = {}

    for s in stories:
        if s['subtask_rootcauses']:
            
            story_with_defect = {
                'key': s['key'],
                'self': s['self'],
                'subtask_rootcauses': s['subtask_rootcauses'],
                'timespent_on_defects': s['subtask_rootcauses_timespent'],
            }

            stories_with_defects.append(story_with_defect)

            for key, value in s['subtask_rootcauses'].items():

                if key in defects_total_count:
                    defects_total_count[key] += value
                else:
                    defects_total_count[key] = value



    return {'stories_with_defects': stories_with_defects, 'defects_total_count': defects_total_count}


# ------------------ SETUP ------------------ #

def start(sprint):

    global SPRINT_LOG
    SPRINT_LOG = {}

    global DEBUG
    DEBUG = {
        'changelog': True,
        'burndown': True,
    }

    OFFLINE_MODE = True

    if OFFLINE_MODE:
        with open('stories.pkl', 'rb') as f:
            stories = pickle.load(f)
        with open('subtasks.pkl', 'rb') as f:
            subtasks = pickle.load(f)

        print('-'*20)
        print()
        print('!! OFFLINE MODE !!')
        print()
        print('-'*20)

    else:
        stories = get_issues(sprint, search="stories")
        subtasks = get_issues(sprint, search="subtasks")

        print("Stories received:", len(stories))
        print("Subtasks received:", len(subtasks))

        with open('stories.pkl', 'wb') as f:
            pickle.dump(stories, f)
        with open('subtasks.pkl', 'wb') as f:
            pickle.dump(subtasks, f)

    data = format_data(stories, subtasks)

    print(SPRINT_LOG)

    return data


if __name__ == "__main__":

    sprint = 77

    stories = get_issues(sprint, search="stories")
    subtasks = get_issues(sprint, search="subtasks")
    data = format_data(stories, subtasks)
