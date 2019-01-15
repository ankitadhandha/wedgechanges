"""
This module is called when the Parser encounters psp tokens.  It creates a generator to handle the psp
token.  When the PSP source file is fully parsed, this module calls all of the generators in turn to
output their source code.


-----------------------------------------------------------------------------------------------------
    (c) Copyright by Jay Love, 2000 (mailto:jsliv@jslove.net)

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee or royalty is hereby granted,
    provided that the above copyright notice appear in all copies and that
    both that copyright notice and this permission notice appear in
    supporting documentation or portions thereof, including modifications,
    that you make.

    THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD TO
    THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS, IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY SPECIAL,
    INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
    FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
    NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
    WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

    This software is based in part on work done by the Jakarta group.

"""


from Generators import *
import string




class ParseEventHandler:
	"""This is a key class.  It implements the handling of all the parsing elements.  Note:  This files JSP cousin is called ParseEventListener, I don\'t know why, but Handler seemed more appropriate to me."""

	aspace=' '
	defaults = {'BASE_CLASS':'WebKit.Page',
				'BASE_METHOD':'writeHTML',
				'imports':{'filename':'classes'},
				'threadSafe':'no',
				'instanceSafe':'yes',
				'indent':int(4),
				'gobbleWhitespace':1,
				'formatter':'str',
				}

	def __init__(self, ctxt, parser):

		self._ctxt = ctxt

		self._gens=[]

		self._reader = ctxt.getReader()
		self._writer = ctxt.getServletWriter()
		self._parser = parser

		self._imports=[]
		self._importedSymbols = []
		self._baseMethod = self.defaults['BASE_METHOD']
		self._baseClasses = [self.defaults['BASE_CLASS']]
		self._threadSafe = self.defaults['threadSafe']
		self._instanceSafe = self.defaults['instanceSafe']
		self._indent=self.defaults['indent']
		self._gobbleWhitespace=self.defaults['gobbleWhitespace']
		self._formatter=self.defaults['formatter']

	def addGenerator(self, gen):
		self._gens.append(gen)


	def handleExpression(self, start, stop, attrs):
		"""Flush any template data into a CharGen and then create a new Expression Gen"""
		self._parser.flushCharData(self.tmplStart, self.tmplStop)
		exp = ExpressionGenerator(self._reader.getChars(start,stop))
		self.addGenerator(exp)

	def handleCharData(self, start, stop, chars):
		"""flush character data into a chargen"""
		if chars !='' or '\n':
			gen = CharDataGenerator(chars)
			self.addGenerator(gen)


	def handleComment(self, start, stop):
		"""Comments get swallowed into nothing"""
		self._parser.flushCharData(self.tmplStart, self.tmplStop)
		return #just eats the comment


	def handleInclude(self, attrs,param):
		"""
		this is for includes of the form <psp:include ...>
		This function essentially forwards the request to the specified URL and includes that output.
		"""
		self._parser.flushCharData(self.tmplStart, self.tmplStop)
		gen = IncludeGenerator(attrs, param,self._ctxt)
		self.addGenerator(gen)

	def handleInsert(self, attrs,param):
		""" this is for includes of the form <psp:insert ...>
		This type of include is not parsed, it is just inserted in the output stream."""
		self._parser.flushCharData(self.tmplStart, self.tmplStop)
		gen = InsertGenerator(attrs, param,self._ctxt)
		self.addGenerator(gen)


	def importHandler(self, imports, start, stop):
		importlist = string.split(imports,',')
		for i in importlist:
			if string.find(i,':') != -1:
				module, symbol = string.split(i, ':')[:2]
				self._importedSymbols.append(string.strip(symbol))
				implist = "from " + module + " import " + symbol
				self._imports.append(implist)
			else:
				self._imports.append('import '+string.strip(i))

	def extendsHandler(self,bc,start,stop):
		"""extends is a page directive.  It sets the base class (or multiple base classes) for the class that this class
		will generate.  The choice of base class affects the choice of a method to override with
		the BaseMethod page directive.  The default base class is PSPPage.  PSPPage inherits from Page.py."""
		self._baseClasses = map(string.strip, string.split(bc, ','))

	def mainMethodHandler(self, method, start, stop):
		"""BaseMethod is a page directive.  It sets the class method that the main body
		of this PSP page over-rides.  The default is WriteHTML. This value should be set to either WriteHTML
		or writeBody.  See the PSPPage.py and Page.py servlet classes for more information."""
		self._baseMethod=method

	def threadSafeHandler(self, bool, start, stop):
		"""isThreadSafe is a page directive.  The value can be "yes" or "no".  Default is no because the default base class,
		PAge.py, isn't thread safe."""
		self._threadSafe=bool

	def instanceSafeHandler(self, bool, start, stop):
		"""isInstanceSafe tells the Servlet Engine whether it is safe to use object instances of this page
	multiple times. The default is "yes".  Saying "no" here hurts performance."""
		self._instanceSafe=bool

	def indentTypeHandler(self,type,start, stop):
		"""Use tabs to indent source code?"""
		type = string.lower(type)

		if type !="tabs" and type !="spaces" and type !="braces":
			raise "Invalid Indentation Type"
		self._writer.setIndentType(type)


	def indentSpacesHandler(self,amount,start,stop):
		"""set number of spaces used to indent in generated source"""
		self._indentSpaces=int(amount)#don't really need this
		self._writer.setIndentSpaces(int(amount))

	def gobbleWhitespaceHandler(self, value, start, stop):
		"""  Should we gobble up whitespace between script tags"""
		if string.upper(value) == "NO" or value=="0":
			self._gobbleWhitespace=0

	def formatterHandler(self, value, start, stop):
		""" set an alternate formatter function to use instead of str() """
		self._formatter = value


	directiveHandlers = {'imports':importHandler,
						'import':importHandler,
						 'extends':extendsHandler,
						 'method':mainMethodHandler,
						 'isThreadSafe':threadSafeHandler,
						 'isInstanceSafe':instanceSafeHandler,
						 'BaseClass':extendsHandler,
						 'indentSpaces':indentSpacesHandler,
						 'indentType':indentTypeHandler,
						 'gobbleWhitespace':gobbleWhitespaceHandler,
						 'formatter':formatterHandler}


	def handleDirective(self, directive, start, stop, attrs):
		validDirectives = ['page','include']
		"""Flush any template data into a CharGen and then create a new Directive Gen"""
		self._parser.flushCharData(self.tmplStart, self.tmplStop)
		#big switch

		if directive == 'page':
			e = attrs.keys()
			for i in e:
				if self.directiveHandlers.has_key(i):
					self.directiveHandlers[i](self,attrs[i],start,stop)
				else:
					print i
					raise 'No Page Directive Handler'

		elif directive == 'include':
			try:
				filenm = attrs['file']
				encoding = attrs['encoding']
			except KeyError:
				if filenm !=None:
					encoding = None
				else:
					raise KeyError
			try:
				self._reader.pushFile(filenm, encoding)
			except 'File Not Found':
				raise 'PSP Error: Include File not Found'
		else:
			print directive
			raise "Invalid Directive"



	def handleScript(self, start, stop, attrs):
		"""handling scripting elements"""
		self._parser.flushCharData(self.tmplStart, self.tmplStop)
		gen = ScriptGenerator(self._reader.getChars(start, stop),attrs)
		self.addGenerator(gen)

	def handleEndBlock(self):
	    self._parser.flushCharData(self.tmplStart, self.tmplStop)
	    gen = EndBlockGenerator()
	    self.addGenerator(gen)

	def handleMethod(self, start, stop, attrs):
		self._parser.flushCharData(self.tmplStart, self.tmplStop)
		gen = MethodGenerator(self._reader.getChars(start, stop),attrs)
		self.addGenerator(gen)

	def handleMethodEnd(self, start, stop, attrs):
		#self._parser.flushCharData(self.tmplStart, self.tmplStop)
		gen = MethodEndGenerator(self._reader.getChars(start, stop),attrs)
		self.addGenerator(gen)

    #####################################################################
    ##The generation of the page begins here
    ####################################################################3

	def beginProcessing(self):
   		pass

	def endProcessing(self):
		self.generateHeader()
		self.generateDeclarations() #I'll overwrite this later when I can handle extends
		self.generateInitPSP()
		self.generateAll('Declarations')
		self._writer.println('\n')
		self.generateMainMethod()
		self.optimizeCharData()
		if self._gobbleWhitespace:
			self.gobbleWhitespace()
		self.generateAll('Service')
		self._writer.println()
		self.generateFooter()

	def setTemplateInfo(self, start, stop):
		"""marks non code data"""
		self.tmplStart = start
		self.tmplStop = stop

	def generateHeader(self):
		for i in self._imports:
			self._writer.println(i)
