#!/usr/bin/env python
"""
TestDesign.py
"""

from TestCommon import *
from MiddleKit.Design.Generate import Generate
from MiddleKit.Core.Model import Model


def importPyClasses(klasses):
	# See if we can import all of the classes
	print 'importing classes:', ', '.join(klasses.keys())
	for klassName in klasses.keys():
		code = 'from %s import %s\n' % (klassName, klassName)
		#sys.stdout.write(code)
		results = {}
		exec code in results
		assert results.has_key(klassName)


def test(modelFilename, workDir=workDir, toTestDir='../'):
	"""
	modelFilename: the correct filename to the existing model
	workDir:       the directory to remove and create and then put the
	               generated files in
	toTestDir:     a relative path to get from inside the workDir back
	               to the MiddleKit/Tests dir

	In most cases, the defaults for workDir and toTestDir are
	sufficient.	In funkalicious cases, like the MKMultipleStores test,
	overriding these defaults comes in handy.
	"""
	rmdir(workDir)     # get rid of files from previous runs
	os.mkdir(workDir)  # make a space for the files from this run

	# Run generate, load the model, and import some classes
	Generate().main('Generate.py --outdir %s --db MySQL --model %s' % (workDir, modelFilename))
	curDir = os.getcwd()
	os.chdir(workDir)
	try:
		model = Model(toTestDir+modelFilename)
		importPyClasses(model.klasses())
		return model
	finally:
		os.chdir(curDir)


if __name__=='__main__':
	try:
		test(sys.argv[1])
	except:
		import traceback
		exc_info = sys.exc_info()
		traceback.print_exception(*exc_info)
		print '>> ABOUT TO EXIT WITH CODE 1'
		sys.exit(1)
