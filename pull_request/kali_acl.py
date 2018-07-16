#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Проверка прав через Kalithea API в зависимости от ветки, куда вносятся изменения

Как подключить?

Должны быть доступны библиотеки mercurial и python-redmine (redminelib).
В этом файле необъходимо указать путь к Kallithea в переменной kali_url.

Нужно настроить подключения и логин в файле config.py (см. config.py.sample)

К репозиторию добавить хук:

[hooks]
pretxnchangegroup.acl = python:path/to/script/kali_acl.py:hook

Или локально:

[hooks]
pretxncommit.acl = python:path/to/script/kali_acl.py:hook

"""
from __future__ import absolute_import

import getpass
import re
import config

from mercurial.httppeer import httplib
from mercurial.i18n import _
from mercurial import  error
from redminelib import Redmine
from urllib import unquote

redmine_statuses = (1, 2) #Новая = 1 В работе = 2

def get_ticket_num(branch):
    refs = re.search(u"ticket-\d+[-]?", branch)
    if not refs is None:
        num = re.search(u"\d+", refs.group(0))
        if not num is None:
            return num.group(0)
    return None


def check_issue_status(branch):
    refnum = get_ticket_num(branch)
    print refnum
    if refnum is None:
        return False
    redmine = Redmine(config.redmine_url, username=config.usr, password = config.passw)
    issue = redmine.issue.get(resource_id=refnum)
    return issue.status.id in redmine_statuses


def check_manager_branch(branch):
    return branch=='default' \
           or not re.search(u'\d+\.\d+\.\*-RELEASE', branch) is None \
           or not re.search(u'\d+\.\d+\.\*-CLIENT', branch) is None \
           or not re.search(u"ticket-\d+.+", branch) is None


def get_user_group(repo, user):
    api_path = "/kalitheaapi/pullrequest/user/permission?repo=%s&user=%s" % (repo, user)
    print api_path, repo, user
    conn = httplib.HTTPConnection(config.kali_url)
    conn.request("GET", api_path)
    r1 = conn.getresponse()
    print r1.status, r1.reason
    if r1.status!=200:
        return None
    else:
        return  r1.read()


def hook(ui, repo, hooktype, node=None, source=None, **kwargs):

    ui.warn('\nkali_acl.py (проверка прав через Kalithea API)')

    if hooktype not in ['pretxnchangegroup', 'pretxncommit']:
        raise error.Abort(_('config error - hook type "%s" cannot stop incoming changesets nor commits') % hooktype)

    user = None

    if source == 'serve' and 'url' in kwargs:
        url = kwargs['url'].split(':')
        if url[0] == 'remote' and url[1].startswith('http'):
            user = unquote(url[3])

    if user is None:
        user = getpass.getuser()

    #Получаем данные из Kallithea
    repo_ = str(repo.root)[24:].replace('/', '.')
    ui.warn('user: %s, repo name %s' % (user, repo_))

    group = get_user_group(repo_, user)

    #Если нет прав manager или default, то вносить правки нельзя вообще
    if group != 'manager' and group != 'default':
        ui.warn('\nthe pusher should be in the group "manager" or "default"')
        return True

    for rev in xrange(repo[node], len(repo)):
        ctx = repo[rev]
        branch = ctx.branch()
        ui.warn('\nchangeset: "%s" on branch "%s"' % (ctx, branch))

        if group=='manager':
            # Если имя ветки default, то её может править только пользователь с правом manager
            # Если имя ветки <>*.-RELEASE, то её может править только пользователь с правом manager
            # Если имя ветки <>-CLIENT, то её может править только пользователь с правом manager
            if not check_manager_branch(branch):
                ui.warn('\n"manager" should push in "default", "*-RELEASE" or "*-CLIENT" branch '
                        'or in "ticket-NNNN" branch')
                return True
        elif group=='default':
            # Если имя ветки ticket-<N задачи>-<Любой постфикс>, то её может править только пользователь с правом default.
            # В таком случае задача с <N задачи> должна сушествовать в Redmine и находится в редактируемом статусе (Новая, В работе).
            if not check_issue_status(branch):
                ui.warn('\n"default" user %s should push in "ticket-NNNN" branch, '
                        'and branch task shoud be in Redmine with "In work" or "New" status' % (user))
                return True

    return False

def testCheckIssue():
    comment = u"fjsdklf ticket-3432-33 refs #44337 0.44.*-RELEASE"
    print get_ticket_num(comment)
    print check_manager_branch(comment)
    print get_user_group('Consolidation/pull_request', 'postnikov')

if __name__ == '__main__':
    testCheckIssue()