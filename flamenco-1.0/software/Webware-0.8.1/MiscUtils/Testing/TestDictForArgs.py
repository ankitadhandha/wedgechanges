import sys
sys.path.insert(1, '..')
from DictForArgs import *


def Test():
	TestDictForArgs()
	TestPyDictForArgs()


def TestDictForArgs():
	print 'Testing DictForArgs()...'
	errCount = TestPositives()
	errCount = errCount + TestNegatives()
	if errCount:
		if errCount>1:
			suffix = 's'
		else:
			suffix = ''
		print '%d error%s found.' % (errCount, suffix)
	else:
		print 'All cases pass.'
	return errCount


def TestPositives():
	print 'Positive cases:'
	tests ='''\
# Basics
x=1       == {'x': '1'}
x=1 y=2   == {'x': '1', 'y': '2'}

# Strings
x='a'     == {'x': 'a'}
x="a"     == {'x': 'a'}
x='a b'   == {'x': 'a b'}
x="a b"   == {'x': 'a b'}
x='a"'    == {'x': 'a"'}
x="a'"    == {'x': "a'"}
x="'a'"   == {'x': "'a'"}
x='"a"'   == {'x': '"a"'}

# No value
x         == {'x': '1'}
x y       == {'x': '1', 'y': '1'}
x y=2     == {'x': '1', 'y': '2'}
x=2 y     == {'x': '2', 'y': '1'}
'''
	tests = string.split(tests, '\n')
	errCount = 0
	TestPositive('', {})
	TestPositive(' ', {})
	for test in tests:
		if '#' in test:
			test = test[:string.index(test, '#')]
		test = string.strip(test)
		if test:
			input, output = string.split(test, '==')
			output = eval(output)
			success = TestPositive(input, output)
			if success:
				success = TestPositive(string.strip(input), output)
			if not success:
				errCount = errCount + 1
	print
	return errCount

def TestPositive(input, output):
	print repr(input)
	sys.stdout.flush()
	result = DictForArgs(input)
	if result!=output:
		print 'ERROR\nExpecting: %s\nGot: %s\n' % (repr(output), repr(result))
		success = 0
	else:
		success = 1
	return success


def TestNegatives():
	print 'Negative cases:'
	cases = '''\
-
$
!@#$
'x'=5
x=5 'y'=6
'''
	cases = string.split(cases, '\n')
	errCount = 0
	for case in cases:
		if '#' in case:
			case = case[:string.index(case, '#')]
		case = string.strip(case)
		if case:
			success = TestNegative(case)
			if not success:
				errCount = errCount + 1
	print
	return errCount

def TestNegative(input):
	print repr(input)
	sys.stdout.flush()
	try:
		result = DictForArgs(input)
	except DictForArgsError:
		success = 1
	except:
		success = 0
		result = sys.exc_info()
	else:
		success = 0
	if not success:
		print 'ERROR\nExpecting DictForArgError.\nGot: %s.\n' % repr(result)
	return success


def TestPyDictForArgs():
	cases = '''\
		x=1 == {'x': 1}
		x=1; y=2 == {'x': 1, 'y': 2}
		x='a' == {'x': 'a'}
		x="a"; y="""b""" == {'x': 'a', 'y': 'b'}
		x=(1, 2, 3) == {'x': (1, 2, 3)}
		x=['a', 'b'] == {'x': ['a', 'b']}
		x='a b'.split() == {'x': ['a', 'b']}
		x=['a b'.split(), 1]; y={'a': 1} == {'x': [['a', 'b'], 1], 'y': {'a': 1}}
'''.split('\n')
	for case in cases:
		case = case.strip()
		if case:
			source, answer = case.split('==')
			answer = eval(answer)
			assert PyDictForArgs(source)==answer


if __name__=='__main__':
	Test()
