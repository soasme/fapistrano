# -*- coding: utf-8 -*-

from blinker import signal
from fabric.api import env, run, show

def init():
    if not hasattr(env, 'refresh_supervisor'):
        env.refresh_supervisor = False

    if not hasattr(env, 'wait_before_refreshing'):
        env.wait_before_refreshing = False

    signal('deploy.started').connect(_check_supervisor_config)
    signal('deploy.published').connect(_restart_service_via_supervisor)
    signal('deploy.restarting').connect(_restart_service_via_supervisor)

def _get_supervisor_conf():
    if not hasattr(env, 'supervisor_conf'):
        env.supervisor_conf = '%(current_path)s/configs/supervisor_%(env)s_%(role)s.conf' % env
    return env.supervisor_conf

def _check_supervisor_config(sender, **kwargs):
    _get_supervisor_conf()
    run('ln -nfs %(supervisor_conf)s /etc/supervisor/conf.d/%(project_name)s.conf' % env)
    run('supervisorctl reread')

def _restart_service_via_supervisor(sender, **kwargs):
    with show('output'):
        if not env.refresh_supervisor:
            run('supervisorctl restart %(supervisor_target)s' % env)
        else:
            run('supervisorctl stop %(supervisor_target)s' % env)
            if env.wait_before_refreshing:
                raw_input('type any key to refresh supervisor')
            run('supervisorctl reread')
            if not run('supervisorctl update'):
                run('supervisorctl start %(supervisor_target)s' % env)

        # since supervisorctl does not support `supervisorctl status group_name:*` syntax
        run('supervisorctl status | grep %(project_name)s' % env)