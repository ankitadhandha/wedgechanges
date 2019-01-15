from Common import *
from Servlet import Servlet
import string


class HTTPServlet(Servlet):
	"""
	HTTPServlet implements the respond() method to invoke methods such as respondToGet() and respondToPut() depending on the type of HTTP request.
	Example HTTP request methods are GET, POST, HEAD, etc.
	Subclasses implement HTTP method FOO in the Python method respondToFoo.
	Unsupported methods return a "501 Not Implemented" status.

	Note that HTTPServlet inherits awake() and respond() methods from Servlet and that subclasses may make use of these.

	See also: Servlet

	FUTURE
		* Document methods (take hints from Java HTTPServlet documentation)
	"""

	## Init ##

	def __init__(self):
		Servlet.__init__(self)
		self._methodForRequestType = {}  # a cache; see respond()


	## Transactions ##

	def respond(self, trans):
		""" Invokes the appropriate respondToSomething() method depending on the type of request (e.g., GET, POST, PUT, ...). """
		httpMethodName = trans.request().method()
		method = self._methodForRequestType.get(httpMethodName, None)
		if not method:
			methName = 'respondTo' + string.capitalize(httpMethodName)
			method = getattr(self, methName, self.notImplemented)
			self._methodForRequestType[httpMethodName] = method
		method(trans)

	def notImplemented(self, trans):
		trans.response().setHeader('Status', '501 Not Implemented')

	def respondToHead(self, trans):
		"""
		A correct but inefficient implementation.
		Should at least provide Last-Modified and Content-Length.
		"""
		res = trans.response()
		w = res.write
		res.write = lambda *args: None
		self.respondToGet(trans)
		res.write = w
