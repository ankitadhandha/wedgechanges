"""
This module co-ordinates the reading of the source file.
It maintains the current position of the parser in the source file.

--------------------------------------------------------------------------
   (c) Copyright by Jay Love, 2000 (mailto:jsliv@jslove.net)

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee or royalty is hereby granted,
    provided that the above copyright notice appear in all copies and that
    both that copyright notice and this permission notice appear in
    supporting documentation or portions thereof, including modifications,
    that you make.

    THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD TO
    THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
    INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
    FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
    NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
    WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

        This software is based in part on work done by the Jakarta group.

"""

from Context import *

import types
import copy
import string
import os



class Mark:
	"""The Mark class marks a point in an input stream."""

	def __init__(self, reader, fileid=None, stream=None, inBaseDir=None, encoding=None):
		
		if isinstance(reader,StreamReader):
			self.reader = reader
			self.fileid = fileid
			self.includeStack = []
			self.cursor = 0
			self.stream = stream
			self.baseDir=inBaseDir
			self.encoding=encoding

		else:
			self = copy.copy(reader)
		
##		I think the includeStack will be copied correctly, but check here for problems
##		raise 'clone include stack'


## JSP has an equals function, but I don't think I need that, b/c of using copy,
## but maybe I do

	def getFile(self):
		return self.reader.getFile(self.fileid)

	def __str__(self):
		return self.getFile() + '(' + str(self.line) + str(self.col) + ')'
	
	
	def __repr__(self):
		return self.getFile() + '(' + str(self.col) + ')'	

	def pushStream(self, infileid, inStream, inBaseDir, inEncoding):
		self.includeStack.append((self.cursor, self.fileid, self.baseDir, self.encoding, self.stream))
		self.cursor=0
		self.fileid=infileid
		self.baseDir=inBaseDir
		self.encoding=inEncoding
		self.stream=inStream


	def popStream(self):
		if len(self.includeStack) == 0:
			return 0 #false
		list=self.includeStack[len(self.includeStack)-1]
		del self.includeStack[len(self.includeStack)-1]
		self.cursor=list[0]
		self.fileid=list[1]
		self.baseDir=list[2]
		self.encoding=list[3]
		self.stream=list[4]
		return 1 #true
	 




class StreamReader:
	"""This class handles the psp source file
	It provides the characters to the other parts of the system.
	It can move forward and backwards in a file and remember locactions"""

	def __init__(self,filename,ctxt):
		self._pspfile = filename
		self._ctxt = ctxt
		self._filehandle = None
		self.sourcefiles=[]
		self.current = None
		self.size = 0
		self.master=None

	def init(self):
		self.pushFile(self._ctxt.getFullPspFileName())


	def registerSourceFile(self, file):
		self.sourcefiles.append(file)
		self.size = self.size+1 #what is size for?
		return len(self.sourcefiles)-1

	def pushFile(self, file, encoding=None):
		assert type(file)==type('')
		#if type(file) != type(''): #we've got an open filehandle-don't think this case exists

		#don't know what this master stuff is, but until I do, implement it
		#Oh, it's the original file

		if self.master == None:
			parent = None
			self.master=file
		else:
			parent = os.path.split(self.master)[0]

		isAbsolute = os.path.isabs(file)

		if parent != None and not isAbsolute:
			file = os.path.join(parent,file)


		fileid = self.registerSourceFile(file)
		handle = open(file,'r')
		stream = handle.read()
		handle.seek(0,0)
		lines = handle.readlines() #(self, reader, linearray, fileid, includestack, stream):
		#mark = Mark(self, lines, fileid, None, stream, self._ctxt.getBaseUri(),encoding)

		z=0
		for i in lines:
			lines[z]=string.replace(i,'\r\n','\n')
			z=z+1
		
		stream=string.join(lines,'')

		if self.current == None:
			#self.current = mark
			self.current = mark = Mark(self, fileid, stream, self._ctxt.getBaseUri(),encoding)
		else:
			self.current.pushStream(fileid, stream, self._ctxt.getBaseUri(), encoding) #don't use yet

	def popFile(self):
		
		if self.current == None:
			return 0
		self.size = self.size-1 #what the hell is this?
		r=self.current.popStream()
		return r

	def getFile(self,i):
		return self.sourcefiles[i]

	def newSourceFile(self,filename):
		if filename in self.sourcefiles:
			return None
		sourcefiles.append(filename)
		return len(self.sourcefiles)

	def Mark(self):
		return copy.copy(self.current)
		#return Mark(self.current)

