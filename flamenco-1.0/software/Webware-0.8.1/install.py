#!/usr/bin/env python

"""
install.py
Webware for Python

FUTURE
	* Look for an install.py in each component directory and run it
	  (there's not a strong need right now).
	* Upon successful install, create "installed" file with info such
	  as date, time, py ver, etc. Maybe just put the output of this
	  in there.
"""


import os, string, sys, compileall
from time import time, localtime, asctime
from string import count, join, rfind, split, strip, replace
from glob import glob
from MiscUtils.PropertiesObject import PropertiesObject

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

MinimumVersionErrorMsg="""
!!! This Release of Webware requires Python %s.  Your current version
of Python is:
  %s.
Please go to http://www.python.org for the latest version of Python.
You may continue to install, but Webware may not perform as expected.
Do you wish to continue with the installation?  [yes/no]
"""

ThreadingEnabled = """
!!! Webware requires that Python be compiled with threading support.
This version of Python does not appear to support threading.  You may
continue, but you will have to run the AppServer with a Python
interpreter that has threading enabled.

Do you wish to continue with the installation? [yes/NO]
"""

class Installer:
	"""
	The _comps attribute is a list of components, each of which is an instance of MiscUtils.PropertiesObject.
	"""

	## Init ##

	def __init__(self):
		self._props = PropertiesObject('Properties.py')
		self._htHeader = self.htFragment('Header')
		self._htFooter = self.htFragment('Footer')
		self._comps = []

	## debug printing facility
	def _nop (self, msg): pass
	def _printMsg (self, msg): print msg


	## Running the installation ##

	def run(self, verbose=0, passprompt=1, defaultpass=''):
		self._verbose = verbose
		if self._verbose: self.printMsg = self._printMsg
		else: self.printMsg = self._nop
		self.clearInstalledFile()
		self.printHello()
		if not self.checkPyVersion(): return
		if not self.checkThreading(): return
		self.detectComponents()
		self.installDocs()
		self.backupConfigs()
		self.compileModules()
		self.fixPermissions()
		self.setupWebKitPassword(passprompt, defaultpass)
		self.finished()
		self.printGoodbye()
		return self

	def clearInstalledFile(self):
		"""
		Removes the _installed file which will get created at the very
		end of installation, provided there are no errors.
		"""
		if os.path.exists('_installed'):
			os.remove('_installed')

	def printHello(self):
		print '%(name)s %(versionString)s' % self._props
		print 'Installer'
		print
		self.printKeyValue('Date', asctime(localtime(time())))
		self.printKeyValue('Python ver', sys.version)
		self.printKeyValue('Op Sys', os.name)
		self.printKeyValue('Platform', sys.platform)
		self.printKeyValue('Cur dir', os.getcwd())
		print

	def checkPyVersion(self,minver=[2,0]):
		try:
			version_info = sys.version_info
		except:
			version_info=None
		if not version_info or version_info[0]<minver[0] or (version_info[0]==minver[0] and version_info[1]<minver[1]):
			minVersionString=str(minver[0])+"."+str(minver[1])
			response=raw_input( MinimumVersionErrorMsg % (minVersionString,sys.version))
			if response and string.upper(response)[0] == "Y":
				rtncode=1
			else:
				rtncode=0
		else:
			rtncode = 1
		return rtncode

	def checkThreading(self):
		try:
			import threading
		except ImportError:
			response=raw_input(ThreadingEnabled)
			if response and string.upper(response)[0] == "Y":
				return 1
			else:
				return 0
		return 1

	def detectComponents(self):
		print 'Scanning for components...'
		filenames = os.listdir('.')
		maxLen = max(filter(None, map(lambda name: os.path.isdir(name) and len(name), filenames)))
		count = 0
		needPrint = 0
		for filename in os.listdir('.'):
			if os.path.isdir(filename):
				propName = os.path.join(filename, 'Properties.py')
				displayName = string.ljust(filename, maxLen)
				if os.path.exists(propName):
					comp = PropertiesObject(propName)
					comp['filename'] = filename
					self._comps.append(comp)
					print '  yes', displayName,
				else:
					print '   no', displayName,
				if count%2==1:
					print
					needPrint = 0
				else:
					needPrint = 1
				count = count + 1
		if needPrint:
			print
		print
		self._comps.sort(lambda a, b: cmp(a['name'], b['name']))


	def setupWebKitPassword(self, prompt, defpass):
		""" Setup a password for WebKit Application server. """
		print 'Setting passwords...'
		print

		password = ''
		if defpass:
			if prompt:
				print 'Choose a Password for WebKit Application Server.'
				print 'If you will just press enter without entering anything,'
				print 'the password specified on the command-line will be used;'
				print 'you can check the password after installation at:'
				print 'WebKit/Configs/Application.config'
				import getpass
				password = getpass.getpass()
			else:
				print 'A password was specified on the command-line; check'
				print 'the file: WebKit/Configs/Application.config'
				print 'after installation for the password'

			if len(password) == 0:
				password = defpass
		else:
			if prompt:
				print 'Choose a Password for WebKit Application Server.'
				print 'If you will just press enter without entering anything'
				print 'a random password will be generated; you can check the password'
				print 'after installation at: WebKit/Configs/Application.config'
				import getpass
				password = getpass.getpass()
			else:
				print 'A password was autogenerated; check the file: ',
				print 'WebKit/Configs/Application.config'
				print 'after installation for the password'

			if len(password) == 0:
				# Generate 7 digits worth of a password.
				# The random function gives back a real number.
				characters = string.letters + string.digits

				import random
				for i in range(8):
					password = password + random.choice(characters)

		try:
			data = open('WebKit/Configs/Application.config', 'r').read()
		except IOError:
			print 'Error reading config file, possibly a permission problem,'
			print 'password not replaced, make sure to edit it by hand.'
			return

		# This will search for the construct:
		# 'AdminPassword': 'password'
		# and replace whatever password is written there with what is
		# given in the 'password' variable.
		pattern = "('AdminPassword'\s*:)\s*'.*?'"
		repl    = "\g<1>\t'%s'" % (password,)
		import re
		# Still need to verify that we actually found a match!
		data = re.sub(pattern, repl, data)

		try:
			open('WebKit/Configs/Application.config', 'w').write(data)
		except IOError:
			print 'Error writing config file, possibly a permission problem,'
			print 'password not replaced, make sure to edit it by hand.'
			return

		print 'Password replaced successfully.'

	def installDocs(self):
		self.propagateStyleSheet()
		self.processRawFiles()
		self.createBrowsableSource()
		self.createComponentIndex()
		self.createIndex()
		self.createComponentIndexes()

	def propagateStyleSheet(self):
		""" Copy Docs/StyleSheet.css and GenIndex.css into other Docs dirs. """
		print 'Propagating stylesheets...'
		for name in ['StyleSheet.css', 'GenIndex.css']:
			stylesheet = open('Docs/%s' % name, 'rb').read()
			for comp in self._comps:
				#print '  %s...' % comp['filename']
				target = os.path.join(comp['filename'], 'Docs', name)
				open(target, 'wb').write(stylesheet)
		print

	def processRawFiles(self):
		print 'Processing raw doc files...'
		self.requirePath('DocSupport')
		from RawToHTML import RawToHTML
		processor = RawToHTML()
		processor.main(['install.RawToHTML', 'Docs/*.raw'])
		print

	def createBrowsableSource(self):
		""" Create HTML documents for class hierarchies, summaries, source files, etc. """

		print 'Creating browsable source and summaries...'
		self.requirePath('DocSupport')

		for comp in self._comps:
			filename = comp['filename']
			print '  %s...' % filename

			sourceDir = '%s/Docs/Source' % filename
			self.makeDir(sourceDir)

			filesDir = sourceDir + '/Files'
			self.makeDir(filesDir)

			summariesDir = sourceDir + '/Summaries'
			self.makeDir(summariesDir)

			docsDir = sourceDir + '/Docs'  # @@ 2000-08-17 ce: Eventually for pydoc/gendoc
			#self.makeDir(docsDir)

			for pyFilename in glob('%s/*.py' % filename):
				self.createHighlightedSource(pyFilename, filesDir)
				self.createSummary(pyFilename, summariesDir)
				#self.createDocs(pyFilename, docsDir)  # @@ 2000-08-17 ce: Eventually for pydoc/gendoc

			self.createBrowsableClassHier(filename, sourceDir)
			#self.createBrowsableFileList(filename, sourceDir)
		print

	def createHighlightedSource(self, filename, dir):
		import py2html
		targetName = '%s/%s.html' % (dir, os.path.basename(filename))
		self.printMsg('    Creating %s...' % targetName)
		realout = sys.stdout
		sys.stdout = StringIO()
