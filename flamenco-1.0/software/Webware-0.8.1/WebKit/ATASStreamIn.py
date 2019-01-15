"""
Input buffering code for AsyncThreadedAppServer.

This module creates a file interface to data being received through
an asynconous socket.

Based entirely on code contributed by Vladimir Kralik.
Tweaked by Jay Love.

"""


import string

class ATASStreamIn:
	# methods to simulating read file-access to ayncore.dispatcher,
	# idea from StringIO

	def __init__(self, dispatcher, buffersize=8192):
		self._dispatcher=dispatcher
		self._buffersize=buffersize
		self.reset()

	def reset(self):
		self.len = 0
		self.buflist = []
		self.closed = 0
		self.softspace = 0
		self._hasMore=1		# in socket
		self._notQueued=1	# in request queue
 
	def dataAvailable(self):
		return not self._hasMore

 
	def canRecv(self):
		return self._hasMore and self._notQueued
		
	def recv(self):
		assert self._hasMore and self._notQueued
		
		data = self._dispatcher.recv(8192)
		lendata=len(data)
		self.len=self.len+lendata

		if lendata > 0:
			self.buflist.append(data)
		else:
			self.buflist.append(data)
			self._hasMore=0	# all is readed

		if self._hasMore and self.len < self._buffersize:
			pass
		else:
			self._notQueued=0
			self._dispatcher.server.requestQueue.put(self._dispatcher)
			
	# file access 
	def close(self):
		if not self.closed:
			self.closed = 1
			del self.buflist, self.len

	def isatty(self):
		if self.closed:
			raise ValueError, "I/O operation on closed file"
		return 0
	
	def read(self, n = -1):
		assert not self._notQueued

		if self.closed:
			raise ValueError, "I/O operation on closed file"
		if n==0: return ''
		elif n < 0: # read all data
			if self._hasMore: # has more data in socket, read it 
				sock=self._dispatcher.socket
				try :
					sock.setblocking(1)
					while 1:
						data=sock.recv(8192)
						if not data: break
						self.buflist.append(data)
				finally:
					sock.setblocking(0)
					self._hasMore=0
			return string.joinfields(self.buflist,'')
		elif self.buflist:
			outlist=[]
			outlen=0
			while self.buflist:
				data=self.buflist.pop(0)
				lendata=len(data)
				outlen=outlen+lendata
				if outlen>n: break
				outlist.append(data)
			if outlen>n:
				diff=n-outlen+lendata
				outlist.append(data[:diff])
				self.buflist.insert(0, data[diff:])
			elif self._hasMore and outlen<n:
				outlist.append(self.read(n-outlen))
			return string.joinfields(outlist,'')
		elif self._hasMore:
			sock=self._dispatcher.socket
			try :
				sock.setblocking(1)
				data=sock.recv(n)
			finally:
				sock.setblocking(0)
				self._hasMore=0
			return data
		else: return ''

	def _readlinedata(self,data,length,outlist):
		i = string.find(data, '\n')
		if i<0:	# not found
			if length and len(data)>=length:
				i=length
			else:
				outlist.append(data)
				return (0,length and length-len(data))
		elif length and i>=length: i=length
		else: i=i+1
		
		dd=data[:i]
		outlist.append(dd)
		self.buflist.insert(0,data[i:])
		return (1,length and length-len(data)) # read all 
		

	def readline(self, length=None):
		assert not self._notQueued
		if self.closed:
			raise ValueError, "I/O operation on closed file"

		if length==0: return ''
		elif self.buflist:
			outlist=[]
			while self.buflist:
				data=self.buflist.pop(0)
				con,length = self._readlinedata(
					data,length,outlist)
				if con: break
			if self._hasMore and not con:
				outlist.append(self.readline(length))
			return string.joinfields(outlist,'')
		elif self._hasMore:
			sock=self._dispatcher.socket
			try :
				outlist=[]
				sock.setblocking(1)
				while 1:
					if self.buflist:data=self.buflist.pop(0)
					else:
						data=sock.recv(8192)
						if not data:
							self._hasMore=0
							break
					con,length = self._readlinedata(
						data,length,outlist)
					if con: break
				return string.joinfields(outlist,'')
			finally:
				sock.setblocking(0)
		else: return ''

	def readlines(self):
		lines = []
		line = self.readline()
		while line:
			lines.append(line)
			line = self.readline()
		return lines

	def flush(self):
		if self.closed:
			raise ValueError, "I/O operation on closed file"
