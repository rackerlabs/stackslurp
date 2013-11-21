#!/usr/bin/env python

# -*- coding: utf-8 -*-
'''StackSlurp

Pulls tagged questions from StackExchange and posts them to a CloudQueue

It requires a config.yml file laid out like so:

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

At least for now, just run

```
$ python -m stackslurp
```

However, it only runs once and only looks at 10 hours prior.

Eventually this needs to keep track of the time of the last question it saw
and query back to that as its `since`.
'''

__title__ = 'stackslurp'
__version__ = '0.1.0'
__build__ = 0x000100
__author__ = 'Kyle Kelley'
#__license__ = ''
__copyright__ = 'Copyright 2013 Rackspace'
