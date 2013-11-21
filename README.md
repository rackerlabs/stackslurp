StackSlurp
==========

Pulls tagged questions from StackExchange and posts them to a CloudQueue.

# Quick setup

Install the package

```
pip install git+git@github.rackspace.com:DST/stackslurp.git#egg=stackslurp
```

Write a config.yml file like so:

    stackexchange_key: 'STACKEXCHANGE_API_KEY'
    tags:
      - python
      - ruby
    sites:
      - stackoverflow
      - serverfault

    rackspace:
      username: rgbkrk
      api_key: 'RACKSPACE_API_KEY'
      queue_endpoint: https://dfw.queues.api.rackspacecloud.com/v1/

    queue: 'some_queue_name'

Run it:

```
$ slurp
```

# Configuration Notes

* tags
 * There can be [up to 100 tags](https://api.stackexchange.com/docs/vectors).
* queue
 * The queue must exist on Rackspace, under your account, for the region you choose to use (`queue_endpoint`)
* sites
 * Can be any stackexchange site, but not all tags are on all sites nor do they have the same meaning (python on stackoverflow is different than python on pets.stackexchange.com)
* stackexchange_key
 * [Register](http://stackapps.com/apps/oauth/register) for one
* rackspace username
 * The username you log in to Rackspace with
* rackspace api_key
 * Get your API Key from account settings in the cloud control panel
* queue_endpoint
 * You can use public or service net. Pick from the [list of queue endpoints](http://docs.rackspace.com/queues/api/v1.0/cq-devguide/content/serviceEndpoints.html).
