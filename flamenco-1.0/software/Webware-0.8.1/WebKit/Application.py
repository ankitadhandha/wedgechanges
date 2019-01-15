#!/usr/bin/env python

from Common import *
from UserDict import UserDict
from Object import Object
from Servlet import Servlet
from ServletFactory import *
from UnknownFileTypeServlet import UnknownFileTypeServletFactory
from types import FloatType
from glob import glob
import imp
import string
from threading import Lock, Thread, Event
from time import *
from fnmatch import fnmatch

from WebKit.Cookie import Cookie

from WebUtils.HTMLForException import HTMLForException

from ExceptionHandler import ExceptionHandler  

from ConfigurableForServerSidePath import ConfigurableForServerSidePath

from TaskKit.Scheduler import Scheduler

from ASStreamOut import ASStreamOut

debug = 0

class ApplicationError(Exception):
	pass

class EndResponse(Exception):
	"""
	Used to prematurely break out of the awake()/respond()/sleep() cycle
	without reporting a traceback.  During servlet processing, if this
	exception is caught during respond() then sleep() is called and the
	response is sent.  If caught during awake() then both respond() and
	sleep() are skipped and the response is sent.
	"""
	pass

class Application(ConfigurableForServerSidePath, Object):
	"""
	FUTURE
		* 2000-04-09 ce: Automatically open in browser.
		* 2000-04-09 ce: Option to remove HTML comments in responses.
		* 2000-04-09 ce: Option remove unnecessary white space in responses.
		* 2000-04-09 ce: Debugging flag and debug print method.
		* 2000-04-09 ce: A web-based, interactive monitor to the application.
		* 2000-04-09 ce: Record and playback of requests and responses. Useful for regression testing.
		* 2000-04-09 ce: sessionTimeout() and a hook for when the session has timed out.
		* 2000-04-09 ce: pageRefreshOnBacktrack
		* 2000-04-09 ce: terminate() and isTerminating()
		* 2000-04-09 ce: isRefusingNewSessions()
		* 2000-04-09 ce: terminateAfterTimeInterval()
		* 2000-04-09 ce: restoreSessionWithID:inTransaction:
		* 2000-04-09 ce: pageWithNameForRequest/Transaction() (?)
		* 2000-04-09 ce: port() and setPort() (?)
		* 2000-04-09 ce: Does request handling need to be embodied in a separate object?
			  - Probably, as we may want request handlers for various file types.
		* 2000-04-09 ce: Concurrent request handling (probably through multi-threading)
	"""

	## Init ##

	def __init__(self, server=None, transactionClass=None, sessionClass=None, requestClass=None, responseClass=None, exceptionHandlerClass=None, contexts=None, useSessionSweeper=1):

		self._server = server
		self._serverSidePath = server.serverSidePath()

		ConfigurableForServerSidePath.__init__(self)
		Object.__init__(self)

		if self.setting('PrintConfigAtStartUp'):
			self.printConfig()

		self.initVersions()

		if transactionClass:
			self._transactionClass = transactionClass
		else:
			from Transaction import Transaction
			self._transactionClass = Transaction

		if sessionClass:
			self._sessionClass = sessionClass
		else:
			from Session import Session
			self._sessionClass = Session

		if requestClass:
			self._requestClass = requestClass
		else:
			from HTTPRequest import HTTPRequest
			self._requestClass = HTTPRequest

		if responseClass:
			self._responseClass = responseClass
		else:
			from HTTPResponse import HTTPResponse
			self._responseClass = HTTPResponse

		if exceptionHandlerClass:
			self._exceptionHandlerClass = exceptionHandlerClass
		else:
			self._exceptionHandlerClass = None

		# Init other attributes
		self._servletCacheByPath = {}
		self._serverSideInfoCacheByPath = {}
		self._cacheDictLock = Lock()
		self._instanceCacheSize = self._server.setting('MaxServerThreads')
		self._shutDownHandlers = []

		# Set up servlet factories
		self._factoryList = []  # the list of factories
		self._factoryByExt = {} # a dictionary that maps all known extensions to their factories, for quick look up
		self.addServletFactory(PythonServletFactory(self))
		self.addServletFactory(UnknownFileTypeServletFactory(self))
		# ^ @@ 2000-05-03 ce: make this customizable at least through a method (that can be overridden) if not a config file (or both)

## TaskManager
		if self._server.isPersistent():
			self._taskManager = Scheduler(1)
			self._taskManager.start()
## End TaskManager


## Contexts
		if contexts: #Try to get this from the Config file
			defctxt = contexts
		else: #Get it from Configurable object, which gets it from defaults or the user config file
			defctxt = self.setting('Contexts')
		self._contexts={}
		# First load all contexts except the default
		contextDirToName = {}
		for i in defctxt.keys():
			if i != 'default':
				if not os.path.isabs(defctxt[i]):
					path = self.serverSidePath(defctxt[i])
				else:
					path = defctxt[i]
				self.addContext(i, path)
				contextDirToName[path] = i
		# @@ gat: this code would be much cleaner if we had a separate DefaultContext config variable.
		# load in the default context, if any
		self._defaultContextName = None
		if defctxt.has_key('default'):
			if not os.path.isabs(defctxt['default']):
				path = self.serverSidePath(defctxt['default'])
			else:
				path = defctxt['default']

			# see if the default context is the same as one of the other contexts
			self._defaultContextName = contextDirToName.get(path, None)
			if self._defaultContextName:
				# the default context is shared with another context
				self._setContext('default', self.context(self._defaultContextName))
			else:
				# the default context is separate from the other contexts, so add it like any other context
				self._defaultContextName = 'default'
				self.addContext('default', path)
		print
## End Contexts

## Session store
		# Create the session store
		from SessionMemoryStore import SessionMemoryStore
		from SessionFileStore import SessionFileStore
		from SessionDynamicStore import SessionDynamicStore
		klass = locals()['Session'+self.setting('SessionStore','File')+'Store']
		assert type(klass) is ClassType
		self._sessions = klass(self)
