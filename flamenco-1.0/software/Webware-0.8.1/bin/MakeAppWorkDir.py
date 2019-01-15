#!/usr/bin/env python
#----------------------------------------------------------------------
#
# A script to build a WebKit work directory outside of the WebWare tree
#
# By Robin Dunn
#
#----------------------------------------------------------------------

"""
MakeAppWorkDir.py


INTRODUCTION

This utility builds a directory tree that can be used as the current
working directory of an instance of the WebKit application server.  By
using a separate directory tree like this your application can run
without needing write access, etc. to the WebWare directory tree, and
you can also run more than one application server at once using the
same WebWare code.  This makes it easy to reuse and keep WebWare
updated without disturbing your applications.


COMMAND LINE USAGE

python MakeAppWorkDir.py [OPTIONS] SomeDir

OPTIONS:
-c SampleContextName    "SampleContextName" will be used for the pre-
                        installed context.  (Default "MyContext")
--cvsignore             .cvsignore files will be added
-l or --library         A lib/ directory will be added, which will
                        added to the Python the path for the AppServer
"""

#----------------------------------------------------------------------

import sys, os, string
import glob, shutil

#----------------------------------------------------------------------

class MakeAppWorkDir:
	"""Make a new application runtime directory for Webware.

	This class breaks down the steps needed to create a new runtime
	directory for webware.  That includes all the needed
	subdirectories, default configuration files, and startup scripts.
	Each step can be overridden in a derived class if needed.
	"""

	def __init__(self, webWareDir, workDir, verbose=1,
		     sampleContext="MyContext", osType=None,
		     addCVSIgnore=0, makeLibrary=0):
		"""Initializer for MakeAppWorkDir.  Pass in at least the
		Webware directory and the target working directory.  If you
		pass None for sampleContext then the default context will the
		the WebKit/Examples directory as usual.
		"""
		self._webWareDir = webWareDir
		self._webKitDir = os.path.join(webWareDir, "WebKit")
		self._workDir = os.path.abspath(workDir)
		self._verbose = verbose
		self._substVals = {
		    "WEBWARE": string.replace(self._webWareDir, '\\', '/'),
		    "WEBKIT":  string.replace(self._webKitDir,	'\\', '/'),
		    "WORKDIR": string.replace(self._workDir,	'\\', '/'),
		    "DEFAULT": "%s/Examples" % string.replace(self._webKitDir,	'\\', '/'),
		    }
		if makeLibrary:
			self._substVals['libraryPath'] = 'sys.path.append(%s)\n' % repr(os.path.join(self._substVals['WORKDIR'], 'lib'))
		else:
			self._substVals['libraryPath'] = ''
		self._sample = sampleContext
		if sampleContext is not None:
			self._substVals["DEFAULT"] = sampleContext
		self._substVals['executable'] = sys.executable
		if osType is None:
			osType = os.name
		self._osType = osType
		self._addCVSIgnore = addCVSIgnore
		self._makeLibrary = makeLibrary

	def buildWorkDir(self):
		"""These are all the (overridable) steps needed to make a new runtime direcotry."""
		self.makeDirectories()
		self.copyConfigFiles()
		self.copyOtherFiles()
		self.makeLauncherScripts()
		self.makeDefaultContext()
		if self._makeLibrary:
			self.makeLibrary()
		if self._addCVSIgnore:
			self.addCVSIgnore()
		self.printCompleted()

	def makeDirectories(self):
		"""Creates all the needed directories if they don't already exist."""
		self.msg("Creating directory tree at %s" % self._workDir)

		theDirs = [ self._workDir,
			    os.path.join(self._workDir, "Cache"),
			    os.path.join(self._workDir, "Configs"),
			    os.path.join(self._workDir, "ErrorMsgs"),
			    os.path.join(self._workDir, "Logs"),
			    os.path.join(self._workDir, "Sessions"),
			    ]

		for aDir in theDirs:
			if os.path.exists(aDir):
				self.msg("\t%s already exists." % aDir)
			else:
				os.mkdir(aDir)
				self.msg("\t%s created." % aDir)

		self.msg("\n")


	def copyConfigFiles(self):
		"""
		Make a copy of the config files in the Configs directory.
		"""
		configs = glob.glob(os.path.join(self._webKitDir, "Configs", "*.config"))
		for name in configs:
			newname = os.path.join(self._workDir, "Configs", os.path.basename(name))
			shutil.copyfile(name, newname)


	def copyOtherFiles(self):
		"""
		Make a copy of any other necessary files in the new work dir.
		"""
		self.msg("Copying files.")
		otherFiles = [("404Text.txt",   0, None),
					  ("AppServer",     1, 'posix'),
					  ("AppServer.bat", 1, 'nt'),
					  ("Adapters/WebKit.cgi",    0, None),
					  ]
		for name, doChmod, osType in otherFiles:
			if osType and osType != self._osType:
				continue
			oldname = os.path.join(self._webKitDir, name)
			newname = os.path.join(self._workDir, os.path.basename(name))
			self.msg("\t%s" % newname)
			# Here we replace the #!
			f = open(oldname)
			firstLine = f.readline()
			f.close()
			if firstLine[:2] == '#!' \
			   and firstLine.find('python') != -1:
				f = open(oldname)
				new = open(newname, 'w')
				# throw away the first line
				f.readline()
				new.write('#!%s\n' % sys.executable)
				new.write(f.read())
				f.close()
				new.close()
			else:
				shutil.copyfile(oldname, newname)
			if doChmod:
				os.chmod(newname, 0755)
		self.msg("\n")


	def makeLauncherScripts(self):
		"""
		Using templates loacted below, make the Launcher script for
		launching the AppServer in various ways.  Also makes writes
		the Webware and the runtime directories into the CGI adapter
		scripts.
		"""
		self.msg("Creating launcher scripts.")
		scripts = [ ("Launch.py", _Launch_py, None),
			        ("NTService.py", _NTService_py, 'nt'),
			    ]
		for name, template, osType in scripts:
			if osType and osType != self._osType:
				continue
			filename = os.path.join(self._workDir, name)
			open(filename, "w").write(template % self._substVals)
			os.chmod(filename, 0755)
			self.msg("\t%s created." % filename)

		for name in ["WebKit.cgi"]:
			filename = os.path.join(self._workDir, name)
			content = open(filename).readlines()
			output  = open(filename, "wt")
			for line in content:
				s = string.split(line)
				if s and s[0] == 'WebwareDir' and s[2] == 'None':
					line = "WebwareDir = '%(WEBWARE)s'\n" % self._substVals
				elif s and s[0] == 'AppWorkDir' and s[2] == 'None':
					line = "AppWorkDir = '%(WORKDIR)s'\n" % self._substVals
				output.write(line)
			output.close()
			os.chmod(filename, 0755)
			self.msg("\t%s updated." % filename)

		self.msg("\n")


	def makeDefaultContext(self):
		"""
		Make a very simple context for the newbie user to play with.
		"""
		if self._sample is not None:
			self.msg("Creating default context.")
			name = os.path.join(self._workDir, self._sample)
			if not os.path.exists(name):
				os.mkdir(name)
			name2 = os.path.join(name, 'Main.py')
			open(name2, "w").write(_Main_py % self._substVals)
			name2 = os.path.join(name, '__init__.py')
			open(name2, "w").write(_init_py)

			self.msg("Updating config for default context.")
			filename = os.path.join(self._workDir, "Configs", "Application.config")
			content = open(filename).readlines()
			output  = open(filename, "wt")
			for line in content:
				pos = string.find(line, "##MAWD")
				if pos != -1:
					line = "\t\t\t\t\t\t\t '%(CTX)s':     '%(CTX)s',\n"\
							"\t\t\t\t\t\t\t 'default':       '%(CTX)s',\n"\
							% {'CTX' : self._sample}

				output.write(line)
		self.msg("\n")

	def makeLibrary(self):
		print "Creating lib/ library directory."
		os.mkdir(os.path.join(self._workDir, 'lib'))
		f = open(os.path.join(self._workDir, 'lib', '__init__.py'), 'w')
		f.write('#')
		f.close()

	def addCVSIgnore(self):
		print "Creating .cvsignore files."
		files = {'.': '*.pyc\naddress.*\nhttpd.*\nappserverpid.*',
			 'Cache': '[a-zA-Z0-9]*',
			 'ErrorMsgs': '[a-zA-Z0-9]*',
			 'Logs': '[a-zA-Z0-9]*',
			 'Sessions': '[a-zA-Z0-9]*',
			 self._sample: '*.pyc',
			 }
		if self._makeLibrary:
			files['lib'] = '*.pyc'
		for dir, contents in files.items():
			filename = os.path.join(self._workDir, dir, '.cvsignore')
			f = open(filename, 'w')
			f.write(contents)
			f.close()


	def printCompleted(self):
		print """\n\n
Congratulations, you've just created a runtime working directory for
Webware.  To start the app server you can run these commands:

	cd %(WORKDIR)s
	./AppServer

Copy WebKit.cgi to your web server's cgi-bin directory, or
anywhere else that it will execute CGIs from.  Then point your browser
to http://localhost/cgi-bin/WebKit.cgi/ .  The page you
see is generated from the code in the %(DEFAULT)s directory and is
there for you to play with and to build upon.

If you see import errors, then you may need to modify the permissions
on your Webware directory so that the WebKit.cgi script can
access it.

There are also several adapters in the Webware/WebKit directory that
allow you to connect from the web server to the WebKit AppServer
without using CGI.

Have fun!
""" % self._substVals


	def msg(self, text):
		if self._verbose:
			print text





