#!/usr/bin/env python

'''
Just a simple script designed to read from a configuration file and use
stackslurp's modules to read from StackExchange and send data on to
CloudQueues.
'''


import time
from datetime import datetime, timedelta
import calendar
import logging

import yaml

from .stackexchange import StackExchange
from . import utils
from .rackspace import Rackspace

from . import __version__

class SlurpConfig(object):
    def __init__(self, config_file):
        '''Reads in a configuration file for stackslurp, intended for
        stackslurp's console entrypoint/main

        >>> config = SlurpConfig("config.yml")

        >>> fh = open("config2.yml")
        >>> config = SlurpConfig(fh)

        '''
        if isinstance(config_file, basestring):
            config_file = open(config_file)

        config = yaml.load(config_file)
        self.handle_config_dict(config)

    def handle_config_dict(self, config):

        # StackExchange configuration
        self.sites = config['sites']
        self.stackexchange_key = config['stackexchange_key']
        self.tags = config['tags']

        # Rackspace configuration
        self.username = config['rackspace']['username']
        self.api_key = config['rackspace']['api_key']

        # Queue configuration
        self.queue_endpoint = config['rackspace']['queue_endpoint']
        self.queue = config['queue']

        # Timing configuration
        default_wait = timedelta(minutes=10)
        self.wait_time = int(config.get('wait_time', default_wait.seconds))

        default_since = datetime.utcnow() - timedelta(days=1)
        default_since = calendar.timegm(default_since.timetuple())

        starting_since = config.get('starting_since', default_since)
        self.starting_since = int(starting_since)



def main():

    logging.basicConfig(level=logging.DEBUG)

    logging.info("Starting up at " + datetime.utcnow().strftime("%Y-%m-%d %H:%M"))

    config = SlurpConfig("config.yml")

    # Get our Rackspace API set up
    rack = Rackspace(config.username, config.api_key)
    since = config.starting_since

    while(True):
        try:
            # Get all the questions that have been asked with our tags going back
            # on all the sites
            questions = []

            for site in config.sites:
                site_questions = StackExchange.search_questions(since, config.tags,
                                                                site,
                                                                config.stackexchange_key)
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
                       "origin_id": question['question_id'],
                       "title": question['title'],

                       # Provide full sourcing that can be dug up later
                       "extra": question,

                       # Announce our credentials
                       "reporter": "stackslurp v{}".format(__version__)}

                      for question in questions]

            logging.info("{} Events".format(len(events)))

            # Authenticate with Rackspace (get a new token every time we loop here)
            rack.auth()

            # Now we're authenticated, time to send on to a queue
            # Break events up into chunks of 10, per arbitrary queue limit
            for event_chunk in utils.chunks(events, 10):
                rack.enqueue(event_chunk, config.queue, config.queue_endpoint)

            logging.info("Sleeping")
            time.sleep(config.wait_time)
        except Exception as e:
            logging.exception("Exception on " + datetime.utcnow().strftime("%Y-%m-%d %H:%M"))


if __name__ == "__main__":
    main()
