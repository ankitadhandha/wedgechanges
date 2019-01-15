#!/usr/bin/env python
from TestCommon import *
from MiddleKit.Run.MySQLObjectStore import MySQLObjectStore
import MiddleKit.Run.ObjectStore as ObjectStore


def test(filename, pyFilename, deleteData):
	curDir = os.getcwd()
	os.chdir(workDir)
	try:
		filename = '../'+filename

		if os.path.splitext(filename)[1]=='':
			filename += '.mkmodel'
		pyFilename = os.path.join(filename, pyFilename)
		if not os.path.exists(pyFilename):
			print 'No such file', pyFilename
			return

		print 'Testing %s...' % filename

		# Set up the store
		store = MySQLObjectStore()
		store.readModelFileNamed(filename)
		assert store.model()._havePythonClasses # @@@@@@

		# Clear the database
		if deleteData:
			print 'Deleting all database records for test...'
			for klass in store.model().klasses().values():
				if not klass.isAbstract():
					ObjectStore.Store.executeSQL('delete from %s;' % klass.name())

		# Run the test
		results = {}
		execfile(pyFilename, results)
		assert results.has_key('test'), 'No test defined in %s.' % filename
		results['test'](store)
	finally:
		os.chdir(curDir)

def usage():
	print 'TestRun.py <model> <py file> [delete=0|1]'
	print
	sys.exit(1)

def main():
	if len(sys.argv)<3:
		usage()

	modelFilename = sys.argv[1]
	pyFilename = sys.argv[2]
	deleteData = 1

	if len(sys.argv)==4:
		delArg = sys.argv[3]
		parts = delArg.split('=')
		if len(parts)!=2 or parts[0]!='delete':
			usage()
		try:
			deleteData = int(parts[1])
		except:
			usage()
	elif len(sys.argv)>4:
		usage()

	test(modelFilename, pyFilename, deleteData)


if __name__=='__main__':
	try:
		main()
	except:
		import traceback
		exc_info = sys.exc_info()
		traceback.print_exception(*exc_info)
		#print '>> ABOUT TO EXIT WITH CODE 1'
		sys.exit(1)
