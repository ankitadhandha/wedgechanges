#!/usr/bin/env python
import os, sys
from TestCommon import *
from glob import glob


class Test:

	## Init ##

	def __init__(self):
		pass


	## Customization ##

	def cmdLineDB(self):
		""" Returns the database command used for feeding SQL to the database via stdin. """
		return 'mysql'

	def modelNames(self):
		return self._modelNames


	## Testing ##

	def main(self, args=sys.argv):
		# We explicitly list the tests rather than scanning for them (via glob) in order to perform them in a certain order (simplest to most complex)
		self.readArgs(args)
		for self._modelName in self.modelNames():
			print '*** %s ***\n' % self._modelName
			if not self._modelName.endswith('.mkmodel'):
				self._modelName += '.mkmodel'
			self.testDesign()
			self.testEmpty()
			self.insertSamples()
			self.testSamples()
			rmdir(workDir)
			print '\n'

	def readArgs(self, args):
		if len(args)>1:
			self._modelNames = args[1:]
		else:
			self._modelNames = '''
				MKBasic MKNone MKString MKDateTime MKDefaultMinMax
				MKTypeValueChecking MKInheritance MKInheritanceAbstract
				MKList MKObjRef MKObjRefReuse MKDelete MKDeleteMark
				MKMultipleStores MKMultipleThreads
				MKModelInh1 MKModelInh2 MKModelInh3
			'''.split()

	def testEmpty(self):
		"""
		Run all TestEmpty*.py files in the model, in alphabetical order by name.
		"""
		names = glob(os.path.join(self._modelName, 'TestEmpty*.py'))
		if names:
			names.sort()
			for name in names:
				self.createDatabase()
				self.testRun(os.path.basename(name), deleteData=0)
		else:
			self.createDatabase()

	def testSamples(self):
		self.testRun('TestSamples.py', deleteData=0)

	def testRun(self, pyFile, deleteData):
		if os.path.exists(os.path.join(self._modelName, pyFile)):
			print '%s:' % pyFile
			self.run('python TestRun.py %s %s delete=%i' % (self._modelName, pyFile, deleteData))
		else:
			print 'NO %s TO TEST.' % pyFile

	def testDesign(self):
		self.run('python TestDesign.py %s' % self._modelName)

	def createDatabase(self):
		filename = workDir + '/GeneratedSQL/Create.sql'
		filename = os.path.normpath(filename)
		cmd = '%s < %s' % (self.cmdLineDB(), filename)
		self.run(cmd)

	def insertSamples(self):
		self.createDatabase()
		filename = workDir + '/GeneratedSQL/InsertSamples.sql'
		filename = os.path.normpath(filename)
		if os.path.exists(filename):
			cmd = '%s < %s' % (self.cmdLineDB(), filename)
			self.run(cmd)


	## Self utility ##

	def run(self, cmd):
		""" Self utility method to run a system command. """
		print '<cmd>', cmd
		sys.stdout.flush()
		sys.stderr.flush()
		returnCode = os.system(cmd)
		sys.stdout.flush()
		sys.stderr.flush()

		# @@ 2001-02-02 ce: we have a problem, at least on Windows ME,
		# that the return code of os.system() is always 0, even if
		# the program was a Python program exited via sys.exit(1)
		#print '>> RETURN CODE =', returnCode


if __name__=='__main__':
	Test().main()
