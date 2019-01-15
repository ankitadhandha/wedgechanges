import os, sys
from types import ClassType, DictType
from MiscUtils.Configurable import Configurable
from MiscUtils import NoDefault
try:
	from cPickle import load, dump
except ImportError:
	from pickle import load, dump


class Model(Configurable):
	"""
	A Model defines the classes, attributes and enumerations of an application.

	It also provides access to the Python classes that implement these structures for use by other MiddleKit entities including code generators and object stores.
	"""

	pickleVersion = 1
		# increment this if a non-compatible change is made in Klasses,
		# Klass or Attr

	def __init__(self, filename=None, customCoreClasses={}, rootModel=None, havePythonClasses=1):
		Configurable.__init__(self)
		self._havePythonClasses = havePythonClasses
		self._filename = None
		self._coreClasses = customCoreClasses
		self._klasses = None
		self._parents = []  # e.g., parent models
		self._pyClassForName = {}

		# _allModelsByFilename is used to avoid loading the same parent model twice
		if rootModel:
			self._allModelsByFilename = rootModel._allModelsByFilename
		else:
			self._allModelsByFilename = {}
		self._rootModel = rootModel

		if filename!=None:
			self.read(filename)

	def name(self):
		if self._name is None:
			if self._filename:
				self._name = os.path.splitext(os.path.basename(self._filename))[0]
			else:
				self._name = 'unnamed-mk-model'
		return self._name

	def setName(self, name):
		self._name = name

	def filename(self):
		return self._filename

	def read(self, filename):
		assert self._filename is None, 'Cannot read twice.'
		# Assume the .mkmodel extension if none is given
		if os.path.splitext(filename)[1]=='':
			filename += '.mkmodel'
		self._filename = os.path.abspath(filename)
		self._name = None
		self.readParents()
		self.readKlasses()
		self.awakeFromRead()

	def readKlasses(self):
		"""
		Reads the Classes.csv file, or the Classes.pickle.cache file as
		appropriate.
		"""
		csvPath = os.path.join(self._filename, 'Classes.csv')
		if not os.path.exists(csvPath):
			open(csvPath) # to get a properly constructed IOError

		# read the pickled version of Classes if possible
		data = None
		shouldUseCache = self.setting('UsePickledClassesCache', 1)
		if shouldUseCache:
			from MiscUtils.PickleCache import readPickleCache, writePickleCache
			data = readPickleCache(csvPath, pickleVersion=1, source='MiddleKit')

		# read the regular file if necessary
		if data is None:
			self.klasses().read(csvPath)
			if shouldUseCache:
				writePickleCache(self._klasses, csvPath, pickleVersion=1, source='MiddleKit')
		else:
			self._klasses = data
			self._klasses._model = self

	def __getstate__(self):
		raise Exception, 'Model instances were not designed to be pickled.'

	def awakeFromRead(self):
		# create containers for all klasses, uniqued by name
		models = list(self._searchOrder)
		models.reverse()
		byName = {}
		inOrder = []
		for model in models:
			for klass in model.klasses().klassesInOrder():
				name = klass.name()
				if byName.has_key(name):
					for i in range(len(inOrder)):
						if inOrder[i].name()==name:
							inOrder[i] = klass
				else:
					inOrder.append(klass)
				byName[name] = klass
		assert len(byName)==len(inOrder)
		for name, klass in byName.items():
			assert klass is self.klass(name)
		for klass in inOrder:
			assert klass is self.klass(klass.name())
		self._allKlassesByName = byName
		self._allKlassesInOrder = inOrder

		self._klasses.awakeFromRead()


	def readParents(self, parentFilenames=None):
		"""
		Reads the parent models of the current model, as
		specified in the 'Inherit' setting.

		The attributes _parents and _searchOrder are set.
		"""
		if parentFilenames is None:
			parentFilenames = self.setting('Inherit', [])
		for filename in parentFilenames:
			filename = os.path.abspath(os.path.join(os.path.dirname(self._filename), filename))
			if self._allModelsByFilename.has_key(filename):
				model = self._allModelsByFilename[filename]
				assert model!=self._rootModel
			else:
				model = self.__class__(filename, customCoreClasses=self._coreClasses, rootModel=self, havePythonClasses=self._havePythonClasses)
				self._allModelsByFilename[filename] = model
			self._parents.append(model)

		# establish the search order
		# algorithm taken from http://www.python.org/2.2/descrintro.html#mro
		searchOrder = self.allModelsDepthFirstLeftRight()

		# remove duplicates:
		indexes = range(len(searchOrder))
		indexes.reverse()
		for i in indexes:
			model = searchOrder[i]
			j = 0
			while j<i:
				if searchOrder[j] is model:
					del searchOrder[j]
					i -= 1
				else:
					j += 1

		self._searchOrder = searchOrder


	def allModelsDepthFirstLeftRight(self, parents=None):
		"""
		Returns a list of all models, including self, parents and
		ancestors, in a depth-first, left-to-right order. Does not
		remove duplicates (found in inheritance diamonds).

		Mostly useful for readParents() to establish the lookup
		order regarding model inheritance.
		"""
		if parents is None:
			parents = []
		parents.append(self)
		for parent in self._parents:
			parent.allModelsDepthFirstLeftRight(parents)
		return parents

	def coreClass(self, className):
		""" For the given name, returns a class from MiddleKit.Core or the custom set of classes that were passed in via initialization. """
		pyClass = self._coreClasses.get(className, None)
		if pyClass is None:
			results = {}
			exec 'import MiddleKit.Core.%s as module'%className in results
			pyClass = getattr(results['module'], className)
			assert type(pyClass) is ClassType
			self._coreClasses[className] = pyClass
		return pyClass

	def coreClassNames(self):
		""" Returns a list of model class names found in MiddleKit.Core. """
		# a little cheesy, but it does the job:
		import MiddleKit.Core as Core
		return Core.__all__

	def klasses(self):
		"""
		Return an instance that inherits from Klasses, using the base
		classes passed to __init__, if any.

		See also: klass(), allKlassesInOrder(), allKlassesByName()
		"""
		if self._klasses is None:
			Klasses = self.coreClass('Klasses')
			self._klasses = Klasses(self)
		return self._klasses

	def klass(self, name, default=NoDefault):
		"""
		Returns the klass with the given name, searching the parent
		models if necessary.
		"""
		for model in self._searchOrder:
			klass = model.klasses().get(name, None)
			if klass:
				return klass
		if default is NoDefault:
			raise KeyError, name
		else:
			return default

	def allKlassesInOrder(self):
		"""
		Returns a sequence of all the klasses in this model, unique by
		name, including klasses inherited from parent models.

		The order is the order of declaration, top-down.
		"""
		return self._allKlassesInOrder

	def allKlassesByName(self):
		"""
		Returns a dictionary of all the klasses in this model, unique
		by name, including klasses inherited from parent models.
		"""
		return self._allKlassesByName

	def pyClassForName(self, name):
		"""
		Returns the Python class for the given name, which must be
		present in the object model. Accounts for
		self.setting('Package').

		If you already have a reference to the model klass, then
		you can just ask it for klass.pyClass().
		"""
		pyClass = self._pyClassForName.get(name, None)
		if pyClass is None:
			results = {}
			pkg = self.setting('Package', '')
			if pkg:
				pkg += '.'
			exec 'import %s%s as module' % (pkg, name) in results
			pyClass = getattr(results['module'], 'pyClass', None)
			if pyClass is None:
				pyClass = getattr(results['module'], name)
			# Note: The 'pyClass' variable name that is first looked for is a hook for
			# those modules that have replaced the class variable by something else,
			# like a function. I did this in a project with a class called UniqueString()
			# in order to guarantee uniqueness per string.
			self._pyClassForName[name] = pyClass
		return pyClass


	## Being configurable ##

	def configFilename(self):
		if self._filename is None:
			return None
		else:
			return os.path.join(self._filename, 'Settings.config')

	def defaultConfig(self):
		return {
			'Threaded': 1,
		}
