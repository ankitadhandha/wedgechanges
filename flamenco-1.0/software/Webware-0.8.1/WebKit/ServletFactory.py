from Common import *
from WebKit.Servlet import Servlet
import sys
from types import ClassType, BuiltinFunctionType
import ImportSpy as imp   # ImportSpy provides find_module and load_module
import threading


class ServletFactory(Object):
	"""
	ServletFactory is an abstract class that defines the protocol for all servlet factories.

	Servlet factories are used by the Application to create servlets for transactions.

	A factory must inherit from this class and override uniqueness(), extensions() and servletForTransaction(). Do not invoke the base class methods as they all raise AbstractErrors.

	Each method is documented below.
	"""

	def __init__(self, application):
		""" Stores a reference to the application in self._app, because subclasses may or may not need to talk back to the application to do their work. """
		Object.__init__(self)
		self._app = application
		self._cacheClasses = self._app.setting("CacheServletClasses",1)

	def name(self):
		""" Returns the name of the factory. This is a convenience for the class name. """
		return self.__class__.__name__

	def uniqueness(self):
		""" Returns a string to indicate the uniqueness of the ServletFactory's servlets. The Application needs to know if the servlets are unique per file, per extension or per application. Return values are 'file', 'extension' and 'application'.
			*** NOTE: Application only supports 'file' uniqueness at this point in time. """
		raise AbstractError, self.__class__

	def extensions(self):
		""" Return a list of extensions that match this handler. Extensions should include the dot. An empty string indicates a file with no extension and is a valid value. The extension '.*' is a special case that is looked for a URL's extension doesn't match anything. """
		raise AbstractError, self.__class__

	def servletForTransaction(self, transaction):
		""" Returns a new servlet that will handle the transaction. This method should do no caching (e.g., it should really create the servlet upon each invocation) since caching is already done at the Application level. """
		raise AbstractError, self.__class__

	def flushCache(self):
		"""
		Clear any caches and start fesh.
		"""
		raise AbstractError, self.__class__


	def importAsPackage(self, transaction, serverSidePathToImport):
		"""
		Imports the module at the given path in the proper package/subpackage for the current request.  For example, if the
		transaction has the URL 'http://localhost/WebKit.cgi/MyContextDirectory/MySubdirectory/MyPage' and
		path = 'some/random/path/MyModule.py' and the context is configured to have the name "MyContext" then this function
		imports the module at that path as MyContext.MySubdirectory.MyModule .  Note that the context name may differ
		from the name of the directory containing the context, even though they are usually the same by convention.

		Note that the module imported may have a different name from the servlet name specified in the URL.  This is used in PSP.
		"""
		debug=0

		# Pull out the full server side path and the context path
		request = transaction.request()
		path = request.serverSidePath()
		contextPath = request.serverSideContextPath()
		fullname = request.contextName()

		## There is no context, so import the module standalone and give it a unique name
		if fullname == None:
			remainder = serverSidePathToImport
			remainder = string.replace(remainder, '\\', '_')
			remainder = string.replace(remainder, '/','_')
			fullmodname = string.replace(remainder,'.','_')
			if debug: print __file__, "fullmodname=",fullmodname
			if len(fullmodname) > 100: fullmodname=fullmodname[:-50]
			modname=os.path.splitext(os.path.basename(serverSidePathToImport))[0]
			fp, pathname, stuff = imp.find_module(modname, [os.path.dirname(serverSidePathToImport)])
			module = imp.load_module(fullmodname, fp, pathname, stuff)
			return module


		# First, we'll import the context's package.
		directory, contextDirName = os.path.split(contextPath)
		self._importModuleFromDirectory(fullname, contextDirName, directory, isPackageDir=1)
		directory = contextPath

		# Now we'll break up the rest of the path into components.
		remainder = path[len(contextPath)+1:]
		remainder = string.replace(remainder, '\\', '/')
		remainder = string.split(remainder, '/')

		# Import all subpackages of the context package
		for name in remainder[:-1]:
			fullname = fullname + '.' + name
			self._importModuleFromDirectory(fullname, name, directory, isPackageDir=1)
			directory = os.path.join(directory, name)

		# Finally, import the module itself as though it was part of the package
		# or subpackage, even though it may be located somewhere else.
		moduleFileName = os.path.basename(serverSidePathToImport)
		moduleDir = os.path.dirname(serverSidePathToImport)
		name, ext = os.path.splitext(moduleFileName)
		fullname = fullname + '.' + name
		module = self._importModuleFromDirectory(fullname, name, moduleDir, forceReload=1)
		return module

	def _importModuleFromDirectory(self, fullModuleName, moduleName, directory, isPackageDir=0, forceReload=0):
		"""
		Imports the given module from the given directory.  fullModuleName should be the full
		dotted name that will be given to the module within Python.  moduleName should be the
		name of the module in the filesystem, which may be different from the name given in
		fullModuleName.  Returns the module object.  If forceReload is true then this reloads the module
		even if it has already been imported.

		If isPackageDir is true, then this function creates an empty __init__.py
		if that file doesn't already exist.
		"""
		debug = 0
		if debug: print __file__, fullModuleName, moduleName, directory
		if not forceReload:
			module = sys.modules.get(fullModuleName, None)
			if module is not None:
				return module
		fp = None
		try:
			if isPackageDir:
				# Check if __init__.py is in the directory -- if not, make an empty one.
				packageDir = os.path.join(directory, moduleName)
				initPy = os.path.join(packageDir, '__init__.py')
				if not os.path.exists(initPy):
					file = open(initPy, 'w')
					file.write('#')
					file.close()
			fp, pathname, stuff = imp.find_module(moduleName, [directory])
			module = imp.load_module(fullModuleName, fp, pathname, stuff)
		finally:
			if fp is not None:
				fp.close()
		return module