##		self._writer.println('try:\n')
##		self._writer.pushIndent()
		#self._writer.println('from ' +self._baseClass+ ' import ' +self._baseClass +'\n')
		self._writer.println('import WebKit')
		self._writer.println('from WebKit import Page')
		for baseClass in self._baseClasses:
			if string.find(baseClass,'.')<0 and baseClass not in self._importedSymbols:
				self._writer.println('import ' + baseClass)
##		self._writer.popIndent()
##		self._writer.println('except:\n')
##		self._writer.pushIndent()
##		self._writer.println('pass\n')
##		self._writer.popIndent()
		self._writer.println("__orig_file__ = '%s'" % self._ctxt.getFullPspFileName())

	def generateDeclarations(self):
		# The PSP "extends" directive allows you to use a shortcut -- if the module name
		# is the same as the class name, you can say "Classname" instead of "ClassName.ClassName".
		# But we can't tell right now which names are actually class names, and which
		# names are really module names that contain a class of the same name.
		# So we have to generate code that checks at runtime.
		self._writer.println()
		self._writer.println('import types')
		self._writer.println('_baseClasses = []')
		for baseClass in self._baseClasses:
			className = string.split(baseClass, '.')[-1]
			self._writer.println('if isinstance(%s, types.ModuleType):' % baseClass)
			self._writer.pushIndent()
			self._writer.println('_baseClasses.append(%s.%s)' % (baseClass, className))
			self._writer.popIndent()
			self._writer.println('else:')
			self._writer.pushIndent()
			self._writer.println('_baseClasses.append(%s)' % baseClass)
			self._writer.popIndent()
		self._writer.println()
		# Now write the class line
		self._writer.printChars('class ')
		self._writer.printChars(self._ctxt.getServletClassName())
		self._writer.printChars('(')
		for i in range(len(self._baseClasses)):
			if i > 0:
				self._writer.printChars(',')
			self._writer.printChars('_baseClasses[%d]' % i)
		self._writer.printChars('):')
		#self._writer.printChars('('+self._baseClass+'):')
		self._writer.printChars('\n')

		self._writer.pushIndent()
		self._writer.println('def canBeThreaded(self):') # I Hope to take this out soon!
		self._writer.pushIndent()
		if string.lower(self._threadSafe) == 'no':
			self._writer.println('return 0')
		else:
			self._writer.println('return 1')
		self._writer.popIndent()
		self._writer.println()

		self._writer.println('def canBeReused(self):') # I Hope to take this out soon!
		self._writer.pushIndent()
		if string.lower(self._instanceSafe) == 'no':
			self._writer.println('return 0')
		else:
			self._writer.println('return 1')
		self._writer.popIndent()
		self._writer.println()

		if not AwakeCreated:
			self._writer.println('def awake(self,trans):')
			self._writer.pushIndent()
			self._writer.println('for baseclass in self.__class__.__bases__:')
			self._writer.pushIndent()
			self._writer.println('if hasattr(baseclass, "awake"):')
			self._writer.pushIndent()
			self._writer.println('baseclass.awake(self, trans)')
			self._writer.println('break\n')
			self._writer.popIndent() # end if statement
			self._writer.popIndent() # end for statement