##	def advanceLine(self):
##		raise "NotUsingAnymore"
##		if self.current.row < len(self.current.linearray)-1:
##			self.current.cursor = self.current.cursor + len(self.current.linearray[self.current.row][self.current.col:])
##			self.current.row = self.current.row + 1
##			self.current.col = 0
##		else:
##			self.current.cursor = self.current.cursor + len(self.current.linearray[self.current.row][self.current.col:])
##			self.current.col = len(self.current.linearray[self.current.row][:])
##			if self.hasMoreInput() == 0:
##				raise EOFError()

	def skipUntil(self, st):
		"""greedy search, return the point before the string, but move reader past it"""
		pt = string.find(self.current.stream[self.current.cursor:],st)
		if pt == -1:
			self.current.cursor = len(self.current.stream)
			if self.hasMoreInput():
				self.popFile() #Should I do this here? 6/1/00
				self.skipUntil(st)
			else:
				raise "EndofInputError"
		else:
			self.current.cursor = self.current.cursor+pt
			ret =  self.Mark()
			self.current.cursor = self.current.cursor+len(st)
			return ret



	def reset(self, mark):
		self.current = mark #Mark(mark)    


	def Matches(self,st):
		if st == self.current.stream[self.current.cursor:self.current.cursor+len(st)]:
			return 1
		return 0

	def Advance(self,length):
		"""Advance length characters"""
		if length + self.current.cursor <= len(self.current.stream):
			self.current.cursor = self.current.cursor+length
		else:
			prog = len(self.current.stream) - self.current.cursor
			self.current.cursor=len(self.current.stream) # -1??
			if self.hasMoreInput():
				self.Advance(length-prog)
			else:
				raise EOFError()


	def nextChar(self):
		if self.hasMoreInput() == 0: return -1
		ch = self.current.stream[self.current.cursor]
		self.Advance(1)
		return ch


	def isSpace(self):
		"""no advancing"""
		return self.current.stream[self.current.cursor] == ' ' or self.current.stream[self.current.cursor] == '\n'


	def isDelimiter(self):
		if not self.isSpace():
			ch = self.peekChar()
			#look for single character work delimiter
			if ch == '=' or ch == '\"' or ch == "'" or ch == '/':
				return 1
			#look for end of comment or basic end tag
			if ch == '-':
				mark = self.Mark()
				ch = self.nextChar()
				ch2 = self.nextChar()
				if ch == '>' or (ch == '-' and ch2 == '>'):
					self.reset(mark)
					return 1
				else:
					self.reset(mark)
					return 0
		else:
			return 1
		



	def peekChar(self,cnt=1):
		if self.hasMoreInput():
			return self.current.stream[self.current.cursor:self.current.cursor+cnt]
		raise "EndofStream"

	def skipSpaces(self):
		i = 0
		while self.isSpace():
			self.nextChar()
			i = i+1
		return i

	def getChars(self,start,stop):
		oldcurr = self.Mark()
		self.reset(start)
		chars = self.current.stream[start.cursor:stop.cursor]
		self.reset(oldcurr)
		return chars

	def hasMoreInput(self):
		if self.current.cursor >= len(self.current.stream):
			while self.popFile():
				if self.current.cursor < len(self.current.stream) :
					return 1
			return 0
		return 1

	
	def nextContent(self):
		""" Find next <"""
		cur_cursor = self.current.cursor
		self.current.cursor = self.current.cursor+1
		pt = string.find(self.current.stream[self.current.cursor:],'<')
		if pt == -1:
				self.current.cursor = len(self.current.stream) #-1???
		else:
			self.current.cursor=self.current.cursor+pt
		return self.current.stream[cur_cursor:self.current.cursor]



	def parseTagAttributes(self):
		"""parses the attributes at the beginning of a tag"""

		values = {}
		while 1:
			self.skipSpaces()
			ch = self.peekChar()
			if ch == '>':
				return values
			if ch == '-':
				mark = self.Mark()
				self.nextChar()
				try:
					if self.nextChar() == '-' and self.nextChar() == '>':
						return values
				finally:
					self.reset(mark)
			elif ch == '%':
				mark = self.Mark()
				self.nextChar()
				try:
					ts = self.peekChar()
					if ts == '>':
						self.reset(mark)
						return values
				finally:
					self.reset(mark)

			if ch == None:
				break

			self.parseAttributeValue(values)
		#EOF
		raise 'Unterminated Attribute'

	def parseAttributeValue(self, valuedict):
		self.skipSpaces()
		name = self.parseToken(0)
		self.skipSpaces()
		if self.peekChar() != '=':
			raise 'PSP Error - no attribute value'
		ch = self.nextChar()
		self.skipSpaces()
		value = self.parseToken(1)
		self.skipSpaces()
		valuedict[name]=value

	def parseToken(self, quoted):
		""" This may not be quite right"""
		buffer=[]
		self.skipSpaces()
		ch = self.peekChar()
		if quoted:
			if (ch=='\"' or ch == "\'"):
				endquote = ch
				ch = self.nextChar()
				ch=self.peekChar()
				while ch != None and ch != endquote:
					ch = self.nextChar() 
					if ch == '\\':
						ch = nextChar()
					buffer.append(ch)
					ch = self.peekChar()
				if ch == None:
					raise 'Unterminated Attribute Value'
				self.nextChar()
		else:
			if not self.isDelimiter():
				while not self.isDelimiter():
					ch = self.nextChar()
					if ch == '\\':
						ch = self.peekChar()
						if ch == '\"' or ch == "'" or ch == '>' or ch == '%':
							ch = self.nextChar()
					buffer.append(ch)
		return string.join(buffer,'')
	

