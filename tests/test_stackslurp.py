#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import logging
import os
import random
import re
import StringIO
import tempfile
import unittest
import uuid

import httpretty
import pytest
import yaml

import stackslurp
import stackslurp.main



@httpretty.activate
class FakeSpace(stackslurp.rackspace.Rackspace):
    '''Mock for Rackspace'''
    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key
        self.identity_endpoint = "http://seemslegit.io/v2.0"
        self.token_endpoint = self.identity_endpoint + "/tokens"

        self.client_id = str(uuid.uuid4())

        self.fakequeue = []

    def auth(self):
        self.token = "seemslegit"

    def enqueue(self, messages, queue, endpoint, ttl=300):
        self.fakequeue.extend(messages)

@httpretty.activate
class FakeExchange(stackslurp.stackexchange.StackExchange):
    @classmethod
    def search_questions(cls, since, tags, site, stackexchange_key=None,
                         order="desc", sort_on="creation"):
        # Return a simple list of questions
        questions = [
                {u'answer_count': 0,
                      u'creation_date': 1388784322,
                      u'is_answered': False,
                      u'last_activity_date': 1388784322,
                      u'link': u'http://stackoverflow.com/questions/20912948/color-detection-using-opencv-python',
                      u'owner': {u'accept_rate': 100,
                       u'display_name': u'Vipul Sharma',
                       u'link': u'http://stackoverflow.com/users/2840136/vipul-sharma',
                       u'profile_image': u'http://graph.facebook.com/1187128116/picture?type=large',
                       u'reputation': 56,
                       u'user_id': 2840136,
                       u'user_type': u'registered'},
                      u'question_id': 20912948,
                      u'score': 0,
                      u'tags': [u'python', u'opencv'],
                      u'title': u'color detection using opencv python',
                      u'view_count': 11},
                {u'answer_count': 1,
                      u'creation_date': 1388773319,
                      u'is_answered': False,
                      u'last_activity_date': 1388785067,
                      u'link': u'http://stackoverflow.com/questions/20910273/is-there-an-alternative-to-parse-qs-that-handles-semi-colons',
                      u'owner': {u'accept_rate': 92,
                       u'display_name': u'Kyle Kelley',
                       u'link': u'http://stackoverflow.com/users/700228/kyle-kelley',
                       u'profile_image': u'https://www.gravatar.com/avatar/e76c7ebc9d2e8a4b840f13cd01946437?s=128&d=identicon&r=PG',
                       u'reputation': 2524,
                       u'user_id': 700228,
                       u'user_type': u'registered'},
                      u'question_id': 20910273,
                      u'score': 3,
                      u'tags': [u'python', u'http', u'mocking', u'stackexchange', u'httpretty'],
                      u'title': u'Is there an alternative to parse_qs that handles semi-colons?',
                      u'view_count': 25},
                     ]

        return questions

@pytest.fixture(scope="session")
def stackslurpconfig():
        config_dict = {
                "stackexchange_key": 'THE_SE_KEY',
                "tags": ["python", "ruby"],
                "sites": ["stackoverflow", "serverfault"],
                "rackspace": {"username": "user",
                              "api_key": "rackspace_api",
                              "queue_endpoint":
                                "https://dfw.queues.api.rackspacecloud.com/v1/"
                             },
                "queue": "testing",
                "wait_time": 300
        }

        fh = StringIO.StringIO(yaml.safe_dump(config_dict))

        config = stackslurp.main.read_config(fh)
        return config


class TestUtils(object):
    def test_chunks(self):
        chunks = stackslurp.utils.chunks

        num_chunks = chunks(range(10), 3)
        assert num_chunks.next() == [0, 1, 2]
        assert num_chunks.next() == [3, 4, 5]
        assert num_chunks.next() == [6, 7, 8]
        assert num_chunks.next() == [9]

