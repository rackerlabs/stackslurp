#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import os
import random
import json

import httpretty
import pytest

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

if __name__ == "__main__":
    unittest.main()
