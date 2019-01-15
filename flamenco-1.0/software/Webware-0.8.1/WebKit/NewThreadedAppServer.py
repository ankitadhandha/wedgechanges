#!/usr/bin/env python
"""
AppServer

The WebKit app server is a TCP/IP server that accepts requests, hands them
off to the Application and sends the request back over the connection.

The fact that the app server stays resident is what makes it so much quicker
than traditional CGI programming. Everything gets cached.


FUTURE

	* Implement the additional settings that are commented out below.
"""


from Common import *
from AutoReloadingAppServer import AutoReloadingAppServer as AppServer
from MiscUtils.Funcs import timestamp
from marshal import dumps, loads
import os, sys
from threading import Lock, Thread, Event
import threading
import Queue
import select
import socket
import threading
import time
import errno
import traceback
from WebUtils import Funcs

debug = 0

DefaultConfig = {
	'Port':                 8086,
	'MaxServerThreads':        20,
	'MinServerThreads':        5,
	'StartServerThreads':      10,

	# @@ 2000-04-27 ce: None of the following settings are implemented
#	'RequestQueueSize':     16,#	'RequestBufferSize':    64*1024,
#	'SocketType':           'inet',      # inet, unix
}


#Need to know this value for communications
#Note that this limits the size of the dictionary we receive from the AppServer to 2,147,483,647 bytes
intLength = len(dumps(int(1)))

server = None