class TestMain(object):
    def test_entry_points(self):
        stackslurp
        stackslurp.main
        stackslurp.rackspace
        stackslurp.stackexchange
        stackslurp.utils

    def test_read_config(self, tmpdir):

        config_dict = {
                "stackexchange_key": 'THE_SE_KEY',
                "tags": ["python", "ruby"],
                "sites": ["stackoverflow", "serverfault"],
                "rackspace": {"username": "user",
                              "api_key": "rackspace_api",
                              "queue_endpoint":
                                "https://dfw.queues.api.rackspacecloud.com/v1/"
                             },
                "queue": "testing",
                "wait_time": 300
        }

        fh = StringIO.StringIO(yaml.safe_dump(config_dict))

        config = stackslurp.main.read_config(fh)

        assert config['stackexchange_key'] == config_dict["stackexchange_key"]
        assert config['tags'] == config_dict["tags"]
        assert config['sites'] == config_dict["sites"]
        assert config['rackspace']['username'] == config_dict["rackspace"]["username"]
        assert config['rackspace']['api_key'] == config_dict["rackspace"]["api_key"]
        assert config['rackspace']['queue_endpoint'] == config_dict["rackspace"]["queue_endpoint"]
        assert config['queue'] == config_dict["queue"]
        assert config['wait_time'] == config_dict["wait_time"]

        temp_file = tmpdir.mkdir("config2").join("testconfig.yml")
        config_dict['tags'] = ["go", "node.js"]
        temp_file.write(yaml.safe_dump(config_dict))

        config2 = stackslurp.main.read_config(str(temp_file))
        assert config2['stackexchange_key'] == config_dict["stackexchange_key"]
        assert config2['tags'] == config_dict["tags"]
        assert config2['sites'] == config_dict["sites"]
        assert config2['rackspace']['username'] == config_dict["rackspace"]["username"]
        assert config2['rackspace']['api_key'] == config_dict["rackspace"]["api_key"]
        assert config2['rackspace']['queue_endpoint'] == config_dict["rackspace"]["queue_endpoint"]
        assert config2['queue'] == config_dict["queue"]
        assert config2['wait_time'] == config_dict["wait_time"]

class TestStackSlurp(object):
    def test_init(self, stackslurpconfig):

        stackslurp.main.Rackspace = FakeSpace
        stackslurp.main.StackExchange = FakeExchange

        slurper = stackslurp.main.StackSlurp(stackslurpconfig)

        assert slurper.since is not None
        assert slurper.since == stackslurpconfig['starting_since']

    def test_generate_events(self, stackslurpconfig):

        stackslurp.main.Rackspace = FakeSpace
        stackslurp.main.StackExchange = FakeExchange

        slurper = stackslurp.main.StackSlurp(stackslurpconfig)

        slurper.generate_events()
        assert slurper.since == 1388784322 + 1 # one up from FakeExchange's last

# TODO Turn this into py.test style
class SlurperTestCase(unittest.TestCase):

    class DummySlurper(stackslurp.main.Slurper):
        def __init__(self, slurpconfig):
            super(self.__class__, self).__init__(slurpconfig)
            self.ctr = 0

        def generate_events(self):
            self.ctr = self.ctr + 1
            return [{"url": "http://blog.fict.io/{}".format(self.ctr),
                     "tags": ["saltstack", "rackspace", "bookstore"],
                     "reporter":"DummySlurper"}]

    def setUp(self):
        self.config_dict = {
                "rackspace": {"username": "user",
                              "api_key": "rackspace_api",
                              "queue_endpoint":
                                "https://dfw.queues.api.rackspacecloud.com/v1/"
                             },
                "queue": "testing",
                "wait_time": 300
        }

        fh = StringIO.StringIO(yaml.safe_dump(self.config_dict))
        self.config = stackslurp.main.read_config(fh)

    def tearDown(self):
        del self.config
        del self.config_dict

    @httpretty.activate
    def test_init(self):
        s = self.DummySlurper(self.config)

        assert s.config == self.config
        assert s.rack.username == self.config['rackspace']['username']
        assert s.rack.api_key == self.config['rackspace']['api_key']

    @httpretty.activate
    def test_send_events(self):

        s = self.DummySlurper(self.config)
        s.rack = FakeSpace(self.config['rackspace']['username'],self.config['rackspace']['api_key'])

        events = s.generate_events()
        events2 = s.generate_events()

        s.send_events(events)
        s.send_events(events2)
        assert events != events2 # sanity check

        assert s.rack.fakequeue == events + events2

    @httpretty.activate
    def test_event_loop(self):
        # It should throttle itself as requested

        class FakeTimer(object):
            last_sleep = None
            def sleep(self, length):
                # Finally getting some shut eye
                self.last_sleep = length

        timer = FakeTimer()

        def please_sleep(length):
            timer.last_sleep = length

        stackslurp.main.time.sleep = please_sleep

        s = self.DummySlurper(self.config)
        s.rack = FakeSpace(self.config['rackspace']['username'],self.config['rackspace']['api_key'])

        s.event_loop()

        assert timer.last_sleep == self.config['wait_time']

        # It should log errors from generation
        s2 = self.DummySlurper(self.config)
        s2.rack = FakeSpace(self.config['rackspace']['username'],self.config['rackspace']['api_key'])

        def tosser(*args, **kwargs):
            raise Exception("No run for you")

        s2.generate_events = tosser

        class Loggie(object):
            last_message = None
            def exception(self, last_message):
                self.last_message = last_message

        logger2 = Loggie()
        stackslurp.main.logger.exception = logger2.exception

        s2.event_loop()

        assert "generation" in logger2.last_message

        # It should log errors from sending

        s3 = self.DummySlurper(self.config)
        s3.rack = FakeSpace(self.config['rackspace']['username'],self.config['rackspace']['api_key'])

        def tosser(*args, **kwargs):
            raise Exception("No run for you")

        s3.send_events = tosser

        logger3 = Loggie()
        stackslurp.main.logger.exception = logger3.exception

        s3.event_loop()

        assert "sending" in logger3.last_message

