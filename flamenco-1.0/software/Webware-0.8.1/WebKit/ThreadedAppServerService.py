#!/usr/bin/env python
"""
ThreadedAppServerService

For general notes, see ThreadedAppServer.py.

This version of the app server is a threaded app server that runs as
a Windows NT Service.  This means it can be started and stopped from
the Control Panel or from the command line using "net start" and
"net stop", and it can be configured in the Control Panel to
auto-start when the machine boots.

This requires the win32all package to have been installed.

To see the options for installing, removing, starting, and stopping
the service, just run this program with no arguments.  Typical usage is
to install the service to run under a particular user account and startup
automatically on reboot with

python ThreadedAppServerService.py --username mydomain\myusername --password mypassword --startup auto install

Then, you can start the service from the Services applet in the Control Panel,
where it will be listed as "WebKit Threaded Application Server".  Or, from
the command line, it can be started with either of the following commands:

net start WebKit
python ThreadedAppServerService.py start

The service can be stopped from the Control Panel or with:

net stop WebKit
python ThreadedAppServerService.py stop

And finally, to uninstall the service, stop it and then run:

python ThreadedAppServerService.py remove

FUTURE
	* This shares a lot of code with ThreadedAppServer.py --
	  instead it should inherit from ThreadedAppServer and have
	  very little code of its own.
	* Have an option for sys.stdout and sys.stderr to go to a logfile instead
	  of going nowhere.
	* Optional NT event log messages on start, stop, and errors.
	* Allow the option of installing multiple copies of WebKit with
	  different configurations and different service names.
	* Figure out why I need the Python service hacks marked with ### below.
	* Allow it to work with wkMonitor, or some other fault tolerance
	  mechanism.
"""

import time
startTime = time.time()
import win32serviceutil
import win32service
import os, sys, cStringIO

class ThreadedAppServerService(win32serviceutil.ServiceFramework):
	_svc_name_ = 'WebKit'
	_svc_display_name_ = 'WebKit Threaded Application Server'

	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.server = None
		# Fix the current working directory -- this gets initialized incorrectly
		# for some reason when run as an NT service.
		try:
			os.chdir(os.path.abspath(os.path.dirname(__file__)))
		except:
			pass

	def SvcStop(self):
		# Before we do anything, tell the SCM we are starting the stop process
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		# And set running to 0 in the server.  If it hasn't started yet, we'll
		# have to wait until it does.
		while self.server is None:
			time.sleep(1.0)
		self.server.initiateShutdown()

	def SvcDoRun(self):
		try:
			# Temporarily suck up stdout and stderr into a cStringIO
			stdoutAndStderr = cStringIO.StringIO()
			sys.stdout = sys.stderr = stdoutAndStderr
			# Import the ThreadedAppServer
			if '' not in sys.path:
				sys.path = [''] + sys.path
			os.chdir(os.pardir)
			from WebKit import Profiler
			Profiler.startTime = startTime
			from WebKit.ThreadedAppServer import ThreadedAppServer
			self.server = ThreadedAppServer(self.workDir())
			# Now switch the output to the logfile specified in the appserver's config
			# setting "NTServiceLogFilename"
			if self.server.hasSetting('NTServiceLogFilename'):
				sys.stdout = sys.stderr = open(self.server.setting('NTServiceLogFilename'), 'a+')
				sys.stdout.write('-' * 68 + '\n')
				sys.stdout.write(stdoutAndStderr.getvalue())
			else:
				# Make all output go nowhere.  Otherwise, print statements cause
				# the service to crash, believe it or not.
				sys.stdout = sys.stderr = open('nul', 'w')
			del stdoutAndStderr
			self.server.mainloop()
			self.server._closeThread.join()
		except Exception, e: #Need to kill the Sweeper thread somehow
			print e
			print "Exiting AppServer"
			if 0: #See the traceback from an exception
				tb = sys.exc_info()
				print tb[0]
				print tb[1]
				import traceback
				traceback.print_tb(tb[2])
			if self.server:
				self.server.running=0
				self.server.shutDown()
			raise

	def workDir(self):
		return None

if __name__=='__main__':
	win32serviceutil.HandleCommandLine(ThreadedAppServerService)
	
