# updated ubuntu
#
# VERSION               0.0.1

FROM  ubuntu:14.04

MAINTAINER Ilya Beda "ir4y.ix@gmail.com"

RUN apt-get update

RUN apt-get install -y openssh-server
RUN mkdir /var/run/sshd 
RUN echo 'root:screencast' | chpasswd
ADD sshd_config /etc/ssh/sshd_config

EXPOSE 22
CMD    /usr/sbin/sshd -D
