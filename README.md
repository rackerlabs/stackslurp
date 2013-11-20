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

However, it only runs once and only looks at a week prior.
