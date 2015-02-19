# updated ubuntu
#
# VERSION               0.0.1

FROM  baseimage:0.9.16

MAINTAINER Ilya Beda "ir4y.ix@gmail.com"

RUN rm -f /etc/service/sshd/down
ADD sshd_config /etc/ssh/sshd_config
RUN /etc/my_init.d/00_regen_ssh_host_keys.sh

RUN echo 'root:screencast' | chpasswd

EXPOSE 22
CMD    /usr/sbin/sshd -D
