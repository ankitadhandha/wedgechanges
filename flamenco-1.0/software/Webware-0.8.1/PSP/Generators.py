

"""
	This module holds the classes that generate the python code reulting from the PSP template file.
	As the parser encounters PSP elements, it creates a new Generator object for that type of element.
	Each of these elements is put into a list maintained by the ParseEventHandler object.  When it comes
	time to output the Source Code, each generator is called in turn to create it's source.

	
--------------------------------------------------------------------------------
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




import PSPUtils
import BraceConverter
try:
	import string
except:
	pass

try:
	import os
except:
	pass

#these are global so that the ParseEventHandler and this module agree.
ResponseObject = 'res'
AwakeCreated = 0


class GenericGenerator:
	""" Base class for the generators """
	def __init__(self, ctxt=None):
		self._ctxt = ctxt
		self.phase='Service'


class ExpressionGenerator(GenericGenerator):
	""" This class handles expression blocks.  It simply outputs
	the (hopefully) python expression within the block wrapped
	with a _formatter() call. """

	def __init__(self, chars):
		self.chars = chars
		GenericGenerator.__init__(self)

	def generate(self, writer, phase=None):
		writer.println('res.write(_formatter(' + PSPUtils.removeQuotes(self.chars) + '))')




class CharDataGenerator(GenericGenerator):
	"""This class handles standard character output, mostly HTML.  It just dumps it out.
	Need to handle all the escaping of characters.  It's just skipped for now."""

	def __init__(self, chars):
		GenericGenerator.__init__(self)
		self.chars = chars

	def generate(self, writer, phase=None):
		# Quote any existing backslash so generated python will not interpret it when running.
		self.chars = string.replace(self.chars, '\\', r'\\')

		# quote any single quotes so it does not get confused with our triple-quotes
		self.chars = string.replace(self.chars,'"',r'\"')

		self.generateChunk(writer)

	def generateChunk(self, writer, start=0, stop=None):
		writer.printIndent()#gives a tab
		writer.printChars(ResponseObject+'.write("""')
		writer.printChars(self.chars)
		writer.printChars('""")')
		writer.printChars('\n')

	def mergeData(self, cdGen):
		self.chars = self.chars + cdGen.chars

class ScriptGenerator(GenericGenerator):
	"""generates scripts"""
	def __init__(self, chars, attrs):
		GenericGenerator.__init__(self)	
		self.chars = chars

	def generate(self, writer, phase=None):

		if writer._useBraces:
			# send lines to be output by the braces generator
			bc = BraceConverter.BraceConverter()
			for line in string.splitfields(PSPUtils.removeQuotes(self.chars),'\n'):
				bc.parseLine(line,writer)
			return


		#check for whitespace at the beginning and if less than 2 spaces, remove
		if self.chars[:1]==' ' and self.chars[:2]!= '  ':
			self.chars=string.lstrip(self.chars)
		lines = string.splitfields(PSPUtils.removeQuotes(self.chars),'\n')
		#writer.printList(string.splitfields(PSPUtils.removeQuotes(self.chars),'\n'))
		

		#userIndent check
		if len(lines[-1])>0 and lines[-1][-1] == '$':
			lastline = lines[-1] = lines[-1][:-1]
			if lastline == '': lastline = lines[-2] #handle endscript marker on its own line
			count=0
			while lastline[count] in string.whitespace:
				count=count+1
			userIndent = lastline[:count]
		else:
			userIndent = writer.EMPTY_STRING
			lastline=lines[-1]

		#print out code, (moved from above)
		writer._userIndent = writer.EMPTY_STRING #reset to none
		writer.printList(lines)
		writer.printChars('\n')

		#check for a block
		#lastline = string.splitfields(PSPUtils.removeQuotes(self.chars),'\n')[-1]
		commentstart = string.find(lastline,'#')
		if commentstart > 0: lastline = lastline[:commentstart]
		blockcheck=string.rstrip(lastline)
		if len(blockcheck)>0 and blockcheck[-1] == ':':
			writer.pushIndent()
			writer.println()
			writer._blockcount = writer._blockcount+1
			#check for end of block, "pass" by itself
		if string.strip(self.chars) == 'pass' and writer._blockcount>0:
			writer.popIndent()
			writer.println()
			writer._blockcount = writer._blockcount-1

		#set userIndent for subsequent HTML
		writer._userIndent = userIndent