## End Session store



		print 'Current directory:', os.getcwd()

		self.running = 1

		if useSessionSweeper:
			self.startSessionSweeper()

		self._cacheServletInstances = self.setting("CacheServletInstances",1)
		print

		try:
			# First try the working dir
			self._404Page = open(os.path.join(self._serverSidePath,"404Text.txt"),"r").read()
		except:
			try:
				# Then try the directory this file is located in
				self._404Page = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "404Text.txt"),"r").read()
			except:
				# Fall back on a simple string
				self._404Page = """404 Error<p>File Not Found: %s"""

		# @@ ISB 09/02: make this default or get rid of it eventually
		if self.setting('ExtraPathInfo', 0):
			self.serverSideInfoForRequestOld = self.serverSideInfoForRequest
			self.serverSideInfoForRequest = self.serverSideInfoForRequestNewAlgorithm
			self._serverSideInfoCacheByPathNew = {}
			self._filesToHideRegexes = []
			self._filesToServeRegexes = []
			from fnmatch import translate as fnTranslate
			import re
			for pattern in self.setting('FilesToHide'):
				self._filesToHideRegexes.append(
					re.compile(fnTranslate(pattern)))
			for pattern in self.setting('FilesToServe'):
				self._filesToServeRegexes.append(
					re.compile(fnTranslate(pattern)))


	def initVersions(self):
		"""
		Initialize attributes that store the Webware and WebKit versions
		as both tuples and strings. These are stored in the Properties.py
		files.
		"""
		from MiscUtils.PropertiesObject import PropertiesObject
		props = PropertiesObject(os.path.join(self.webwarePath(), 'Properties.py'))
		self._webwareVersion = props['version']
		self._webwareVersionString = props['versionString']

		props = PropertiesObject(os.path.join(self.webKitPath(), 'Properties.py'))
		self._webKitVersion = props['version']
		self._webKitVersionString = props['versionString']


## Task access
	def taskManager(self):
		return self._taskManager

## Session sweep task
	def startSessionSweeper(self):
		from Tasks import SessionTask
		import time
		task = SessionTask.SessionTask(self._sessions)
		tm = self.taskManager()
		sweepinterval = self.setting('SessionTimeout')*60/10
		tm.addPeriodicAction(time.time()+sweepinterval, sweepinterval, task, "SessionSweeper")
		print "Session Sweeper started"

## Shutdown
	def shutDown(self):
		"""
		Called by AppServer when it is shuting down.  The __del__ function of Application probably won't be called due to circular references.
		"""
		print "Application is Shutting Down"
		self.running = 0
		if hasattr(self, '_sessSweepThread'):
			# We don't always have this, hence the 'if' above
			self._closeEvent.set()
			self._sessSweepThread.join()
			del self._sessSweepThread
		self._sessions.storeAllSessions()
		if self._server.isPersistent():
			self.taskManager().stop()
		del self._sessions
		del self._factoryByExt
		del self._factoryList
		del self._server
		del self._servletCacheByPath

		# Call all registered shutdown handlers
		for shutDownHandler in self._shutDownHandlers:
			shutDownHandler()
		del self._shutDownHandlers

		print "Application has been succesfully shutdown."

	def addShutDownHandler(self, func):
		"""
		Adds this function to a list of functions that are called when the application
		shuts down.
		"""
		self._shutDownHandlers.append(func)

	## Config ##

	def defaultConfig(self):
		return {
			'PrintConfigAtStartUp': 1,
			'DirectoryFile':        ['index', 'Main'],
			'ExtensionsToIgnore':   ['.pyc', '.pyo', '.py~', '.bak', '.tmpl'],
			'ExtensionsToServe':   None,
			'UseCascadingExtensions':1,
			'ExtensionCascadeOrder':['.psp','.py','.html',],


			'FilesToHide': ['.*', '*~', '*bak', '*.tmpl', '*.pyc', '*.pyo', '*.config'],
			'FilesToServe': None,

			'LogActivity':          1,
			'ActivityLogFilename':  'Logs/Activity.csv',
			'ActivityLogColumns':   ['request.remoteAddress', 'request.method', 'request.uri', 'response.size', 'servlet.name', 'request.timeStamp', 'transaction.duration', 'transaction.errorOccurred'],
			'SessionStore':         'Memory',  # can be File or Memory
			'SessionTimeout':        60,  # minutes
			'IgnoreInvalidSession': 1,
			'UseAutomaticPathSessions': 0,

			# Error handling
			'ShowDebugInfoOnErrors': 1,
			'IncludeFancyTraceback': 0,
			'FancyTracebackContext': 5,
			'UserErrorMessage':      'The site is having technical difficulties with this page. An error has been logged, and the problem will be fixed as soon as possible. Sorry!',
			'ErrorLogFilename':      'Logs/Errors.csv',
			'SaveErrorMessages':     1,
			'ErrorMessagesDir':      'ErrorMsgs',
			'EmailErrors':           0, # be sure to review the following settings when enabling error e-mails
			'ErrorEmailServer':      'mail.-.com',
			'ErrorEmailHeaders':     { 'From':         '-@-.com',
			                           'To':           ['-@-.com'],
			                           'Reply-to':     '-@-.com',
			                           'content-type': 'text/html',
			                           'Subject':      'Error'
			                         },
			'MaxValueLengthInExceptionReport': 500,
			'RPCExceptionReturn':    'traceback',
			'ReportRPCExceptionsInWebKit':   1,
			'Contexts':              { 'default':       'Examples',
			                           'Admin':         'Admin',
			                           'Examples':      'Examples',
			                           'Documentation': 'Documentation',
			                           'Testing':       'Testing',
			                         },
			'Debug':	{
				'Sessions': 0,
			},
			'OldStyleActions': 0,
		}

	def configFilename(self):
		return self.serverSidePath('Configs/Application.config')

	def configReplacementValues(self):
		return self._server.configReplacementValues()


	## Versions ##

	def version(self):
		"""
		Returns the version of the application. This implementation
		returns '0.1'. Subclasses should override to return the correct
		version number.
		"""
		## @@ 2000-05-01 ce: Maybe this could be a setting 'AppVersion'
		return '0.1'

	def webwareVersion(self):
		""" Returns the Webware version as a tuple. """
		return self._webwareVersion

	def webwareVersionString(self):
		""" Returns the Webware version as a printable string. """
		return self._webwareVersionString

	def webKitVersion(self):
		""" Returns the WebKit version as a tuple. """
		return self._webKitVersion

	def webKitVersionString(self):
		""" Returns the WebKit version as a printable string. """
		return self._webKitVersionString


	## Dispatching Requests ##

	def dispatchRawRequest(self, newRequestDict, strmOut):
		return self.dispatchRequest(self.createRequestForDict(newRequestDict), strmOut)

	def dispatchRequest(self, request, strmOut):
		""" Creates the transaction, session, response and servlet for the new request which is then dispatched. The transaction is returned. """

		assert request is not None
		transaction = None
		if request.value('_captureOut_', 0):
			real_stdout = sys.stdout
			sys.stdout = StringIO()

		transaction = self.createTransactionForRequest(request)
		response	= self.createResponseInTransaction(transaction, strmOut)

		try:
			ssPath = request.serverSidePath()
			if ssPath is None or not os.path.exists(ssPath):
				self.handleBadURL(transaction)
			elif isdir(ssPath) and noslash(request.pathInfo()): # (*) see below
				self.handleDeficientDirectoryURL(transaction)
			elif self.isSessionIdProblematic(request):
				self.handleInvalidSession(transaction)
			elif self.setting('UseAutomaticPathSessions') and not request.hasPathSession():
				self.handleMissingPathSession(transaction)
			else:
				validFile = 1
				baseName = os.path.split(ssPath)[1]
				for patternToHide in self.setting('FilesToHide'):
					if fnmatch(baseName, patternToHide):
						validFile = 0

				patternsToServe = self.setting('FilesToServe')
				if patternsToServe:
					validFile = 0
					for patternToServe in self.setting('FilesToServe'):
						if fnmatch(baseName, patternToServe):
							validFile = 1
				if not validFile:
					self.handleBadURL(transaction)
				else:
					self.handleGoodURL(transaction)

			if request.value('_captureOut_', 0):
				response.write('''<br><p><table><tr><td bgcolor=#EEEEEE>
					<pre>%s</pre></td></tr></table>''' % sys.stdout.getvalue())
				sys.stdout = real_stdout

			response.deliver()

			# (*) We have to use pathInfo() instead of uri() when looking for the trailing slash, because some webservers, notably Apache, append a trailing / to REQUEST_URI in some circumstances even though the user did not specify that (for example: http://localhost/WebKit.cgi).

		except:
			if debug: print "*** ERROR ***"
			if transaction:
				transaction.setErrorOccurred(1)
			self.handleExceptionInTransaction(sys.exc_info(), transaction)
			transaction.response().deliver() # I hope this doesn't throw an exception. :-)   @@ 2000-05-09 ce: provide a secondary exception handling mechanism
			pass


		if self.setting('LogActivity'):
			self.writeActivityLog(transaction)

		path = request.serverSidePath()
		self.returnInstance(transaction, path)

		# possible circular reference, so delete it
		request.clearTransaction()
		response.clearTransaction()

		return transaction

	def handleBadURL(self, transaction):
		res = transaction.response()
		res.setHeader('Status', '404 Error')
