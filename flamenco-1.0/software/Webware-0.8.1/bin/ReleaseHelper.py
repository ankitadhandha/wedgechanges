#!/usr/bin/env python
"""
Helps with cutting Python releases.

This script creates a tar file named Webware-VER.tar.gz from a live CVS
workspace. The workspace is updated, but is not destroyed in the process.
The workspace should NOT have had install.py run on it, or your distro
will end up with generated docs.

To run:

  > ReleaseHelper.py

- The version number is taken from Webware/Properties.py like you would
  expect.
- You don't have to be in the current directory:
    > bin/ReleaseHelper.py
    > Webware/bin/ReleaseHelper.py
- This script only works on posix. Releases are not created on Windows
  because permissions and EOLs can be problematic for other platforms.

For more information, see the Release Procedures in the Webware docs.

TO DO

  - Using ProperitesObject, this program could suggest a version string
    from the Webware version.
"""

import os, sys, time


class ReleaseHelper:
	def __init__(self):
		self.args = { 'method' : 'export'
			}
	def main(self):
		self.writeHello()
		self.checkPlatform()
		self.readArgs()

		if self.args.get("method",None) == "export":
			return self.release_export()
		
		self.release_current()

	def release_current(self):

		progPath = os.path.join(os.getcwd(), sys.argv[0])  # the location of this script
		webwarePath = os.path.dirname(os.path.dirname(progPath))  # because we're in Webware/bin/
		parentPath = os.path.dirname(webwarePath)  # where the tarball will land

		self.chdir(webwarePath)

		if os.path.exists('_installed'):
			self.error('This Webware has already been installed.')

		from MiscUtils.PropertiesObject import PropertiesObject
		props = PropertiesObject(os.path.join(webwarePath, 'Properties.py'))
		ver = props['versionString']
		print 'Webware version is:', ver

		self.run('cvs update -dP')  # get new directories; prune empty ones

		try:
			tempName = os.tmpnam()
			os.mkdir(tempName)
			self.run('cp -pr %s %s' % (webwarePath, tempName))

			# Get rid of CVS files
			self.run("find %s -name '.cvs*' -exec rm {} \;" % tempName)
			self.run("rm -rf `find %s -name CVS -print`" % tempName)

			self.chdir(tempName)
			pkgName = 'Webware-%s.tar.gz' % ver
			self.run('tar czf %s Webware' % pkgName)

			# Put the results next to the Webware directory
			self.run('cp %s %s' % (pkgName, parentPath))

			assert os.path.exists(os.path.join(parentPath, pkgName))

		finally:
			# Clean up
			self.run('rm -rf %s' % tempName)

		self.writeGoodBye(locals())

	def release_export(self):
		"""
		Prepare a release by using the cvs export approach.  This means the release will
		match exactly what is in CVS, and reduces the risk of local changes, modified
		files, or new files which are not in CVS from showing up in the release.

		Furthermore, this takes the version number from the checked out information.
		This means it is possible to specify a tag=cvstag on the command line and
		build a release associated with that tag.

		    > ReleaseHelper.py [tag=cvstag]

	        So specifying a CVS tag such as Release-0_7 will export the CVS files tagged
		with Release-0_7 and build Webware-0.7.tar.gz
		"""
		
		self.writeHello()
		self.checkPlatform()
		self.readArgs()

		progPath = os.path.join(os.getcwd(), sys.argv[0])  # the location of this script
		webwarePath = os.path.dirname(os.path.dirname(progPath))  # because we're in Webware/bin/
		parentPath = os.path.dirname(webwarePath)  # where the tarball will land
		if webwarePath not in sys.path:
			# insert in the path but ahead of anything that PYTHONPATH might
			# have created.
			sys.path.insert(1,webwarePath)

		self.chdir(webwarePath)
		from MiscUtils.PropertiesObject import PropertiesObject

		if self.args.has_key('tag'):
			dtag = '-r ' + self.args['tag']
			datestamp = ''
		else:
			# timestamp for tomorrow to insure we get latest data off
			# of the trunk.  Is this needed?
			year,month,day = time.gmtime(time.time()+3600*24)[:3]  
			dtag = '-D %04d-%02d-%02d' % (year,month,day)

			# timestamp for time of release used to in versioning the file.
			year,month,day = time.localtime(time.time())[:3]  
			datestamp = "%04d%02d%02d" % (year,month,day)

			# drop leading 2 digits from year. (Ok, itn's not Y2K but it is short
			# and unique in a narrow time range of 100 years.)
			datestamp = datestamp[2:]
			
			print "No cvs tag specified, assuming snapshot of CVS."
			
		tempName = "ReleaseHelper-Export"
		if os.path.exists( tempName ):
			print "There is incomplete ReleaseHelper data in:", tempName
			print "Please remove this directory."
			return 1
		
		cleanup = [ tempName ]
		
		try:
			self.run('cvs -z3 export %s -d %s Webware' % (dtag, tempName))
			if not os.path.exists( tempName ):
				print "** Unable to find the exported package.  Perhaps the tag %s does not exist." % \
				      self.args['tag']
				return 1
			props = PropertiesObject(os.path.join(webwarePath, tempName, 'Properties.py'))
			ver = props['versionString']

			print "Webware version is:", ver
			if datestamp:
				ver = ver + "-" + datestamp
				print "Packaged release will be:", ver

			pkgDir = "Webware-%s" % ver
			
			if os.path.exists(pkgDir):
				print "** %s is in the way, please remove it." % pkgDir
				return

			# rename the tempName to the pkgDir so the extracted parent
			# directory from the tarball will be unique to this package.
			self.run("mv %s %s" % (tempName, pkgDir))
			
			cleanup.append( pkgDir )
			
			pkgName = os.path.join(parentPath, pkgDir + ".tar.gz")

			# cleanup .cvs files
			self.run("find %s -name '.cvs*' -exec rm {} \;" % pkgDir)

			# cleanup any other files not part of this release. (ie: documentation?)

			# build any internal documentation for release.
			
			self.run('tar czf %s %s' % (pkgName, pkgDir))

			assert os.path.exists(os.path.join(parentPath, pkgName))

		finally:
			# Clean up
			for path in cleanup:
				if os.path.exists(path):
					self.run('rm -rf %s' % os.path.join(webwarePath, path))
			 
		self.writeGoodBye(locals())

	def writeHello(self):
		print 'Webware for Python'
		print 'Release Helper'
		print

	def checkPlatform(self):
		if os.name!='posix':
			print 'This script only runs on posix. Your op sys is %s.' % os.name
			print 'Webware release are always created on posix machines.'
			print 'These releases work on both posix and MS Windows.'
			self.error()

	def readArgs(self):
		args = self.args.copy()     # initialize with default.
		for arg in sys.argv[1:]:
			try:
				name, value = arg.split('=')
			except ValueError:
				self.error('Invalid argument: %s' % arg)
			args[name] = value
		self.args = args

	def error(self, msg=''):
		if msg:
			print 'ERROR: %s' % msg
		sys.exit(1)

	def chdir(self, path):
		print 'chdir %s' % path
		os.chdir(path)

	def run(self, cmd):
		""" Runs an arbitrary UNIX command. """
		print 'cmd>', cmd
		results = os.popen(cmd).read()
		print results

	def writeGoodBye(self, vars):
		print
		print 'file: %(pkgName)s' % vars
		print 'dir:  %(parentPath)s' % vars
		print 'size: %i' % os.path.getsize(os.path.join(vars['parentPath'], vars['pkgName']))
		print
		print 'Success.'
		print


if __name__=='__main__':
	ReleaseHelper().main()