class EndBlockGenerator(GenericGenerator):
	def __init__(self):
		GenericGenerator.__init__(self)

	def generate(self, writer, phase=None):
		if writer._blockcount>0:
			writer.popIndent()
			writer.println()
			writer._blockcount = writer._blockcount-1
		writer._userIndent = writer.EMPTY_STRING
		
		

class MethodGenerator(GenericGenerator):
	""" generates class methods defined in the PSP page.  There are two parts to method generation.  This
	class handles getting the method name and parameters set up."""
	def __init__(self, chars, attrs):
		GenericGenerator.__init__(self)
		self.phase='Declarations'
		self.attrs=attrs
	
	def generate(self, writer, phase=None):
		writer.printIndent()
		writer.printChars('def ')
		writer.printChars(self.attrs['name'])
		writer.printChars('(')
		#self.attrs['params']
		writer.printChars('self')
		if self.attrs.has_key('params') and self.attrs['params'] != '':
			writer.printChars(', ')
			writer.printChars(self.attrs['params'])
		writer.printChars('):\n')
		if self.attrs['name'] == 'awake':  #This is hacky, need better method, but it works: MAybe I should require a standard parent and do the intPSP call in that awake???????
			AwakeCreated = 1
			#below indented on 6/1/00, was outside if block
			writer.pushIndent()
			writer.println('self.initPSP()\n')
			writer.popIndent()
			writer.println()

class MethodEndGenerator(GenericGenerator):
	""" Part of class method generation.  After MethodGenerator, MethodEndGenerator actually generates
	the code for th method body."""
	def __init__(self, chars, attrs):
		GenericGenerator.__init__(self)
		self.phase='Declarations'
		self.attrs=attrs
		self.chars=chars

	def generate(self, writer, phase=None):
		writer.pushIndent()
		writer.printList(string.splitfields(PSPUtils.removeQuotes(self.chars),'\n'))
		writer.printChars('\n')
		writer.popIndent()


class IncludeGenerator(GenericGenerator):
	"""
	Handles psp:include directives.  This is a new version of this directive that actually
	forwards the request to the specified page.
	"""

#	_theFunction = """
#__pspincludepath = self.transaction().request().urlPathDir() + "%s"
#self.transaction().application().includeURL(self.transaction(), __pspincludepath)
	_theFunction = """
__pspincludepath = "%s"
self.transaction().application().includeURL(self.transaction(), __pspincludepath)
"""

	def __init__(self, attrs, param, ctxt):
		GenericGenerator.__init__(self,ctxt)
		self.attrs = attrs
		self.param = param
		self.scriptgen = None

		self.url = attrs.get('path')
		if self.url == None:
			raise "No path attribute in Include"
	
		self.scriptgen = ScriptGenerator(self._theFunction % self.url, None)
	

	def generate(self, writer, phase=None):
		"""
		Just insert theFunction
		"""
		self.scriptgen.generate(writer, phase)


class InsertGenerator(GenericGenerator):
	""" Include files designated by the psp:insert syntax.
	If the attribute static is set to true or 1, we include the file now, at compile time.
	Otherwise, we use a function added to every PSP page named __includeFile, which reads the file at run time.
	"""
	def __init__(self, attrs, param, ctxt):
		GenericGenerator.__init__(self,ctxt)
		self.attrs = attrs
		self.param = param
		self.static=1
		self.scriptgen = None

		self.page = attrs.get('file')
		if self.page == None:
			raise "No Page attribute in Include"
		thepath=self._ctxt.resolveRelativeURI(self.page)


		self.static = attrs.get('static', None)
		if self.static == string.lower("true") or self.static == "1":
			self.static=1
	
		if not os.path.exists(thepath):
			print self.page
			raise "Invalid included file",thepath
		self.page=thepath

		if not self.static:
			self.scriptgen = ScriptGenerator("self.__includeFile('%s')" % string.replace(thepath, '\\', '\\\\'), None)

	def generate(self, writer, phase=None):
		""" JSP does this in the servlet.  I'm doing it here because I have triple quotes.
		Note: res.write statements inflate the size of the resulting classfile when it is cached.
		Cut down on those by using a single res.write on the whole file, after escaping any triple-double quotes."""

		if self.static:
			data = open(self.page).read()
			data=string.replace(data,'"""',r'\"""')
			writer.println('res.write("""'+data+'""")')
			writer.println()
		else:
			self.scriptgen.generate(writer, phase)
			
		

