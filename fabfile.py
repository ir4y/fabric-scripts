from __future__ import unicode_literals

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
            sudo("mkdir -p sites/{0}".format(user))
            sudo("mkdir -p var/run")
            sudo("mkdir -p var/log")

    with settings(sudo_user='postgres'):
        sudo("psql -c 'create user {0}'".format(user))
        sudo("psql -c 'create database {0} owner {0}'".format(user))

    append("/etc/supervisor/conf.d/{0}_gunicorn.conf".format(user),"""[program:{0}_gunicorn]
command=python /home/{0}/site/{0}/manage.py run_gunicorn -b 127.0.0.1:9000  --pid /home/{0}/var/run/gunicorn.pid
directory=/home/{0}/site/{0}
environment=PATH="/home/{0}/bin",LANG="ru_RU.UTF-8",LC_ALL="ru_RU.UTF-8",LC_LANG="ru_RU.UTF-8"
user={0}
autostart=false
autorestart=false
""".format(user))

    append("/etc/nginx/sites-available/{0}.ru".format(user),"""server {{
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
}}""".format(user))

    run("mkdir -p /usr/share/nginx/www/{0}".format(user))
    run("ln -s /home/{0}/sites/{0}/media  /usr/share/nginx/www/{0}".format(user))
    run("ln -s /home/{0}/sites/{0}/static  /usr/share/nginx/www/{0}".format(user))
