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
        stackslurp.utils

    def test_chunks(self):
        chunks = stackslurp.utils.chunks

        num_chunks = chunks(range(10), 3)
        assert num_chunks.next() == [0, 1, 2]
        assert num_chunks.next() == [3, 4, 5]
        assert num_chunks.next() == [6, 7, 8]
        assert num_chunks.next() == [9]

        # TODO Add doctests

if __name__ == "__main__":
    #testSuite = unittest.TestSuite()
    #testSuite.addTest(doctest.DocTestSuite(stackslurp))

    unittest.main()
