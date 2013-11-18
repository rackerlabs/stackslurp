#!/usr/bin/env python
'''
Just a quick little prototype of a slurper for tagged StackExchange questions.

It requires a config.yml file laid out like so:

    stackexchange_key: 'STACKEXCHANGE_API_KEY'
    tags:
      - python
      - ruby
    site: stackoverflow

    rackspace:
      username: rgbkrk
      api_key: 'RACKSPACE_API_KEY'
      queue_endpoint: https://dfw.queues.api.rackspacecloud.com/

    queue: 'some_queue_name'

At least for now, just run

$ python slurp.py

'''

import json
import time
import uuid

from urlparse import urljoin

import requests
import yaml

stacksearch = "https://api.stackexchange.com/2.1/search"


class PerilEvent(object):
    '''
    Dummy object to create a proper peril event

    Totally overkill at this point
    '''

    def __init__(self, url, tags, reporter):
        self.url = url
        self.tags = tags
        self.reporter = reporter

    def to_dict(self):
        return {"url": self.url,
                "tags": self.tags,
                "reporter": self.reporter}

    def to_json(self):
        return json.dumps(self.to_dict())

    def __repr__(self):
        return str(self.to_json())


def get_questions(since, tags, site, stackexchange_key=None):
    '''Get all questions tagged on site since the time provided.

    >>> get_questions(since=1384752718, tags=['python'], site='stackoverflow')

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

if __name__ == "__main__":

    ff = open("config.yml")
    config = yaml.load(ff)
    ff.close()

    print(config)

    site = config['site']
    stackexchange_key = config['stackexchange_key']
    tags = config['tags']

    # Completely arbitrary start point
    since = int(time.time() - 3600*10)

    # Get all the questions since
    questions = get_questions(since, tags, site, stackexchange_key)

    # Create events
    events = [PerilEvent(question["link"], question["tags"], "slerp")
              for question in questions]

    print(events)


    # Authenticate with Rackspace
    endpoint = 'https://identity.api.rackspacecloud.com/v2.0/'
    username = config['rackspace']['username']
    api_key = config['rackspace']['api_key']

    auth_data = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": username,
                "apiKey": api_key
            }
        }
    }
    headers = {'Content-type': 'application/json'}

    resp = requests.get("https://identity.api.rackspacecloud.com/v2.0/tokens",
                        data=json.dumps(auth_data), headers=headers)
    resp.raise_for_status()
    identity_data = resp.json()
    token = identity_data['access']['token']['id']

    # Now we're authenticated, time to send on to a queue
    queue_endpoint = config['rackspace']['queue_endpoint']

    # Every queue client needs a unique ID
    client_id = str(uuid.uuid4())

    post_message_url = urljoin(queue_endpoint, "/v1/queues/{}/messages".format(config['queue']))
    headers = {'Content-type': 'application/json', "Client-ID": client_id, "X-Auth-Token": token}

    def chunks(lst, n):
        """ Yield successive n-sized chunks from lst.
        """
        for i in xrange(0, len(lst), n):
            yield lst[i:i+n]

    # Break events up into chunks of 10, per queue limit (configurable?)
    # TODO: Figure out if more than 10 messages can be sent at one time a different way
    for event_chunk in chunks(events, 10):
      data = [{"ttl": 300, "body": event.to_dict()} for event in event_chunk]

      print(data)
      print(json.dumps(data))

      resp = requests.post(post_message_url, data=json.dumps(data), headers=headers)
      print(resp.reason)
      print(resp.content)
