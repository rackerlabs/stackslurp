#!/usr/bin/env python

'''
Just a simple script designed to read from a configuration file and use
stackslurp's modules to read from StackExchange and send data on to
CloudQueues.
'''

import time
import calendar

from datetime import datetime, timedelta

import yaml

from . import stackexchange
from .utils import Utils
from .rackspace import Rackspace


def main():

    with open("config.yml") as y:
        config = yaml.load(y)

    # StackExchange configuration
    sites = config['sites']
    stackexchange_key = config['stackexchange_key']
    tags = config['tags']

    # Rackspace configuration
    username = config['rackspace']['username']
    api_key = config['rackspace']['api_key']

    # Queue configuration
    queue_endpoint = config['rackspace']['queue_endpoint']
    queue = config['queue']

    # Timing configuration
    default_wait = timedelta(minutes=10)
    wait_time = int(config.get('wait_time', default_wait.seconds))

    default_since = datetime.utcnow() - timedelta(days=1)
    default_since = calendar.timegm(default_since.timetuple())

    starting_since = config.get('starting_since', default_since)
    since = int(starting_since)

    # Get our Rackspace API set up
    rack = Rackspace(username, api_key)

    while(True):
        # Get all the questions that have been asked with our tags going back
        # on all the sites
        questions = []

        for site in sites:
            site_questions = stackexchange.search_questions(since, tags,
                                                            site,
                                                            stackexchange_key)
            questions.extend(site_questions)

        if(len(questions) > 0):
            # Track the last creation date to get new questions on the next run
            # `since` is >= in the stackexchange call, so we go 1 second later
            # so the slurper doesn't keep reporting the same last event over
            # and over.
            since = questions[0]["creation_date"] + 1

        # Create events
        events = [{"url": question["link"],
                  "tags": question["tags"],
                  "incident_date": question["creation_date"],
                  "reporter": "stackslurp"} for question in questions]

        print("Events:")
        print(events)

        # Authenticate with Rackspace (get a new token every time we loop here)
        rack.auth()

        # Now we're authenticated, time to send on to a queue
        # Break events up into chunks of 10, per arbitrary queue limit
        for event_chunk in Utils.chunks(events, 10):
            rack.enqueue(event_chunk, queue, queue_endpoint)

        time.sleep(wait_time)

if __name__ == "__main__":
    main()
