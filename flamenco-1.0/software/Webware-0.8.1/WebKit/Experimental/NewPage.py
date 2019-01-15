from WebKit.Servlet import Servlet
from WebKit.Common import *
import HTTPExceptions
from WebUtils import Funcs
import base64
from WebKit.Cookie import Cookie
from types import *

True, False = 1==1, 0==1

class NewPage(Servlet):

    def __init__(self):
        Servlet.__init__(self)
        self._methodForRequestType = {}  # a cache; see respond()
        if not hasattr(self, '_title'):
            self._title = self.__class__.__name__
        self.exc = ExceptionGetter(self)

    def respond(self, trans):
        try:
            if self.actionLogin:
                self.actionLogin()
            self.setup()
            httpMethodName = trans.request().method()
            method = self._methodForRequestType.get(httpMethodName)
            if not method:
                methName = 'respondTo' + string.capitalize(httpMethodName)
                method = getattr(self, methName, self.notImplemented)
                self._methodForRequestType[httpMethodName] = method
            method()
        except HTTPExceptions.HTTPError, v:
            self._contentAction = 'error'
            self._exception = v
            self.resetResponse()
            trans.response().setStatus(v.code(servlet=self),
                                       v.codeMessage(servlet=self))
            for name, value in v.headers(servlet=self).items():
                trans.response().setHeader(name, value)
            self.response().write(v.htDescription(servlet=self))
        self.teardown()

    actionLogin = None

    def setup(self):
        pass

    def teardown(self):
        """
        Cleanup anything necessary.  This method will be called
        *regardless* of any exceptions.  So things that you expect
        to be initialized may not have been.
        """
        pass
    
    def notImplemented(self):
        raise self.exc.NotImplemented

    ## The 200-series of statuses aren't errors, so they aren't set
    ## by exceptions.  200 OK is the default, of course.

    def statusCreated(self):
        self.response().setStatus(201, 'Created')
        
    def statusNoContent(self):
        self.response().setStatus(204, 'No Content')
        
    def statusMultiStatus(self):
        self.response().setStatus(207, 'Multi-Status')
	
    def host(self):
        """The hostname of the server, with port number if necessary
        (i.e., not 80)"""
        env = self.request().environ()
        if env.has_key('SCRIPT_URI'):
            host = env['SCRIPT_URI']
            host = host[string.find(host, '//'):] # get rid of http://
            host = host[:string.find(host, '/')] # get rid of rest of path
            return host
        ## @@: maybe this should check if it's https, and the applicable
        ## port number for that... then we need a protocol method too
        host = self._environ['HTTP_HOST']
        port = int(self._environ['HTTP_PORT'])
        if port != 80:
            host = "%s:%i" % (host, port)
        return host

    def webKitURL(self):
        """Similar to adapterName: this returns the first portion of
        the URL that points to the WebKit base."""
        req = self.request()
        env = req.environ()
        if env.has_key('SCRIPT_URL'):
            path = env['SCRIPT_URL']
            contextName = req.contextName()
            if path.find('/%s/' % contextName) != -1:
                path = path[:path.find('/%s/' % contextName)]
                return path
            else:
                ## @@: I should be checking for something else here,
                ## like a servlet name or something, as in
                ## /WK/SomeServlet (in default context)
                return ''
        return req.adapterName()

    def contextURL(self):
        """Everything up to the context (including webKitURL)"""
        req = self.request()
        env = req.environ()
        contextName = req.contextName()
        if env.has_key('SCRIPT_URL'):
            path = env['SCRIPT_URL']
            if path.find('/%s/' % contextName) != -1:
                path = path[:path.find('/%s/' % contextName) + 1 +
                            len(contextName)]
                return path
            else:
                return ''
        ## @@: There should be a urljoin function... I guess urlparse
        ## might even have it, but whatever...
        return '%s/%s' % (req.webKitURL(), contextName)

    def servletURL(self, extraPath=1, queryString=0):
        """Everything through the servlet (and perhaps beyond!)"""
        return self.url()

    def url(self, servletName=None, extraPath=None, args=None,
            absolute=1, host=0):
        assert absolute, 'Relative URLs not yet supported'
        if not servletName:
            ## @@: doesn't work with packages
            servletName = self.__class__.__name__
        extraPath = extraPath or ''
        if args:
            args = "?" + dictToGetArgs(args)
        else:
            args = ''
        if host:
            url = 'http://' + self.host()
        else:
            url = ''
        url = url + self.contextURL()
        url = url + '/' + servletName.replace('.', '/') + extraPath + args
        if self.urlSession():
            url = self.session().sessionEncode(url)
        return url

    def urlSession(self):
        """If you want to encode the session ID in the url,
        return True."""
        return 0

    def awake(self, transaction):
        Servlet.awake(self, transaction)
        self._transaction = transaction
        self._response    = transaction.response()
        self._request     = transaction.request()
        self._session     = None  # don't create unless needed
        self._messagesDisplayed = 0
        self._contentAction = None
        self._exception = None
        self.field = self._request.field
        self.fields = self._request.fields
        self.hasField = self._request.hasField
        assert self._transaction is not None
        assert self._response    is not None
        assert self._request     is not None

    def sleep(self, transaction):
        Servlet.sleep(self, transaction)
        self._session     = None
        self._request     = None
        self._response    = None
        self._transaction = None
        self.field = None
        self.fields = None
        self.hasField = None
        self._exception = None

    def respondToGet(self):
        """ Invokes _respond() to handle the transaction. """
        self._respond()
        
    def respondToPost(self):
        """ Invokes _respond() to handle the transaction. """
        self._respond()
        
    def respondToHead(self):
        """
        A correct but inefficient implementation.
        Should perhaps provide Last-Modified.
        """
        bytes = [0]
        d = DummyWriter()
        res = self.response()
        w = res.write
        res.write = d.write
        self.respondToGet(trans)
        res.write = w
        res.setHeader('Content-Length', d.bytes)

    def _respond(self):
        """
        Handles actions if an _action_ field is defined, otherwise
        invokes writeHTML().
        Invoked by both respondToGet() and respondToPost(),
        and indirectly by respondToHead().
        """
        req = self.request()
        # Check for actions
        for action in self.actions():
            if req.hasField('_action_%s' % action) \
               or req.hasField('_action_%s.x' % action):
                self._contentAction = action
        self.writeHTML()

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

    def contentAction(self):
        """
        The kind of action we are handling.  None means normal.  If
        you use _action_actionName, then it will be the string "actionName".
        If there is an error, it will be "error"
        """
        return self._contentAction

    def title(self):
        """
        The title of the page.  It is recommended you override
        pageTitle() or set self._title
        """
        if self.contentAction() == "error":
            return self._exception.title()
        else:
            return self.pageTitle()

    def pageTitle(self):
        """
        Override to create a dynamic title.  You may want to pay
        attention to self.contentAction() (if an _action_* has been
        invoked).
        """
        return self._title

    def htTitle(self):
        """
        Subclasses may override this to provide an HTML enhanced
        version of the title. This is the method that should be
        used when including the page title in the actual page
        contents.  Override htPageTitle()
        """
        if self.contentAction() == "error":
            return self._exception.htTitle()
        else:
            return self.htPageTitle()

    def htPageTitle(self):
        return self.pageTitle()

    def htBodyArgs(self):
        """
        Returns the arguments used for the HTML <body> tag. Invoked by
        writeBody().  If you return a dictionary, the attributes given
        will be included, like:
          {'bgcolor': '#ffffff', 'onLoad': 'cacheImages()'}
        """
        return ''

    def writeHTML(self):
        """
        Writes all the HTML for the page.
        
        Subclasses may override this method (which is invoked by
        respondToGet() and respondToPost()) or more commonly its
        constituent methods, writeDocType(), writeHead() and
        writeBody().

        If you wish to send non-HTML content, or unadorned HTML,
        you might override fullPage()
        """
        full = self.fullPage()
        if not full or self.contentAction() == 'error':
            self.writeDocType()
            self.write('<html>\n')
            self.writeHead()
            self.writeBody()
            self.write('</html>\n')
        else:
            self.writeBodyContent()

    def writeDocType(self):
        """
        Invoked by writeHTML() to write the <!DOCTYPE ...> tag. This
        implementation specifies HTML 4.01 Transitional. Subclasses may
        override to specify something else.
        
        You can find out more about doc types by searching for DOCTYPE
        on the web, or visiting:
            http://www.htmlhelp.com/tools/validator/doctype.html
        """
        self.writeln('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')

    def writeHead(self):
        """
        Writes the <head> portion of the page by writing the
        <head>...</head> tags and invoking writeHeadParts() in between.
        """
        self.write('<head>\n')
        self.writeHeadParts()
        self.write('</head>\n')

    def writeHeadParts(self):
        """
        Writes the parts inside the <head>...</head> tags.  It's best
        to override title(), styleSheet(), styleSheetHref(), and
        headJavaScript(), not the write* methods.
        
        Subclasses can override this to add additional items and
        should invoke super.
        """
        self.writeTitle()
        self.writeStyleSheet()
        self.writeHeadJavascript()

    def writeTitle(self):
        self.write('<title>%s</title>\n' % Funcs.htmlEncode(self.title()))

    def writeStyleSheet(self):
        """
        Writes stylesheet (CSS) information -- you should probably
        override styleSheetHref() or styleSheet() instead.
        """
        href = self.styleSheetHref()
        if href:
            self.write('<link rel="stylesheet" href="%s" type="text/css">\n'
                       % Funcs.htmlEncode(href))
        styles = self.styleSheet()
        if styles:
            self.write('<style type="text/css"><!--\n%s\n--></style>\n'
                       % styles)

    def styleSheetHref(self):
        return None

    def styleSheet(self):
        return None

    def writeHeadJavascript(self):
        js = self.headJavascript()
        if js:
            self.write('<script language="JavaScript"><!--\n%s\n//--></script>\n'
                       % js)

    def headJavascript(self):
        return None

    def writeBody(self):
        """
        Writes the <body> portion of the page by writing the
        <body>...</body> (making use of self.htBodyArgs()) and invoking
        self.writeBodyParts() in between.
        """
        wr = self.writeln
        bodyArgs = self.htBodyArgs()
        if type(bodyArgs) is DictionaryType:
            bodyArgs = ' '.join(map(lambda x: '%s="%s"' % (x[0], Funcs.htmlEncode(x[1])),
                                    bodyArgs.items()))
        if bodyArgs:
            wr('<body %s>' % bodyArgs)
        else:
            wr('<body>')
        self.writeBodyContent()
        wr('</body>')

    def writeBodyContent(self):
        a = self.contentAction()
        full = self.fullPage()
        if not full:
            self.writeBodyStart()
        if a is None:
            self.writeContent()
        elif a == "error":
            self.writeErrorContent(self._exception)
        else:
            getattr(self, a)()
        if not full:
            self.writeBodyEnd()

    def fullPage(self):
        """
        Return True here if you don't want anything displayed
        besides writeContent (i.e., no headers, footers, HTML,
        etc.)  Good for non-HTML content.
        """
        return 0

    def writeBodyStart(self):
        """
        Override this to provide a standard header.
        If you want to embed everything in a table, you can
        do something like:
          <table><tr><td>Menu<br>Options</td><td>
        in the header, and in the footer (writeEndBody):
          </td></tr></table>
        """
        self.writeMessages()

    def writeBodyEnd(self):
        """Override this to provide a standard footer"""
        pass

    def writeContent(self):
        """
        Writes the unique, central content for the page.

        Subclasses should override this method (not invoking super) to
        write their unique page content.

        Invoked by writeBodyParts().
        """
        self.write('<p> This page has not yet customized its content. </p>\n')

    def write(self, *args):
        for arg in args:
            self._response.write(str(arg))

    def writeln(self, *args):
        for arg in args:
            self._response.write(str(arg))
        self._response.write('\n')

    ## Threading ##

    def canBeThreaded(self):
        """
        Returns 0 because of the ivars we set up in awake().
        """
        return 0


    ## Actions ##
    
    def actions(self):
        """
        Returns a list of method names that are allowable actions from
        HTML forms. The default implementation returns [].
        """
        return []

    ## Utility functions ##
    ## (you should just have a standard module for these, though)

    def htmlEncode(self, s):
        return Funcs.htmlEncode(s)
    
    def htmlDecode(self, s):
        return Funcs.htmlDecode(s)

    def urlEncode(self, s):
        return Funcs.urlEncode(s)
    
    def urlDecode(self, s):
        return Funcs.urlDecode(s)

    ## Delegation and forwarding ##

    def forward(self, URL):
        """
        Forwards this request to another servlet.  See
        Application.forward() for details.
        The main difference is that here you don't have to pass in
        the transaction as the first argument.
        """
        self.application().forward(self.transaction(), URL)

    def includeURL(self, URL):
        """
        Includes the response of another servlet in the current
        servlet's response.  See Application.includeURL() for details.
        The main difference is that here you don't have to pass in the
        transaction as the first argument.
        """
        self.application().includeURL(self.transaction(), URL)

    def callMethodOfServlet(self, URL, method, *args, **kwargs):
        """
        Call a method of another servlet.  See
        Application.callMethodOfServlet() for details.
        The main difference is that here you don't have to pass in
        the transaction as the first argument.
        """
        return apply(self.application().callMethodOfServlet, (self.transaction(), URL, method) + args, kwargs)

    ## Self utility ##
    
    def sessionEncode(self, url=None):
        """
        Utility function to access session.sessionEncode.
        Takes a url and adds the session ID as a parameter.  This is for
        cases where you don't know if the client will accepts cookies.
        """
        if url == None:
            url = self.request().uri()
        return self.session().sessionEncode(url)

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

    ############################################################
    ## Messages
    ############################################################

    def resetResponse(self):
        """
        When you want to throw away everything you've done,
        and start all over again... for instance, if you've had
        an error.
        """
        self._messagesDisplayed = 0

    def writeMessages(self):
        """
        Call this in your SitePage or other template, so that
        the messages are displayed at the top of the page.
        In your CSS file you'll want to define a style for the
        "message" class.
        """
        ses = self.session()
        if ses.value('messages', None):
            self.write('<div align=center width="60%%" class="message">%s</div>\n'
                       % '<br>\n'.join(ses.value('messages')))
            self._messagesDisplayed = 1

    def message(self, *msg):
        """
        Queue up a message to be sent to the user.  Even if the page
        is redirected, the message will be sent when they arrive at
        the redirected page.  If you set it in your writeContent,
        it may not come to the user until they visit another page --
        in other words, avoid using this in writeContent (except
        when you are about to raise an HTTPError exception).
        """
        msg = ' '.join(map(str, msg))
        ses = self.session()
        if not ses.value('messages', None):
            ses.setValue('messages', [msg])
        else:
            ses.setValue('mesages', ses.value('messages').append(msg))

    def sleep(self, trans):
        if self._messagesDisplayed:
            self.session().setValue('messages', [])
        self._transaction = None
        self._response = None
        self._request = None
        self._session = None
        self._exception = None

    def pathArgs(self):
        args = self.request().extraURLPath()
        if not args:
            return []
        args = filter(None, args.split('/'))
        return args


class DummyWriter:
    """Used for HEAD requests"""

    def __init__(self):
        self.bytes = 0

    def write(self, *args):
        for arg in args:
            self.bytes = self.bytes + len(arg)

class ExceptionGetter:
    """Used to handle exceptions"""

    def __init__(self, servlet):
        self._servlet = servlet

    def __getattr__(self, attr):
        return HTTPExceptions.exception(self._servlet.request().contextName(),
                                        attr)
