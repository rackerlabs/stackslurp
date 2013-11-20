#!/usr/bin/env python
# -*- coding: utf-8 -*-

from invoke import run, task


@task
def test():
    run('py.test', pty=True)
