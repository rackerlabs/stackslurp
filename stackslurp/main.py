import time

import yaml

from . import stackexchange
from .utils import chunks
from .rackspace import Rackspace


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

    queue_endpoint = config['rackspace']['queue_endpoint']
    queue = config['queue']

    # Completely arbitrary start point
    since = int(time.time() - 60 * 60 * 24 * 7)

    # Get all the questions since
    questions = stackexchange.search_questions(since, tags,
                                               site, stackexchange_key)

    # Create events
    events = [{"url": question["link"],
              "tags": question["tags"],
              "reporter": "stackslurp"} for question in questions]

    print(events)

    # Authenticate with Rackspace
    rack = Rackspace(username, api_key)
    rack.auth()

    # Now we're authenticated, time to send on to a queue
    # Break events up into chunks of 10, per arbitrary queue limit
    for event_chunk in chunks(events, 10):
        rack.enqueue(event_chunk, queue, queue_endpoint)

if __name__ == "__main__":
    main()
