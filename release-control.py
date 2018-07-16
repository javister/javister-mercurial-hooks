#!/usr/bin/python -OO
# -*- coding: UTF-8 -*-

"""

Hook для блокирования сливания веток, предназначеных для выпуска релизов.

Подключается централизованно в kallithea

pretxnchangegroup.release_branch_merge_control = python:path/to/script/release-control.py:pretxnchangegroup_badmerges

"""

from mercurial import util
import re

_branch_re = re.compile(r'(\d+)\.(\d+)\.\*-RELEASE$')

def _test_branch(branch):
    """Тестируем branch на предмет принадлежности его к процессу выпуска релизов.
    Такие branch'и имеют формат имени: <major>.<minor>.*-RELEASE"""
    match = _branch_re.match(branch)
    if match:
        return True
	return False

def precommit_badmerge(ui, repo, parent1=None, parent2=None, **kwargs):
	"""Клиентский хук для блокирования создания комитов с мерджем релизной ветки"""
	if not parent2:
        # Not merging: nothing more to check.
		return False

	if repo[parent1].branch() == repo[parent2].branch():
		return False

	target_branch = _test_branch(repo[parent1].branch())
	source_branch = _test_branch(repo[parent2].branch())

	if target_branch or source_branch:
		raise util.Abort('Release brach can not be merged.')
	return False
    
def pretxnchangegroup_badmerges(ui, repo, **kwargs):
	"""Серверный хук для блокирования проталкивания комитов с мерджем релизной ветки"""
	# Extract common values
	node = kwargs['node']
	# Find the range of csets in this cgroup
	ctx = repo[node]
	start = ctx.rev()
	end = len(repo)
	
	debug = ui.debug
    
	for rev in xrange(start, end):
		node = repo[rev]
		if len(node.parents()) > 1:
			if (node.parents()[0].branch() != node.parents()[1].branch()) and (_test_branch(node.parents()[0].branch()) or _test_branch(node.parents()[1].branch())):
				raise util.Abort('Release brach can not be merged.')
	return False
