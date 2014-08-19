fabric scripts
==============
Tools for fast python app deployement with nginx, supervisord and postgres.


TODO
----
[\_] Add `create_celeryd_supervisor`  
[\_] Add `create_celerybeat_supervisor`  
[\_] Add `create_uwsgi_supervisor` with UNIX socket support  
[\_] Add UNIX socket support for  `create_nginx_host`  
[\_] Split `create_database` to `create_database_user` and `create_database`  
[\_] Add `create_site` wich should accept `user` and `git repo` params and deploy repo  
[X] ~~Add packet cache for decrease test time (disable downloading) (maybe mount local dir to packet cache dir)~~  
[\_] Add tests for all tasks  
[\_] Add travis integration (https://github.com/lukecyca/travis-docker-example)  
[\_] Use castom Dockerfile with updated ubuntu 14.04  

Tests
----- 
You need docker.io to run tests.  
```py.test -s --cov fabfile.py```  
It's draft only.
It's not working yet. 
Test is starting nginx over docker.io ssh conteiner and check that it started.
