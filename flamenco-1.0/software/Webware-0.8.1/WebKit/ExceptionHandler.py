from Common import *
import string, time, traceback, types, random, sys, MimeWriter, smtplib, StringIO
from time import asctime, localtime
from MiscUtils.Funcs import dateForEmail
from WebUtils.HTMLForException import HTMLForException
from WebUtils.Funcs import htmlForDict, htmlEncode
from HTTPResponse import HTTPResponse
from types import DictType, StringType

class singleton: pass


class ExceptionHandler(Object):
	"""
	ExceptionHandler is a utility class for Application that is created
	to handle a particular exception. The object is a one-shot deal.
	After handling an exception, it should be removed.

	At some point, the exception handler sends "writeExceptionReport"
	to the transaction (if present), which in turn sends it to the other
	transactional objects (application, request, response, etc.)
	The handler is the single argument for this message.

	Classes may find it useful to do things like this:

	exceptionReportAttrs = 'foo bar baz'.split()
	def writeExceptionReport(self, handler):
		handler.writeTitle(self.__class__.__name__)
		handler.writeAttrs(self, self.exceptionReportAttrs)

	The handler write methods that may be useful are:
		def write(self, s):
		def writeln(self, s):
		def writeTitle(self, s):
		def writeDict(self, d):
		def writeTable(self, listOfDicts, keys=None):
		def writeAttrs(self, obj, attrNames):

	Derived classes must not assume that the error occured in a
	transaction.  self._tra may be None for exceptions outside
	of transactions.

	See the WebKit.html documentation for other information.


	HOW TO CREATE A CUSTOM EXCEPTION HANDLER

	In the __init__.py of your context:

		from WebKit.ExceptionHandler import ExceptionHandler as _ExceptionHandler

		class ExceptionHandler(_ExceptionHandler):

			hideValuesForFields = _ExceptionHandler.hideValuesForFields + ['foo', 'bar']

			def work(self):
				_ExceptionHandler.work(self)
				# do whatever
				# override other methods if you like

		def contextInitialize(app, ctxPath):
			app._exceptionHandlerClass = ExceptionHandler
	"""

	hideValuesForFields = ['creditcard', 'credit card', 'cc', 'password', 'passwd']
		# ^ keep all lower case to support case insensitivity
	if 0: # for testing
		hideValuesForFields.extend('application uri http_accept userid'.split())

	hiddenString = '*** hidden ***'


	## Init ##

	def __init__(self, application, transaction, excInfo):
		Object.__init__(self)

		# Keep references to the objects
		self._app = application
		self._tra = transaction
		self._exc = excInfo
		if self._tra:
			self._req = self._tra.request()
			self._res = self._tra.response()
		else:
			self._req = self._res = None

		# Make some repairs, if needed. We use the transaction & response to get the error page back out
		# @@ 2000-05-09 ce: Maybe a fresh transaction and response should always be made for that purpose
		## @@ 2003-01-10 sd: This requires a transaction which we do not have.
		## Making remaining code safe for no transaction.
		##
                ##if self._res is None:
		##	self._res = HTTPResponse()
		##	self._tra.setResponse(self._res)

		# Cache MaxValueLengthInExceptionReport for speed
		self._maxValueLength = self.setting('MaxValueLengthInExceptionReport')

		# exception occurance time. (overridden by response.endTime())
		self._time = time.time()

		# Get to work
		self.work()


	## Utilities ##

	def setting(self, name):
		return self._app.setting(name)

	def servletPathname(self):
		try:
			return self._tra.request().serverSidePath()
		except:
			
			return None

	def basicServletName(self):
		name = self.servletPathname()
		if name is None:
			return 'unknown'
		else:
			return os.path.basename(name)


	## Exception handling ##

	def work(self):
		''' Invoked by __init__ to do the main work. '''

		if self._res:
			self._res.recordEndTime()
			self._time = self._res.endTime()
			
		self.logExceptionToConsole()

		# write the error page out to the response if available.
		if self._res and (not self._res.isCommitted() or self._res.header('Content-type', None)=='text/html'):
			if not self._res.isCommitted():
				self._res.reset()
			if self.setting('ShowDebugInfoOnErrors')==1:
				publicErrorPage = self.privateErrorPage()
			else:
				publicErrorPage = self.publicErrorPage()
			self._res.write(publicErrorPage)

		privateErrorPage = None
		if self.setting('SaveErrorMessages'):
			privateErrorPage = self.privateErrorPage()
			filename = self.saveErrorPage(privateErrorPage)
		else:
			filename = ''

		self.logExceptionToDisk(errorMsgFilename=filename)

		if self.setting('EmailErrors'):
			if privateErrorPage is None:
				privateErrorPage = self.privateErrorPage()
			self.emailException(privateErrorPage)

	def logExceptionToConsole(self, stderr=None):
		''' Logs the time, servlet name and traceback to the console (typically stderr). This usually results in the information appearing in console/terminal from which AppServer was launched. '''
		if stderr is None:
			stderr = sys.stderr
		stderr.write('[%s] [error] WebKit: Error while executing script %s\n' % (
			asctime(localtime(self._time)), self.servletPathname()))
		traceback.print_exc(file=stderr)

	def publicErrorPage(self):
		return '''<html>
	<head>
		<title>Error</title>
	</head>
	<body fgcolor=black bgcolor=white>
		%s
		<p> %s
	</body>
</html>
''' % (htTitle('Error'), self.setting('UserErrorMessage'))

	def privateErrorPage(self):
		''' Returns an HTML page intended for the developer with useful information such as the traceback. '''
		html = ['''
<html>
	<head>
		<title>Error</title>
	</head>
	<body fgcolor=black bgcolor=white>
%s
<p> %s''' % (htTitle('Error'), self.setting('UserErrorMessage'))]

		html.append(self.htmlDebugInfo())

		html.append('</body></html>')
		return string.join(html, '')

	def htmlDebugInfo(self):
		''' Return HTML-formatted debugging information about the current exception. '''
		self.html = []
		self.writeHTML()
		html = ''.join(self.html)
		self.html = None
		return html

	def writeHTML(self):
		self.writeTraceback()
		self.writeMiscInfo()
		self.writeTransaction()
		self.writeEnvironment()
		self.writeIds()
		self.writeFancyTraceback()


	## Write utility methods ##

	def write(self, s):
		self.html.append(str(s))

	def writeln(self, s):
		self.html.append(str(s))
		self.html.append('\n')

	def writeTitle(self, s):
		self.writeln(htTitle(s))

	def writeDict(self, d):
		self.writeln(htmlForDict(d, filterValueCallBack=self.filterDictValue, maxValueLength=self._maxValueLength))

	def writeTable(self, listOfDicts, keys=None):
		"""
		Writes a table whose contents are given by listOfDicts. The
		keys of each dictionary are expected to be the same. If the
		keys arg is None, the headings are taken in alphabetical order
		from the first dictionary. If listOfDicts is "false", nothing
		happens.

		The keys and values are already considered to be HTML.

		Caveat: There's no way to influence the formatting or to use
		column titles that are different than the keys.

		Note: Used by writeAttrs().
		"""
		if not listOfDicts:
			return

		if keys is None:
			keys = listOfDicts[0].keys()
			keys.sort()

		wr = self.writeln
		wr('<table>\n<tr>')
		for key in keys:
			wr('<td bgcolor=#F0F0F0><b>%s</b></td>' % key)
		wr('</tr>\n')

		for row in listOfDicts:
			wr('<tr>')
			for key in keys:
				wr('<td bgcolor=#F0F0F0>%s</td>' % self.filterTableValue(row[key], key, row, listOfDicts))
			wr('</tr>\n')

		wr('</table>')

	def writeAttrs(self, obj, attrNames):
		"""
		Writes the attributes of the object as given by attrNames.
		Tries obj._name first, followed by obj.name(). Is resilient
		regarding exceptions so as not to spoil the exception report.
		"""
		rows = []
		for name in attrNames:
			value = getattr(obj, '_'+name, singleton) # go for data attribute
			try:
				if value is singleton:
					value = getattr(obj, name, singleton) # go for method
					if value is singleton:
						value = '(could not find attribute or method)'
					else:
						try:
							if callable(value):
								value = value()
						except Exception, e:
							value = '(exception during method call: %s: %s)' % (e.__class__.__name__, e)
						value = self.repr(value)
				else:
					value = self.repr(value)
			except Exception, e:
				value = '(exception during value processing: %s: %s)' % (e.__class__.__name__, e)
			rows.append({'attr': name, 'value': value})
		self.writeTable(rows, ('attr', 'value'))


	## Write specific parts ##

	def writeTraceback(self):
		self.writeTitle('Traceback')
		self.write('<p> <i>%s</i>' % self.servletPathname())
		self.write(HTMLForException(self._exc))

	def writeMiscInfo(self):
		self.writeTitle('MiscInfo')
		info = {
			'time':          asctime(localtime(self._time)),
			'filename':      self.servletPathname(),
			'os.getcwd()':   os.getcwd(),
			'sys.path':      sys.path
		}
		self.writeDict(info)

	def writeTransaction(self):
		if self._tra:
			self._tra.writeExceptionReport(self)
		else:
			self.writeTitle("No current Transaction")
			

	def writeEnvironment(self):
		self.writeTitle('Environment')
		self.writeDict(os.environ)

	def writeIds(self):
		self.writeTitle('Ids')
		self.writeTable(osIdTable(), ['name', 'value'])

	def writeFancyTraceback(self):
		if self.setting('IncludeFancyTraceback'):
			self.writeTitle('Fancy Traceback')
			try:
				from WebUtils.ExpansiveHTMLForException import ExpansiveHTMLForException
				self.write(ExpansiveHTMLForException(context=self.setting('FancyTracebackContext')))
			except:
				self.write('Unable to generate a fancy traceback! (uncaught exception)')
				try:
					self.write(HTMLForException(sys.exc_info()))
				except:
					self.write('<br>Unable to even generate a normal traceback of the exception in fancy traceback!')

	def saveErrorPage(self, html):
		''' Saves the given HTML error page for later viewing by the developer, and returns the filename used. '''
		filename = self._app.serverSidePath(os.path.join(self.setting('ErrorMessagesDir'), self.errorPageFilename()))
		f = open(filename, 'w')
		f.write(html)
		f.close()
		return filename

	def errorPageFilename(self):
		''' Construct a filename for an HTML error page, not including the 'ErrorMessagesDir' setting. '''
		return 'Error-%s-%s-%d.html' % (
			self.basicServletName(),
			string.join(map(lambda x: '%02d' % x, localtime(self._time)[:6]), '-'),
			random.randint(10000, 99999))
			# @@ 2000-04-21 ce: Using the timestamp & a random number is a poor technique for filename uniqueness, but this works for now

	def logExceptionToDisk(self, errorMsgFilename=''):
		''' Writes a tuple containing (date-time, filename, pathname, exception-name, exception-data,error report filename) to the errors file (typically 'Errors.csv') in CSV format. Invoked by handleException(). '''
		logline = (
			asctime(localtime(self._time)),
			self.basicServletName(),
			self.servletPathname(),
			str(self._exc[0]),
			str(self._exc[1]),
			errorMsgFilename)
		filename = self._app.serverSidePath(self.setting('ErrorLogFilename'))
		if os.path.exists(filename):
			f = open(filename, 'a')
		else:
			f = open(filename, 'w')
			f.write('time,filename,pathname,exception name,exception data,error report filename\n')
			
		def fixElement(element):
			element = str(element)
			if string.find(element, ',') or string.find(element, '"'):
				element = string.replace(str(element), '"', '""')
				element = '"' + element + '"'
			return element
		logline = map(fixElement, logline)
		
		f.write(string.join(logline, ','))
		f.write('\n')
		f.close()

	def emailException(self, htmlErrMsg):
		message = StringIO.StringIO()
		writer = MimeWriter.MimeWriter(message)

		## Construct the message headers
		headers = self.setting('ErrorEmailHeaders').copy()
		headers['Date'] = dateForEmail()
		headers['Subject'] = headers.get('Subject','[WebKit Error]') + ' ' \
					 + str(sys.exc_info()[0]) + ': ' \
					 + str(sys.exc_info()[1])
		for h,v in headers.items():
			if isinstance(v, types.ListType):
				v = ','.join(v)
			writer.addheader(h, v)

		## Construct the message body

		if self.setting('EmailErrorReportAsAttachment'):
			writer.startmultipartbody('mixed')
			# start off with a text/plain part
			part = writer.nextpart()
			body = part.startbody('text/plain')
			body.write(
				'WebKit caught an exception while processing ' +
				'a request for "%s" ' % self.servletPathname() +
				'at %s (timestamp: %s).  ' %
				(asctime(localtime(self._time)), self._time) +
				'The plain text traceback from Python is printed below and ' +
				'the full HTML error report from WebKit is attached.\n\n'
				)
			traceback.print_exc(file=body)
			
			# now add htmlErrMsg
			part = writer.nextpart()
			part.addheader('Content-Transfer-Encoding', '7bit')
			part.addheader('Content-Description', 'HTML version of WebKit error message')
			body = part.startbody('text/html; name=WebKitErrorMsg.html')
			body.write(htmlErrMsg)
			
			# finish off
			writer.lastpart()
		else:
			body = writer.startbody('text/html')
			body.write(htmlErrMsg)
			
		# Send the message
		server = smtplib.SMTP(self.setting('ErrorEmailServer'))
		server.set_debuglevel(0)
		server.sendmail(headers['From'], headers['To'], message.getvalue())
		server.quit()


	## Filtering Values ##

	def filterDictValue(self, value, key, dict):
		return self.filterValue(value, key)

	def filterTableValue(self, value, key, row, table):
		"""
		Invoked by writeTable() to afford the opportunity to filter
		the values written in tables. These values are already HTML
		when they arrive here. Use the extra key, row and table
		args as necessary.
		"""
		if row.has_key('attr') and key!='attr':
			return self.filterValue(value, row['attr'])
		else:
			return self.filterValue(value, key)

	def filterValue(self, value, key):
		"""
		This is the core filter method that is used in all filtering.
		By default, it simply returns self.hiddenString if the key is
		in self.hideValuesForField (case insensitive). Subclasses
		could override for more elaborate filtering techniques.
		"""
		if key.lower() in self.hideValuesForFields:
			return self.hiddenString
		else:
			return value


	## Self utility ##

	def repr(self, x):
		"""
		Returns the repr() of x already html encoded. As a special case, dictionaries are nicely formatted in table.

		This is a utility method for writeAttrs.
		"""
		if type(x) is DictType:
			return htmlForDict(x, filterValueCallBack=self.filterDictValue, maxValueLength=self._maxValueLength)
		else:
			rep = repr(x)
			if self._maxValueLength and len(rep) > self._maxValueLength:
				rep = rep[:self._maxValueLength] + '...'
			return htmlEncode(rep)


# Some misc functions
def htTitle(name):
	return '''
<p> <br> <table border=0 cellpadding=4 cellspacing=0 bgcolor=#A00000 width=100%%> <tr> <td align=center>
	<font face="Tahoma, Arial, Helvetica" color=white> <b> %s </b> </font>
</td> </tr> </table>''' % name


def osIdTable():
	''' Returns a list of dictionaries contained id information such as uid, gid, etc.,
		all obtained from the os module. Dictionary keys are 'name' and 'value'. '''
	funcs = ['getegid', 'geteuid', 'getgid', 'getpgrp', 'getpid', 'getppid', 'getuid']
	table = []
	for funcName in funcs:
		if hasattr(os, funcName):
			value = getattr(os, funcName)()
			table.append({'name': funcName, 'value': value})
	return table
