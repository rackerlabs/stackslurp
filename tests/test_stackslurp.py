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

class TestUtils():
    def test_chunks(self):
        chunks = stackslurp.utils.chunks

        num_chunks = chunks(range(10), 3)
        assert num_chunks.next() == [0, 1, 2]
        assert num_chunks.next() == [3, 4, 5]
        assert num_chunks.next() == [6, 7, 8]
        assert num_chunks.next() == [9]

class TestMain():
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

        class FakeSpace(stackslurp.rackspace.Rackspace):
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


        s = self.DummySlurper(self.config)
        s.rack = FakeSpace(self.config['rackspace']['username'],self.config['rackspace']['api_key'])

        events = s.generate_events()
        events2 = s.generate_events()

        s.send_events(events)
        s.send_events(events2)
        assert events != events2 # sanity check

        assert s.rack.fakequeue == events + events2


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


class TestStackExchange(object):

    def search_callback(request, uri, headers):
        print(request)
        print(uri)
        print(headers)


    @httpretty.activate
    def test_search_questions(self):

        httpretty.register_uri(httpretty.GET, "https://api.stackexchange.com/2.1/search"
                               body=queue_success_callback)

        # It should use a stackexchange key if provided

        # It should hanlde not having a stackexchange key gracefully

        # It should handle tags as a list

        # It should handle a single tag

        # It should handle a string of tags, separated by commas

        # It should handle when the response is gzip encoded

        # It should handle when the reponse isn't gzip encoded


if __name__ == "__main__":
    unittest.main()
