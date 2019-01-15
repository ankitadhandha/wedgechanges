#!/usr/bin/env python
# If the Webware installation is located somewhere else,
# then set the WebwareDir variable to point to it.
# For example, WebwareDir = '/Servers/Webware'
WebwareDir = None

# If you used the MakeAppWorkDir.py script to make a separate
# application working directory, specify it here.
AppWorkDir = None


############################################################
## Path setup
############################################################

try:
	import os, sys, string
	if not WebwareDir:
		WebwareDir = os.path.dirname(os.path.dirname(os.getcwd()))
	sys.path.insert(0, WebwareDir)
	webKitDir = os.path.join(WebwareDir, 'WebKit')
	if AppWorkDir is None:
		AppWorkDir = webKitDir
	else:
		sys.path.insert(0, AppWorkDir)

	from WebKit.Adapters.Adapter import Adapter
	(host, port) = string.split(open(os.path.join(webKitDir, 'address.text')).read(), ':')
	if os.name=='nt' and host=='':
		# MS Windows doesn't like a blank host name
		host = 'localhost'
	port = int(port)
except 0:
	## @@: Is there something we should do with exceptions here?
	## I'm apt to just let them print to stderr and quit like normal,
	## but I'm not sure.
	pass



############################################################
## HTTP Server
############################################################

from WebKit.HTTPServer import HTTPHandler, run

class HTTPAdapter(HTTPHandler, Adapter):

	def __init__(self, *vars):
		Adapter.__init__(self, webKitDir)
		HTTPHandler.__init__(self, *vars)

	def doTransaction(self, env, myInput):
		self.transactWithAppServer(env, myInput, host, port)


class ThreadedHTTPServer(BaseHTTPServer.HTTPServer):
	"""
	A threaded version of BaseHTTPServer.
	
	Model taken from a 2001 comp.lang.python post by Michael Abbott.
	"""

	def __init__(self, *args):
		self._threads = {}
		self._threadID = 1
		BaseHTTPServer.HTTPServer.__init__(self, *args)

	def handle_request(self):
		try:
			request, client_address = self.get_request()
		except socket.error:
			return
		t = threading.Thread(target=self.handle_request_body,
						 args=(request, client_address, self._threadID))
		t.start()
		self._threads[self._threadID] = t
		self._threadID += 1
		
	# This part of the processing is run in its own thread
	def handle_request_body(self, request, client_address, threadID):
		if self.verify_request(request, client_address):
			try:
				self.process_request(request, client_address)
			except:
				self.handle_error(request, client_address)
		self.close_request(request)
		del self._threads[threadID]

	def serve_forever(self):
		self._keepGoing = 1
		while self._keepGoing:
			self.handle_request()
		self.socket.close()

	def shutDown(self):
		self._keepGoing = 0
		for thread in self._threads.values():
			thread.join()
		self.socket.shutdown(2)
		self.socket.close()


def run(serverAddress, klass=HTTPHandler):
	httpd = ThreadedHTTPServer(serverAddress, klass)
	httpd.serve_forever()


############################################################
## Comand-line interface
############################################################

usage = """HTTPServer - Standalone HTTP server to connect to AppServer
Usage:
	python HTTPServer.py [OPTIONS]
Options:
	-p PORT     Port to connect to (default: 80)
	-h HOST     Host to server from (for computers with multiple
				interfaces, default 127.0.0.1)
	-d          Run as daemon
"""

def main():
	import getopt
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'p:h:d',
								   ['port=', 'host=', 'daemon'])
	except getopt.GetoptErrro:
		print usage
		sys.exit(2)
	for o, a in opts:
		if o in ('-p', '--port'):
			port = int(a)
		elif o in ('-h', '--host'):
			host = a
		elif o in ('-d', '--daemon'):
			daemon = 1
	if daemon:
		if os.fork() or os.fork():
			sys.exit(0)
	print "PS: This adapter is experimental and should not be used in\na production environment"
	run()

if __name__ == '__main__':
	main()


