#!/usr/bin/python -OO
# -*- coding: UTF-8 -*-

"""

Хук проверяет, что логин - валидный почтовый адрес пользователя Кристы или ССКсофт

Подключение централизованное, через Kallithea

pretxnchangegroup.release_branch_merge_control = python:path/to/script/check-login.py:pretxnchangegroup_badmerges

"""

domains = ['foo.bar', 'example.com']

def precommit_badbranch(ui, repo, node, **kwargs):
    for rev in xrange(repo[node].rev(), len(repo)):
        domain = repo[rev].user().split('@')[1]
        if not domain in domains:
            ui.warn('invalid username (it should be in email format), provided username: %s' % domain)
            return True
    return False
