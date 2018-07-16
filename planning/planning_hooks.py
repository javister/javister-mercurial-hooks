#!/usr/bin/python -OO
# -*- coding: UTF-8 -*-

"""
Hook для блокирования сливания веток, предназначеных для выпуска релизов.
Работает с репозиториями из группы Planning, за исключением веток, указанных в exclude_repo

Подключается централизованно через Kallithea, так как фильрует репо по имени

pretxnchangegroup.planning_hook_client_release = python:/путь/planning_hooks.py:client_release

"""

import getpass
import re
from urllib import unquote

import os
from mercurial import error

exclude_repo = ('knowledge-environment', 'knowledge-runtime', 'knowledge-utils' )

def client_release(ui, repo, hooktype, node=None, source=None, **kwargs):

    if hooktype not in ['pretxnchangegroup', 'pretxncommit']:
        raise error.Abort('config error - hook type "%s" cannot stop incoming changesets nor commits' % hooktype)

    dirs = str(repo.root).replace('\\', '/').split('/');
    if len(dirs)>1:
        mrepo = dirs[len(dirs) - 2]

        # Это не наш репозиторий, разрешаем
        if mrepo!="Planning":
            return False
        subrepo = dirs[len(dirs) - 1]

        if ((re.search(u'knowledge-\S+', subrepo) is None) and (re.search(u'planning-dist-\S+', subrepo) is None)) or subrepo in exclude_repo:
            return False

        # если репо Planning, пробегаемся по ченчсету
        for rev in xrange(repo[node], len(repo)):
            ctx = repo[rev]
            branch = ctx.branch()
            ui.warn("branch: " + branch)
            # Допустимо постить только в бранчи не default и не *-RELEASE
            if (branch==u'default') or (not re.search(u'\S+\*-RELEASE', branch) is None):
                raise error.Abort('branch name "%s" not allowed in repo %s/%s' % (branch, mrepo, subrepo))

    # Это не наш репозиторий
    return False

def file_lock_test(ui, repo, hooktype, node=None, source=None, **kwargs):


    if hooktype not in ['pretxnchangegroup', 'pretxncommit']:
        raise error.Abort('config error - hook type "%s" cannot stop incoming changesets nor commits' % hooktype)

    filename = os.path.sep.join([str(repo.root), '.hg', '.user.lock'])

    if os.path.exists(filename):

        s = None
        with open(filename, 'r') as f:
            s = f.read().strip()

        if not (s is None) and len(s)>0:

            user = None
            if source == 'serve' and 'url' in kwargs:
                url = kwargs['url'].split(':')
                if url[0] == 'remote' and url[1].startswith('http'):
                    user = unquote(url[3])
            ui.warn('kwargs: %s\n' % (str(kwargs)))
            ui.warn('kwargs url: %s, source: %s\n' %(str(kwargs['url']), str(source)))

            if user is None or len(user.strip())==0:
                user = getpass.getuser()
                ui.warn('getpass.GetUser: %s\n' % (user))

            if not s==user:
                raise error.Abort('Locked by by another user %s' % (s))

    return False
