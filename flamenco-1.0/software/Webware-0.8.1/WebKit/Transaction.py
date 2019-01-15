from Common import *
from WebUtils.Funcs import htmlEncode
import traceback


class Transaction(Object):
	"""
	A transaction serves as:

		* A container for all objects involved in the transaction. The
		  objects include application, request, response, session and
		  servlet.

		* A message dissemination point. The messages include awake(),
		  respond() and sleep().

	When first created, a transaction has no session. However, it will
	create or retrieve one upon being asked for session().

	The life cycle of a transaction begins and ends with Application's
	dispatchRequest().
	"""


	## Init ##

	def __init__(self, application, request=None):
		Object.__init__(self)
		self._application   = application
		self._request       = request
		self._response      = None
		self._session       = None
		self._servlet       = None
		self._errorOccurred = 0

	attrNames = 'application request response session servlet errorOccurred'.split()

	def __repr__(self):
		s = []
		for name in self.attrNames:
			s.append('%s=%r' % (name, getattr(self, '_'+name, '(no attr)')))
		s = ' '.join(s)
		return '<%s %s>' % (self.__class__.__name__, s)


	## Access ##

	def application(self):
		return self._application

	def request(self):
		return self._request

	def response(self):
		return self._response

	def setResponse(self, response):
		self._response = response

	def hasSession(self):
		""" Returns true if the transaction has a session. """
		return self._session is not None

	def session(self):
		""" Returns the session for the transaction, creating one if necessary. Therefore, this method never returns None. Use hasSession() if you want to find out if there one already exists. """
		if not self._session:
			self._session = self._application.createSessionForTransaction(self)
		return self._session

	def setSession(self, session):
		self._session = session

	def servlet(self):
		""" Return the current servlet that is processing. Remember that servlets can be nested. """
		return self._servlet

	def setServlet(self, servlet):
		self._servlet = servlet

	def duration(self):
		""" Returns the duration, in seconds, of the transaction (basically response end time minus request start time). """
		return self._response.endTime() - self._request.time()

	def errorOccurred(self):
		return self._errorOccurred

	def setErrorOccurred(self, flag):
		""" Invoked by the application if an exception is raised to the application level. """
		self._errorOccurred = flag
		#self._servlet = None
		# @@ 2002-02-05 ce: disabled above statement so that custom exception handlers can examine the servlet


	## Transaction stages ##

	def awake(self):
		""" Sends awake() the to session (if there is one) and the servlet. Currently, the request and response do not partake in the awake()-respond()-sleep() cycle. This could definitely be added in the future if any use was demonstrated for it. """
		if self._session:
			self._session.awake(self)
		self._servlet.awake(self)

	def respond(self):
		if self._session:
			self._session.respond(self)
		self._servlet.respond(self)

	def sleep(self):
		""" Note that sleep() is sent in reverse order as awake() (which is typical for shutdown/cleanup methods). """
		self._servlet.sleep(self)
		if self._session:
			self._session.sleep(self)


	## Debugging ##

	def dump(self, file=None):
		""" Dumps debugging info to stdout. """
		if file is None:
			file = sys.stdout
		wr = file.write
		wr('>> Transaction: %s\n' % self)
		for attr in dir(self):
			wr('%s: %s\n' % (attr, getattr(self, attr)))
		wr('\n')


	## Die ##

	def die(self):
		""" This method should be invoked when the entire transaction is finished with. Currently, this is invoked by AppServer. This method removes references to the different objects in the transaction, breaking cyclic reference chains and allowing either older versions of Python to collect garbage, or newer versions to collect it faster. """
		from types import InstanceType
		for attrName in self.__dict__.keys():
			# @@ 2000-05-21 ce: there's got to be a better way!
			attr = getattr(self, attrName)
			if type(attr) is InstanceType and hasattr(attr, 'resetKeyBindings'):
				#print '>> resetting'
				attr.resetKeyBindings()
			delattr(self, attrName)


	## Exception handling ##

	exceptionReportAttrNames = 'application request response session servlet'.split()

	def writeExceptionReport(self, handler):
		handler.writeTitle(self.__class__.__name__)
		handler.writeAttrs(self, self.exceptionReportAttrNames)

		for name in self.exceptionReportAttrNames:
			obj = getattr(self, '_'+name, None)
			if obj:
				try:
					obj.writeExceptionReport(handler)
				except Exception, e:
					handler.writeln('<p> Uncaught exception while asking <b>%s</b> to write report:\n<pre>' % name)
					traceback.print_exc(file=handler)
					handler.writeln('</pre>')
