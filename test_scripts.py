import requests
from fabric.api import settings, local, run, env
import paramiko
from fabfile import setup_utils

paramiko.util.log_to_file("ssh.log")


def docker(cmd):
    return local("docker.io %s" % cmd, capture=True)


def inside_docker(fn):
    def inside(*args, **kwargs):
        container = docker('run -d -p 22 -p 80 -v /var/cache/apt/archives:/var/cache/apt/archives dhrp/sshd /usr/sbin/sshd -D ')
        ssh_port = docker('port %s 22' % container).split(":")[1]
        web_port = docker('port %s 80' % container).split(":")[1]
        container_host = '%(user)s@%(host)s:%(port)s' % {'user': 'root',
                                                         'host': '127.0.0.1',
                                                         'port': ssh_port}
        try:
            with settings(host_string=container_host,
                          passwords={container_host: 'screencast'},
                          web_port=web_port):
                fn(*args, **kwargs)
        finally:
            docker('kill %s' % container)
            docker('rm %s' % container)
    return inside


@inside_docker
def test_nginx():
    setup_utils()
    run("service nginx start")
    url = "http://%(host)s:%(port)s" % {'host': '127.0.0.1',
                                        'port': env.web_port}
    page = requests.get(url)
    assert page.status_code == 200
    assert page.content ==  '<html>\n<head>\n<title>Welcome to nginx!</title>\n</head>\n<body bgcolor="white" text="black">\n<center><h1>Welcome to nginx!</h1></center>\n</body>\n</html>\n'
