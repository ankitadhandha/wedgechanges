from Common import *
from Request import Request
from WebKit.Cookie import CookieEngine
Cookie = CookieEngine.SimpleCookie
import os, cgi, sys, traceback
from types import ListType
from WebUtils.Funcs import requestURI
from WebUtils import FieldStorage

debug=0

class HTTPRequest(Request):
	"""
	FUTURE
		* How about some documentation?
		* The "Information" section is a bit screwed up. Because the WebKit server adapter is a CGI script, these values are oriented towards that rather than the servlet.
	"""


	## Initialization ##

	def __init__(self, dict={}):
##		import pprint
##		pprint.pprint(dict)
		Request.__init__(self)
		self._parents = []
		if dict:
			# Dictionaries come in from web server adapters like the CGIAdapter
			assert dict['format']=='CGI'
			self._time    = dict['time']
			self._environ = dict['environ']
			self._input   = dict['input']
			self._fields  = FieldStorage.FieldStorage(self._input, environ=self._environ, keep_blank_values=1, strict_parsing=0)
			self._fields.parse_qs()
			self._cookies = Cookie()
			if self._environ.has_key('HTTP_COOKIE'):
				# Protect the loading of cookies with an exception handler, because some cookies
				# from IE are known to break the cookie module.
				try:
					self._cookies.load(self._environ['HTTP_COOKIE'])
				except:
					traceback.print_exc(file=sys.stderr)
		else:
			# If there's no dictionary, we pretend we're a CGI script and see what happens...
			import time
			self._time    = time.time()
			self._environ = os.environ.copy()
			self._input   = None
			self._fields  = cgi.FieldStorage(keep_blank_values=1)
			self._cookies = Cookie()

		# Debugging
		if 0:
			f = open('env.text', 'a')
			save = sys.stdout
			sys.stdout = f
			print '>> env for request:'
			keys = self._environ.keys()
			keys.sort()
			for key in keys:
				print '%s: %s' % (repr(key), repr(self._environ[key]))
			print
			sys.stdout = save
			f.close()

		# Fix up environ if it doesn't look right.

		# Fix #1: No PATH_INFO
		# This can happen when there is no extra path info past the adapter.
		# e.g., http://localhost/WebKit.cgi
		if not self._environ.has_key('PATH_INFO'):
			self._environ['PATH_INFO'] = ''

		# Fix #2: No REQUEST_URI
		# REQUEST_URI isn't actually part of the CGI standard and some
		# web servers like IIS don't set it (as of 8/22/2000).
		if not self._environ.has_key('REQUEST_URI'):
			self._environ['REQUEST_URI'] = requestURI(self._environ)

		self._adapterName = self._environ.get('SCRIPT_NAME', '')

		# We use the cgi module to get the fields, but then change them into an ordinary dictionary of values
		try:
			keys = self._fields.keys()
		except TypeError:
			# This can happen if, for example, the request is an XML-RPC request, not
			# a regular POST from an HTML form.  In that case we just create an empty
			# set of fields.
			keys = []
		dict = {}

		for key in keys:
			value = self._fields[key]
			if type(value) is not ListType:
				if value.filename:
					if debug: print "Uploaded File Found"
				else:
					value = value.value # i.e., if we don't have a list, we have one of those cgi.MiniFieldStorage objects. Get it's value.
			else:
				value = map(lambda miniFieldStorage: miniFieldStorage.value, value) # extract those .value's

			dict[key] = value
		self._fieldStorage = self._fields
		self._fields = dict
		self._pathInfo = None

		# We use Tim O'Malley's Cookie class to get the cookies, but then change them into an ordinary dictionary of values
		dict = {}
		for key in self._cookies.keys():
			dict[key] = self._cookies[key].value
		self._cookies = dict

		self._transaction    = None
		self._serverRootPath = ""
		self._extraURLPath  = ""

		# try to get automatic path session
		# if UseAutomaticPathSessions is enabled in Application.config
		# Application.py redirects the browser to a url with SID in path 
		# http://gandalf/a/_SID_=2001080221301877755/Examples/
		# _SID_ is extracted and removed from path 
		self._pathSession = None
		if self._environ['PATH_INFO'][1:6] == '_SID_':
			self._pathSession = self._environ['PATH_INFO'][7:].split('/',1)[0]
			self._cookies['_SID_'] = self._pathSession
			sidstring = '_SID_=' +  self._pathSession +'/'
			self._environ['REQUEST_URI'] = self._environ['REQUEST_URI'].replace(sidstring,'')
			self._environ['PATH_INFO'] = self._environ['PATH_INFO'].replace(sidstring,'')
			if self._environ.has_key('PATH_TRANSLATED'):
				self._environ['PATH_TRANSLATED'] = self._environ['PATH_TRANSLATED'].replace(sidstring,'')
			assert(not self._environ.has_key('WK_URI')) # obsolete?

		self._sessionExpired = 0

		# Save the original urlPath.
		self._originalURLPath = self.urlPath()

		if debug: print "Done setting up request, found keys %s" % repr(self._fields.keys())


	## Transactions ##

	def transaction(self):
		return self._transaction


	def setTransaction(self, trans):
		""" This method should be invoked after the transaction is created for this request. """
		self._transaction = trans


	## Values ##

	def value(self, name, default=NoDefault):
		""" Returns the value with the given name. Values are fields or cookies. Use this method when you're field/cookie agnostic. """
		if self._fields.has_key(name):
			return self._fields[name]
		else:
			return self.cookie(name, default)

	def hasValue(self, name):
		return self._fields.has_key(name) or self._cookies.has_key(name)

	def extraURLPath(self):
		return self._extraURLPath


	## Fields ##

	def fieldStorage(self):
		return self._fieldStorage

	def field(self, name, default=NoDefault):
		if default is NoDefault:
			return self._fields[name]
		else:
			return self._fields.get(name, default)

	def hasField(self, name):
		return self._fields.has_key(name)

	def fields(self):
		return self._fields

	def setField(self, name, value):
		self._fields[name] = value

	def delField(self, name):
		del self._fields[name]


	## Cookies ##

	def cookie(self, name, default=NoDefault):
		""" Returns the value of the specified cookie. """
		if default is NoDefault:
			return self._cookies[name]
		else:
			return self._cookies.get(name, default)

	def hasCookie(self, name):
		return self._cookies.has_key(name)

	def cookies(self):
		""" Returns a dictionary-style object of all Cookie objects the client sent with this request. """
		return self._cookies


    ## Variables passed by server ##
	def serverDictionary(self):
		"""
		Returns a dictionary with the data the web server gave us, like HTTP_HOST or
		HTTP_USER_AGENT.
		"""
		return self._environ


	## Sessions ##

	def session(self):
		""" Returns the session associated with this request, either as specified by sessionId() or newly created. This is a convenience for transaction.session() """
		return self._transaction.session()

	def isSessionExpired(self):
		"""
		Returns bool: whether or not this request originally contained an expired session ID.  Only works if
		the Application.config setting "IgnoreInvalidSession" is set to 1; otherwise you get a canned error page
		on an invalid session, so your servlet never gets processed.
		"""
		return self._sessionExpired
	
	def setSessionExpired(self, sessionExpired):
		self._sessionExpired = sessionExpired


	## Authentication ##

	def remoteUser(self):
		""" Always returns None since authentication is not yet supported. Take from CGI variable REMOTE_USER. """
		# @@ 2000-03-26 ce: maybe belongs in section below. clean up docs
		return self._environ['REMOTE_USER']


	## Remote info ##

	def remoteAddress(self):
		""" Returns a string containing the Internet Protocol (IP) address of the client that sent the request. """
		return self._environ['REMOTE_ADDR']

	def remoteName(self):
		""" Returns the fully qualified name of the client that sent the request, or the IP address of the client if the name cannot be determined. """
		env = self._environ
		return env.get('REMOTE_NAME', env['REMOTE_ADDR'])

	## Path ##

	def urlPath(self):
		""" Returns the URL path of the servlet sans host, adapter and query string. For example, http://host/WebKit.cgi/Context/Servlet?x=1 yields '/Context/Servlet'. """
		self._absolutepath = 0
