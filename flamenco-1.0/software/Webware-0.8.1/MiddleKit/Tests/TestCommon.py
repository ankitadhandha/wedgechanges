"""
TestCommon.py

This is just a convenience module for the various test modules (TestFoo.py).
"""


import os, string, sys, time
import FixPath
import MiscUtils
import MiddleKit
from MiddleKit.Core.Klasses import Klasses

workDir = 'WorkDir'

def rmdir(dirname, shouldPrint=1):
	""" Really remove the directory, even if it has files (and directories) in it. """
	if shouldPrint:
		print 'Removing %s...' % dirname
	if os.path.exists(dirname):
		exceptions = (os.curdir, os.pardir)
		for name in os.listdir(dirname):
			if name not in exceptions:
				fullName = os.path.join(dirname, name)
				if os.path.isdir(fullName):
					rmdir(fullName, shouldPrint=0)
				else:
					os.remove(fullName)
		os.rmdir(dirname)
