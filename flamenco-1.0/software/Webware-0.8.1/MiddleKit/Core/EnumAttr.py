from Attr import Attr


class EnumAttr(Attr):

	def __init__(self, dict):
		Attr.__init__(self, dict)
		# We expect than an 'Enums' key holds the enumeration values
		enums = self['Enums']
		enums = enums.split(',')
		enums = [enum.strip() for enum in enums]
		self._enums = enums
		set = {}
		for enum in self._enums:
			set[enum] = 1
		self._enumSet = set

	def enums(self):
		return self._enums

	def hasEnum(self, name):
		return self._enumSet.has_key(name)