#		py2html.main([None, '-stdout', '-format:rawhtml', '-files', filename])
		py2html.main([None, '-stdout', '-files', filename])
		result = sys.stdout.getvalue()
		result = replace(result, '\t', '    ')  # 4 spaces per tab
		open(targetName, 'w').write(result)
		sys.stdout = realout

	def createSummary(self, filename, dir):
		from PySummary import PySummary
		targetName = '%s/%s.html' % (dir, os.path.basename(filename))
		self.printMsg('    Creating %s...' % targetName)
		sum = PySummary()
		sum.readConfig('DocSupport/PySummary.config')
		sum.readFileNamed(filename)
		html = sum.html()
		open(targetName, 'w').write(html)

	def createDocs(self, filename, dir):
		from PySummary import PySummary
		targetName = '%s/%s.html' % (dir, os.path.basename(filename))
		self.printMsg('    Creating %s...' % targetName)
		# @@ 2000-08-17 ce: use something like pydoc or gendoc here
		raise NotImplementedError

	def createBrowsableClassHier(self, filesDir, docsDir):
		""" Create HTML class hierarchy listings of the source files. """
		from classhier import ClassHier

		classHierName = os.path.join(os.getcwd(), docsDir, 'ClassHier.html')
		listName = os.path.join(os.getcwd(), docsDir, 'ClassList.html')
		saveDir = os.getcwd()
		os.chdir(filesDir)
		try:
			ch = ClassHier()
			# @@ 2000-08-17 ce:  whoa! look at that hard-coding!
			ch.addFilesToIgnore(['zCookieEngine.py', 'WebKitSocketServer.py', '_on_hold_HierarchicalPage.py', 'fcgi.py'])
			ch.readFiles('*.py')
			ch.printHierForWeb(classHierName)
			ch.printListForWeb(listName)
		finally:
			os.chdir(saveDir)

	def createBrowsableFileList(self, filesDir, docsDir):
		""" Create HTML list of the source files. """
		# @@ 2000-08-18 ce: not yet
		fullnames = glob('%s/*.py' % filesDir)
		filenames = map(lambda filename: os.path.basename(filename), fullnames)
		filenames.sort()
		ht = []
		ht.append('<table cellpadding=2 cellspacing=0 style="font-family: Arial, Helvetica, sans-serif; font-size: 14;">\n')
		for filename in filenames:
			ht.append('<tr> <td> summary </td> <td> source </td> <td> %s </td> </tr>' % filename)
		ht.append('</table>')
		ht = string.join(ht, '')
		open(docsDir+'/FileList.html', 'w').write(ht)

	def backupConfigs(self):
		""" Copies *.config to *.config.default, if the .default files don't already exist. This allows the user to always go back to the default config file if needed (for troubleshooting for example). """
		print 'Backing up original config files...'
		print '   ',
		self._backupConfigs(os.curdir)
		print

	def _backupConfigs(self, dir):
		wr = sys.stdout.write
		for filename in os.listdir(dir):
			fullPath = os.path.join(dir, filename)
			if os.path.isdir(fullPath):
				self._backupConfigs(fullPath)
			elif filename[0]!='.' and \
					os.path.splitext(filename)[1]=='.config':
				backupName = fullPath + '.default'
				if not os.path.exists(backupName):
					contents = open(fullPath, 'rb').read()
					open(backupName, 'wb').write(contents)
					del contents
					wr('.')
				else:
					wr('-')
				sys.stdout.flush()

	def compileModules(self):
		import StringIO
		print """Byte compiling all modules\n------------------------------------------\n"""
		stdout = sys.stdout
		stderr = sys.stderr
		sys.stdout = StringIO.StringIO() #the compileall is a little verbose
		sys.stderr = StringIO.StringIO()
		compileall.compile_dir(".", 10, '', 1)
		sys.stdout = stdout
		sys.stderr = stderr
		print "\n\n"

	def fixPermissions(self):
		if os.name=='posix':
			print 'Setting permissions on CGI scripts...'
			for comp in self._comps:
				#print '  %s...' % comp['name']
				for filename in glob('%s/*.cgi' % comp['filename']):
					#self.printMsg('    %s...' % os.path.basename(filename))
					cmd = 'chmod a+rx %s' % filename
					print '  %s' % cmd
					os.system(cmd)
			print

	def createComponentIndex(self):
		print 'Creating ComponentIndex.html...'
		ht = []
		wr = ht.append
		wr("Don't know where to start? Try <a href=../WebKit/Docs/index.html>WebKit</a>. <p>")
		wr('<table align=center border=0 cellpadding=2 cellspacing=2 width=100%>')
		wr('<tr class=ComponentHeadings> <td nowrap>Component</td> <td>Status</td> <td>Ver</td> <td nowrap>Py ver</td> <td>Summary</td> </tr>')
		row = 0
		for comp in self._comps:
			comp['nameAsLink'] = '<a href=../%(filename)s/Docs/index.html>%(name)s</a>' % comp
			comp['indexRow'] = row+1
			wr('''\
<tr valign=top class=ComponentRow%(indexRow)i>
	<td class=NameVersionCell> <span class=Name>%(nameAsLink)s</span>
	<!-- <br><span class=Version>%(versionString)s</span>-->
	</td>
	<td> %(status)s </td>
	<td> <span class=Version>%(versionString)s</span> </td>
	<td> %(requiredPyVersionString)s </td>
	<td> %(synopsis)s </td>
</tr>''' % comp)
			row = (row+1)%2  # e.g., 1, 2, 1, 2, ...
		wr('</table>')
		ht = string.join(ht, '\n')
		self.writeDocFile('Webware Component Index', 'Docs/ComponentIndex.html', ht, extraHead='<link rel=stylesheet href=ComponentIndex.css type=text/css>')

	def createIndex(self):
		print 'Creating index.html...'
		ht = self.htFragment('index')
		ht = ht % self._props
		self.writeDocFile('Webware Documentation', 'Docs/index.html', ht, extraHead='<link rel=stylesheet href=GenIndex.css type=text/css>')

		# @@ 2000-12-23 Uh, we sneak in Copyright.html here until
		# we have a more general mechanism for adding the header
		# and footer to various documents
		ht = self.htFragment('Copyright')
		self.writeDocFile('Webware Copyright et al', 'Docs/Copyright.html', ht)

		# @@ 2001-03-11 ce: Uh, we sneak in RelNotes.html here, as well
		ht = self.htFragment('RelNotes')
		self.writeDocFile('Webware Release Notes', 'Docs/RelNotes.html', ht)


	def createComponentIndexes(self):
		print "Creating components' index.html..."
		indexFrag = self.htFragment('indexOfComponent')
		link = '<a href=%s>%s</a> <br>\n'
		for comp in self._comps:
			comp['webwareVersion'] = self._props['version']
			comp['webwareVersionString'] = self._props['versionString']

			# Create 'htDocs' as a readable HTML version comp['docs']
			ht = []
			for doc in comp['docs']:
				ht.append(link % (doc['file'], doc['name']))
			ht = string.join(ht, '')
			comp['htDocs'] = ht

			# Set up release notes
			ht = []
			releaseNotes = glob(os.path.join(comp['filename'], 'Docs', 'RelNotes-*.html'))
			if releaseNotes:
