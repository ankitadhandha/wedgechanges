#!/usr/bin/env python

def foo():
	t = [1, 2]
	i = 3
	print t[i]

def main():
	try:
		foo()
	except:
		raise Exception, 'hi'

main()