class ThreadedAppServer(AppServer):
	"""
	"""

	## Init ##

	def __init__(self, path=None):
		AppServer.__init__(self, path)
		threadCount = self.setting('StartServerThreads')
		self._maxServerThreads = self.setting('MaxServerThreads')
		self._minServerThreads = self.setting('MinServerThreads')
		self._threadPool = []
		self._threadCount = 0
		self._threadUseCounter = []
		# twice the number of threads we have:
		self._requestQueue = Queue.Queue(self._maxServerThreads * 2)
		self._addr = None
		self._requestID = 1

		out = sys.stdout

		out.write('Creating %d threads' % threadCount)
		for i in range(threadCount):
			self.spawnThread()
			out.write(".")
			out.flush()
		out.write("\n")

		self.recordPID()

		self._socketHandlers = {}
		self._handlerCache = {}
		self._sockets = {}

		self.addSocketHandler(self.address(), AdapterHandler)

		self.readyForRequests()

	def addSocketHandler(self, serverAddress, handlerClass):
		self._socketHandlers[serverAddress] = handlerClass
		self._handlerCache[serverAddress] = []
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
			sock.bind(serverAddress)
			sock.listen(1024)
		except:
			if self.running:
				self.initiateShutdown()
			self._closeThread.join()
			raise
		print "Listening on", serverAddress
		f = open(self.serverSidePath(
			'%s.text' % handlerClass.protocolName), 'w')
		f.write('%s:%d' % (serverAddress[0], serverAddress[1]))
		f.close()
		self._sockets[serverAddress] = sock

	def isPersistent(self):
		return 1

	def mainloop(self, timeout=1):
		from errno import EINTR

		threadCheckInterval = self._maxServerThreads*2
		threadUpdateDivisor = 5 #grabstat interval
		threadCheck=0

		while 1:
			if not self.running:
				return

			#block for timeout seconds waiting for connections
			try:
				input, output, exc = select.select(
					self._sockets.values(), [], [], timeout)
			except select.error, v:
				if v[0] == EINTR or v[0]==0: break
				else: raise

			for sock in input:
				print sock.getsockname()
				self._requestID += 1
				client, addr = sock.accept()
				serverAddress = sock.getsockname()
				try:
					handler = self._handlerCache[serverAddress].pop()
				except IndexError:
					handler = self._socketHandlers[serverAddress](self, serverAddress)
				handler.activate(client, self._requestID)
				self._requestQueue.put(handler)

			if threadCheck % threadUpdateDivisor == 0:
				self.updateThreadUsage()

			if threadCheck > threadCheckInterval:
				threadCheck=0
				self.manageThreadCount()
			else:
				threadCheck = threadCheck + 1

			self.restartIfNecessary()

	def activeThreadCount(self):
		"""
		Get a snapshot of the number of threads currently in use.
		"""
		count = 0
		for i in self._threadPool:
			if i._processing:
				count = count + 1
		return count

	def updateThreadUsage(self):
		"""
		Update the threadUseCounter list.
		"""
		count = self.activeThreadCount()
		if len(self._threadUseCounter) > self._maxServerThreads:
			self._threadUseCounter.pop(0)
		self._threadUseCounter.append(count)


	def manageThreadCount(self):
		"""
		Adjust the number of threads in use.  This algorithm
		needs work.  The edges (ie at the minserverthreads)
		are tricky.  When working with this, remember thread
		creation is CHEAP
		"""

		average = 0
		max = 0
		debug = 0

		if debug: print "ThreadUse Samples=%s" % str(self._threadUseCounter)
		for i in self._threadUseCounter:
			average += i
			if i > max:
				max = i
		average = average / len(self._threadUseCounter)
		if debug: print "Average Thread Use: ", avg
		if debug: print "Max Thread Use: ", max
		if debug: print "ThreadCount: ", self.threadCount

		if len(self._threadUseCounter) < self._maxServerThreads:
			return #not enough samples

		margin = self._threadCount / 2 #smoothing factor
		if debug: print "margin=", margin

		if average > self._threadCount - margin and \
		   self._threadCount < self._maxServerThreads:
			# Running low: double thread count
			n = min(self._threadCount,
				self._maxServerThreads - self._threadCount)
			if debug: print "Adding %s threads" % n
			for i in range(n):
				self.spawnThread()
		elif average < self._threadCount - margin and \
		     self._threadCount > self._minServerThreads:
			n=min(self._threadCount - self._minServerThreads,
			      self._threadCount - max) 
			self.absorbThread(n)
		else:
			#cleanup any stale threads that we killed but haven't joined
			self.absorbThread(0)

	def spawnThread(self):
		debug=0
		if debug: print "Spawning new thread"
		t = Thread(target=self.threadloop)
		t._processing = 0
		t.start()
		self._threadPool.append(t)
		self._threadCount += 1
		if debug: print "New Thread Spawned, threadCount=", self._threadCount
		#self.threadUseCounter=[] #reset

	def absorbThread(self, count=1):
		"""
		Absorb a thread.  We do this by putting a None on the
		Queue.  When a thread gets it, that tells it to exit.
		BUT, even though we put it on, the thread may not have
		retrieved it before we exit this function.  So we need
		to decrement the thread count even if we didn't find a
		thread that isn't alive. We'll get it the next time
		through.
		"""
		debug = 0
		if debug: print "Absorbing %s Threads" % count
		for i in range(count):
			self._requestQueue.put(None)
			self._threadCount -= 1
		for i in self._threadPool:
			if not i.isAlive():
				rv = i.join() #Don't need a timeout, it isn't alive
				self._threadPool.remove(i)
				if debug: print "Thread Absorbed, Real Thread Count=", len(self.threadPool)
		#self.threadUseCounter=[] #reset


	def threadloop(self):
		self.initThread()

		t=threading.currentThread()
		t.processing=0

		try:
			while 1:
				try:
					handler = self._requestQueue.get()
					if handler is None: #None means time to quit
						if debug: print "Thread retrieved None, quitting"
						break
					t.processing=1
					try:
						handler.handleRequest()
					except:
						traceback.print_exc(file=sys.stderr)
					t.processing=0
					handler.close()
				except Queue.Empty:
					pass
		finally:
			self.delThread()
		if debug: print threading.currentThread(), "Quitting"

	def initThread(self):
		"""
		Invoked immediately by threadloop() as a hook for
		subclasses. This implementation does nothing and
		subclasses need not invoke super.
		"""
		pass

	def delThread(self):
		"""
		Invoked immediately by threadloop() as a hook for
		subclasses. This implementation does nothing and
		subclasses need not invoke super.
		"""
		pass

	def awakeSelect(self):
		""" Send a connect to ourself to pop the select() call
		out of it's loop safely """
		for addr in self._sockets.keys():
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				sock.connect(addr)
				sock.close()
			except:
				pass

	def shutDown(self):
		self.running=0
		self.awakeSelect()
		self._shuttingdown=1  #jsl-is this used anywhere?
		print "ThreadedAppServer: Shutting Down"
		for sock in self._sockets.values():
			sock.close()
		for i in range(self._threadCount):
			self._requestQueue.put(None)#kill all threads
		for i in self._threadPool:
			try:
				i.join()
			except:
				pass
		AppServer.shutDown(self)

	## Network Server ##

	def address(self):
		if self._addr is None:
			self._addr = (self.setting('Host'), self.setting('Port'))
		return self._addr

