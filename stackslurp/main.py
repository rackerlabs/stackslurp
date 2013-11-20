import json
import time
import uuid

from urlparse import urljoin

import requests
import yaml

from . import stackexchange
from .utils import chunks
from .rackspace import Rackspace

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


def main():

    ff = open("config.yml")
    config = yaml.load(ff)
    ff.close()

    print(config)

    site = config['site']
    stackexchange_key = config['stackexchange_key']
    tags = config['tags']
    username = config['rackspace']['username']
    api_key = config['rackspace']['api_key']

    # Completely arbitrary start point
    since = int(time.time() - 3600*48)

    # Get all the questions since
    questions = stackexchange.search_questions(since, tags, site, stackexchange_key)

    # Create events
    events = [PerilEvent(question["link"], question["tags"], "stackslurp")
              for question in questions]

    print(events)

    rack = Rackspace(username, api_key)
    rack.auth()

    # Now we're authenticated, time to send on to a queue
    queue_endpoint = config['rackspace']['queue_endpoint']

    # Every queue client needs a unique ID
    client_id = str(uuid.uuid4())

    post_message_url = urljoin(queue_endpoint, "/v1/queues/{}/messages".format(config['queue']))
    headers = {'Content-type': 'application/json', "Client-ID": client_id, "X-Auth-Token": rack.token}

    # Break events up into chunks of 10, per queue limit (configurable?)
    # TODO: Figure out if more than 10 messages can be sent at one time a different way
    for event_chunk in chunks(events, 10):
      data = [{"ttl": 300, "body": event.to_dict()} for event in event_chunk]

      print(data)
      print(json.dumps(data))

      resp = requests.post(post_message_url, data=json.dumps(data), headers=headers)
      print(resp.reason)
      print(resp.content)
