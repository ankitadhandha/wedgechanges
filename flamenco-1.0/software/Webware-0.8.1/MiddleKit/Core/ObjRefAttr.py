from Attr import Attr


def objRefJoin(klassId, serialNum):
	""" Given a klass id and object serial number, returns a 64-bit obj ref value (e.g., a long). """
	return (long(klassId)<<32) | long(serialNum)

def objRefSplit(objRef):
	""" Returns a tuple with (klassId, serialNum) given the 64-bit (e.g., long type) objRef. """
	return ((objRef & 0xFFFFFFFF00000000L) >> 32, objRef & 0xFFFFFFFFL)


class ObjRefAttr(Attr):
	"""
	This is an attribute that refers to another user-defined object.
	For a list of objects, use ListAttr.
	"""

	def __init__(self, dict):
		Attr.__init__(self, dict)
		self._className = dict['Type']

	def className(self):
		""" Returns the name of the base class that this obj ref attribute points to. """
		return self._className
