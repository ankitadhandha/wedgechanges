import ihooks
import os
import sys

"""
ImportSpy.py

The purpose of this module is to record the filepath of every module which 
is imported.  This is used by the AutoReloadingAppServer (see doc strings 
for more information) to restart the server if any source files change.

Other than keeping track of the filepaths, the behaviour of this module
loader is identical to Python's default behaviour.
"""

True, False = 1==1, 0==1

class ModuleLoader(ihooks.ModuleLoader):

	def __init__(self):
		assert modloader is None, \
		       "ModuleLoader can only be instantiated once"
		ihooks.ModuleLoader.__init__(self)
		self._fileList = {}
		self._notifyHook = None
		self._installed = False

	def load_module(self,name,stuff):
		try:
			mod = ihooks.ModuleLoader.load_module(self, name, stuff)
			self.recordFileName(stuff, mod)
		except:
			self.recordFileName(stuff, None)
			raise
		return mod

	def recordModules(self, moduleNames):
		for name in moduleNames:
			mod = sys.modules[name]
			if not hasattr(mod, '__file__'):
				# If we can't find it, we can't monitor it
				continue
			file = mod.__file__
			pathname = os.path.dirname(file)
			desc = None
			self.recordFileName((file, pathname, desc),
					    sys.modules[name])

	def fileList(self):
		return self._fileList

	def notifyOfNewFiles(self, hook):
		""" Called by someone else to register that they'd like to 
		be know when a new file is imported """
		self._notifyHook = hook

	def watchFile(self, filepath, getmtime=os.path.getmtime):
		modtime = getmtime(filepath)
		self._fileList[filepath] = modtime
		# send notification that this file was imported 
		if self._notifyHook:
			self._notifyHook(filepath,modtime)

	def recordFileName(self, stuff, mod, isfile=os.path.isfile):
		file, pathname, desc = stuff

		fileList = self._fileList
		if mod:
			# __orig_file__ is used for cheetah and psp mods; we want 
			# to record the source filenames, not the auto-generated modules
			f2 = getattr(mod, '__orig_file__', 0) 
			f = getattr(mod, '__file__', 0)

			if f2 and f2 not in fileList.keys():
				try:
					if isfile(f2):
						self.watchFile(f2)
				except OSError:
					pass
			elif f and f not in fileList.keys():
				# record the .py file corresponding to each '.pyc'
				if f[-4:] == '.pyc':
					f = f[:-1]
				try:
					if isfile(f):
						self.watchFile(f)
					else:
						self.watchFile(os.path.join(f, '__init__.py'))
				except OSError:
					pass

		# also record filepaths which weren't successfully
		# loaded, which may happen due to a syntax error in a
		# servlet, because we also want to know when such a
		# file is modified
		elif pathname:
			if isfile(pathname):
				self.watchFile(pathname)

	def activate(self):
		imp = ihooks.ModuleImporter(loader=modloader)
		ihooks.install(imp)
		self.recordModules(sys.modules.keys())
		self._installed = True

# We do this little double-assignment trick to make sure ModuleLoader
# is only instantiated once.
modloader = None
modloader = ModuleLoader()

""" These two methods are compatible with the 'imp' module (and can
therefore be useds as drop-in replacements), but will use the
above ModuleLoader to record the pathnames of imported modules.
"""

def load_module(name, file, filename, description):
	return modloader.load_module(name,(file,filename,description))

def find_module(name,path=None):
	return modloader.find_module(name,path)
