StackExchangeSlurper
====================

Just a quick little prototype of a slurper for tagged StackExchange questions.

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
    site: stackoverflow

    rackspace:
      username: rgbkrk
      api_key: 'RACKSPACE_API_KEY'
      queue_endpoint: https://dfw.queues.api.rackspacecloud.com/v1/

    queue: 'some_queue_name'

Run it:

```
$ slurp
```

However, it only runs once and only looks at 10 hours prior.

Eventually this needs to keep track of the time of the last question it saw and query back to that as its `since`.


