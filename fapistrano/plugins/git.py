# -*- coding: utf-8 -*-

from blinker import signal
from fabric.api import cd, env, run, local, task
from ..utils import green_alert

def init():
    signal('deploy.delta.publishing').connect(publish_git_delta)
    signal('deploy.head.publishing').connect(publish_git_head)
    signal('deploy.reverted').connect(check_reverted_git_repo)
    signal('deploy.updating').connect(update_git_repo)

def publish_git_delta(sender=None, **kwargs):
    delta_log = _get_delta()
    if not delta_log:
        green_alert('No delta.')
        return
    green_alert('Get delta:\n%s' % delta_log)
    signal('git.delta.publishing').send(None, delta_log=delta_log)

def publish_git_head(sender=None, **kwargs):
    head = _get_remote_head()
    green_alert('Get head: \n%s' % head)
    signal('git.head.publishing').send(None, head=head)

def check_reverted_git_repo(sender=None, **kwargs):
    head = _get_remote_head()
    green_alert('Get head: \n%s' % head)
    signal('git.reverted').send(None, head=head)

def update_git_repo(sender=None, **kwargs):
    delta_log = _get_delta(bsd=kwargs.get('git_bsd', True))

    if kwargs.get('git_use_reset'):
        run('git fetch -q')
        run('git reset --hard origin/%(branch)s' % env)
    else:
        run('git pull -q')
        run('git checkout %(branch)s' % env)

    head = _get_remote_head()
    green_alert('Release to %s' % head)

    if delta_log:
        green_alert('Release log:\n%s' % delta_log)

    signal('git.updated').send(None, delta_log=delta_log, head=head)


def _get_remote_head():
    with cd(env.current_path):
        return run("git rev-parse --short HEAD", quiet=True)


def _get_delta(upstream='upstream', bsd=True):
    version = _get_remote_head()
    green_alert('Current version: %s' % version)

    local('/usr/bin/env git fetch -q %s' % upstream)
    #FIXME
    return local(
        'cd /Users/soasme/space/liwushuo/nasdaq ; '
        '/usr/bin/env git log --reverse --pretty="%%h %%s: %%b" --merges %s..%s/master | '
        '/usr/bin/env sed -%s "s/Merge pull request #([0-9]+) from ([^/]+)\\/[^:]+/#\\1\\/\\2/"' % (
            version, upstream, 'E' if bsd else 'r'), capture=True).decode('utf8')