import os, sys

try:
	import MiscUtils
except:
	# When the Webware tarball unravels,
	# the components sit next to each other
	sys.path.append(os.path.abspath('..'))
	import MiscUtils
from MiscUtils.NamedValueAccess import NamedValueAccess


class Object(NamedValueAccess):
	"""
	Object is the root class for all classes in the WebKit.

	This is a placeholder for any future functionality that might be appropriate
	for all objects in the framework.
	"""

	def __init__(self):
		""" Initializes the object. Subclasses should invoke super. """
		pass

	def deprecated(self, method):
		"""
		The implementation of WebKit sometimes invokes this method which prints a warning that the method you are using has been deprecated.
		This method expects that deprecated methods say so at the beginning of their doc string and terminate that msg with @.
		For example:

			DEPRECATED: Class.foo() on 01/24/01 in ver 0.5. Use Class.bar() instead. @

		Putting this information in the doc string is important for accuracy in the generated docs.

		Example call:
			self.deprecated(self.foo)
		"""
		import string
		docString = method.__doc__
		if not docString:
			msg = 'DEPRECATED: %s, (no doc string)' % method
		else:
			msg = string.strip(string.split(method.__doc__, '@')[0])
		print msg


	# 2000-05-21 ce: Sometimes used for debugging:
	#
	#def __del__(self):
	#	print '>> del', self
