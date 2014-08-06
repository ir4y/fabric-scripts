from os import environ, path
from fabric.api import run, put, sudo, settings, cd
from fabric.contrib.files import append

def upload_rsa():
    key_path = path.join(environ['HOME'], ".ssh/id_rsa.pub")
    rsa_key = open(key_path).read()
    run("mkdir ~/.ssh")
    run("touch ~/.ssh/authorized_keys")
    append("~/.ssh/authorized_keys", rsa_key)

UTILS_PACKAGES = [
    "screen",
    "git",
    "mercurial",
    "nginx",
    "redis-server",
]

PYTHON_PACKAGES = [
    "python",
    "python-dev",
    "python-virtualenv",
    "gcc",
    "make",
    "libjpeg-dev",
    "libcurl4-openssl-dev",
]

POSTGRESQL_PACKAGES = [
    "libpq-dev",
    "postgresql-9.3",
]




def setup_python():
    run("apt-get -y --force-yes install {0}".format(" ".join(PYTHON_PACKAGES)))

def setup_postgresql():
    run("apt-get -y --force-yes install {0}".format(" ".join(POSTGRESQL_PACKAGES)))

def setup_utils():
    run("apt-get -y --force-yes install {0}".format(" ".join(UTILS_PACKAGES)))

def setup_all():
    setup_utils()
    setup_python()
    setup_postgresql()

def create_project(user):
    run("useradd -s /bin/bash -m {0}".format(user))

    with settings(sudo_user=user):
        with cd("/home/{0}".format(user)):
            key_path = path.join(environ['HOME'], ".ssh/id_rsa.pub")
            rsa_key = open(key_path).read()
            sudo("mkdir .ssh")
            sudo("touch .ssh/authorized_keys")
            append(".ssh/authorized_keys", rsa_key, use_sudo=True)
            sudo("virtualenv ./")
            append(".bashrc", "source ~/bin/activate", use_sudo=True)
            sudo("mkdir sites")
            sudo("mkdir -p var/run")
            sudo("mkdir -p var/log")

    with settings(sudo_user='postgres'):
        sudo("psql -c 'create user {0}'".format(user))
        sudo("psql -c 'create database {0} owner {0}'".format(user))