class Handler:

	def __init__(self, server, serverAddress):
		self._server = server
		self._serverAddress = serverAddress

	def activate(self, sock, requestID):
		"""
		Activates the handler for processing the request.
		Number is the number of the request, mostly used to identify
		verbose output. Each request should be given a unique,
		incremental number.
		"""
		self._requestID = requestID
		self._sock = sock

	def close(self):
		self._sock = None
		self._server._handlerCache[self._serverAddress].append(self)

	def handleRequest(self):
		pass

	def receiveDict(self):
		"""
		Utility function to receive a marshalled dictionary.
		"""
		chunk = ''
		missing = intLength
		while missing > 0:
			block = self._sock.recv(missing)
			if not block:
				self._sock.close()
				raise NotEnoughDataError, 'received only %d of %d bytes when receiving dictLength' % (len(chunk), intLength)
			chunk += block
			missing = intLength - len(chunk)
		dictLength = loads(chunk)
		if type(dictLength) != type(1):
			self._sock.close()
			raise ProtocolError, "Invalid AppServer protocol"
		chunk = ''
		missing = dictLength
		while missing > 0:
			block = self._sock.recv(missing)
			if not block:
				self._sock.close()
				raise NotEnoughDataError, 'received only %d of %d bytes when receiving dict' % (len(chunk), dictLength)
			chunk += block
			missing = dictLength - len(chunk)
		return loads(chunk)
	

class MonitorHandler(Handler):

	protcolName = 'monitor'

	def handleRequest(self):

		verbose = self.server._verbose
		startTime = time.time()
		if verbose:
			print 'BEGIN REQUEST'
			print time.asctime(time.localtime(startTime))
		conn = self._sock
		if verbose:
			print 'receiving request from', conn

		BUFSIZE = 8*1024

		dict = self.receiveDict()

		if dict['format'] == "STATUS":
			conn.send(str(self.server._reqCount))

		if dict['format'] == 'QUIT':
			conn.send("OK")
			conn.close()
			self.server.shutDown()


from WebKit.ASStreamOut import ASStreamOut
class TASASStreamOut(ASStreamOut):

	def __init__(self, sock):
		ASStreamOut.__init__(self)
		self._socket = sock

	def flush(self):
		debug=0
		result = ASStreamOut.flush(self)
		if result: ##a true return value means we can send
			reslen = len(self._buffer)
			sent = 0
			while sent < reslen:
				try:
					sent = sent + self._socket.send(self._buffer[sent:sent+8192])
				except socket.error, e:
					if e[0]==errno.EPIPE: #broken pipe
						pass
					else:
						print "StreamOut Error: ", e
					break
			self.pop(sent)


class AdapterHandler(Handler):

	protocolName = 'address'

	def handleRequest(self):
		verbose = self._server._verbose
		self._startTime = time.time()
		if verbose:
			print '%5i  %s ' % (self._requestID, timestamp()['pretty']),

		data = []
		dict = self.receiveDict()
		if dict and verbose and dict.has_key('environ'):
			requestURI = Funcs.requestURI(dict['environ'])
			print requestURI
		else:
			requestURI = None

		dict['input'] = self.makeInput()
		streamOut = TASASStreamOut(self._sock)
		transaction = self._server._app.dispatchRawRequest(dict, streamOut)
		streamOut.close()

		try:
			self._sock.shutdown(1)
			self._sock.close()
		except:
			pass

		if self._server._verbose:
			duration = '%0.2f secs' % (time.time() - self._startTime)
			duration = string.ljust(duration, 19)
			print '%5i  %s  %s' % (self._requestID, duration, requestURI)
			print

		transaction._application=None
		transaction.die()
		del transaction

	def makeInput(self):
		return self._sock.makefile("rb",8012)

