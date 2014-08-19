import requests
from fabric.api import settings, local, run, env, sudo
import paramiko
from fabfile import setup_python, setup_postgresql, setup_utils

paramiko.util.log_to_file("ssh.log")


def docker(cmd):
    return local("docker.io %s" % cmd, capture=True)


def inside_docker(*ports):
    def wrap(fn):
        def inside(*args, **kwargs):
            all_ports = (22, ) + ports
            port_options = " ".join("-p {0}".format(p) for p in all_ports)
            apt_cache = "-v /var/cache/apt/archives:/var/cache/apt/archives"
            container = docker(
                'run -d {0} {1} dhrp/sshd /usr/sbin/sshd -D'.format(
                    port_options,
                    apt_cache))
            get_port = lambda p: docker('port {0} {1}'.format(
                container, p)).split(":")[1]
            contariner_ports = {p: get_port(p) for p in all_ports}
            container_host = '%(user)s@%(host)s:%(port)s' % {
                'user': 'root',
                'host': '127.0.0.1',
                'port': contariner_ports[22]}
            try:
                with settings(host_string=container_host,
                              passwords={container_host: 'screencast'},
                              contariner_ports=contariner_ports):
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
    with settings(sudo_user="postgres"):
        assert 2 == sudo('psql -c "select 1 + 1" -A -t')


@inside_docker(80)
def test_utils():
    setup_utils()
    run("service nginx start")
    url = "http://%(host)s:%(port)s" % {'host': '127.0.0.1',
                                        'port': env.contariner_ports[80]}
    page = requests.get(url)
    assert page.status_code == 200
    assert page.content == '<html>\n<head>\n<title>Welcome to nginx!</title>\n</head>\n<body bgcolor="white" text="black">\n<center><h1>Welcome to nginx!</h1></center>\n</body>\n</html>\n'

    run("screen -v")
    run("git -v")
    run("hg -v")
    run("redis-cli set foo bar")
    assert "bar" == run("redis-cli get foo")
    run("supervisorctl status")
