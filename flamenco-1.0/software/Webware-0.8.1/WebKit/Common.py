"""
The Common module provides some commmon globals to all modules/classes in
WebKit. It's intended for internal use, not for modules outside the WebKit.

Typically usage is:

	from Common import *

The globals provided are:
	* the modules, os, string, sys and time
	* the root class, Object
	* the package WebUtils
	* the class AbstractError, an exception that methods in abstract classes often raise.
"""


import os, string, sys, time

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

from Object import Object
import WebUtils
from MiscUtils import NoDefault
from MiscUtils import AbstractError


# @@ 2000-05-10 ce: Consider if all the following should be located in MiscUtils

def asclocaltime():
	""" Returns a readable string of the current, local time. Useful for time stamps in log files. """
	return time.asctime(time.localtime(time.time()))


# @@ 2002-11-10 ce: Tombstone is now deprecated (post 0.7)
Tombstone = NoDefault