#				releaseNotes = [{'filename': os.path.basename(filename)} for filename in releaseNotes]
				results = []
				for filename in releaseNotes:
					results.append({'filename': os.path.basename(filename)})
				releaseNotes = results

				for item in releaseNotes:
					filename = item['filename']
					item['name'] = filename[string.rfind(filename,'-')+1:string.rfind(filename,'.')]
				releaseNotes.sort(self.sortReleaseNotes)
				for item in releaseNotes:
					ht.append(link % (item['filename'], item['name']))
			else:
				ht.append('None\n')
			ht = string.join(ht, '')
			comp['htReleaseNotes'] = ht

			# Write file
			title = comp['name'] + ' Documentation'
			filename = os.path.join(comp['filename'], 'Docs', 'index.html')
			contents = indexFrag % comp
			cssLink = '<link rel=stylesheet href=GenIndex.css type=text/css>'
			self.writeDocFile(title, filename, contents, extraHead=cssLink)

	def finished(self):
		"""
		This method is invoked just before printGoodbye().
		It writes the _installed file to disk.
		"""
		open('_installed', 'w').write('This file is written upon successful installation.\nLeave this file in place.\n')

	def printGoodbye(self):
		print '''
Installation looks successful.

Welcome to Webware!

You can find more information at:
  * Docs/index.html  (e.g., local docs)
  * http://webware.sourceforge.net

Installation is finished.'''


	## Self utility ##

	def printKeyValue(self, key, value):
		# Handle values with line breaks by indenting extra lines
		value = str(value)
		value = string.replace(value, '\n', '\n'+' '*14)

		print '%12s: %s' % (key, value)

	def makeDir(self, dirName):
		if not os.path.exists(dirName):
			self.printMsg('    Making %s...' % dirName)
			os.mkdir(dirName)

	def requirePath(self, path):
		if path not in sys.path:
			sys.path.insert(1, path)

	def sortReleaseNotes(self, a, b):
		""" Used by createComponentIndexes(). You pass this to list.sort(). """
		# We append '.0' below so that values like 'x.y' and 'x.y.z'
		# compare the way we want them too (x.y.z is newer than x.y)
		a = a['name']
		if string.count(a, '.')==1:
			a = a + '.0'
		b = b['name']
		if string.count(b, '.')==1:
			b = b + '.0'
		return -cmp(a, b)

	def htFragment(self, name):
		""" Returns an HTML fragment with the given name. """
		return open(os.path.join('Docs', name+'.htmlf')).read()

	def writeDocFile(self, title, filename, contents, extraHead=''):
		values = locals()
		file = open(filename, 'w')
		file.write(self._htHeader % values)
		file.write(contents)
		file.write(self._htFooter % values)
		file.close()


def printHelp():
	print 'Usage: install.py [options]'
	print 'Install WebWare in the local directory.'
	print
	print '  -h, --help                  This help screen'
	print '  -v, --verbose               Print extra information messages during install'
	print '  --password-prompt=yes/no    Do not prompt for password during install'
	print '                              Will autogenerate a random password'
	print '  --set-password=password     Set the password, if you follow it with'
	print '                              --password-prompt=yes it will be used as a default'

if __name__=='__main__':
	import getopt
	verbose=0
	passprompt=1
	defaultpass=''
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "verbose", "password-prompt=", "set-password="])
	except getopt.GetoptError:
		printHelp()
	else:
		for o, a in opts:
			if o in ("-v", "--verbose"): verbose=1
			if o in ("--password-prompt",):
				if a in ("1", "yes", "true"):
					passprompt=1
				elif a in ("0", "no", "false"):
					passprompt=0
			if o in ("--set-password",):
				defaultpass=a
				passprompt=0
			if o in ("-h", "--help", "h", "help"):
				printHelp()
				sys.exit(0)

		Installer().run(verbose=verbose, passprompt=passprompt, defaultpass=defaultpass)
