from ServletFactory import ServletFactory
import os, mimetypes, time

debug = 0

class UnknownFileTypeServletFactory(ServletFactory):
	"""
	This is the factory for files of an unknown type (e.g., not .py .psp, etc).
	"""

	def uniqueness(self):
		return 'file'

	def extensions(self):
		return ['.*']

	def servletForTransaction(self, transaction):
		return UnknownFileTypeServlet(transaction.application())

	def flushCache(self):
		pass


fileCache = {}
	# A cache of the files served up by UnknownFileTypeServlet cached by absolute, server side path.
	# Each content is another dictionary with keys: content, mimeType, mimeEncoding.
	# Previously, this content was stored directly in the attributes of the UnknownFileTypeServlets, but with that approach subclasses cannot dynamically serve content from different locations.

from HTTPServlet import HTTPServlet
from MiscUtils.Configurable import Configurable
class UnknownFileTypeServlet(HTTPServlet, Configurable):
	"""
	Normally this class is just a "private" utility class for WebKit's
	purposes. However, you may find it useful to subclass on occasion,
	such as when the server side file path is determined by something
	other than a direct correlation to the URL. Here is such an example:


	from WebKit.AppServer import globalAppServer
	from WebKit.UnknownFileTypeServlet import UnknownFileTypeServlet
	import os

	class Image(UnknownFileTypeServlet):

		imageDir = '/var/images'

		def filename(self, trans):
			filename = trans.request().field('i')
			filename = os.path.join(self.imageDir, filename)
			return filename
	"""

	## Candidates for subclass overrides ##

	def filename(self, trans):
		"""
		Returns the filename to be served. A subclass could override
		this in order to serve files from other disk locations based
		on some logic.
		"""
		filename = getattr(self, '_serverSideFilename', None)
		if filename is None:
			filename = trans.request().serverSidePath()
			self._serverSideFilename = filename  # cache it
		return filename

	def shouldCacheContent(self):
		"""
		Returns a boolean that controls whether or not the content served through this servlet is cached. The default behavior is to return the CacheContent setting. Subclasses may override to always True or False, or incorporate some other logic.
		"""
		return self.setting('CacheContent')


	## Init et al ##

	def __init__(self, application=None):
		HTTPServlet.__init__(self)
		Configurable.__init__(self)
		if application is None:
			from WebKit.AppServer import globalAppServer
			application = globalAppServer.application()
			assert application is not None
		self._application = application

	def userConfig(self):
		""" Get the user config from the 'UnknownFileTypes' section in the Application's configuration. """
		return self._application.setting('UnknownFileTypes')

	def configFilename(self):
		return self._application.configFilename()

	def canBeReused(self):
		return self.setting('ReuseServlets')

	def validTechniques(self):
		return ['serveContent', 'redirectSansAdapter']

	def respondToGet(self, trans):
		""" Responds to the transaction by invoking self.foo() for foo is specified by the 'Technique' setting. """
		technique = self.setting('Technique')
		assert technique in self.validTechniques(), 'technique = %s' % technique
		method = getattr(self, technique)
		method(trans)

	respondToHead = respondToGet

	def respondToPost(self, trans):
		"""
		Invokes self.respondToGet().
		Since posts are usually accompanied by data, this might not be the best policy. However, a POST would most likely be for a CGI, which currently no one is mixing in with their WebKit-based web sites.
		"""
		# @@ 2001-01-25 ce: See doc string for why this might be a bad idea.
		self.respondToGet(trans)

	def redirectSansAdapter(self, trans):
		""" Sends a redirect to a URL that doesn't contain the adapter name. Under the right configuration, this will cause the web server to then be responsible for the URL rather than the app server. This has only been test with "*.[f]cgi" adapters.
		Keep in mind that links off the target page will NOT include the adapter in the URL. """
		# @@ 2000-05-08 ce: the following is horribly CGI specific and hacky
		env = trans.request()._environ
		# @@ 2001-01-25 ce: isn't there a func in WebUtils to get script name? because some servers are different?
		newURL = os.path.split(env['SCRIPT_NAME'])[0] + env['PATH_INFO']
		newURL = newURL.replace('//', '/')  # hacky
		trans.response().sendRedirect(newURL)


	def serveContent(self, trans):
		response = trans.response()

		# @@ temp variables, move to config
		MaxCacheContentSize = 128*1024
		ReadBufferSize = 32*1024

		#start sending automatically
		response.streamOut().autoCommit(1)

		filename = self.filename(trans)
		file = fileCache.get(filename, None)
		if file is None:
			fileSize = os.path.getsize(filename)
		else:
			fileSize = file['size']

		isHead = trans.request().method().upper()[0]=='H' # as in HEAD
		if isHead:
			response.setHeader('Content-Length', str(fileSize))
			mtime = os.path.getmtime(filename)
			response.setHeader('Last-Modified',
				time.strftime('%a, %d %b %Y %H:%M:%S GMT',
				time.gmtime(mtime)))

		if debug:
			print '>> UnknownFileType.serveContent()'
			print '>> filename =', filename
		if file is None:
			if debug: print '>> reading file'
			fileType = mimetypes.guess_type(filename)
			mimeType = fileType[0]
			mimeEncoding = fileType[1]

			if mimeType is None:
				mimeType = 'text/html'  # @@ 2000-01-27 ce: should this just be text?
			response.setHeader('Content-type', mimeType)
			if mimeEncoding:
				response.setHeader('Content-encoding', mimeEncoding)

			if self.setting('ReuseServlets') and self.shouldCacheContent() and fileSize<MaxCacheContentSize:
				if debug: print '>> caching'
				file = {
					'content':      open(filename, "rb").read(),
					'mimeType':     mimeType,
					'mimeEncoding': mimeEncoding,
					'mtime':        os.path.getmtime(filename),
					'size':         os.path.getsize(filename),
					'filename':     filename,
				}
				fileCache[filename] = file
				if isHead:
					return
				response.write(file['content'])
			else:  # too big or not supposed to cache
				if isHead:
					return
				f = open(filename, "rb")
				numBytesSent = 0
				while numBytesSent<fileSize:
					data = f.read(ReadBufferSize)
					response.write(data)
					numBytesSent += len(data)
		else:  # We already have the file cached in memory
			if self.setting('CheckDate'):
				# check the date and re-read if necessary
				actual_mtime = os.path.getmtime(filename)
				if actual_mtime>file['mtime']:
					if debug: print '>> reading updated file'
					file['content'] = open(filename, 'rb').read()
					file['mtime']   = actual_mtime
			response.setHeader('Content-type', file['mimeType'])
			if file.get('mimeEncoding'):
				response.setHeader('Content-encoding', file['mimeEncoding'])
			if isHead:
				return
			response.write(file['content'])