##commented out for new awake version per conversation w/ chuck
##	    self._writer.println('if "init" in dir(self) and type(self.init) == type(self.__init__):\n')
##	    self._writer.pushIndent()
##	    self._writer.println('self.init()\n')
##	    self._writer.popIndent()
			self._writer.println('self.initPSP()\n')
			self._writer.println()
			self._writer.popIndent()
			self._writer.println()

		self._writer.println('def __includeFile(self, filename):')
		self._writer.pushIndent()
		self._writer.println('self.write(open(filename).read())')
		self._writer.popIndent()
		self._writer.println()

		return

	def generateInitPSP(self):
		self._writer.println('def initPSP(self):\n')
		self._writer.pushIndent()
		self._writer.println('pass\n') #nothing for now
		self._writer.popIndent()
		self._writer.println()

	def generateMainMethod(self):
		self._writer.printIndent()
		self._writer.printChars('def ')
		self._writer.printChars(self._baseMethod) #method we're creating
		self._writer.printChars('(self, transaction=None):\n')
		self._writer.pushIndent()
		self._writer.println('trans = self._transaction')
		self._writer.println(ResponseObject+ '= trans.response()')
		self._writer.println('req = trans.request()')
		self._writer.println('_formatter = %s' % self._formatter)

	#self._writer.println('app = trans.application()')

	def generateFooter(self):
		"""cant decide if this is in the class or outside.  Guess Ill know when Im done"""
		self._writer.popIndent()
		self._writer.println('##footer')

	def generateAll(self,phase):
		for i in self._gens:
			if i.phase == phase:
				i.generate(self._writer)

	def optimizeCharData(self):
		""" Too many char data generators make the Servlet Slow.  If the current Generator and the next are both CharData type, merge their data."""
		gens=self._gens
		count=0
		gencount = len(gens)

		while count < gencount-1:
			if isinstance(gens[count],CharDataGenerator) and isinstance(gens[count+1],CharDataGenerator):
				gens[count].mergeData(gens[count+1])
				gens.remove(gens[count+1])
				gencount = gencount-1
			else:
				count = count+1


	def gobbleWhitespace(self):
		"""
		This method looks for a character block between two psp blocks that contains only whitespace.
		If it finds one, it deletes it.
		This is necessary so that a write()  line can't sneek in between a if/else, try/except etc.
		"""
		debug=0
		gens=self._gens
		sideClasses=(ScriptGenerator, EndBlockGenerator)##, ExpressionGenerator)
		count=1
		gencount = len(gens)
		if debug:
			for i in gens:
				print "Generator type=%s" % i.__class__
		while count < gencount-1:
			if isinstance(gens[count],CharDataGenerator) and gens[count+1].__class__ in sideClasses and gens[count-1].__class__ in sideClasses:
				if checkForTextHavingOnlyGivenChars(gens[count].chars):
					gens.remove(gens[count])
					gencount=gencount-1
			count = count+1
		

def checkForTextHavingOnlyGivenChars(text, ws=string.whitespace):
	""" Does the given text contain anything other than the ws characters?
	Return true if text is only ws characters
	Should redo this as a regex.
	"""
	for i in text:
		if i not in ws:
			return 0
	return 1