##		res.write('<p> 404 Not found: %s' % transaction.request().uri())
		res.write(self._404Page % (transaction.request().uri()))
		# @@ 2000-06-26 ce: This error page is pretty primitive
		# @@ 2000-06-26 ce: We should probably load a separate template file and display that

	def handleDeficientDirectoryURL(self, transaction):
		# @@ 2000-11-29 gat:
		# This splitting and rejoining is necessary in order to handle
		# url's like http://localhost/WebKit.cgi/Examples?foo=1
		# without infinite looping.  I'm not sure this is the "right"
		# way to do this, as it seems to contradict the docstring of
		# uri(), but it works.  Needs further investigation.
		uri = string.split(transaction.request().uri(), '?')
		uriEnd = string.split(uri[0], '/')[-1]
		# @@ gat 2000-05-19: this was changed to use a relative redirect starting with "." to force
		# a client redirect instead of a server redirect.  This fixes problems on IIS.
		uri[0] = './' + uriEnd + '/'
		newURL = string.join(uri, '?')
		if debug: print "* handleDeficientDirectoryURL - reditrect to",newURL
		
		res = transaction.response()
		res.setHeader('Status', '301 Redirect')
		res.setHeader('Location', newURL)
		res.write('''<html>
	<head>
		<title>301 Moved Permanently</title>
	</head>
	<body>
		<h1>Moved Permanently</h1>
		<p> The document has moved to <a href="%s">%s</a>.
	</body>
</html>''' % (newURL, newURL))

	def isSessionIdProblematic(self, request, debug=0):
		"""
		Returns 1 if there is a session id and it's not valid (either because it doesn't exist or because it has expired due to inactivity). Having no session id is not considered problematic.
		This method will also expire the session if it's too old.
		This method is invoked by dispatchRequest() as one of the major steps in handling requests.
		"""
		debug = self.setting('Debug')['Sessions']
		if debug: prefix = '>> [session] isSessionIdProblematic:'
		sid = request.sessionId()
		if sid:
			if self._sessions.has_key(sid):
				if (time()-request.session().lastAccessTime()) >= request.session().timeout():
					if debug: print prefix, 'session expired: %s' % repr(sid)
					del self._sessions[sid]
					problematic = 1
				else:
					problematic = 0
			else:
				if debug: print prefix, 'session does not exist: %s' % repr(sid)
				problematic = 1
		else:
			problematic = 0
		if debug: print prefix, 'isSessionIdProblematic =', problematic, ',  id =', sid
		return problematic

	def handleInvalidSession(self, transaction):
		res = transaction.response()
		debug = self.setting('Debug')['Sessions']
		if debug: prefix = '>> handleInvalidSession:'
		cookie = Cookie('_SID_', '')
		cookie.setPath('/')
		res.addCookie(cookie)
		if debug: print prefix, "set _SID_ to ''"
		if self.setting('IgnoreInvalidSession'):
			# Delete the session ID cookie (and field since session IDs can also
			# be encoded into fields) from the request, then handle the servlet
			# as though there was no session
			try:
				del transaction.request().cookies()['_SID_']
			except KeyError:
				pass
			try:
				transaction.request().delField('_SID_')
			except KeyError:
				pass
			transaction.request().setSessionExpired(1)
			if self.setting('UseAutomaticPathSessions'):
				self.handleMissingPathSession(transaction)
			else:
				self.handleGoodURL(transaction)
		else:
			res.write('''<html> <head> <title>Session expired</title> </head>
				<body> <h1>Session Expired</h1>
				<p> Your session has expired and all information related to your previous working session with this site has been cleared. <p> You may try this URL again by choosing Refresh/Reload, or revisit the front page.
				</body>
				</html>
				''')
			# @@ 2000-08-10 ce: This is a little cheesy. We could load a template...

	def handleMissingPathSession(self,transaction):
		"""
		if UseAutomaticPathSessions is enabled in Application.config
		we redirect the browser to a url with SID in path
		http://gandalf/a/_SID_=2001080221301877755/Examples/
		_SID_ is extracted and removed from path in HTTPRequest.py

		this is for convinient building of webapps that must not
		depend on cookie support
		"""
		newSid = transaction.session().identifier()
		request = transaction.request()
		url = request.adapterName() + '/_SID_='+ newSid + '/' + request.pathInfo() + (request.extraURLPath() or '')

		if request.queryString():
			url = url + '?' + request.queryString()
		if self.setting('Debug')['Sessions']:
			print ">> [sessions] handling UseAutomaticPathSessions, redirecting to", url
		transaction.response().sendRedirect(url)

	def handleGoodURL(self, transaction):
		self.createServletInTransaction(transaction)
		try:
			self.awake(transaction)
			try:
				self.respond(transaction)
			except EndResponse:
				pass
			self.sleep(transaction)
		except EndResponse:
			pass

	def processURLPath(self, req, URL):
		"""
		Return a URL Path relative to the current request and context.
		Absolute references in the URL (starting with '/' are treated
		absolute to the current context.
		"""
		
		# Construct the url path for the servlet we're calling
		urlPath = req.urlPath()
		if urlPath=='':
			urlPath = '/'
		elif urlPath[-1]=='/':
			urlPath = urlPath
		else:
			lastSlash = string.rfind(urlPath, '/')
			urlPath = urlPath[:lastSlash+1] 

		extraPath = ''
		if URL[:1] == "/":
			extraPath = req.siteRootFromCurrentServlet()

		urlPath = WebUtils.Funcs.normURL(urlPath + extraPath + URL)

		if debug:
			print "*processURLPath(%s)=%s" % (URL, urlPath)

		return urlPath

	def forward(self, trans, URL):
		"""
		Enable a servlet to pass a request to another servlet. The Request object is kept the same, and may be used
		to pass information to the next servlet.  The next servlet may access the parent servlet through request.parent(),
		which will return the parent servlet.  The first servlet will not be able to send any new response data once
		the call to forwardRequest returns.
		New Response and Transaction objects are created.
		Currently the URL is always relative to the existing URL.

		NOTE: @@ sgd 2003-01-15 - presently this goes through dispatchRequest() which
		under some circumstances can result in sending a redirect() which causes the
		browser to re-get the URL.  This defeats the purpose of passing information
		to a servlet in the request or transaction objects.  This only happens in
		cases like a forward to a directory where no trailing / was specified.
		"""

		# @@ sgd 2003-01-15
		# to fix the above warning about using dispatchRequest() consider
		# using the includeURL() code but handle the session and clearing
		# the output stream here.
		
		if debug: print "> forward(%s)" % str(URL)

		req = trans.request()

		urlPath = self.processURLPath(req, URL)
		
		#save the original URL
		oldURL = req.urlPath()
		req.setURLPath(urlPath)

		#add a reference to the parent servlet
		req.addParent(req.transaction()._servlet)

		# Store the session so that the new servlet can access its values
		if trans.hasSession():
			self._sessions.storeSession(trans.session())

		# We might have created a brand-new session prior to this call.  If so, we need
		# to set the _SID_ identifier in the request so that the new transaction will
		# know about the new session.
		# gat 200-06-21: this feels like a hack, but it is necessary to prevent losing
		# session information.
		if trans.hasSession() and not req.hasValue('_SID_'):
			if debug: print 'Application.forward(): propagating new session ID into request'
			req.setField('_SID_', trans.session().identifier())

		#get the output stream and set it in the new response
		strmOut = req.transaction().response().streamOut()
		strmOut.clear()
		newTrans = self.dispatchRequest(req, strmOut)
		req.popParent()
		req.setURLPath(oldURL)

		#give the old response a dummy streamout- nasty hack, better idea anyone?
		trans.response()._strmOut = ASStreamOut()
		req._transaction = trans  #this is needed by dispatchRequest

		# Get rid of the session in the old transaction so it won't try to save it,
		# thereby wiping out session changes made in the servlet we forwarded to
		trans.setSession(None)


	def forwardRequest(self, trans, URL):
		print "forwardRequest is deprecated.  Use forward()"
		return self.forward(trans, URL)
		
	def includeURL(self, trans, URL):
		"""
		Enable a servlet to pass a request to another servlet.  This implementation
		handles chaining and requestDispatch in Java.

		The Request, Rssponse and Session objects are all kept the same, so the Servlet
		that is called may receive information through those objects.  The catch is that
		the function WILL return to the calling servlet, so the calling servlet should either
		take advantage of that or return immediately.
		Also, if the response has already been partially sent, it can't be reversed.
		"""

		if debug: print "> includeURL(%s)" % str(URL)

		req = trans.request()

		#Save the things we're gonna change.
		currentPath=req.urlPath()
		currentServlet=trans._servlet

		urlPath = self.processURLPath(req, URL)
		
		req.setURLPath(urlPath)
		req.addParent(currentServlet)

		#Get the new servlet
		self.createServletInTransaction(trans)

		#call the servlet, but not session, it's already alive
		try:
			trans.servlet().awake(trans)
			try:
				trans.servlet().respond(trans)
			except EndResponse:
				pass
			trans.servlet().sleep(trans)
		except EndResponse:
			pass

		self.returnInstance(trans,trans.request().serverSidePath())

		#replace things like they were
		#trans.request()._serverSidePath=currentPath
		req.setURLPath(currentPath)
		req.popParent()
		trans._servlet=currentServlet


	def forwardRequestFast(self, trans, url):
		print "forwardRequestFast is deprecated.  Use includeURL()"
		return self.includeURL(trans, url)

	def callMethodOfServlet(self, trans, URL, method, *args, **kwargs):
		"""
		Enable a servlet to call a method of another servlet.  Note: the servlet's awake() is called,
		then the method is called with the given arguments, then sleep() is called.  The result
		of the method call is returned.
		"""
		req = trans.request()

		if debug: print "> callMethodOfServlet(%s, %s)" % (URL, method)

		# Save the current url path and servlet
		currentPath = req.urlPath()
		currentServlet = trans._servlet

		urlPath = self.processURLPath( req, URL )
		
		# Modify the request to use the new URL path
		req.setURLPath(urlPath)

		# Add the current servlet as a parent
		req.addParent(currentServlet)

		# Get the new servlet
		self.createServletInTransaction(trans)

		# Awaken, call the method, and sleep
		servlet = trans.servlet()

		try:
			servlet.awake(trans)
			try:
				result = getattr(servlet, method)(*args, **kwargs)
			except EndResponse:
				pass
			servlet.sleep(trans)
		except EndResponse:
			pass

		# Return the servlet instance to the cache
		self.returnInstance(trans, trans.request().serverSidePath())

		# Replace things like they were
		req.setURLPath(currentPath)
		req.popParent()
		trans._servlet=currentServlet

		# Done
		return result
	
	## Transactions ##

	def awake(self, transaction):
		transaction.awake()

	def respond(self, transaction):
		transaction.respond()

	def sleep(self, transaction):
		transaction.sleep()
		# Store the session
		if transaction.hasSession():
			self._sessions.storeSession(transaction.session())


	## Sessions ##

	def session(self, sessionId, default=NoDefault):
		if default is NoDefault:
			return self._sessions[sessionId]
		else:
			return self._sessions.get(sessionId, default)

	def hasSession(self, sessionId):
		return self._sessions.has_key(sessionId)

	def sessions(self):
		return self._sessions


	## Misc Access ##

	def server(self):
		return self._server

	def serverSidePath(self, path=None):
		"""	Returns the absolute server-side path of the WebKit application. If the optional path is passed in, then it is joined with the server side directory to form a path relative to the app server.
		"""
		if path:
			return os.path.normpath(os.path.join(self._serverSidePath, path))
		else:
			return self._serverSidePath

	def webwarePath(self):
		return self._server.webwarePath()

	def webKitPath(self):
		return self._server.webKitPath()


	def name(self):
		return sys.argv[0]

	def transactionClass(self):
		return self._transactionClass

	def setTransactionClass(self, newClass):
		assert isclass(newClass)
		self._transactionClass = newClass

	def responseClass(self, newClass):
		return self._responseClass

	def setResponseClass(self, newClass):
		assert isclass(newClass)
		self._responseClass = newClass


	## Contexts ##

	def context(self, name, default=NoDefault):
		""" Returns the value of the specified context. """
		if default is NoDefault:
			return self._contexts[name]
		else:
			return self._contexts.get(name, default)

	def hasContext(self, name):
		return self._contexts.has_key(name)

	def _setContext(self, name, value):#use addContext
		if self._contexts.has_key(name):
			print 'WARNING: Overwriting context %s (=%s) with %s' % (
				repr(name), repr(self._contexts[name]), repr(value))
		self._contexts[name] = value

	def contexts(self):
		return self._contexts

	def addContext(self, name, dir):
		if self._contexts.has_key(name):
			print 'WARNING: Overwriting context %s (=%s) with %s' % (
				repr(name), repr(self._contexts[name]), repr(dir))
			__contextInitialized = 1 # Assume already initialized.
		else:
			__contextInitialized = 0
			
		try:
			importAsName = name
			localdir, pkgname = os.path.split(dir)
			if sys.modules.has_key(importAsName):
				mod = sys.modules.get(importAsName)
			else:
				res = imp.find_module(pkgname, [localdir])
				mod = imp.load_module(name, res[0], res[1], res[2])
				__contextInitialized = 0  # overwriting context - re-initialize
				
		except ImportError,e:
			print "Error loading context: %s: %s: dir=%s" % (name, e, dir)
			return

		if not __contextInitialized and mod.__dict__.has_key('contextInitialize'):
			result = mod.__dict__['contextInitialize'](self,
								   os.path.normpath(os.path.join(os.getcwd(),dir)))
			if result != None and result.has_key('ContentLocation'):
				dir = result['ContentLocation']
		print 'Loading context: %s at %s' % (name, dir)
		self._contexts[name] = dir


	## Factory access ##

	def addServletFactory(self, factory):
		assert isinstance(factory, ServletFactory)
		self._factoryList.append(factory)
		for ext in factory.extensions():
			assert not self._factoryByExt.has_key(ext), 'Extension (%s) for factory (%s) was already used by factory (%s)' % (ext, self._factoryByExt[ext].name(), factory.name())
			self._factoryByExt[ext] = factory

	def factories(self):
		return self._factoryList


	## Activity Log ##

	def writeActivityLog(self, transaction):
		"""
		Writes an entry to the script log file. Uses settings ActivityLogFilename and ActivityLogColumns.
		"""
		filename = self.serverSidePath(self.setting('ActivityLogFilename'))
		if os.path.exists(filename):
			file = open(filename, 'a')
		else:
			file = open(filename, 'w')
			file.write(string.join(self.setting('ActivityLogColumns'), ',')+'\n')
		values = []
		# We use UserDict on the next line because we know it inherits NamedValueAccess and reponds to valueForName()
		objects = UserDict({
			'application': self,
			'transaction': transaction,
			'request':	 transaction.request(),
			'response':	transaction.response(),
			'servlet':	 transaction.servlet(),
			'session':	 transaction._session, #don't cause creation of session
		})
		for column in self.setting('ActivityLogColumns'):
			try:
				value = objects.valueForName(column)
			except:
				value = '(unknown)'
			if type(value) is FloatType:
				value = '%0.2f' % value   # probably need more flexibility in the future
			else:
				value = str(value)
			values.append(value)
		file.write(string.join(values, ',')+'\n')
		file.close()

		for i in objects.keys():
			objects[i]=None


	## Utilities/Hooks ##

	def createRequestForDict(self, newRequestDict):
		return self._requestClass(dict=newRequestDict)

	def createTransactionForRequest(self, request):
		trans = self._transactionClass(application=self, request=request)
		request.setTransaction(trans)
		return trans

	def createResponseInTransaction(self, transaction, strmOut):
		response = self._responseClass(transaction, strmOut)
		transaction.setResponse(response)
		return response

	def createSessionForTransaction(self, transaction):
		debug = self.setting('Debug')['Sessions']
		if debug: prefix = '>> [session] createSessionForTransaction:'
		sessId = transaction.request().sessionId()
		if debug: print prefix, 'sessId =', sessId
		if sessId:
			session = self.session(sessId)
			if debug: print prefix, 'retrieved session =', session
		else:
			session = self._sessionClass(transaction)
			self._sessions[session.identifier()] = session
			if debug: print prefix, 'created session =', session
		transaction.setSession(session)
		return session

	def getServlet(self, transaction, path, cache=None): #send the cache if you want the cache info set
		ext = os.path.splitext(path)[1]
		# Add the path to sys.path. @@ 2000-05-09 ce: not the most ideal solution, but works for now
		dir = os.path.dirname(path)

		factory = self._factoryByExt.get(ext, None)
		if not factory:
			factory = self._factoryByExt.get('.*', None) # special case: .* is the catch-all
			if not factory:
				raise ApplicationError, 'Unknown extension (%s). No factory found.' % ext
			# ^ @@ 2000-05-03 ce: Maybe the web browser doesn't want an exception for bad extensions. We probably need a nicer message to the user...
			#					 On the other hand, that can always be done by providing a factory for '.*'
		assert factory.uniqueness()=='file', '%s uniqueness is not supported.' % factory.uniqueness()

		# @@ 2001-05-10 gat: removed this because it allows 2 different copies of the same
		# module to be imported, one as "foo" and one as "context.foo".
		#if not dir in sys.path:
		#	sys.path.insert(0, dir)
		inst = factory.servletForTransaction(transaction)
		assert inst is not None, 'Factory (%s) failed to create a servlet upon request.' % factory.name()

		if cache:
			cache['threadsafe']=inst.canBeThreaded()
			cache['reuseable']=inst.canBeReused()
		return inst

	def returnInstance(self, transaction, path):
		""" The only case I care about now is threadsafe=0 and reuseable=1"""
		cache = self._servletCacheByPath.get(path, None)
		if cache and cache['reuseable'] and not cache['threadsafe']:
			srv = transaction.servlet()
			if srv:
				cache['instances'].append(transaction.servlet())
				return

	def newServletCacheItem(self,key,item):
		""" Safely add new item to the main cache.  Not worried about the retrieval for now.
		I'm not even sure this is necessary, as it's a one bytecode op, but it doesn't cost
		much of anything speed wise.
		"""
		#self._cacheDictLock.acquire()
		self._servletCacheByPath[key] = item
		#self._cacheDictLock.release()

	def flushServletCache(self):
		self._servletCacheByPath = {}

	def createServletInTransaction(self, transaction):
		# Get the path
		path = transaction.request().serverSidePath()
		assert path is not None

		inst = None
		cache = None


		# Cached?
		if self._cacheServletInstances:
			cache = self._servletCacheByPath.get(path, None)

		# File is not newer?
		if cache and cache['timestamp']<os.path.getmtime(path):
			cache['instances'][:] = []
			cache = None

		if not cache:
			cache = {
				'instances':  [],
				'path':	      path,
				'timestamp':  os.path.getmtime(path),
				'threadsafe': 0,
				'reuseable':  0,
				}

			self.newServletCacheItem(path,cache)
			inst = self.getServlet(transaction,path,cache)

			if cache['threadsafe']:
				"""special case, put in the cache now"""
				cache['instances'].append(inst)

		# Instance can be reused?
		elif not cache['reuseable']:
			# One time servlet
			inst = self.getServlet(transaction, path)

		elif not cache['threadsafe']:
			# Not threadsafe, so need multiple instances
			try:
				inst = cache['instances'].pop()
			except IndexError: # happens if list was empty
				inst = self.getServlet(transaction, path)

		else:
			# Must be reuseable and threadsafe - just use the instance in the cache
			# without removing it
			inst = cache['instances'][0]

		# Set the transaction's servlet
		transaction.setServlet(inst)

	def handleExceptionInTransaction(self, excInfo, transaction):
		if self._exceptionHandlerClass is None:
			self._exceptionHandlerClass = ExceptionHandler
		self._exceptionHandlerClass(self, transaction, excInfo)

	def handleException(self, excInfo=None):
		"""Handle the exception by calling the configured ExceptinHandler.
		Note that the exception handler must be capable of taking
		a transaction of None for exceptions that occur outside of
		a transaction.
		"""
		if excInfo is None:
			excInfo = sys.exc_info()
		if self._exceptionHandlerClass is None:
			self._exceptionHandlerClass = ExceptionHandler
		self._exceptionHandlerClass(self, None, excInfo)

	def filenamesForBaseName(self, baseName):

		"""Returns a list of all filenames with extensions existing for
		baseName, but not including extension found in the setting
		ExtensionsToIgnore. This utility method is used by
		serverSideInfoForRequest().  Example: '/a/b/c' could yield
		['/a/b/c.py', '/a/b/c.html'], but will never yield a
		'/a/b/c.pyc' filename since .pyc files are ignored."""

		if string.find(baseName, '*') >= 0:
			return []
		filenames = []
		ignoreExts = self.setting('ExtensionsToIgnore')
		for filename in glob(baseName+'.*'):
			# consider this because CVS leaves files with extensions like '*.py.~1.2.3~'
			# filename[-1:] == '~':	continue
			if os.path.splitext(filename)[1] not in ignoreExts:
				# @@ 2000-06-22 ce: linear search
				filenames.append(filename)

		extensionsToServe = self.setting('ExtensionsToServe')
		if extensionsToServe:
			filteredFilenames = []
			for filename in filenames:
				if os.path.splitext(filename)[1] in extensionsToServe:
					filteredFilenames.append(filename)
			filenames = filteredFilenames

		if debug:
			print '>> filenamesForBaseName(%s) returning %s' % (
				repr(baseName), repr(filenames))
		return filenames

	def defaultContextNameAndPath(self):
		"""
		Returns the default context name and path in a tuple.  If there's an explicitly named context with the same
		path as the "default" context, then we'll use that name instead.  Otherwise, we'll just
		use "default" as the name.
		"""
		if not self._defaultContextName:
			defaultContextPath = self._contexts['default']
			for contextName, contextPath in self._contexts.items():
				if contextPath == defaultContextPath:
					self._defaultContextName = contextName
					break
			else:
				self._defaultContextName = 'default'
		return self._defaultContextName, self.context(self._defaultContextName)



	def serverSideInfoForRequest(self, request):
		"""
		Returns a tuple (requestPath, contextPath, contextName) where requestPath is
		the server-side path of this request, contextPath is the
		server-side path of the context for this request, and contextName is the
		name of the context, which is not necessarily the same as the name
		of the directory that houses the context.
		This is a 'private' service method for use by HTTPRequest.
		Returns (None, None, None) if there is no corresponding server side path for the URL.

		This method supports:
			* Contexts
			* A default context
			* Auto discovery of directory vs. file
			* For directories, auto discovery of file, configured by DirectoryFile
			* For files, auto discovery of extension, configured by ExtensionsToIgnore
			* Rejection of files (not directories) that end in a slash (/)
			* "Extra path" URLs where the servlet is actually embedded in the path
			  as opposed to being at the end of it. (ex: http://foo.com/servlet/extra/path).
			  The ExtraPath information will be available through request.extraPathInfo().
			  The Application.config file must have ExtraPathInfo set to 1 for this to be functional.

		IF YOU CHANGE THIS VERY IMPORTANT, SUBTLE METHOD, THEN PLEASE REVIEW
		AND COMPLETE http://localhost/WebKit.cgi/Testing/ BEFORE CHECKING IN
		OR SUBMITTING YOUR CHANGES.
		"""

		debug=0
		extraURLPath=''

		urlPath = request.urlPath()
		if debug: print '>> urlPath =', repr(urlPath)

		##if the requested file is in the filesystem outside of any context...
		if request._absolutepath:
			if isdir(urlPath):
				urlPath = self.findDirectoryIndex(urlPath, debug)
			return urlPath, None, None  #no contextpath, no contextname

		# try the cache first
		ssPath, contextPath, contextName = self._serverSideInfoCacheByPath.get(urlPath, (None, None, None))
		if ssPath is not None:
			if debug: print '>> returning path from cache: %s' % repr(ssPath)
			return ssPath, contextPath, contextName


		# case: no URL then use the default context
		if urlPath=='' or urlPath=='/':
			contextName, ssPath = self.defaultContextNameAndPath()
			if debug:
				print '>> no urlPath, so using default context %s at path: %s' % (contextName, ssPath)
		else:
			# Check for and process context name:
			assert urlPath[0]=='/', 'urlPath=%s' % repr(urlPath)
			if string.rfind(urlPath, '/')>0: # no / in url (other than the preceding /)
				blank, contextName, restOfPath = string.split(urlPath, '/', 2)
			else:
				contextName, restOfPath = urlPath[1:], ''
			if debug: print '>> contextName=%s, restOfPath=%s' % (repr(contextName), repr(restOfPath))

			# Look for context
			try:
				prepath = self._contexts[contextName]
			except KeyError:
				restOfPath = urlPath[1:]  # put the old path back, there's no context here
				contextName, prepath = self.defaultContextNameAndPath()
				if debug:
					print '>> context not found so assuming default:'
			if debug: print '>> ContextName=%s, prepath=%s, restOfPath=%s' % (contextName, repr(prepath), repr(restOfPath))
			#ssPath = os.path.join(prepath, restOfPath)
			if restOfPath != '':
				ssPath = prepath + os.sep + restOfPath
			else:
				ssPath = prepath
			if debug: print ">> ssPath= %s" % ssPath

		contextPath = self._contexts[contextName]

		lastChar = ssPath[-1]
		ssPath = os.path.normpath(ssPath)

		# 2000-07-06 ce: normpath() chops off a trailing / (or \)
		# which is NOT what we want. This makes the test case
		# http://localhost/WebKit.cgi/Welcome/ pass when it should
		# fail. URLs that name files must not end in slashes because
		# relative URLs in the resulting document will get appended
		# to the URL, instead of replacing the last component.
		if lastChar=='\\' or lastChar=='/':
			if debug: print "lastChar was %s" % lastChar
			ssPath = ssPath + os.sep

		if debug: print '>> normalized ssPath =', repr(ssPath)


		if self.setting('ExtraPathInfo'):  #check for extraURLPath
			ssPath, urlPath, extraURLPath = self.processExtraURLPath(ssPath, urlPath, debug)
			request.setURLPath(urlPath)
			request._extraURLPath = extraURLPath

			##Finish extraURLPath checks
			##Check cache again
			cachePath, cacheContextPath, cacheContextName = self._serverSideInfoCacheByPath.get(urlPath, (None, None, None))
			if cachePath is not None:
				if debug:
					print 'checked cache for urlPath %s' % urlPath
					print '>> returning path for %s from cache: %s' % (repr(ssPath), repr(cachePath))
				return cachePath, cacheContextPath, cacheContextName


		if isdir(ssPath):
			# URLs that map to directories need to have a trailing slash.
			# If they don't, then relative links in the web page will not be
			# constructed correctly by the browser.
			# So in the following if statement, we're bailing out for such URLs.
			# dispatchRequest() will detect the situation and handle the redirect.

			if debug: print ">> ssPath is a directory"
			if extraURLPath == '' and (urlPath=='' or urlPath[-1]!='/'):
				if debug:
					print '>> BAILING on directory url: %s' % repr(urlPath)
				return ssPath, contextPath, contextName


			ssPath = self.findDirectoryIndex(ssPath, debug)

		elif os.path.splitext(ssPath)[1]=='':
			# At this point we have a file (or a bad path)
			filenames = self.filenamesForBaseName(ssPath)
			if len(filenames)==1:
				ssPath = filenames[0]
				if debug: print '>> discovered extension, file = %s' % repr(ssPath)
			elif len(filenames) > 1:
				foundMatch = 0
				if self.setting('UseCascadingExtensions'):
					for ext in self.setting('ExtensionCascadeOrder'):
						if (ssPath + ext) in filenames:
							ssPath = ssPath + ext
							foundMatch = 1
							break
				if not foundMatch:
					print 'WARNING: For %s, did not get precisely 1 filename: %s' %\
					      (urlPath, filenames)
					return None, None, None
			else:
				return None, None, None

		elif not os.path.isfile(ssPath):
			return None, None, None

		self._serverSideInfoCacheByPath[urlPath] = ssPath, contextPath, contextName

		if debug:
			print '>> returning %s, %s, %s\n' % (repr(ssPath), repr(contextPath), repr(contextName))
		return ssPath, contextPath, contextName


	def findDirectoryIndex(self, ssPath, debug=0):
		"""
		Given a url that points to a directory, find an index file in that directory.
		"""
		# URLs that map to directories need to have a trailing slash.
		# If they don't, then relative links in the web page will not be
		# constructed correctly by the browser.
		# So in the following if statement, we're bailing out for such URLs.
		# dispatchRequest() will detect the situation and handle the redirect.

		# Handle directories
		if debug: print '>> directory = %s' % repr(ssPath)
		for dirFilename in self.setting('DirectoryFile'):
			filenames = self.filenamesForBaseName(os.path.join(ssPath, dirFilename))
			num = len(filenames)
			if num==1:
				break  # we found a file to handle the directory
			elif num>1:
				print 'WARNING: the directory is %s which contains more than 1 directory file: %s' % (ssPath, filenames)
				return None
		if num==0:
			if debug: print 'WARNING: For %s, the directory contains no directory file.' % (ssPath)
			return None
		ssPath = filenames[0] # our path now includes the filename within the directory
		if debug: print '>> discovered directory file = %s' % repr(ssPath)
		return ssPath


	def processExtraURLPath(self, ssPath, urlPath, debug=0):
		"""
		given a server side path (ssPath) and the original request URL (urlPath), determine which portion of the URL is a request path and which portion is extra request information.
		Return a tuple of:
		ssPath: the corrected (truncted) ssPath,
		urlPath:  the corrected (trunctated) urlPath,
		extraPathInfo: the extra path info
		"""
		extraURLPath = ''

		if debug: print "*** processExtraURLPath starting for ssPath=", ssPath
		if os.path.exists(ssPath):  ##bail now if the whole thing exists
			if debug: print "*** entire ssPath exists"
			return ssPath, urlPath, ''

		if debug: print "starting ssPath=%s, urlPath=%s " % (ssPath, urlPath)
		goodindex = 0  #this marks the last point where the path exists

		index = string.find(ssPath, os.sep)
		if index == -1: return ssPath, urlPath, extraURLInfo  ##bail if no seps found
		if not index: index=1  #start with at least one character

		if debug: print "testing ", ssPath[:index]

		while os.path.exists(ssPath[:index]) and index != -1:
			goodindex = index
			index = string.find(ssPath, os.sep, index+1)
			if debug: print "testing ", ssPath[:index]
		if debug: print "quitting loop with goodindex= ",ssPath[:goodindex]

		if index != -1: ##there is another slash, but we already know its invalid
			if debug: print "last loop got an index of -1"
			searchpath = ssPath[:index]
		else:    #no more slashes, so the last element is either a file without an extension, or the real URL is a directory and the last piece is extraURLInfo
			searchpath = ssPath


		## Now test to see if the next element is a file without an extension
		filenames = self.filenamesForBaseName(searchpath)
		if debug: print "found %s valid files" % len(filenames)
		if len(filenames)>0:
			extralen=0

		else:
			extralen = len(ssPath) - goodindex
			if isdir(ssPath[:goodindex]):
				extralen = extralen-1  ##leave the last slash on the path



		if extralen > 0:
			urlPath, extraURLPath = urlPath[:-extralen] , urlPath[-extralen:]
			ssPath = ssPath[:-extralen]

		if extraURLPath and extraURLPath[0] != '/':
			extraURLPath = '/' + extraURLPath
		if debug: print "processExtraURLPath returning %s, %s, %s" % ( ssPath, urlPath, extraURLPath )
		return ssPath, urlPath, extraURLPath

	def writeExceptionReport(self, handler):
		# Nothing particularly useful that I can think of needs to be
		# added to the exception reports by the Application.
		# See ExceptionHandler.py for more info.
		pass


	## New Path Algorithm ##

	def serverSideInfoForRequestNewAlgorithm(self, request):
		"""
		Returns a tuple (requestPath, contextPath,
		contextName) where requestPath is the server-side path
		of this request, contextPath is the server-side path
		of the context for this request, and contextName is
		the name of the context, which is not necessarily the
		same as the name of the directory that houses the
		context.
		
		Returns (None, None, None) if there is no
		corresponding server side path for the URL.
		"""

		fullPath = request.urlPath()
		contextPath, contextName, rest = self.findContext(fullPath)
		servletPath, extraPath = self.findServlet(contextPath, rest)
		request._extraURLPath = extraPath
		if debug: print "> ssifr na:",(servletPath, contextPath, contextName, extraPath, request.urlPath())
		return (servletPath, contextPath, contextName)


	def findContext(self, fullPath):
		"""
		Internal method: returns (contextPath, contextName, restOfPath)
		restOfPath will start with a /
		"""

		assert not fullPath or fullPath[0] == '/'
		if not fullPath or fullPath == '/':
			contextName, contextPath = self.defaultContextNameAndPath()
			return (contextPath, contextName, fullPath)
		pathParts = string.split(fullPath, '/', 2)
		if len(pathParts) == 3:
			blank, first, rest = pathParts
		elif len(pathParts) == 2:
			first, rest = pathParts[1], ''
		else:
			first, rest = '', ''
		if not self._contexts.has_key(first):
			contextName, contextPath = self.defaultContextNameAndPath()
			return (contextPath, contextName, fullPath)
		else:
			return (self._contexts[first], first, '/' + rest)

	def findServlet(self, contextPath, urlPath):
		"""
		Internal method: returns (servletPath, extraURLPath)
		extraURLPath will start with '/' (unless no extraURLPath
		was given, in which case extraURLPath will be '')
		"""
		cache = self._serverSideInfoCacheByPathNew
		if cache.has_key(urlPath):
			return (cache[urlPath], '')
		parts = string.split(urlPath, '/')
		for i in range(len(parts)):
			url = string.join(parts[:-i], '/')
			if cache.has_key(url):
				return cache[url], '/' + string.join(parts[-i:], '/')
		currentPath = contextPath
		while 1:
			if not parts:
				filename = self.findDirectoryIndex(currentPath)
				if filename:
					return (filename, '')
				else:
					return None, None # 404 Not Found
			first = parts[0]
			if os.path.isdir(os.path.join(currentPath, first)):
				currentPath = os.path.join(currentPath, first)
				parts = parts[1:]
				continue
			filenames = self.filenamesForBaseNameNew(os.path.join(currentPath, first))
			if filenames:
				if len(filenames) == 1:
					return (filenames[0], 
						'/' + string.join(parts[1:], '/'))
				print "WARNING: More than one file matches basename %s (%s)" % (repr(os.path.join(currentPath, first)), filenames)
				return None, None
			else:
				filename = self.findDirectoryIndex(currentPath)
				if filename:
					return (filename, '/' + string.join(parts, '/'))

				return None, None

	def filenamesForBaseNameNew(self, baseName):
		if string.find(baseName, '*') != -1:
			return []
		filenames = glob(baseName + "*")
		good = []
		toIgnore = self.setting('ExtensionsToIgnore')
		toServe = self.setting('ExtensionsToServe')
		for filename in filenames:
			ext = os.path.splitext(filename)[1]
			shortFilename = os.path.basename(filename)
			if ext in toIgnore and filename != baseName:
				continue
			if toServe and ext not in toServe:
				continue
			for regex in self._filesToHideRegexes:
				if regex.match(shortFilename):
					continue
			if self._filesToServeRegexes:
				shouldServe = 0
				for regex in self._filesToServeRegexes:
					if regex.match(shortFilename):
						shouldServe = 1
						break
				if not shouldServe:
					continue
			good.append(filename)
		if len(good) > 1 and self.setting('UseCascadingExtensions'):
			for extension in self.setting('ExtensionCascadeOrder'):
				actualExtension = os.path.splitext(baseName)[1]
				if baseName + extension in good \
				   or extension == actualExtension:
					return [baseName + extension]
		return good



	## Deprecated ##

	def serverSidePathForRequest(self, request, debug=0):
		"""
		This is maintained for backward compatibility; it just returns the first part of the tuple
		returned by serverSideInfoForRequest.
		"""
		self.deprecated(self.serverSidePathForRequest)
		return self.serverSideInfoForRequest(request, debug)[0]

	def serverDir(self):
		"""
		deprecated: Application.serverDir() on 1/24 in ver 0.5, use serverSidePath() instead @
		Returns the directory where the application server is located.
		"""
		self.deprecated(self.serverDir)
		return self.serverSidePath()




