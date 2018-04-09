import requests
import json
import dateutil.parser
import csv
from datetime import timedelta
import pickle
import time


def get_sprint_meta():

    url = 'https://fullprofile.atlassian.net/rest/agile/latest/board/12/sprint/'
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

    # print(json.dumps(sprints, indent = 4))


get_sprint_meta()