##		if self._environ.has_key('WK_URI'): #added by the adapter
##			self._environ['PATH_INFO'] = self._environ['WK_URI']
##			return self._environ['WK_URI']
		if self._environ.has_key('WK_ABSOLUTE'): #set by the adapter, used by modpHandler
			self._absolutepath = 1
			return self.fsPath()
		return self._environ['PATH_INFO']

	def originalURLPath(self):
		""" Returns the URL path of the _original_ servlet before any forwarding. """
		return self._originalURLPath
		
	def urlPathDir(self):
		"""
		Same as urlPath, but only gives the directory
		"""
		path = self.urlPath()
		if not path[:-1] == "/":
			path = path[:string.rfind(path, "/")+1]
		return path


	_evars = ('PATH_INFO', 'REQUEST_URI', 'SCRIPT_NAME')
	_pvars = ('_absolutepath', '_serverSidePath', '_serverSideContextPath',
		  '_adapterName')

	def getstate(self):
		"""
		Debugging and testing code. This will likely be removed in the future.
		"""
		rv = []
		env = self._environ
		for key in self._evars:
			rv.append("  * env['%s'] = %s" % (key, env.get(key,"* no def *")))
		for key in self._pvars + ('_contextName', '_extraURLPath'):
			if not hasattr(self,key):
				# reload cached values.
				self.serverSideContextPath()
			rv.append("  * req.%s = %s" % (key, getattr(self,key, "* no def *")))
		return string.join(rv, '\n')
		
	def setURLPath(self, path):
		""" Sets the URL path of the request. There is rarely a need to do this. Proceed with caution. The only known current use for this is Application.forwardRequest(). """
		if hasattr(self, '_serverSidePath'):
			del self._serverSidePath
			del self._serverSideContextPath
		if hasattr(self, '_serverSideDir'):
			del self._serverSideDir
		self._environ['PATH_INFO'] = path
		self._environ['REQUEST_URI'] = self.adapterName() + path

	def serverSidePath(self, path=None):
		"""	Returns the absolute server-side path of the request. If the optional path is passed in, then it is joined with the server side directory to form a path relative to the object.
		"""
		if not hasattr(self, '_serverSidePath'):
			app = self._transaction.application()
			self._serverSidePath, self._serverSideContextPath, self._contextName = app.serverSideInfoForRequest(self)
		if path:
			return os.path.normpath(os.path.join(os.path.dirname(self._serverSidePath), path))
		else:
			return self._serverSidePath

	def serverSideContextPath(self, path=None):
		""" Returns the absolute server-side path of the context of this request.
		If the optional path is passed in, then it is joined with the server side context directory
		to form a path relative to the object.

		This directory could be different from the result of serverSidePath() if the request
		is in a subdirectory of the main context directory."""
		if not hasattr(self, '_serverSideContextPath'):
			app = self._transaction.application()
			self._serverSidePath, self._serverSideContextPath, self._contextName = app.serverSideInfoForRequest(self)
		if path:
			return os.path.normpath(os.path.join(self._serverSideContextPath, path))  # The contextPath is already the dirname, no need to dirname it again
		else:
			return self._serverSideContextPath

	def contextName(self):
		""" Returns the name of the context of this request.  This isn't necessarily the same as the name of the directory containing the context. """
		if not hasattr(self, '_contextName'):
			app = self._transaction.application()
			self._serverSidePath, self._serverSideContextPath, self._contextName = app.serverSideInfoForRequest(self)
		return self._contextName

	def servletURI(self):
		"""This is the URI of the servlet, without any query strings or extra path info"""

		sspath=self.serverSidePath() #ensure that extraURLPath has been stripped
		pinfo=self.pathInfo()
		if not self._extraURLPath:
			if pinfo[-1]=="/": pinfo = pinfo[:-1]
			return pinfo
		URI=pinfo[:string.rfind(pinfo,self._extraURLPath)]
		if URI[-1]=="/": URI=URI[:-1]
		return URI

	def uriWebKitRoot(self):
		if not self._serverRootPath:
			self._serverRootPath = ''
			loc = self.urlPath() #self.servletURI()
			loc,curr = os.path.split(loc)
			while 1:
				loc,curr = os.path.split(loc)
				if curr:
					self._serverRootPath = self._serverRootPath + "../"
				else: break
		return self._serverRootPath

	def fsPath(self):
		""" The filesystem path of the request, using the webserver's docroot"""
		docroot = self._environ['DOCUMENT_ROOT']
		requri = self._environ['REQUEST_URI'][1:]#strip leading /
		if self.queryString():
			qslength = len(self.queryString())+1
			requri = requri[:-qslength] ##pull off the query string and the ?-mark
		fspath = os.path.join(docroot,requri)
		return fspath

	def serverURL(self):
		""" Returns the full internet path to this request, without any extra path info or query strings.
		ie: www.my.own.host.com/WebKit/TestPage.py
		"""
		host = self._environ['HTTP_HOST']
		adapter = self.adapterName()
		path = self.urlPath()
		return host+adapter+path

	def serverURLDir(self):
		"""
		Returns the Directory of the URL in full internet form.  This is the same as serverURL,
		but removes the actual page name if it was included.
		"""
		fullurl = self.serverURL()
		if fullurl[-1]!="/":
			fullurl = fullurl[:string.rfind(fullurl,"/")+1]
		return fullurl

	def siteRoot(self):
		"""
		Returns the URL path components necessary to get back home from
		the current location.

		Examples:
			''
			'../'
			'../../'

		You can use this as a prefix to a URL that you know is based off
		the home location.  Any time you are in a servlet that may have been
		forwarded to from another servlet at a different level,
		you should prefix your URL's with this.  That is, if servlet "Foo/Bar"
		forwards to "Qux", then the qux servlet should use siteRoot() to construct all
		links to avoid broken links.  This works properly because this method
		computes the path based on the _original_ servlet, not the location of the
		servlet that you have forwarded to.
		"""
		url = self.originalURLPath()[1:]
		contextName = self.contextName() + '/'
		if url.startswith(contextName):
			url = url[len(contextName):]
		numStepsBackward = len(url.split('/')) - 1
		return '../' * numStepsBackward
		
	def siteRootFromCurrentServlet(self):
		"""
		Similar to siteRoot() but instead, it returns the site root
		relative to the _current_ servlet, not the _original_ servlet.
		"""
		url = self.urlPath()[1:]
		contextName = self.contextName() + '/'
		if url.startswith(contextName):
			url = url[len(contextName):]
		numStepsBackward = len(url.split('/')) - 1
		return '../' * numStepsBackward
		
	def servletPathFromSiteRoot(self):
		"""
		Returns the "servlet path" of this servlet relative to the siteRoot.  In
		other words, everything after the name of the context (if present).
		If you append this to the result of self.siteRoot() you get back to the
		current servlet.  This is useful for saving the path to the current servlet
		in a database, for example.
		"""
		urlPath = self.urlPath()
		if urlPath[:1] == '/':
			urlPath = urlPath[1:]
		parts = urlPath.split('/')
		newParts = []
		for part in parts:
			if part == '..':
				if newParts:
					newParts.pop()
			else:
				newParts.append(part)
		if newParts[:1] == [self.contextName()]:
			newParts[:1] = []
		return '/'.join(newParts)

	## Special ##

	def adapterName(self):
		"""
		Returns the name of the adapter as it appears in the URL.
		Example: '/WebKit.cgi'
		This is useful in special cases when you are constructing URLs. See Testing/Main.py for an example use.
		"""
		return self._adapterName

	def rawRequest(self):
		""" Returns the raw request that was used to initialize this request object. """
		return self._rawRequest

	def environ(self):
		return self._environ  # @@ 2000-05-01 ce: To implement ExceptionHandler.py

	def addParent(self, servlet):
		self._parents.append(servlet)

	def popParent(self):
		if self._parents:
			self._parents.pop()

	def parent(self):
		"""
		Get the servlet that passed this request to us, if any.
		"""
		if self._parents:
			return self._parents[len(self._parents)-1]

	def parents(self):
		"""
		Returns the parents list
		"""
		return self._parents

	def rawInput(self, rewind=0):
		"""
		This gives you a file-like object for the data that was
		sent with the request (e.g., the body of a POST request,
		or the documented uploaded in a PUT request).

		The file might not be rewound to the beginning if there
		was valid, form-encoded POST data.  Pass rewind=1 if
		you want to be sure you get the entire body of the request.
		"""
		fs = self.fieldStorage()
		if rewind:
			fs.file.seek(0)
		return fs.file

	def time(self):
		"""
		Returns the time that the request was received.
		"""
		return self._time


	## Information ##

	# @@ 2000-05-10: See FUTURE section of class doc string

	def servletPath(self):
		# @@ 2000-03-26 ce: document
		return self._environ['SCRIPT_NAME']

	def contextPath(self):
		""" Returns the portion of the request URI that is the context of the request. """
		# @@ 2000-03-26 ce: this comes straight from Java servlets. Do we want this?
		raise NotImplementedError

	def pathInfo(self):
		""" Returns any extra path information associated with the URL the client sent with this request. Equivalent to CGI variable PATH_INFO. """
		if self._pathInfo is None:
			self._pathInfo = self._environ['PATH_INFO'][1:]
			# The [1:] above strips the preceding '/' that we get with Apache 1.3
		return self._pathInfo

	def pathTranslated(self):
		""" Returns any extra path information after the servlet name but before the query string, translated to a file system path. Equivalent to CGI variable PATH_TRANSLATED. """
