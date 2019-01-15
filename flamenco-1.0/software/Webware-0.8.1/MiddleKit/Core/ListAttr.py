from Attr import Attr


class ListAttr(Attr):
	"""
	This is an attribute that refers to a set of other user-defined objects.
	It cannot include basic data types or instances of classes that are not part of the object model.
	"""

	def __init__(self, dict):
		Attr.__init__(self, dict)
		self._className = dict['Type'].split()[-1]
		# @@ 2000-11-25 ce: check that the class really exists
		
	def className(self):
		""" Returns the name of the base class that this obj ref attribute points to. """
		return self._className
