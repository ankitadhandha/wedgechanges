"""
This module defines a class for handling writing reponses.
"""

import string
import exceptions
import types

debug = 0

class InvalidCommandSequence(exceptions.Exception):
	pass

class ASStreamOut:
	"""
	This is a response stream to the client.
	The key attributes of this class are:
	
	autoCommit: if True (1), the stream will automatically start sending data once
	it has accumulated bufferSize data.  This means that it will ask the response
	to commit itself, without developer interaction.

	bufferSize: The size of the data buffer.  This is only used when autocommit is true (1).
	If not using autocommit, the whole response is buffered and sent in one shot when the
	servlet is done..

	flush(): Send the accumulated response data now. Will ask the Response to commit if
	it hasn't already done so.
	"""

	def __init__(self):
		self._autoCommit = 0
		self._bufferSize = 8192
		self._committed = 0
		self._needCommit = 0
		self._chunks = []
		self._buffer=''
		self._chunkLen=0
		self._closed = 0


	def autoCommit(self, val=0):
		"""Get/Set the value of autoCommit."""
		assert type(val) is types.IntType, "autoCommit must be an integer"
		self._autoCommit = val
		return val

	def bufferSize(self, size=8192):
		"""
		Returns the size of the buffer, and sets a new size if one is
		provided.
		"""
		assert type(size) is types.IntType, "bufferSize must be an Integer"
		self._bufferSize=size
		return self._bufferSize

	def flush(self):
		"""
		Send available data as soon as possible, ie Now
		Returns 1 if we are ready to send, otherwise 0
		"""
		assert not self._closed, "Trying to flush when already closed"
		if debug: print ">>> Flushing ASStreamOut"
		if not self._committed:
			if self._autoCommit:
				if debug: print "ASSTreamOut.flush setting needCommit"
				self._needCommit = 1
			return 0
		try:
			self._buffer = self._buffer + string.join(self._chunks,'')
		finally:
			self._chunks = []
			self._chunkLen = 0
		return 1

	def buffer(self):
		"""
		Return accumulated data which has not yet been
		flushed.  We want to be able to get at this data
		without having to call flush first, so that we can
		(for example) integrate automatic HTML validation.
		"""
		# if flush has been called, return what was flushed
		if self._buffer:
			return self._buffer
		# otherwise return the buffered chunks 
		else:
			return string.join(self._chunks,'')

	def clear(self):
		"""
		Try to clear any accumulated response data.  Will fail if the response is already sommitted.
		"""
		if debug: print ">>> strmOut clear called"
		if self._committed: raise InvalidCommandSequence()
		self._buffer = ''
		self._chunks = []
		self._chunkLen=0

	def close(self):
		"""
		Close this buffer.  No more data may be sent.
		"""
		if debug: print ">>> ASStream close called"
		self.flush()
		self._closed = 1
		self._committed = 1
		self._autocommit = 1

	def closed(self):
		"""
		Are we closed to new data?
		"""
		return self._closed

	def size(self):
		"""
		Returns the current size of the data held here
		"""
		return self._chunkLen + len(self._buffer)

	def prepend(self, charstr):
		"""
		Add the attached string to front of the response buffer.
		Invalid if we are already committed.
		"""
		if self.committed() or self.closed():
			raise InvalidCommandSequence()
		if self._buffer:
			self._buffer = charstr + self._buffer
		else:
			self._chunks.insert(0,charstr)
			self._chunkLen = self._chunkLen + len(charstr)

	def pop(self, count):
		"""
		Remove count bytes from the front of the buffer
		"""
		if debug: print "AStreamOut popping %s" % count
		#should we check for an excessive pop length?
		assert count <= len(self._buffer)
		self._buffer = self._buffer[count:]

	def committed(self):
		"""
		Are we committed?
		"""
		return self._committed


	def needCommit(self):
		"""
		Called by the HTTPResponse instance that is using this instance
		to ask if the response needs to be prepared to be delivered.
		The response should then commit it's headers, etc.
		"""
		return self._needCommit

	def commit(self, autoCommit=1):
		"""
		Called by the Response to tell us to go.
		If autoCommit is 1, then we will be placed into autoCommit mode.
		"""
		if debug: print ">>> ASStreamOut Committing"
		self._committed = 1
		self._autoCommit = autoCommit
		self.flush()

	def write(self, charstr):
		"""
		Write a string to the buffer.
		"""
		if debug: print ">>> ASStreamOut writing %s characters" % len(charstr)
		assert not self._closed, "Stream Already Closed"
		self._chunks.append(charstr)
		self._chunkLen = self._chunkLen + len(charstr)
		if  self._autoCommit and self._chunkLen > self._bufferSize:
				if debug: print ">>> ASStreamOut.write flushing"
				self.flush()
			