#----------------------------------------------------------------------
# A template for the launcher script

_Launch_py = """\
#!%(executable)s

import os, sys

webwarePath = '%(WEBWARE)s'
appWorkPath = '%(WORKDIR)s'
%(libraryPath)s

def main(args):
	global webwarePath, appWorkPath
	newArgs = []
	for arg in args:
		if arg.startswith('--webware-path='):
			webwarePath = arg[15:]
		elif arg.startswith('--working-path='):
			appWorkPath = arg[15:]
		else:
			newArgs.append(arg)
	args = newArgs
	# ensure Webware is on sys.path
	sys.path.insert(0, webwarePath)

	# import the master launcher
	import WebKit.Launch

	if len(args) < 2:
		WebKit.Launch.usage()

	# Go!
	WebKit.Launch.launchWebKit(args[1], appWorkPath, args[2:])


if __name__=='__main__':
	main(sys.argv)
"""

#----------------------------------------------------------------------
# A template for the NTService script

_NTService_py = """\
import os, re, sys, win32serviceutil

# settings
appWorkPath = '%(WORKDIR)s'
webwarePath = '%(WEBWARE)s'
serviceName = 'WebKit'
serviceDisplayName = 'WebKit App Server'

# ensure Webware is on sys.path
sys.path.insert(0, webwarePath)

# Construct customized version of ThreadedAppServerService that uses our
# specified service name, service display name, and working dir
from WebKit.ThreadedAppServerService import ThreadedAppServerService
class NTService(ThreadedAppServerService):
	_svc_name_ = serviceName
	_svc_display_name_ = serviceDisplayName
	def workDir(self):
		return appWorkPath

# Handle the command-line args
if __name__=='__main__':
	win32serviceutil.HandleCommandLine(NTService)
"""