class PythonServletFactory(ServletFactory):
	"""
	This is the factory for ordinary, Python servlets whose extensions are empty or .py. The servlets are unique per file since the file itself defines the servlet.
	"""

	def __init__(self,app):
		ServletFactory.__init__(self,app)
		self._cache = {}
		self._lock = threading.RLock()

	def uniqueness(self):
		return 'file'

	def extensions(self):
		return ['.py']

	def flushCache(self):
		self._cache = {}

#	def old_servletForTransaction(self, transaction):
#		path = transaction.request().serverSidePath()
#		globals = {}
#		execfile(path, globals)
#		from types import ClassType
#		name = os.path.splitext(os.path.split(path)[1])[0]
#		assert globals.has_key(name), 'Cannot find expected servlet class named "%s".' % name
#		theClass = globals[name]
#		assert type(theClass) is ClassType
#		assert issubclass(theClass, Servlet)
#		return theClass()

	def servletForTransaction(self, transaction):
		request = transaction.request()
		path = request.serverSidePath()
		name = os.path.splitext(os.path.split(path)[1])[0]
		# Use a lock to prevent multiple simultaneous imports of the same module
		self._lock.acquire()
		try:
			if not self._cache.has_key(path):
				self._cache[path] = {}
			if os.path.getmtime(path) > self._cache[path].get('mtime', 0):
				# Import the module as part of the context's package
				module = self.importAsPackage(transaction, path)
				assert module.__dict__.has_key(name), 'Cannot find expected servlet class named %s in %s.' % (repr(name), repr(path))
				# Pull the servlet class out of the module
				theClass = getattr(module, name)
				# new-style classes aren't ClassType, but they
				# are okay to use.  They are subclasses of
				# type.  But type isn't a class in older
				# Python versions, it's a builtin function.
				# So we test what type is first, then use
				# isinstance only for the newer Python
				# versions
				if type(type) is BuiltinFunctionType:
					assert type(theClass) is ClassType
				else:
					assert type(theClass) is ClassType \
					       or isinstance(theClass, type)
				assert issubclass(theClass, Servlet)
				self._cache[path]['mtime'] = os.path.getmtime(path)
				self._cache[path]['class'] = theClass
			else:
				theClass = self._cache[path]['class']
				if not self._cacheClasses:
					del self._cache[path]
			return theClass()
		finally:
			self._lock.release()

#	def import_servletForTransaction(self, transaction):
#		path = transaction.request().serverSidePath()
#		name = os.path.splitext(os.path.split(path)[1])[0]
#		if not self.cache.has_key(name): self.cache[name]={}
#		if os.path.getmtime(path) > self.cache[name].get('mtime',0):
#			if not os.path.split(path)[0] in sys.path: sys.path.append(os.path.split(path[0]))
#			module_obj=__import__(name)
#			reload(module_obj)#force reload
#			inst =  module_obj.__dict__[name]()
#			self.cache[name]['mtime']=os.path.getmtime(path)
#		else:
#			inst = sys.modules[name].__dict__[name]()
#		return inst
