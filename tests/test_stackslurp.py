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

def test_chunks():
    chunks = stackslurp.utils.chunks

    num_chunks = chunks(range(10), 3)
    assert num_chunks.next() == [0, 1, 2]
    assert num_chunks.next() == [3, 4, 5]
    assert num_chunks.next() == [6, 7, 8]
    assert num_chunks.next() == [9]

def test_read_config(tmpdir):

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

class MainTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_entry_points(self):
        stackslurp
        stackslurp.main
        stackslurp.rackspace
        stackslurp.stackexchange
        stackslurp.utils





class SlurperTestCase(unittest.TestCase):

    class DummySlurper(stackslurp.main.Slurper):
        def generate_events(self):
            return [{"url": "http://blog.fict.io",
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

    def test_generate_events(self):
        s = self.DummySlurper(self.config)
        events = s.generate_events()

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

    def tearDown(self):
        pass


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

if __name__ == "__main__":
    unittest.main()
