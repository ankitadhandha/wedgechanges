#!/usr/bin/env python
"""
TestFuncs.py
Webware for Python

This tests the performace of utility functions in WebUtils vs. their standard Python alternatives.
"""

import os, string, sys, time
sys.path.insert(1, os.path.abspath(os.pardir))
from Funcs import *
import urllib

allChars = string.join(map(lambda i: chr(i), range(256)), '')

URLEncodeTests = [
	'NothingIsChangedTest',
	'This test has spaces',
	'This test	has	tabs',
	' boundary	',
	allChars
]

def TestEncodeAndDecode(encodeFunc, decodeFunc, tests):
	print 'Test %s and %s' % (encodeFunc.__name__, decodeFunc.__name__)
	for test in tests:
		s = encodeFunc(test)
		if decodeFunc(encodeFunc(test))==test:
			print '  Passed test'
		else:
			print '  Failed test!'
			print '    string=(%s)' % test
			print '    encoded=(%s)' % encodeFunc(test)
			print '    decoded=(%s)' % decodeFunc(encodeFunc(test))
	print

def TestURLEncodeAndDecode():
	TestEncodeAndDecode(urlEncode, urlDecode, URLEncodeTests)


def Benchmark(func, tests, metacount=500, count=10):
	start = time.time()
	for majorLoop in xrange(metacount):
		for test in tests:
			for minorLoop in xrange(count):
				func(test)
	stop = time.time()

	return stop - start

def BenchmarkURLEncode():
	print 'Benchmark urlEncode() vs. quote_plus()'
	t1 = Benchmark(urllib.quote_plus, URLEncodeTests)
	t2 = Benchmark(urlEncode, URLEncodeTests)
	print '  quote_plus()   = %6.2f secs' % t1
	print '  urlEncode()    = %6.2f secs' % t2
	print '  diff           = %6.2f secs' % (t2 - t1)
	print '  diff %%         = %6.2f %%' % ((t2 - t1) / t1 * 100.0)
	print '  factor         = %6.2f X' % (t1/t2)
	print


URLDecodeTests = map(lambda s: urlEncode(s),  URLEncodeTests)

def BenchmarkURLDecode():
	print 'Benchmark urlDecode() vs. unquote_plus()'
	t1 = Benchmark(urllib.unquote_plus, URLDecodeTests)
	t2 = Benchmark(urlDecode, URLDecodeTests)
	print '  unquote_plus() = %6.2f secs' % t1
	print '  urlDecode()    = %6.2f secs' % t2
	print '  diff           = %6.2f secs' % (t2 - t1)
	print '  diff %%         = %6.2f %%' % ((t2 - t1) / t1 * 100.0)
	print '  factor         = %6.2f X' % (t1/t2)
	print


HTMLEncodeTests = [
	'Nothing special.',
	'Put your HTML tags in <brackets>.',
	'a & b & c',
	'A \n newline',
	'A newline \n x < y < z \n <tag>&<tag>'
]

def TestHTMLEncodeAndDecode():
	TestEncodeAndDecode(htmlEncode, htmlDecode, HTMLEncodeTests)


if __name__=='__main__':
	# To remove allChars, change to 'if 1:'
	#    With allChars, we look really good - URLEncode() is 6 X faster
	#    However, it's not a realistic case; reality is 2 X faster
	if 1:
		del URLEncodeTests[-1]
		del URLDecodeTests[-1]

	# run tests
	TestURLEncodeAndDecode()
	BenchmarkURLEncode()
	BenchmarkURLDecode()

	TestHTMLEncodeAndDecode()
