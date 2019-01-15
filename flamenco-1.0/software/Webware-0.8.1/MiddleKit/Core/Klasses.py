from ModelObject import ModelObject
from Model import Model
from Klass import Klass
from Attr import Attr
from MiscUtils.DataTable import DataTable
from MiscUtils.DictForArgs import *
from UserDict import UserDict
from types import *
import os


class Klasses(ModelObject, UserDict):
	"""
	A Klasses object can read a list of class specifications in a spreadsheet (.csv).

	Note that Klasses inherits UserDict, allowing you to access class specifications by name.
	"""


	## Init ##

	def __init__(self, model):
		UserDict.__init__(self)

		assert isinstance(model, Model)
		self._model         = model
		self._klasses       = []
		self._filename      = None
		self._name          = None
		self._tableHeadings = None

		self.initTypeMap()


	def classNames(self):
		return ['ModelObject', 'Klasses', 'Klass', 'Attr', 'BasicTypeAttr', 'ObjRefAttr', 'EnumAttr', 'DateTimeAttr']


	def initTypeMap(self):
		"""
		Initializes self._typeNamesToAttrClassNames which maps MiddleKit type names (like int and enum) to the name of the attribute class that would implement them.
		Mapping to class names rather than actual classes is key, because in __init__, a different set of attribute classes can be passed in.
		"""
		map = {}

		names = 'bool int long float string enum date time list ObjRef decimal'
		names = names.split()
		for name in names:
			map[name] = name.capitalize()+'Attr'

		map['datetime'] = 'DateTimeAttr'

		self._typeNamesToAttrClassNames = map


	## Accessing ##

	def filename(self):
		return self._filename

	def klassesInOrder(self):
		""" Returns a list of all the Klasses in the order they were declared. Do not modify the list. """
		return self._klasses


	## Reading files ##

	def read(self, filename):
		# @@ 2000-11-24 ce: split into readTable()
		self._filename = filename
		table = DataTable(filename, usePickleCache=0)  # because PickleCache is used at the Model level
		# in case we want to look at these later:
		self._tableHeadings = table.headings()

		for row in table:
			row = ExpandDictWithExtras(row, dictForArgs=PyDictForArgs)
			for key in ['Class', 'Attribute']:
				if not row.has_key(key):
					print 'ERROR'
					print 'Required key %s not found in row:' % key
					print 'row:', row
					print 'keys:', row.keys()
					print row[key]  # throws exception
			if row['Class']:
				pyClass = self._model.coreClass('Klass')
				klass = pyClass(self, row)
				self.addKlass(klass)
			else:
				name = row['Attribute']
				if name and name[0]!='#' and name[-1]!=':':
					pyClassName = self.pyClassNameForAttrDict(row)
					pyClass = self._model.coreClass(pyClassName)
					klass.addAttr(pyClass(row))

	def awakeFromRead(self):
		"""
		Performs further initialization.
		Expected to be invoked by the model.
		"""
		for klass in self._klasses:
			klass.awakeFromRead()

	def __getstate__(self):
		"""
		For pickling purposes, the back reference to the model that owns self is removed.
		"""
		assert self._model
		attrs = self.__dict__.copy()
		del attrs['_model']
		return attrs


	## Adding classes ##

	def addKlass(self, klass):
		""" Restrictions: Cannot add two classes with the same name. """
		name = klass.name()
		assert not self.has_key(name), 'Already have %s.' % name
		self._klasses.append(klass)
		self[klass.name()] = klass

		supername = klass.supername()
		if supername!='MiddleObject':
			klass.setSuperklass(self._model.klass(supername))

		klass.setKlasses(self)


	## Self utility ##

	def pyClassNameForAttrDict(self, dict):
		""" Given a raw attribute definition (in the form of a dictionary), this method returns the name of the Python class that should be instantiated for it. This method relies primarily on dict['Type']. """
		typeName = dict['Type']
		if not typeName:
			raise Exception, 'Blank type for dict: %s' % dict

		if typeName[0].upper()==typeName[0]:
			return 'ObjRefAttr'

		# to support "list of <class>":
		typeName = typeName.split()[0]

		try:
			return self._typeNamesToAttrClassNames[typeName]
		except IndexError:
			raise Exception, 'Unknown type %s.' % typeName


	## Debugging ##

	def dump(self):
		""" Prints each class. """
		for klass in self._klasses:
			print klass
