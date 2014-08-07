import requests
from fabric.api import settings, local, run, hide
import paramiko

paramiko.util.log_to_file("ssh.log")

def docker(cmd):
    return local("docker.io %s" % cmd, capture=True)

def setup_nginx():
    run("apt-get -y --force-yes install nginx")
    run("service nginx start")

def test_install_nginx():
    with hide('output','running','warnings'):
        container = docker('run -d -p 22 -p 80 dhrp/sshd /usr/sbin/sshd -D')
        ssh_port = docker('port %s 22' % container).split(":")[1]
        web_port = docker('port %s 80' % container).split(":")[1]
        container_host = '%(user)s@%(host)s:%(port)s' % {'user': 'root', 'host': '127.0.0.1', 'port': ssh_port}
        try:
            with settings(host_string=container_host,
                        passwords={container_host:'screencast'}):
                setup_nginx()
                url = "http://%(host)s:%(port)s" % {'host': '127.0.0.1', 'port': web_port}
                page = requests.get(url)
                assert page.status_code == 200
                assert page.content ==  '<html>\n<head>\n<title>Welcome to nginx!</title>\n</head>\n<body bgcolor="white" text="black">\n<center><h1>Welcome to nginx!</h1></center>\n</body>\n</html>\n'
        finally:
            docker('kill %s' % container)
