"""
This module handles requests from the application for PSP pages.


--------------------------------------------------------------------------
   (c) Copyright by Jay Love, 2000 (mailto:jsliv@jslove.net)

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee or royalty is hereby granted,
    provided that the above copyright notice appear in all copies and that
    both that copyright notice and this permission notice appear in
    supporting documentation or portions thereof, including modifications,
    that you make.

    THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD TO
    THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
    INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
    FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
    NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
    WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !


"""

from WebKit.ServletFactory import ServletFactory


import string
import os,sys,string
from PSP import Context, PSPCompiler
import time, threading


class PSPServletFactory(ServletFactory):
	"""
	Servlet Factory for PSP files.
	Very sloppy.  Need to come back and do a serious cleanup.

	"""

	def __init__(self,application):
		ServletFactory.__init__(self,application)
		self.cacheDir = application.serverSidePath('Cache/PSP')
		self._classcache={}
		sys.path.append(self.cacheDir)

		self._cacheClassFiles = self._cacheClasses

		l = ['_'] * 256
		for c in string.digits + string.letters:
			l[ord(c)] = c
		self._classNameTrans = string.join(l, '')

		if application.setting('ClearPSPCacheOnStart', 1):
			self.clearFileCache()
		self._lock = threading.RLock()

	def uniqueness(self):
		 return 'file'

	def extensions(self):
		 return ['.psp']

	def flushCache(self):
		"""
		Clean out the cache of classes we keep in memory.  Also, clear the class files stored on disk.
		"""
		self._classcache = {}
		self.clearFileCache()

	def clearFileCache(self):
		"""
		Clear class files stored on disk.
		"""
		import glob
		files = glob.glob(os.path.join(self.cacheDir,'*.*'))
		map(os.remove, files)

	def computeClassName(self,pagename):
		"""
		Generates a <hopefully> unique class/file name for each PSP file.
		Argument: pagename:  the path to the PSP source file
		Returns:  A unique name for the class generated fom this PSP source file.
		"""
		# Compute class name by taking the path and substituting underscores for
		# all non-alphanumeric characters.
		return string.translate(os.path.splitdrive(pagename)[1], self._classNameTrans)

#	def import_createInstanceFromFile(self,transaction,path,classname,mtime,reimp=0):
#		"""
#		Create an actual instance of a PSP class.  This version uses import to generate the instance.
#
#		"""
#		globals={}
#		module_obj=__import__(classname)
#		if reimp:
#			reload(module_obj)
#		instance = module_obj.__dict__[classname]()
#		code=module_obj.__dict__[classname]
#		self._classcache[classname] = {'code':code,
#					   'filename':path,
#					   'mtime':time.time(),}
#		return instance

#	def createInstanceFromFile(self,transaction,filename,classname,mtime,reimp=0):
#		"""
#		Create an actual class instance.  This version uses "exec" to generate the class instance.
#		"""
#		globals={}
#		execfile(filename,globals)
#		assert globals.has_key(classname)
#		instance = globals[classname]()
#		code=globals[classname]
#		self._classcache[classname] = {'code':code,
#					   'filename':filename,
#					   'mtime':time.time(),}
#		return instance

	def createInstanceFromFile(self,transaction,filename,classname,mtime,reimp=0):
		"""
		Create an actual class instance.  The module containing the class is imported as though it
		were a module within the context's package (and appropriate subpackages).
		"""
		module = self.importAsPackage(transaction,filename)
		assert module.__dict__.has_key(classname), 'Cannot find expected class named %s in %s.' % (repr(classname), repr(filename))
		code = getattr(module, classname)
		instance = code()
		self._classcache[classname] = {'code':code,
					   'filename':filename,
					   'mtime':time.time(),}
		return instance


	def checkClassCache(self, classname, mtime):
		"""
		Check our cache to see if we already have this class in memory.
		"""
		if self._classcache.has_key(classname) and self._classcache[classname]['mtime'] > mtime:
			return self._classcache[classname]['code']()
		return None


	def servletForTransaction(self, trans):
		"""
		The entry point to getting a PSP servlet instance.
		"""
		fullname = trans.request().serverSidePath()
		path,pagename = os.path.split(fullname)
		mtime = os.path.getmtime(fullname)
		instance = None

		classname = self.computeClassName(fullname)

		# Use a lock to prevent multiple simultaneous compilations/imports of the same PSP
		self._lock.acquire()
		try:
			#see if we can just create a new instance
			if self._cacheClasses:
				instance = self.checkClassCache(classname,mtime)
			if instance != None:
				return instance

			cachedfilename = os.path.join(self.cacheDir,str(classname + '.py'))

			if self._cacheClassFiles and os.path.exists(cachedfilename) and os.stat(cachedfilename)[6] > 0:
				if os.path.getmtime(cachedfilename) > mtime:
					instance = self.createInstanceFromFile(trans,cachedfilename,classname,mtime,0)
					return instance

			pythonfilename = cachedfilename

			context = Context.PSPCLContext(fullname,trans)
			context.setClassName(classname)
			context.setPythonFileName(pythonfilename)


			clc = PSPCompiler.Compiler(context)

			#print 'creating python class: ' , classname
			clc.compile()

			instance = self.createInstanceFromFile(trans,cachedfilename,classname,mtime,1)
			return instance
		finally:
			self._lock.release()

