#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""

Хук для Консолидации

Проверяет возможность внесения изменений в зависимости от статуса связанной задачи в redmine и ее наполнения

Нужно настроить подключения и логин в файле config.py (см. config.py.sample)

Подключение на сервере:

[hooks]
pretxnchangegroup = python:path/to/script/redmine_control_hooks.py:checkAllCommitMessage

Или локально:

[hooks]
pretxncommit = python:path/to/script/redmine_control_hooks.py:checkCommitMessage

"""

import re
from redminelib import Redmine
import config

newStatusId = 1
workStatusId = 2

def parseComment(comment):
    refs = re.search(u"refs\s?#\s?\d+", comment)
    if not refs is None:
        num = re.search(u"\d+", refs.group(0))
        if not num is None:
            return num.group(0)
    return None

def checkIssue(comment, ui):
    ui.warn('\nredmine_control_hooks.py')
    try:
        refnum = parseComment(comment)
        if refnum is None:
            # Комментарий не содержит ссылки, разрешаем
            return True
        redmine = Redmine(config.redmine_url, username=config.usr, password=config.passw)
        # получаем список задач из проекта
        issues = redmine.issue.filter(project_id=config.redmine_project_id)
        if len(filter(lambda x: int(x['id'])==int(refnum), issues))==0:
            # Нет задачи в проекте, запрещаем
            msg = ' '.join(["***** REDMINE HOOK: Project ", str(config.redmine_project_id), "does not contain task", str(refnum), ", check refs #.\n"])
            msg += ' '.join([" ", "Проект", str(config.redmine_project_id), "не содержит задачу", str(refnum), ", проверте refs#.\n"])
            if ui<>None:
                ui.warn(msg)
            else:
                print(msg)
            return False

        project = redmine.project.get(config.redmine_project_id)
        issue = redmine.issue.get(resource_id=refnum, project_id=project.internal_id, include='journals')
        # Задача новая, к выполнению приступили неявно
        if issue.status.id==newStatusId:
            # Пропускаем - новая задача
            return True
        if len(issue.journals)>0:
            #Статус - не новая и есть комментарии (записи) в редмайн
            if issue.status.id==workStatusId:
                # отсортируем журналы по дате
                journals = sorted(issue.journals, key=lambda o: o.created_on, reverse=True)
                #ищем первую запись, где менялся статус, параллельно проверяем, есть ли каменты
                for j in journals:
                    for d in j['details']:
                        #Предудущий статус "Новая"
                        if d['name'] == 'status_id' and d['old_value']==newStatusId:
                            # Пропускаем без проверки, так как предыдущий статус - "Новая"
                            return True;
                            # Предудущий статус не "Новая" и есть комментарий
                        if d['name'] == 'status_id' and d['old_value']!=newStatusId and hasattr(j, 'notes') and len(j['notes'])>0:
                            # "Пропускаем - предыдущий статус - не "Новая", но есть примечания"
                            return True;
            else:
                msg = "***** REDMINE HOOK: Can not be commited, if task not new and not in work.\n"
                msg += " Нельзя коммитить, если задача не новая и не в работе.\n"
                if ui <> None:
                    ui.warn(msg)
                else:
                    print(msg)
                return False
        else:
            if ui<>None:
                msg = "***** REDMINE HOOK: Task was in work, but no comments in Redmine.\n"
                msg += " Задача была в работе, но в Redmine нет комментариев.\n"
                if ui <> None:
                    ui.warn(msg)
                else:
                    print(msg)
                return False
        # 'Пропускаем - нет номера задачи в комментарии'
        return True
    except Exception as e:
        ui.warn(" ".join(["***** REDMINE HOOK:", str(e), "\n"]))
        return True


def checkCommitMessage(ui, repo, **kwargs):
    message = repo['tip'].description()
    return not checkIssue(message, ui)


def checkAllCommitMessage(ui, repo, node, **kwargs):
    for rev in xrange(repo[node].rev(), len(repo)):
        message = repo[rev].description()
        if not checkIssue(message, ui):
            return True
    return False

def testCheckIssue():
    comment = u"fjsdklf refs #44337"
    print comment
    print checkIssue(comment, None)
    comment = u"fjsdklf refs #39283 sdfsdfsdf"
    print comment
    print checkIssue(comment, None)
    comment = u"fjsdklf refs #44125 ffss"
    print comment
    print checkIssue(comment, None)

if __name__ == '__main__':
    testCheckIssue()
