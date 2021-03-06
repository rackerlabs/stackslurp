'''
For now, this is built for Rackspace only.

This module helps with auth and working with queues.
'''

import logging
import json
import uuid
from urlparse import urljoin

import requests

logger = logging.getLogger(__name__)

class Rackspace(object):
    '''Simple Encapsulation of Auth and posting messages to CloudQueues'''

    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key

        self.identity_endpoint = "https://identity.api.rackspacecloud.com/v2.0"

        self.token_endpoint = self.identity_endpoint + "/tokens"

        # Generate a client ID for Queue usage
        self.client_id = str(uuid.uuid4())

    def auth(self):
        '''Authenticate with Rackspace.

        This generates the token that is used by calls to Rackspace services.

        >>> rack = Rackspace("myuser", "XXXXXXXXXXXXXXXX")
        >>> rack.auth()
        >>> rack.token
        '''
        auth_data = {
            "auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                    "username": self.username,
                    "apiKey": self.api_key
                }
            }
        }

        headers = {'Content-type': 'application/json'}

        resp = requests.post(self.token_endpoint, data=json.dumps(auth_data),
                            headers=headers)
        resp.raise_for_status()
        identity_data = resp.json()
        self.token = identity_data['access']['token']['id']

    def enqueue(self, messages, queue, endpoint, ttl=300):
        '''Sends messages to the named queue on the given endpoint.

        Endpoint can be PublicNet or ServiceNet.

        Messages must be JSON-serializable dicts.
        '''
        post_message_url = urljoin(endpoint,
                                   "/v1/queues/{}/messages".format(queue))

        headers = {'Content-type': 'application/json',
                   "Client-ID": self.client_id,
                   "X-Auth-Token": self.token}

        data = [{"ttl": ttl, "body": message} for message in messages]

        resp = requests.post(post_message_url, data=json.dumps(data),
                             headers=headers)
        resp.raise_for_status()

        logger.debug("enqueue response")
        logger.debug(resp.json())