#		return self._environ['PATH_TRANSLATED']
# @@ 2000-06-22 ce: resolve this
		return self._environ.get('PATH_TRANSLATED', None)

	def queryString(self):
		""" Returns the query string portion of the URL for this request. Taken from the CGI variable QUERY_STRING. """
		return self._environ.get('QUERY_STRING', '')

	def uri(self):
		""" Returns the request URI, which is the entire URL except for the query string. """
		return self._environ['REQUEST_URI']

	def method(self):
		""" Returns the HTTP request method (in all uppercase), typically from the set GET, POST, PUT, DELETE, OPTIONS and TRACE. """
		return string.upper(self._environ['REQUEST_METHOD'])

	def sessionId(self):
		""" Returns a string with the session id specified by the client, or None if there isn't one. """
		sid = self.value('_SID_', None)
		if self._transaction.application().setting('Debug')['Sessions']:
			print '>> sessionId: returning sid =', sid
		return sid

	def hasPathSession(self):
		return self._pathSession is not None
	

	## Inspection ##

	def info(self):
		""" Returns a list of tuples where each tuple has a key/label (a string) and a value (any kind of object). Values are typically atomic values such as numbers and strings or another list of tuples in the same fashion. This is for debugging only. """
		# @@ 2000-04-10 ce: implement and invoke super if appropriate
		# @@ 2002-06-08 ib: should this also return the unparsed body
		# of the request?
		info = [
			('time',    self._time),
			('environ', self._environ),
			('input',   self._input),
			('fields',  self._fields),
			('cookies', self._cookies)
		]

		# Information methods
		for method in _infoMethods:
			info.append((method.__name__, apply(method, (self,))))

		return info

	def htmlInfo(self):
		""" Returns a single HTML string that represents info(). Useful for inspecting objects via web browsers. """
		return htmlInfo(self.info())
		info = self.info()
		res = ['<table border=1>\n']
		for pair in info:
			value = pair[1]
			if hasattr(value, 'items') and (type(value) is type({}) or hasattr(value, '__getitem__')):
				value = _infoForDict(value)
			res.append('<tr valign=top> <td> %s </td>  <td> %s&nbsp;</td> </tr>\n' % (pair[0], value))
		res.append('</table>\n')
		return string.join(res, '')

	exceptionReportAttrNames = Request.exceptionReportAttrNames + 'uri servletPath serverSidePath pathInfo pathTranslated queryString method sessionId parents fields cookies environ'.split()


	## Deprecated ##

	def serverSideDir(self):
		""" deprecated: HTTPRequest.serverSideDir() on 01/24/01 in 0.5. use serverSidePath() instead. @ Returns the directory of the Servlet (as given through __init__()'s path). """
		self.deprecated(self.serverSideDir)
		if not hasattr(self, '_serverSideDir'):
			self._serverSideDir = os.path.dirname(self.serverSidePath())
		return self._serverSideDir

	def relativePath(self, joinPath):
		""" deprecated: HTTPRequest.relativePath() on 01/24/01 in 0.5. use serverSidePath() instead. @ Returns a new path which includes the servlet's path appended by 'joinPath'. Note that if 'joinPath' is an absolute path, then only 'joinPath' is returned. """
		self.deprecated(self.relativePath)
		return os.path.join(self.serverSideDir(), joinPath)


_infoMethods = (
	HTTPRequest.servletPath,
	HTTPRequest.contextPath,
	HTTPRequest.pathInfo,
	HTTPRequest.pathTranslated,
	HTTPRequest.queryString,
	HTTPRequest.uri,
	HTTPRequest.method,
	HTTPRequest.sessionId
)


def htmlInfo(info):
	""" Returns a single HTML string that represents the info structure. Useful for inspecting objects via web browsers. """
	res = ['<table border=1>\n']
	for pair in info:
		value = pair[1]
		if hasattr(value, 'items') and (type(value) is type({}) or hasattr(value, '__getitem__')):
			value = htmlInfo(_infoForDict(value))
		res.append('<tr valign=top> <td> %s </td>  <td> %s&nbsp;</td> </tr>\n' % (pair[0], value))
	res.append('</table>\n')
	return string.join(res, '')

def _infoForDict(dict):
	""" Returns an "info" structure for any dictionary-like object. """
	items = dict.items()
	items.sort(lambda a, b: cmp(a[0], b[0]))
	return items
