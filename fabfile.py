from __future__ import unicode_literals

from os import environ, path

import string
from fabric.api import run, sudo, settings, cd
from fabric.contrib.files import append
from random import choice


def upload_rsa(user=None, use_sudo=False):
    key_path = path.join(environ['HOME'], ".ssh/id_rsa.pub")
    rsa_key = open(key_path).read()
    home_path = run("echo ~{0}".format(user)) if user else "~"
    execute = sudo if use_sudo else run
    execute("mkdir -p {0}/.ssh".format(home_path))
    execute("touch {0}/.ssh/authorized_keys".format(home_path))
    append("{0}/.ssh/authorized_keys".format(home_path),
           rsa_key,
           use_sudo=use_sudo)

UTILS_PACKAGES = [
    "screen",
    "git",
    "mercurial",
    "nginx",
    "redis-server",
    "supervisor",
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
    run("apt-get -y install {0}".format(
        " ".join(PYTHON_PACKAGES)))


def setup_postgresql():
    run("apt-get -y install {0}".format(
        " ".join(POSTGRESQL_PACKAGES)))


def setup_utils():
    run("apt-get -y install {0}".format(
        " ".join(UTILS_PACKAGES)))


def setup_all():
    setup_utils()
    setup_python()
    setup_postgresql()


def create_project(user):
    create_user(user)
    create_database(user)
    create_gunicorn_supervisor(user)
    create_nginx_host(user)


def create_user(user):
    run("useradd -s /bin/bash -m {0}".format(user))
    with settings(sudo_user=user):
        with cd("/home/{0}".format(user)):
            upload_rsa(user=user, use_sudo=True)
            sudo("virtualenv ./")
            append(".bashrc", "source ~/bin/activate", use_sudo=True)
            sudo("mkdir -p sites/{0}".format(user))
            sudo("mkdir -p var/run")
            sudo("mkdir -p var/log")


def generate_password():
    chars = string.letters + string.digits
    length = 8
    return ''.join(choice(chars) for _ in range(length))


def create_database(user, use_password=False):
    with settings(sudo_user='postgres'):
        password_string = ''
        if use_password:
            password = generate_password()
            print(password)
            password_string = "WITH PASSWORD '{0}'".format(password)
        sudo('psql -c "create user {0} {1};"'.format(user, password_string))
        sudo('psql -c "create database {0} owner {0};"'.format(user))


def create_gunicorn_supervisor(app):
    append("/etc/supervisor/conf.d/{0}_gunicorn.conf".format(app),
           """[program:{0}_gunicorn]
command=python /home/{0}/sites/{0}/manage.py run_gunicorn -b 127.0.0.1:9000  --pid /home/{0}/var/run/gunicorn.pid
directory=/home/{0}/sites/{0}
environment=PATH="/home/{0}/bin",LANG="ru_RU.UTF-8",LC_ALL="ru_RU.UTF-8",LC_LANG="ru_RU.UTF-8"
user={0}
autostart=false
autorestart=false
""".format(app))


def create_nginx_host(host):
    append("/etc/nginx/sites-available/{0}.ru".format(host),
           """server {{
    listen   80;
    server_name {0}.ru;
    # no security problem here, since / is alway passed to upstream
    root /usr/share/nginx/www/{0};
    # serve directly - analogous for static/staticfiles
    location /media/ {{
        # if asset versioning is used
        if ($query_string) {{
            expires max;
        }}
    }}
    location /static/ {{
        # if asset versioning is used
        if ($query_string) {{
            expires max;
        }}
    }}
    location / {{
        proxy_pass_header Server;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_connect_timeout 10;
        proxy_read_timeout 10;
        proxy_pass http://localhost:9000/;
    }}
    # what to serve if upstream is not available or crashes
    error_page 500 502 503 504 /usr/share/nginx/www/50x.html;
}}""".format(host))

    run("mkdir -p /usr/share/nginx/www/{0}".format(host))
    run("ln -s /home/{0}/sites/{0}/media  /usr/share/nginx/www/{0}".format(
        host))
    run("ln -s /home/{0}/sites/{0}/static  /usr/share/nginx/www/{0}".format(
        host))