#----------------------------------------------------------------------
# This is used to create a very simple sample context for the new
# work dir to give the newbie something easy to play with.

_init_py = """
def contextInitialize(appServer, path):
	# You could put initialization code here to be executed when
	# the context is loaded into WebKit.
	pass
"""

_Main_py = """
from WebKit.Page import Page

class Main(Page):

	def title(self):
		return 'My Sample Context'

	def writeContent(self):
		self.writeln('<h1>Welcome to Webware!</h1>')
		self.writeln('''
		This is a sample context generated for you and has purposly been kept very simple
		to give you something to play with to get yourself started.  The code that implements
		this page is located in <b>%%s</b>.
		''' %% self.request().serverSidePath())

		self.writeln('''
		<p>
		There are more examples and documentaion in the Webware distribution, which you
		can get to from here:<p><ul>
		''')

		adapterName = self.request().adapterName()
		ctxs = self.application().contexts().keys()
		ctxs = filter(lambda ctx: ctx!='default', ctxs)
		ctxs.sort()
		for ctx in ctxs:
			self.writeln('<li><a href="%%s/%%s/">%%s</a>' %% (adapterName, ctx, ctx))

		self.writeln('</ul>')

"""

#----------------------------------------------------------------------


if __name__ == "__main__":
	targetDir = None
	contextName = 'MyContext'
	addCVSIgnore = 0
	makeLibrary = 0
	args = sys.argv[1:]
	# lame little command-line handler
	while args:
		if args[0] == '--cvsignore':
			addCVSIgnore = 1
			args = args[1:]
			continue
		if args[0] == '-c':
			if len(args) < 2:
				print __doc__
				sys.exit(1)
			contextName = args[1]
			args = args[2:]
			continue
		if args[0] in ['-l', '--library']:
			makeLibrary = 1
			args = args[1:]
			continue
		if not targetDir and not args[0].startswith('-'):
			targetDir = args[0]
			args = args[1:]
			continue
		# Must be an error:
		print "Unknown option: %s" % args[0]
		print __doc__
		sys.exit(1)
	if not targetDir:
		print __doc__
		sys.exit(1)

	# this assumes that this script is still located in Webware/bin
	p = os.path
	webWareDir = p.abspath(p.join(p.dirname(sys.argv[0]), ".."))

	mawd = MakeAppWorkDir(webWareDir, targetDir,
	                      sampleContext=contextName,
			      addCVSIgnore=addCVSIgnore,
			      makeLibrary=makeLibrary)
	mawd.buildWorkDir()

