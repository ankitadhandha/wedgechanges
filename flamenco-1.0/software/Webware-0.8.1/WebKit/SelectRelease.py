"""
Used by the AsyncThreadedAppServer module.

This file implements an object that can force a call to select in the main asyncore.poll loop to return.
This dispathcher is added to the asyncore polling group.  It is polled for reads.  We make this object available to everyone.  When we need the asyncore select loop to return, ie, we have some data ready to go, we call the release() method, which does a quick write to it's own socket/file-descriptor.  This causes select to return.
"""

import asyncore
import asynchat

import os
import socket
import string
import thread


if os.name == 'posix':

	class SelectRelease (asyncore.file_dispatcher):
		"""
		In a posix environment, we can use a file descriptor as the object that we include in the polling loop that we force a read on.

		"""

		def __init__ (self):
			r, w = os.pipe()
			self.wpipe = w
			asyncore.file_dispatcher.__init__ (self, r)

		def readable (self):
			return 1

		def writable (self):
			return 0

		def handle_connect (self):
			pass

		def release (self):
			os.write (self.wpipe, 'x')

		def handle_read (self):
			self.recv (8192)

		def log(self,message):
			pass


else:

	class SelectRelease (asyncore.dispatcher):
		"""
		MSW can't hanlde file descriptors in a select poll, so a real socket has to be used.
		This method was adapted from a similar module in the Zope Medusa server.
		"""

		address = ('127.9.9.9', 19999)

		def __init__ (self):
			a = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
			w = socket.socket (socket.AF_INET, socket.SOCK_STREAM)

			w.setsockopt(socket.IPPROTO_TCP, 1, 1)

			# get a pair of connected sockets
			host='127.9.9.9'
			port=19999
			while 1:
				try:
					self.address=(host, port)
					a.bind(self.address)
					break
				except:
					if port <= 19950:
						raise 'Bind Error', 'Cannot bind trigger!'
					port=port - 1

			a.listen (1)
			w.setblocking (0)
			try:
				w.connect (self.address)
			except:
				pass
			r, addr = a.accept()
			a.close()
			w.setblocking (1)
			self.trigger = w

			asyncore.dispatcher.__init__ (self, r)
			self._trigger_connected = 0

		def __repr__ (self):
			return '<select-trigger (loopback) at %x>' % id(self)

		def readable (self):
			return 1

		def writable (self):
			return 0

		def handle_connect (self):
			pass

		def release (self, thunk=None):
			self.trigger.send ('x')

		def handle_read (self):
			self.recv (8192)

		def log(self, message):
			pass
