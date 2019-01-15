import BaseHTTPServer, mimetools
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO
import threading, socket
from WebKit.NewThreadedAppServer import Handler
from WebKit.ASStreamOut import ASStreamOut
import time

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	"""Handles incoming requests.  Recreated with every request.
	Abstract base class.
	"""

	## This sends certain CGI variables.  These are some that
	## should be sent, but aren't:
	## SERVER_ADDR
	## SERVER_PORT
	## SERVER_SOFTWARE
	## SERVER_NAME
	## HTTP_CONNECTION
	## SERVER_PROTOCOL
	## HTTP_KEEP_ALIVE

	## These I don't think are needed:
	## DOCUMENT_ROOT
	## PATH_TRANSLATED
	## GATEWAY_INTERFACE
	## PATH
	## SERVER_SIGNATURE
	## SCRIPT_NAME (?)
	## SCRIPT_FILENAME (?)
	## SERVER_ADMIN (?)

	def doRequest(self):
		"""
		Actually performs the request, creating the environment and
		calling self.doTransaction(env, myInput) to perform the
		response.
		"""
		self.server_version = 'Webware/0.1'
		env = {}
		if self.headers.has_key('Content-Type'):
			env['CONTENT_TYPE'] = self.headers['Content-Type']
			del self.headers['Content-Type']
		self.headersToEnviron(self.headers, env)
		env['REMOTE_ADDR'], env['REMOTE_PORT'] = map(str, self.client_address)
		env['REQUEST_METHOD'] = self.command
		path = self.path
		if path.find('?') != -1:
			env['REQUEST_URI'], env['QUERY_STRING'] = path.split('?', 1)
		else:
			env['REQUEST_URI'] = path
			env['QUERY_STRING'] = ''
		env['PATH_INFO'] = env['REQUEST_URI']
		myInput = ''
		if self.headers.has_key('Content-Length'):
			myInput = self.rfile.read(int(self.headers['Content-Length']))
		self.doTransaction(env, myInput)

	do_GET = do_POST = do_HEAD = doRequest
	# These methods are used in WebDAV requests:
	do_OPTIONS = do_PUT = do_DELETE = doRequest
	do_MKCOL = do_COPY = do_MOVE = doRequest
	do_PROPFIND = doRequest

	def headersToEnviron(self, headers, env):
		"""Use a simple heuristic to convert all the headers to
		environmental variables..."""
		for header, value in headers.items():
			env['HTTP_%s' % (header.upper().replace('-', '_'))] = value
		return env

	def processResponse(self, data):
		"""
		Takes a string (like what a CGI script would print) and
		sends the actual HTTP response (response code, headers, body).
		"""
		s = StringIO(data)
		headers = mimetools.Message(s)
		self.doLocation(headers)
		self.sendStatus(headers)
		self.sendHeaders(headers)
		self.sendBody(s)

	def doLocation(self, headers):
		"""If there's a Location header and no Status header,
		we need to add a Status header ourselves."""
		if headers.has_key('Location'):
			if not headers.has_key('Status'):
				## @@: is this the right status header?
				headers['Status'] = '301 Moved Temporarily'

	def sendStatus(self, headers):
		if not headers.has_key('Status'):
			status = "200 OK"
		else:
			status = headers['Status']
			del headers['Status']
		pos = status.find(' ')
		if pos == -1:
			code = int(status)
			message = ''
		else:
			code = int(status[:pos])
			message = status[pos:].strip()
		self.send_response(code, message)

	def sendHeaders(self, headers):
		for header, value in headers.items():
			self.send_header(header, value)
		self.end_headers()

	def sendBody(self, bodyFile):
		self.wfile.write(bodyFile.read())
		bodyFile.close()


class HTTPAppServerHandler(Handler, HTTPHandler):

	"""
	Adapters HTTPHandler to fit with ThreadedAppServer's
	model of an adapter
	"""

	protocolName = 'http'

	def handleRequest(self):
		HTTPHandler.__init__(self, self._sock, self._sock.getpeername(), None)

	def doTransaction(self, env, myInput):
		streamOut = ASStreamOut()
		requestDict = {
			'format': 'CGI',
			'time': time.time(),
			'environ': env,
			'input': StringIO(myInput),
			}
		self.dispatchRawRequest(requestDict, streamOut)
		self.processResponse(streamOut._buffer)
		self._sock.shutdown(2)

	def dispatchRawRequest(self, requestDict, streamOut):
		transaction = self._server._app.dispatchRawRequest(requestDict, streamOut)
		streamOut.close()
		transaction._application=None
		transaction.die()
		del transaction

