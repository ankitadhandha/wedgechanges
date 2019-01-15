from Common import *
from HTTPServlet import HTTPServlet
from WebUtils import Funcs
from Application import EndResponse


class PageError(Exception):
	pass


class Page(HTTPServlet):
	"""
	Page is a type of HTTPServlet that is more convenient for Servlets which represent HTML pages generated in response to GET and POST requests. In fact, this is the most common type of Servlet.
	Subclasses typically override writeHeader(), writeBody() and writeFooter().
	They might also choose to override writeHTML() entirely.
	In awake(), the page sets self attributes, _transaction, _response and _request which subclasses should use as appropriate.
	For the purposes of output, the write() and writeln() convenience methods are provided.
	When developing a full-blown website, it's common to create a subclass of Page called SitePage which defines the common look and feel of the website and provides site-specific convenience methods. Then all other page classes inherit from SitePage.
	"""

	## Transactions ##

	def awake(self, transaction):
		HTTPServlet.awake(self, transaction)
		self._response    = transaction.response()
		self._request     = transaction.request()
		self._session     = None  # don't create unless needed
		assert self._transaction is not None
		assert self._response    is not None
		assert self._request     is not None

	def respondToGet(self, transaction):
		""" Invokes _respond() to handle the transaction. """
		self._respond(transaction)

	def respondToPost(self, transaction):
		""" Invokes _respond() to handle the transaction. """
		self._respond(transaction)

	def _respond(self, transaction):
		"""
		Handles actions if an _action_ field is defined, otherwise
		invokes writeHTML().
		Invoked by both respondToGet() and respondToPost().
		"""
		req = transaction.request()

		# Support old style actions from 0.5.x and below.
		# Use setting OldStyleActions in Application.config
		# to use this.
		if self.transaction().application().setting('OldStyleActions', ) \
		   and req.hasField('_action_'):
			action = self.methodNameForAction(req.field('_action_'))
			actions = self._actionSet()
			if actions.has_key(action):
				self.preAction(action)
				apply(getattr(self, action), (transaction,))
				self.postAction(action)
				return
			else:
				raise PageError, "Action '%s' is not in the public list of actions, %s, for %s." % (action, actions.keys(), self)

		# Check for actions
		for action in self.actions():
			if req.hasField('_action_%s' % action) or \
			   req.field('_action_', None) == action or \
			   (req.hasField('_action_%s.x' % action) and \
			    req.hasField('_action_%s.y' % action)):
				if self._actionSet().has_key(action):
					self.handleAction(action)
					return

		self.writeHTML()

	def sleep(self, transaction):
		self._session = None
		self._request  = None
		self._response = None
		self._transaction = None
		HTTPServlet.sleep(self, transaction)


	## Access ##

	def application(self):
		return self._transaction.application()

	def transaction(self):
		return self._transaction

	def request(self):
		return self._request

	def response(self):
		return self._response

	def session(self):
		if not self._session:
			self._session = self._transaction.session()
		return self._session


	## Generating results ##

	def title(self):
		""" Subclasses often override this method to provide a custom title. This title should be absent of HTML tags. This implementation returns the name of the class, which is sometimes appropriate and at least informative. """
		return self.__class__.__name__

	def htTitle(self):
		""" Return self.title(). Subclasses sometimes override this to provide an HTML enhanced version of the title. This is the method that should be used when including the page title in the actual page contents. """
		return self.title()

	def htBodyArgs(self):
		"""
		Returns the arguments used for the HTML <body> tag. Invoked by
		writeBody().

		With the prevalence of stylesheets (CSS), you can probably skip
		this particular HTML feature.
		"""
		return 'color=black bgcolor=white'

	def writeHTML(self):
		"""
		Writes all the HTML for the page.

		Subclasses may override this method (which is invoked by
		respondToGet() and respondToPost()) or more commonly its
		constituent methods, writeDocType(), writeHead() and
		writeBody().
		"""
		self.writeDocType()
		self.writeln('<html>')
		self.writeHead()
		self.writeBody()
		self.writeln('</html>')

	def writeDocType(self):
		"""
		Invoked by writeHTML() to write the <!DOCTYPE ...> tag.

		@@ sgd-2003-01-29 - restored the 4.01 transitional as per discussions
		on the mailing list for the 0.8 release.

		# This implementation USED TO specify HTML 4.01 Transitional, but
		# some versions of Mozilla acted strangely with that. The current
		# implementation does nothing.

		Subclasses may override to specify something else.

		You can find out more about doc types by searching for DOCTYPE
		on the web, or visiting:
			http://www.htmlhelp.com/tools/validator/doctype.html
		"""
		self.writeln('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
		pass

	def writeHead(self):
		"""
		Writes the <head> portion of the page by writing the
		<head>...</head> tags and invoking writeHeadParts() in between.
		"""
		wr = self.writeln
		wr('<head>')
		self.writeHeadParts()
		wr('</head>')

	def writeHeadParts(self):
		"""
		Writes the parts inside the <head>...</head> tags. Invokes
		writeTitle() and writeStyleSheet(). Subclasses can override this
		to add additional items and should invoke super.
		"""
		self.writeTitle()
		self.writeStyleSheet()

	def writeTitle(self):
		"""
		Writes the <title> portion of the page. Uses title().
		"""
		self.writeln('\t<title>%s</title>' % self.title())

	def writeStyleSheet(self):
		"""
		Writes the style sheet for the page, however, this default
		implementation does nothing. Subclasses should override if
		necessary. A typical implementation is:
			self.writeln('\t<link rel=stylesheet href=StyleSheet.css type=text/css>')
		"""
		pass

	def writeBody(self):
		"""
		Writes the <body> portion of the page by writing the
		<body>...</body> (making use of self.htBodyArgs()) and invoking
		self.writeBodyParts() in between.
		"""
		wr = self.writeln
		bodyArgs = self.htBodyArgs()
		if bodyArgs:
			wr('<body %s>' % bodyArgs)
		else:
			wr('<body>')
		self.writeBodyParts()
		wr('</body>')

	def writeBodyParts(self):
		"""
		Invokes writeContent(). Subclasses should only override this
		method to provide additional page parts such as a header,
		sidebar and footer, that a subclass doesn't normally have to
		worry about writing.

		For writing page-specific content, subclasses should override
		writeContent() instead.

		See SidebarPage for an example override of this method.

		Invoked by writeBody().
		"""
		self.writeContent()

	def writeContent(self):
		"""
		Writes the unique, central content for the page.

		Subclasses should override this method (not invoking super) to
		write their unique page content.

		Invoked by writeBodyParts().
		"""
		self.writeln('<p> This page has not yet customized its content. </p>')


	## Writing ##

	def write(self, *args):
		for arg in args:
			self._response.write(str(arg))

	def writeln(self, *args):
		for arg in args:
			self._response.write(str(arg))
		self._response.write('\n')


	## Threading ##

	def canBeThreaded(self):
		""" Returns 0 because of the ivars we set up in awake(). """
		return 0


	## Actions ##

	def handleAction(self, action):
		"""
		Invoked by _respond() when a legitimate action has been found
		in a form. Invokes preAction(), the actual action method and
		postAction().

		Subclasses rarely override this method.
		"""
		self.preAction(action)
		getattr(self, action)()
		self.postAction(action)

	def actions(self):
		"""
		Returns a list of method names that are allowable actions from
		HTML forms. The default implementation returns [].
		"""
		return []

	def preAction(self, actionName):
		"""
		Invoked by self prior to invoking a action method. The
		implementation basically writes everything up to but not
		including the body tag.  Subclasses may override to customize
		and may or may not invoke super as they see fit. The actionName
		is passed to this method, although it seems a generally bad
		idea to rely on this. However, it's still provided just in case
		you need that hook.
		"""
		self.writeDocType()
		self.writeln('<html>')
		self.writeHead()

	def postAction(self, actionName):
		"""
		Invoked by self after invoking a action method. The
		implementation basically writes everything after the close of
		the body tag (in other words, just the </html> tag).  Subclasses
		may override to customize and may or may not invoke super as
		they see fit. The actionName is passed to this method, although
		it seems a generally bad idea to rely on this. However, it's
		still provided just in case you need that hook.
		"""
		self.writeln('</html>')

	def methodNameForAction(self, name):
		"""
		This method exists only to support "old style" actions from
		WebKit 0.5.x and below.

		Invoked by _respond() to determine the method name for a given
		action name (which usually comes from an HTML submit button in a
		form). This implementation simple returns the name. Subclasses
		could "filter" the name by altering it or looking it up in a
		dictionary. Subclasses should override this method when action
		names don't match their method names.
		"""
		return name


	## Convenience ##

	def htmlEncode(self, s):
		return Funcs.htmlEncode(s)

	def htmlDecode(self, s):
		return Funcs.htmlDecode(s)

	def urlEncode(self, s):
		return Funcs.urlEncode(s)

	def urlDecode(self, s):
		return Funcs.urlDecode(s)

	def forward(self, URL):
		"""
		Forwards this request to another servlet.  See Application.forward() for details.
		The main difference is that here you don't have to pass in the transaction as the first argument.
		"""
		self.application().forward(self.transaction(), URL)

	def includeURL(self, URL):
		"""
		Includes the response of another servlet in the current servlet's response.  See Application.includeURL() for details.
		The main difference is that here you don't have to pass in the transaction as the first argument.
		"""
		self.application().includeURL(self.transaction(), URL)

	def callMethodOfServlet(self, URL, method, *args, **kwargs):
		"""
		Call a method of another servlet.  See Application.callMethodOfServlet() for details.
		The main difference is that here you don't have to pass in the transaction as the first argument.
		"""
		return apply(self.application().callMethodOfServlet, (self.transaction(), URL, method) + args, kwargs)

	def endResponse(self):
		"""
		If this is called during sleep() or awake() then the rest of awake(), response(), and
		sleep() are skipped and the accumulated response is sent immediately with no further
		processing.  If this is called during respond() then the rest of respond() is
		skipped but sleep() is called, then the accumulated response is sent.
		"""
		raise EndResponse

	def sendRedirectAndEnd(self, url):
		"""
		Sends a redirect back to the client and ends the response. This
		is a very popular pattern.
		"""
		self.response().sendRedirect(url)
		self.endResponse()


	## Self utility ##

	def sessionEncode(self, url=None):
		"""
		Utility function to access session.sessionEncode.
		Takes a url and adds the session ID as a parameter.  This is for cases where
		you don't know if the client will accepts cookies.
		"""
		if url == None:
			url = self.request().uri()
		return self.session().sessionEncode(url)


	## Private utility ##

	def _actionSet(self):
		""" Returns a dictionary whose keys are the names returned by actions(). The dictionary is used for a quick set-membership-test in self._respond. Subclasses don't generally override this method or invoke it. """
		if not hasattr(self, '_actionDict'):
			self._actionDict = {}
			for action in self.actions():
				self._actionDict[action] = 1
		return self._actionDict


	## Validate HTML output (developer debugging) ##

	def validateHTML(self, closingTags='</body></html>'):
		"""
		Validate the current response data using Web Design
		Group's HTML validator available at
		http://www.htmlhelp.com/tools/validator/

		Make sure you install the offline validator (called
		"validate") which can be called from the command-line.
		The "validate" script must be in your path.
		
		Add this method to your SitePage (the servlet from
		which all your servlets inherit), override
		Page.writeBodyParts() in your SitePage like so:
		    def writeBodyParts(self):
		        Page.writeBodyParts()
		        self.validateHTML()

		The "closingtags" param is a string which is appended
		to the page before validation.  Typically, it would be
		the string "</body></html>".  At the point this method
		is called (e.g. from writeBodyParts() the page is not
		yet 100% complete, so we have to fake it.
		"""

		# don't bother validating if the servlet has redirected
		status = self.response().header('status', None)
		if status and status.find('Redirect') != -1:
			return

		response = self.response().rawResponse()
		contents = response['contents'] + closingTags
		from WebUtils import WDGValidator
		errorText = WDGValidator.validateHTML(contents)
		if not errorText:
			return
		self.write(errorText)

	## Exception reports ##

	def writeExceptionReport(self, handler):
		handler.writeTitle(self.__class__.__name__)
		handler.writeln('''Servlets can provide debugging information here by overriding writeExceptionReport().<br>For example:
<pre>    exceptionReportAttrs = 'foo bar baz'.split()
    def writeExceptionReport(self, handler):
        handler.writeTitle(self.__class__.__name__)
        handler.writeAttrs(self, self.exceptionReportAttrs)
        handler.write('any string')
</pre>

See WebKit/ExceptionHandler.py for more information.
''')
