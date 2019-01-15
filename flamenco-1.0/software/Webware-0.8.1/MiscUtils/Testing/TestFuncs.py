import sys
sys.path.insert(1, '..')
import string
from Funcs import *


def TestCommas():
	testSpec = '''
		0 '0'
		0.0 '0.0'
		1 '1'
		11 '11'
		111 '111'
		1111 '1,111'
		11111 '11,111'
		1.0 '1.0'
		11.0 '11.0'
		1.15 '1.15'
		12345.127 '12,345.127'
		-1 '-1'
		-11 '-11'
		-111 '-111'
		-1111 '-1,111'
		-11111 '-11,111'
	'''
	tests = string.split(testSpec)
	count = len(tests)
	i = 0
	while i<count:
		source = eval(tests[i])
		result = eval(tests[i+1])
		#print '%r yields %r' % (source, result)
		assert commas(source)==result, '%r %r' % (commas(source), result)

		# Now try the source as a string instead of a number:
		source = eval("'%s'" % tests[i])
		#print '%r yields %r' % (source, result)
		assert commas(source)==result, '%r %r' % (commas(source), result)

		i = i+2


def TestLocalIP():
	ip = localIP()
	assert localIP()==ip  # second invocation
	assert localIP(useCache=None)==ip
	assert localIP(remote=None, useCache=None)==ip
	assert localIP(remote=('www.aslkdjsfliasdfoivnoiedndfgncvb.com', 80), useCache=None)==ip


def TestHostName():
	# About all we can do is invoke hostName() to see that no
	# exceptions are thrown, and do a little type checking on the
	# return type.
	host = hostName()
	assert host is None  or  type(host) is type(''), \
		'host type = %s, host = %s' % (type(host), repr(host))


def TestUniqueId():
	lastResult = None
	for x in range(5):
		result = uniqueId()
		assert type(result) is type('')
		assert len(result)==32
		assert result!=lastResult

		result = uniqueId(TestUniqueId)
		assert type(result) is type('')
		assert len(result)==32
		assert result!=lastResult


def TestValueForString():
	evalCases = '''
		1
		5L
		5.5
		True
		False
		None
		[1]
		['a']
		{'x':1}
		(1, 2, 3)
		'a'
		"z"
		"""1234"""
	'''
	
	stringCases = '''
		kjasdfkasdf
		2389234lkdsflkjsdf
		*09809
	'''

	evalCases = [s.strip() for s in evalCases.strip().split('\n')]
	for case in evalCases:
		assert valueForString(case)==eval(case), 'case=%r, valueForString()=%r, eval()=%r' % (case, valueForString(case), eval(case))

	stringCases = [s.strip() for s in stringCases.strip().split('\n')]
	for case in stringCases:
		assert valueForString(case)==case, 'case=%r, valueForString()=%r' % (case, valueForString(case))


def TestWordWrap():
	# an example with some spaces and newlines
	msg = """Arthur:  "The Lady of the Lake, her arm clad in the purest \
shimmering samite, held aloft Excalibur from the bosom of the water, \
signifying by Divine Providence that I, Arthur, was to carry \
Excalibur. That is why I am your king!"

Dennis:  "Listen. Strange women lying in ponds distributing swords is \
no basis for a system of government. Supreme executive power derives \
from a mandate from the masses, not from some farcical aquatic \
ceremony!\""""

	for margin in range(20, 200, 20):
		s = wordWrap(msg, margin)
		for line in s.split('\n'):
			assert len(line)<=margin, 'len=%i, margin=%i, line=%r' % (len(line), margin, line)


def Test():
	TestCommas()
	TestHostName()
	TestLocalIP()
	TestUniqueId()
	TestValueForString()
	TestWordWrap()


if __name__=='__main__':
	Test()
