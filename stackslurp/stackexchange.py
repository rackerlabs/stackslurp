'''
Utilities for pulling question data back from StackExchange sites
'''

import requests

search_api = "https://api.stackexchange.com/2.1/search"


def search_questions(since, tags, site,
                     stackexchange_key=None,
                     order="desc",
                     sort_on="creation"):
    '''Get all questions with `tags` on `site` since the time provided.

    >>> search_questions(since=1384752718, tags=['c'], site='stackoverflow')

    '''

    # When provided a list, form the proper tag string
    if(not isinstance(tags, basestring)):
        tags = ";".join(tags)

    params = {
        "fromdate": since,
        "order": order,
        "sort": sort_on,
        "tagged": tags,
        "site": site,
    }

    if(stackexchange_key):
        params["key"] = stackexchange_key

    resp = requests.get(search_api, params=params)
    resp.raise_for_status()

    data = resp.json()
    questions = data['items']

    return questions