def isdir(s):
	"""
	*** Be sure to use this isdir() function rather than os.path.isdir()
		in this file.

	2000-07-06 ce: Only on Windows, does an isdir() call with a
	path ending in a slash fail to return 1. e.g.,
	isdir('C:\\tmp\\')==0 while on UNIX isdir('/tmp/')==1.
	"""
	if s and os.name=='nt' and s[-1]==os.sep:
		return os.path.isdir(s[:-1])
	else:
		return os.path.isdir(s)

def noslash(s):
	""" Return 1 if s is blank or does end in /.  A little utility for dispatchRequest(). """
	return s=='' or s[-1]!='/'


def main(requestDict):
	"""
	Returns a raw reponse. This method is mostly used by OneShotAdapter.py.
	"""
	from WebUtils.HTMLForException import HTMLForException
	try:
		assert type(requestDict) is type({})
		app = Application(useSessionSweeper=0)
		return app.dispatchRawRequest(requestDict).response().rawResponse()
	except:
		return {
			'headers': [('Content-type', 'text/html')],
			'contents': '<html><body>%s</html></body>' % HTMLForException()
		}


# You can run Application as a main script, in which case it expects a single
# argument which is a file containing a dictionary representing a request. This
# technique isn't very popular as Application itself could raise exceptions
# that aren't caught. See CGIAdapter.py and AppServer.py for a better example of
# how things should be done.
if __name__=='__main__':
	if len(sys.argv)!=2:
		sys.stderr.write('WebKit: Application: Expecting one filename argument.\n')
	requestDict = eval(open(sys.argv[1]).read())
	main(requestDict)