class RackspaceTestCase(unittest.TestCase):

    @httpretty.activate
    def setUp(self):
        print "Setting up"

        self.identity_response_dict = {
            "access":
                # Randomly pick a token for authentication
                {"token":{ "id": format(random.randint(0,2**(32*4)), 'x')}},

                # The next two are left out, as we're not using them right now.
                # If they do get used, this test case should fail (which is a success).
                #"serviceCatalog":{}, # Access points for various services
                #"user":{} # Roles
        }

        self.token = self.identity_response_dict['access']['token']['id']

        self.identity_response = json.dumps(self.identity_response_dict)

        httpretty.register_uri(httpretty.POST,
                   "https://identity.api.rackspacecloud.com/v2.0/tokens",
                   body=self.identity_response,
                   content_type="application/json")

        Rackspace = stackslurp.rackspace.Rackspace

        username = "eve"
        api_key = "8675309"

        rack = Rackspace(username, api_key)
        rack.auth()

        self.rack = rack

    @httpretty.activate
    def test_auth(self):
        httpretty.register_uri(httpretty.POST,
                               "https://identity.api.rackspacecloud.com/v2.0/tokens",
                               body=self.identity_response,
                               content_type="application/json")

        Rackspace = stackslurp.rackspace.Rackspace

        username = random.choice(["dave", "steve", "eve"])
        api_key = "Ovaltine"

        rack = Rackspace(username, api_key)
        rack.auth()

        req = httpretty.last_request()

        auth_received = json.loads(req.body)

        creds = auth_received['auth']['RAX-KSKEY:apiKeyCredentials']
        assert creds['username'] == username
        assert creds['apiKey'] == api_key
        assert rack.token == self.token

    @httpretty.activate
    def test_enqueue(self):

        endpoint = "https://dfw.queues.api.rackspacecloud.com"
        queue_name = "event_line"

        def queue_success_callback(request, uri, headers):
            '''
            This callback mocks the queueing response as if successful
            '''

            # Get the headers stackslurp sends over
            headers_dict = request.headers.dict

            # Check to see that they authenticated properly
            assert headers_dict['x-auth-token'] == self.token

            # Check to make sure a valid UUID was passed in for the client
            their_uuid = headers_dict['client-id']
            # This will throw an exception if formatted incorrectly
            uuid.UUID(their_uuid)

            # Now we can handle their messages and send an appropriate response
            messages = json.loads(request.body)

            # Pull the queue name out of the request
            their_queue_name = re.findall(r"queues/(\w*)/messages", uri)[0]

            assert their_queue_name == queue_name

            resource_base = '/v1/queues/{}/messages/'.format(their_queue_name)

            assert len(messages) <= 10

            # Validate their messages
            for message in messages:
                assert set(message.keys()) == set(['ttl','body'])
                assert message['ttl'] >= 60
                assert message['ttl'] <= 1209600

                json.dumps(message['body'])

            response = {u'partial': False,
                        u'resources': [ resource_base + str(msg_id)
                                        for msg_id in range(len(messages)) ]}

            response = json.dumps(response)

            return (201, headers, response)


        httpretty.register_uri(httpretty.POST,
                               endpoint + "/v1/queues/{}/messages".format(queue_name),
                               body=queue_success_callback,
                               content_type="application/json")

        self.rack.enqueue([{'stuff':23}, {'moo':53}], queue_name, endpoint)

    @httpretty.activate
    def test_enqueue_failure(self):

        endpoint = "https://dfw.queues.api.rackspacecloud.com"
        queue_name = "my_queue"

        queue_url = endpoint + "/v1/queues/{}/messages".format(queue_name)

        # TODO: Handle errors
        ## Most important one to test for -- server error where the service
        ## can't be used for some reason.
        #httpretty.register_uri(httpretty.POST,
        #                       queue_url,
        #                       body="Service Unavailable", # Not the real message
        #                       status=503,
        #                       content_type="application/json")

        #self.rack.enqueue([{'super_critical_data': 'the cake is great'}],
        #                  queue_name,
        #                  endpoint)

        ## Generic placeholder for the other error codes we expect
        #for message,status in [
        #                        ('badRequest', 400),
        #                        ('unauthorized', 401),
        #                        ('unauthorized', 406),
        #                        ('tooManyRequests', 429),
        #                        ('itemNotFound', 404)
        #                      ]:
        #    httpretty.register_uri(httpretty.POST,
        #                           queue_url,
        #                           body="Needs Testing", # Not the real message
        #                           status=status,
        #                           content_type="application/json")

        #    self.rack.enqueue([{'super_critical_data': 'the cake is great'}],
        #                      queue_name,
        #                      endpoint)

