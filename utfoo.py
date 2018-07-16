#!/usr/bin/python -OO
# vim: set fileencoding=utf-8 :
# Д. Попов, popov@krista.ru, с 02.02.2012
# $Id: utfoo.py,v 1.5 2012/02/07 10:58:01 popov Exp $
# Задача: http://rabbitsrv.krista.ru:3000/issues/1609
# Mercurial API: http://mercurial.selenic.com/wiki/MercurialApi
#
# Скрипт предназначен для использования в качетсве хука в репозитарии Mеркуриала для
# предотвращения попадания в него коммитов с кривыми кодировками русских строк в именах
# файлов и в комментариях.
#
# Типовая вешалка hgrc:
# [hooks]
# pretxncommit.utfoo = python:/path/utfoo.py:hook
# pretxnchangegroup.utfoo = python:/path/utfoo.py:hook


import mercurial
from mercurial import util
from datetime import datetime
import re
from mercurial.error import Abort

russian = re.compile( U"[а-яА-ЯёЁ]+", re.U )


def is_double(strdata, encname):
	'''Проверяет, не может ли строка быть двойной перекодировкой из заданной кодировки в UTF-8.
	Возвращает булевское значение, истина, если признаки двойной перекодировки есть.'''
	try:
		double = strdata.decode('utf-8').encode(encname).decode('utf-8')
	except UnicodeDecodeError:
		return False
	except UnicodeEncodeError:
		return False
	if russian.search(double) != None:
		return True
	return False
	
def checkenc(strdata, errmessage):
	'''Проверяет строку. Если всё в порядке, просто возвращает управление. Иначе плюёт исключение.'''
	try:
		strdata.decode('utf-8')
	except UnicodeDecodeError:
		raise util.Abort(errmessage)
	# На входе может быть двойная перекодировка из 1251 или 866 в утф-8. Не должно проходить,
	# по крайней мере с русскими буквами.
	if is_double(strdata, 'cp1251') or is_double(strdata, 'cp866'):
		raise util.Abort(errmessage)

def node_str(node):
	''' Преобразует идентификатор коммита из двоичного хеша в шестнадцатеричную строку, для печати '''
	res = ''
	for b in list(node)[:6]:
		res += ("%02x" % ord(b))
	return res

def hook(ui, repo, **kwargs):
	'''Хук для Меркуриала. Требование к событию: 1) Входное 2) Контролируемое. 3) Содержит в себе node.
	То есть pretxncommit, pretxnchangegroup'''
	if not 'node' in kwargs:
		raise Abort('You must use the utfoo hook in a context with a `node` parameter (e.g. pretxncommit)')
	node = repo[kwargs['node']];
	nodeinfo = 'rev=%s, node=%s, author=%s, time=%s' % ( node.rev(), node_str(node.node()), node.user(), datetime.fromtimestamp(node.date()[0]).isoformat() )

	for filename in node:
		errmessage = 'Non-UTF-8 characters in filename. file=%s, %s' % ( filename, nodeinfo )
		checkenc( filename, errmessage )
	errmessage = 'Non-UTF-8 characters in description. %s' % nodeinfo
	checkenc( node.description(), errmessage )

############################# Как-бы юнит-тест при прямом запуске скрипта
def print_ex(message, exception):
	''' Ругательный метод '''
	sys.stdout.write( '%s: %s: %s' % (message, exception.__class__, str(exception)) )

if __name__ == '__main__':
	import sys
	test = u'абвёэюяАБВЁЭЮЯ'
	
	sys.stdout.write('\nTest good UTF-8:\t')
	try:
		checkenc( test.encode('utf-8'), 'UTF-8 string' )
		sys.stdout.write('Ok, no exception')
	except Exception as ex:
		print_ex('Failed, exception', ex)
	
	sys.stdout.write('\nTest bad win1251:\t')
	try:
		checkenc( test.encode('cp1251'), 'Windows-1251 string' )
		sys.stdout.write('Failed, exception lost')
	except mercurial.error.Abort:
		sys.stdout.write('Ok, right exception')
	except Exception as ex:
		print_ex('Failed, invalid exception')
	
	sys.stdout.write('\nTest bad dos866:\t')
	try:
		checkenc( test.encode('cp866'), 'DOS-866 string' )
		sys.stdout.write('Failed, exception lost')
	except mercurial.error.Abort:
		sys.stdout.write('Ok, right exception')
	except Exception as ex:
		print_ex('Failed, invalid exception')
	
	sys.stdout.write('\nTest double 1251:\t')
	try:
		checkenc( test.encode('utf-8').decode('cp1251').encode('utf-8'), 'Double encoded from 1251 to UTF-8' )
		sys.stdout.write('Failed, exception lost')
	except mercurial.error.Abort:
		sys.stdout.write('Ok, right exception')
	except Exception as ex:
		print_ex('Failed, invalid exception', ex)
	
	sys.stdout.write('\nTest double 866:\t')
	try:
		checkenc( test.encode('utf-8').decode('866').encode('utf-8'), 'Double encoded from 866 to UTF-8' )
		sys.stdout.write('Failed, exception lost')
	except mercurial.error.Abort:
		sys.stdout.write('Ok, right exception')
	except Exception as ex:
		print_ex('Failed, invalid exception', ex)
	
	sys.stdout.write('\nTest function node_str:\t')
	sys.stdout.write( 'Ok' if node_str("ABCDEFGHIJKMNOPQRSTU") == "414243444546" else "Failed" )
	
	sys.stdout.write('\nTests ended.\n')

