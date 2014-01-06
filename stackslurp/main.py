#!/usr/bin/env python

'''
Just a simple script designed to read from a configuration file and use
stackslurp's modules to read from StackExchange, sending data on to
CloudQueues.
'''


import abc
import time
from datetime import datetime, timedelta
import calendar
import logging

import yaml

from .stackexchange import StackExchange
from . import utils
from .rackspace import Rackspace

from . import __version__

logger = logging.getLogger(__name__)

def read_config(config_file):
        '''Reads in a configuration file for stackslurp, intended for
        stackslurp's console entrypoint/main

        >>> config = read_config("config.yml")

        >>> fh = open("config2.yml")
        >>> config = read_config(fh)

        '''
        if isinstance(config_file, basestring):
            config_file = open(config_file)

        config = yaml.load(config_file)

        # Timing configuration
        default_wait = timedelta(minutes=10)
        config.setdefault('wait_time', default_wait.seconds)

        default_since = datetime.utcnow() - timedelta(days=1)
        default_since = calendar.timegm(default_since.timetuple())

        starting_since = config.setdefault('starting_since', default_since)
        config.setdefault('starting_since', int(starting_since))

        config.setdefault('ttl', 86400)

        return config

class Slurper(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, slurpconfig):
        self.config = slurpconfig
        self.rack = Rackspace(self.config['rackspace']['username'],
                self.config['rackspace']['api_key'])

    @abc.abstractmethod
    def generate_events(self):
        '''Generate peril style events. Subclasses need to implement this for
        their flavor of slurping.


        Each event should be a dict in this form:
        {
          // Required: uniquely identifies the incident.
          // If the incident already exists, this event will update it instead.
          "url": "http://stackoverflow.com/questions/20218241/editable-choice-field-drop-down-box-in-django-forms",

          // Required: arbitrary name for the producer.
          // Used to distinguish manually added incidents (and debug event producers).
          "reporter": "stackoverflow-slurp",

          // Optional: id from the original service this was pulled from
          // This is to aid later lookups
          "origin_id": "20218241",

          // Optional: Title of the event
          "title": "Editable Choice Field Drop Down Box in Django Forms",

          // Optional: array of tags to apply to the incident.
          // Will currently *override* existing tags.
          "tags": ["python", "django", "openstack"],

          // Optional: the effective date of the incident, in seconds since the epoch.
          "incident_date": 1384983822,

          // Optional: indicate that someone is already working this issue, by Rackspace SSO login.
          // (Required if "assigned_at" is provided.)
          // You could automatically detect comments in a forum thread, for example.
          "assignee": "racker1234",

          // Optional: indicate when someone started working this issue.
          // Defaults to the current time if "assignee" is provided.
          // Format: seconds since the epoch.
          "assigned_at": 1384983832,

          // Optional: indicate that this incident has been handled and signed off on.
          // If one of us have provided an answer on StackOverflow and it's been accepted, say.
          // Format: seconds since the epoch.
          "completed_at": 1384983842,

          // Optional: Any additional metadata you'd like to keep
          "extra": {}
        }

        generate_events should return a list of the above dicts.

        '''
        pass

    def send_events(self, events):
        '''A simple utility method to send events on to Rackspace CloudQueues.
        Events need to be in the peril format shown in `generate_events`
        '''
        # Authenticate with Rackspace
        # Get a (possibly) new token every time we use this
        self.rack.auth()

        # Now we're authenticated, time to send on to a queue
        # Break events up into chunks of 10, per arbitrary queue limit
        for event_chunk in utils.chunks(events, 10):
            self.rack.enqueue(event_chunk, self.config['queue'],
                              self.config['rackspace']['queue_endpoint'],
                              self.config['ttl'])

    def event_loop(self):
        try:
            events = self.generate_events()

        except Exception as e:
            logger.exception("Event generation exception at " +\
                             datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        else:
            try:
                self.send_events(events)
            except Exception as e:
                logger.exception("Event sending exception at " +\
                                 datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        finally:
            logger.info("Sleeping")
            time.sleep(self.config['wait_time'])
            return

    def go(self):
        while(True):
            self.event_loop()


class StackSlurp(Slurper):
    '''StackSlurp is a Slurper that pulls from StackExchange.'''
    def __init__(self, slurpconfig):
        '''Create a Slurper that pulls from StackExchange. Requires a
        configuration file.
        '''
        super(StackSlurp,self).__init__(slurpconfig)
        self.since = self.config['starting_since']

    def generate_events(self, since=None):
        '''
        Generate events for Peril. This can return between 0 and "a lot" of
        events.

        This will update the value of `since` within StackSlurp (the last time
        we pulled a question).
        '''

        if since==None:
            since = self.since

        # Get all the questions that have been asked with our tags going back
        # on all the sites
        questions = []

        for site in self.config['sites']:
            site_questions = StackExchange.search_questions(since, self.config['tags'],
                                                            site,
                                                            self.config['stackexchange_key'])
            questions.extend(site_questions)

        if(len(questions) > 0):
            # Track the last creation date to get new questions on the next run
            # `since` is >= in the stackexchange call, so we go 1 second later
            # so the slurper doesn't keep reporting the same last event over
            # and over.
            self.since = questions[0]["creation_date"] + 1

        events = []

        for question in questions:
            event = {"url": question["link"],
                     "tags": question["tags"],
                     "incident_date": question["creation_date"],
                     "origin_id": question['question_id'],
                     "title": question['title'],

                     # Provide full sourcing that can be dug up later
                     "extra": question,

                     # Announce our credentials
                     "reporter": "stackslurp v{}".format(__version__)}
            logger.debug("Event: ")
            logger.debug(event)

            events.append(event)

        logger.info("{} Events".format(len(events)))

        return events

def main(config_file):
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Starting up at " + datetime.utcnow().strftime("%Y-%m-%d %H:%M"))

    config = read_config(config_file)

    slurper = StackSlurp(config)

    slurper.go()

if __name__ == "__main__":
    main("config.yml")
