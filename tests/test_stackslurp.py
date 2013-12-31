#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import os
import random
import json
import StringIO

import httpretty
import pytest
import yaml

import stackslurp
import stackslurp.main


class StackslurpTestCase(unittest.TestCase):
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

    def test_chunks(self):
        chunks = stackslurp.utils.chunks

        num_chunks = chunks(range(10), 3)
        assert num_chunks.next() == [0, 1, 2]
        assert num_chunks.next() == [3, 4, 5]
        assert num_chunks.next() == [6, 7, 8]
        assert num_chunks.next() == [9]

        # TODO Add doctests

class SlurpConfigTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_config(self):

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

        SlurpConfig = stackslurp.main.SlurpConfig

        config = SlurpConfig(fh)

        assert config.stackexchange_key == config_dict["stackexchange_key"]
        assert config.tags == config_dict["tags"]
        assert config.sites == config_dict["sites"]
        assert config.username == config_dict["rackspace"]["username"]
        assert config.api_key == config_dict["rackspace"]["api_key"]
        assert config.queue_endpoint == config_dict["rackspace"]["queue_endpoint"]
        assert config.queue == config_dict["queue"]
        assert config.wait_time == config_dict["wait_time"]



class RackspaceTestCase(unittest.TestCase):
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


if __name__ == "__main__":
    #testSuite = unittest.TestSuite()
    #testSuite.addTest(doctest.DocTestSuite(stackslurp))

    unittest.main()
