'''
Deploys stackslurp.

To use this fabfile, you'll need

* A local config.yml file written per the README
* fabric installed (pip install fabric)
* fabric-virtualenv installed

To do the full deploy run

$ fab pack deploy

If you make changes to your config, you're going to need to restart supervisor's group for slurp

$ fab restart_slurp
'''

import os
import StringIO

from itertools import ifilter

import fabric.api
from fabric.api import parallel
from fabric.api import env, run
from fabric.api import local
from fabric.api import cd
from fabric.api import put
from fabric.contrib import files
from fabric.context_managers import settings

import fabvenv

env.user = 'root'
env.key_filename = os.path.expanduser("~/.ssh/id_rsa")

def apt_update():
    run('apt-get -y update')
    run('apt-get -y upgrade')

def install_pip():
    # Good setuptools
    run('wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py\
        -O - | python2.7')

    # Good pip
    run('curl --show-error --retry 5\
    https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python2.7')

def install_deps():
    run('apt-get install -y curl wget build-essential python-dev')
    run('apt-get install -y libyaml-0-2 libyaml-dev')
    run('apt-get install -y supervisor')
    install_pip()

def pack():
    # create a new source distribution as tarball
    local('python setup.py sdist --formats=gztar', capture=False)

def supervise(venv):
    supervisor_conf_templ = '''[program:slurp]
command = {slurp}
user = nobody
stdout_logfile = {logfile}.out
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=15
stderr_logfile = {logfile}.err
stderr_logfile_maxbytes=10MB
stderr_logfile_backups=15
redirect_stderr = false
directory = {cwd}
'''
    conf = supervisor_conf_templ.format(slurp=os.path.join(venv, "bin/slurp"),
                                        logfile="/var/slurp/log",
                                        cwd="/var/slurp")

    sio = StringIO.StringIO(conf)

    put(sio, '/etc/supervisor/conf.d/slurp.conf')

    run('supervisorctl reread')
    run('supervisorctl update')

def restart_slurp():
    run('supervisorctl restart slurp:')

def deploy():
    apt_update()
    install_deps()

    virtualenv_location = '/var/slurp/venv'
    fabvenv.prepare_virtualenv()
    fabvenv.make_virtualenv(virtualenv_location, system_site_packages=False)

    # figure out the release name and version
    dist = local('python setup.py --fullname', capture=True).strip()
    # upload the source tarball to the temporary folder on the server
    put('dist/%s.tar.gz' % dist, '/tmp/slurp.tar.gz')
    # create a place where we can unzip the tarball, then enter
    # that directory and unzip it
    run('mkdir /tmp/slurp')
    with cd('/tmp/slurp'):
        run('tar xzf /tmp/slurp.tar.gz')

        with cd('/tmp/slurp/%s' % dist):
          # now setup the package with our virtual environment's
          # python interpreter
          run(os.path.join(virtualenv_location, "bin/python") + ' setup.py install')
    # now that all is set up, delete the folder again
    run('rm -rf /tmp/slurp /tmp/slurp.tar.gz')

    put('config.yml', '/var/slurp/config.yml')

    supervise(virtualenv_location)

