#!/usr/bin/env python

import sys
if sys.version[0] == '1':
	print """Webware requires Python version 2.0+.  Webware is currently being
run with the Python version:
  %s
This Python interpreter is located at:
  %s
You may need to change the AppServer script, giving the full path of
the appropriate Python interpreter.""" % (sys.version, sys.executable)
	sys.exit(1)

import time; startTime = time.time()

runProfile = 0   # as in Python's profile module. See doc string of Profiler.py

import os, sys, string

profiler = None  # Forget this and read the doc string of Profiler.py


def usage():
	print 'error: Launch.py (of WebKit)'
	print 'usage: Launch.py SERVER ARGS'
	sys.exit(1)


def launchWebKit(server, appWorkPath, args):
	"""
	Import and launch the specified WebKit server.
	"""
	# allow for a .py on the server name
	if server[-3:]=='.py':
		server = server[:-3]

	# clean up sys.path
	def ok(directory):
		return directory not in ['', '.'] and string.lower(directory[-6:])!='webkit'
	sys.path = filter(ok, sys.path)
	sys.path.insert(0, '')

	# Import the server's main()
	import WebKit
	code = 'from WebKit.%s import main' % server
	dict = {}
	exec code in dict
	main = dict['main']

	# Set up a reference to our profiler so applications can import and use it
	from WebKit import Profiler
	Profiler.startTime = startTime
	if runProfile:
		Profiler.profiler = profiler

	# Run!
	args = args + ['workdir=' + appWorkPath]
	main(args)


def main(args=None):
	if args is None:
		args = sys.argv
	if len(args)<2:
		usage()

	server = args[1] # the server

	# figure out directory locations
	webKitPath = os.path.dirname(os.path.join(os.getcwd(), sys.argv[0]))
	webwarePath = os.path.dirname(webKitPath)

	# go to Webware dir so that:
	#   - importing packages like 'WebUtils' hits this Webware
	#   - we cannot import WebKit modules without qualifying them
	os.chdir(webwarePath)

	# Go!
	launchWebKit(server, webKitPath, args[2:])


if __name__=='__main__':
	if runProfile:
		print 'Profiling is on. See doc string in Profiler.py for more info.'
		from profile import Profile
		profiler = Profile()
		profiler.runcall(main)
		from WebKit import Profiler
		Profiler.dumpStats()
	else:
		main()
