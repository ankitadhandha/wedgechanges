#!/usr/bin/env python
"""
Instructions:
	- stop the app server
	- set WebKit/Application.config SessionTimeout to 1
	- remove WebKit/Sessions/*.ses
	- start the app server
	- go to http://localhost/webkit/Admin/
	- Note the "Active sessions: 1"
	- Run this program. Watch the memory increase.
	- Refresh the admin and you should see a large number of sessions.
	- Wait for sessions to expire and check memory:
		ps auxwww | grep -n appserver
	- Run this program again, wait for expiration, check memory

When reporting results, include:
	- Py ver
	- Webware ver
	- Op sys
	- Application.config SessionStore
	- Memory results
"""

import os, sys, time
from urllib2 import urlopen

url = 'http://localhost/webkit/Examples/CountVisits'
iters = 5000
delay = .001
printFreq = 100
shouldPrintShort = 1

def main():
	for x in range(iters):
		if x % printFreq==0:
			printMem(x)
		urlopen(url).read()
		time.sleep(delay)
	printMem(x+1)

	print


def printMem(x):
	lines = os.popen('ps auxwww | grep AppServer').readlines()
	for line in lines:
		if line.find('ThreadedAppServer')!=-1:
			line.strip()
			if shouldPrintShort:
				line = ' '.join(line.split()[4:6])
			print '%4i: %s' % (x, line)
			break

main()