def param_check_callback(golden_params):

    def param_check(params):
        for key in golden_params:
            assert params[key][0] == golden_params[key]

    return create_callback_check(param_check)

def create_callback_check(checker):

    def search_callback(request, uri, headers):
        params = request.querystring

        assert 'site' in params

        assert 'fromdate' in params

        int(params['fromdate'][0])
        assert 'tagged' in params

        checker(params)

        return (200, headers, '{"items":[]}')

    return search_callback



class TestStackExchange(object):

    @httpretty.activate
    def test_search_questions(self):



        StackExchange = stackslurp.stackexchange.StackExchange
        search_questions = StackExchange.search_questions


        #since = calendar.timegm((datetime.utcnow() - timedelta(days=1)).timetuple())
        since = 1388594252

        # It should use a stackexchange key if provided
        httpretty.register_uri(httpretty.GET,
                               "https://api.stackexchange.com/2.1/search",
                               body=param_check_callback({'key': 'superkey'}))
        search_questions(since=since, tags=["python"], site="pets",
                stackexchange_key="superkey", order="desc", sort_on="creation")


        # It should handle not having a stackexchange key gracefully
        def lack_key_check(params):
            assert 'key' not in params

        httpretty.register_uri(httpretty.GET,
                               "https://api.stackexchange.com/2.1/search",
                               body=create_callback_check(lack_key_check))
        search_questions(since=since, tags=["python"], site="pets",
                         order="desc", sort_on="creation")


        # To get around how parse_qs works (urlparse, under the hood of
        # httpretty), we'll leave the semi colon quoted.
        # 
        # See https://github.com/gabrielfalcao/HTTPretty/issues/134
        orig_unquote = httpretty.core.unquote_utf8
        httpretty.core.unquote_utf8 = (lambda x: x)

        # It should handle tags as a list
        httpretty.register_uri(httpretty.GET,
                               "https://api.stackexchange.com/2.1/search",
                               body=param_check_callback({'tagged': 'python;dog'}))
        search_questions(since=since, tags=["python", "dog"], site="pets")

        # It should handle a single tag
        httpretty.register_uri(httpretty.GET,
                               "https://api.stackexchange.com/2.1/search",
                               body=param_check_callback({'tagged': 'python'}))
        search_questions(since=since, tags=["python"], site="pets")

        httpretty.register_uri(httpretty.GET,
                               "https://api.stackexchange.com/2.1/search",
                               body=param_check_callback({'tagged': 'python'}))
        search_questions(since=since, tags="python", site="pets")

        # It should handle a string of tags, separated by commas
        httpretty.register_uri(httpretty.GET,
                               "https://api.stackexchange.com/2.1/search",
                               body=param_check_callback({'tagged': 'python'}))
        search_questions(since=since, tags="python", site="pets")

        # Back to normal for the rest
        httpretty.core.unquote_utf8 = orig_unquote
        # Test the test by making sure this is back to normal
        assert httpretty.core.unquote_utf8("%3B") == ";"

        # TODO: It should handle when the response is gzip encoded

        # TODO: It should handle when the response isn't gzip encoded

        # TODO: It should do *something* when the quota has been reached (within
        # resp.json()['quota_remaining'])

        # TODO: When there are multiple pages of results, it should aggregate them
        # This won't go well if there are lots, as it will have to block at
        # this point

        # TODO: Handle error responses

if __name__ == "__main__":
    unittest.main()