def run(useMonitor = 0, http=0, workDir=None):
	global server
	global monitor
	monitor = useMonitor
	try:
		server = None
		server = ThreadedAppServer(workDir)
		if useMonitor:
			addr = server.address()
			server.addSocketHandler((addr[0], addr[1]-1),
						MonitorHandler)
		if http:
			from WebKit.HTTPServer import HTTPAppServerHandler
			addr = ('127.0.0.1', 8080)
			server.addSocketHandler(addr, HTTPAppServerHandler)

		# On NT, run mainloop in a different thread because
		# it's not safe for Ctrl-C to be caught while
		# manipulating the queues.  It's not safe on Linux
		# either, but there, it appears that Ctrl-C will
		# trigger an exception in ANY thread, so this fix
		# doesn't help.

		if os.name == 'nt':
			# catch the exception raised by sys.exit so
			# that we can re-call it in the main thread.
			global exitStatus
			exitStatus = None
			def windowsmainloop(server):
				global exitStatus
				try:
					server.mainloop()
				except SystemExit, e:
					exitStatus = e.code

			# Run the server thread
			t = threading.Thread(target=windowsmainloop, args=(server,))
			t.start()
			try:
				while server.running:
					time.sleep(1.0)
			except KeyboardInterrupt:
				pass
			server.running = 0
			t.join()

			# re-call sys.exit if necessary
			if exitStatus:
				sys.exit(exitStatus)
		else:
			try:
				server.mainloop()
			except KeyboardInterrupt, e:
				server.shutDown()
	except Exception, e:
		if not isinstance(e, SystemExit):
			import traceback
			traceback.print_exc(file=sys.stderr)
		print
		print "Exiting AppServer"
		if server:
			if server.running:
				server.initiateShutdown()
			server._closeThread.join()
		# if we're here as a result of exit() being called,
		# exit with that return code.
		if isinstance(e,SystemExit):
			sys.exit(e)

	sys.exit()


def shutDown(arg1,arg2):
	global server
	print "Shutdown Called", time.asctime(time.localtime(time.time()))
	if server:
		server.initiateShutdown()
	else:
		print 'WARNING: No server reference to shutdown.'

import signal
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)




usage = """
The AppServer is the main process of WebKit.  It handles requests for
servlets from webservers.  ThreadedAppServer takes the following
command line arguments: stop: Stop the currently running Apperver.
daemon: run as a daemon If AppServer is called with no arguments, it
will start the AppServer and record the pid of the process in
appserverpid.txt
"""


import re
settingRE = re.compile(r'^--([a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z][a-zA-Z0-9]*)=')
from MiscUtils import Configurable

def main(args):
	monitor = 0
	http = 0
	function = run
	daemon = 0
	workDir = None

	for i in args[:]:
		if settingRE.match(i):
			match = settingRE.match(i)
			name = match.group(1)
			value = i[match.end():]
			Configurable.addCommandLineSetting(name, value)
		elif i == "monitor":
			print "Enabling Monitoring"
			monitor=1
		elif i == "stop":
			import AppServer
			function=AppServer.stop
		elif i == "daemon":
			daemon=1
		elif i == "start":
			pass
		elif i[:8] == "workdir=":
			workDir = i[8:]
		elif i == "http":
			http = 1
		else:
			print usage

	if daemon:
		if os.name == "posix":
			pid=os.fork()
			if pid:
				sys.exit()
		else:
			print "daemon mode not available on your OS"
	function(useMonitor=monitor, http=http, workDir=workDir)


