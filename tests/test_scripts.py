import paramiko
import requests
from fabric.api import settings, local, run, env, sudo

from fabfile import *

paramiko.util.log_to_file("ssh.log")


def generate_username():
    chars = string.letters
    length = 8
    return ''.join(choice(chars) for _ in range(length))


def build_container():
    docker("build -t fab-test-ubuntu tests")


def docker(cmd):
    return local("docker.io %s" % cmd, capture=True)


def inside_docker(*ports):
    def wrap(fn):
        def inside(*args, **kwargs):
            build_container()  # move to setUp
            all_ports = (22, ) + ports
            port_options = " ".join("-p {0}".format(p) for p in all_ports)
            apt_cache = "-v /var/cache/apt/archives:/var/cache/apt/archives"
            container = docker(
                'run -d {0} {1} fab-test-ubuntu /usr/sbin/sshd -D'.format(
                    port_options,
                    apt_cache))
            get_port = lambda p: docker('port {0} {1}'.format(
                container, p)).split(":")[1]
            container_ports = {p: get_port(p) for p in all_ports}
            container_host = '%(user)s@%(host)s:%(port)s' % {
                'user': 'root',
                'host': '127.0.0.1',
                'port': container_ports[22]}
            try:
                with settings(host_string=container_host,
                              passwords={container_host: 'screencast'},
                              container_ports=container_ports):
                    fn(*args, **kwargs)
            finally:
                docker('kill %s' % container)
                docker('rm %s' % container)
        return inside
    return wrap


@inside_docker()
def test_python():
    setup_python()
    py_version = run("python --version").split(" ")
    assert py_version[0] == "Python"
    assert py_version[1][:3] == "2.7"


@inside_docker()
def test_postgres():
    setup_postgresql()
    run("service postgresql start")
    with settings(sudo_user="postgres"):
        sudo("psql -c 'create user root'")
    assert '2' == run("psql postgres -c 'select 1 + 1' -A -t")


@inside_docker(80)
def test_utils():
    setup_utils()
    run("service nginx start")
    url = "http://%(host)s:%(port)s" % {'host': '127.0.0.1',
                                        'port': env.container_ports[80]}
    page = requests.get(url)
    assert page.status_code == 200

    run("git --version")

    run("hg --version")

    run("service redis-server start")
    run("redis-cli set foo bar")
    assert '"bar"' == run("redis-cli get foo")

    run("service supervisor start")
    run("supervisorctl status")


@inside_docker()
def test_upload_rsa():
    upload_rsa()
    with settings(passwords=None):
        assert run("whoami") == "root"


@inside_docker()
def test_create_user():
    setup_python()
    user = generate_username()
    create_user(user)
    container_host = '%(user)s@%(host)s:%(port)s' % {
        'user': user,
        'host': '127.0.0.1',
        'port': env.container_ports[22]}

    with settings(host_string=container_host,
                  passwords={}):
        assert run("whoami") == user


@inside_docker()
def test_deploy():
    user = generate_username()
    setup_all()
    run("service postgresql start")
    create_project(user)
    container_host = '%(user)s@%(host)s:%(port)s' % {
        'user': user,
        'host': '127.0.0.1',
        'port': env.container_ports[22]}
    with settings(host_string=container_host,
                  passwords={}):
        assert '2' == run("psql {0} -c 'select 1 + 1' -A -t".format(user))
