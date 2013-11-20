'''
Utilities for pulling question data back from StackExchange sites
'''

import requests

stacksearch = "https://api.stackexchange.com/2.1/search"

def search_questions(since, tags, site, stackexchange_key=None):
    '''Get all questions with `tags` on `site` since the time provided.

    >>> search_questions(since=1384752718, tags=['c'], site='stackoverflow')

    '''

    # When provided a list, form the proper tag string
    if(not isinstance(tags, basestring)):
        tags = ";".join(tags)

    params = {
        "fromdate": since,
        "order": "desc",
        "sort": "creation",
        "tagged": tags,
        "site": site,
    }

    if(stackexchange_key):
        params["key"] = stackexchange_key

    resp = requests.get(stacksearch, params=params)

    data = resp.json()
    questions = data['items']

    return questions
