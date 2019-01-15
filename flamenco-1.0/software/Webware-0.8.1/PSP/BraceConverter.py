"""
  BraceConverter (2000-09-04) by Dave Wallace (dwallace@delanet.com)
  
    Converts Brace-blocked Python into normal indented Python.
    Brace-blocked Python is non-indentation aware and blocks are delimited by ':{' and '}' pairs.

    Thus:
    for x in range(10) :{
      if x%2 :{ print x } else :{ print z }
    }
    
    Becomes: (roughly, barring some spurious newlines)
    for x in range(10) :
       if x%2 :
          print x
       else :
          print z

    This implementation is fed a line at a time via parseLine(), outputs to
    a PSPServletWriter, and tracks the current quotation and block levels internally.
    

"""
import re
import string
import sys


class BraceConverter:

    CSKIP = re.compile("(^[^\"'{}:#]+)")
    COLONBRACE=re.compile(":\s*{\s*([^\s].*)?$")
    
    def __init__(self):
        self.inquote = 0
        self.dictlevel = 0


    # The only public method of this class, call with subsequent lines and an
    # instance of PSPServletWriter
    def parseLine(self,line,writer):
        self.line = line

        if self.inquote and self.line:
            self.skipquote(writer)

        self.line = string.lstrip(self.line)
        if not self.line:
            writer.printChars('\n')
            return

        writer.printIndent()       

        while self.line:
            while self.inquote and self.line:
                self.skipquote(writer)

            match = self.CSKIP.search(self.line)
            if match:
                writer.printChars(self.line[:match.end(1)])
                self.line = self.line[match.end(1):]
            else:
                ch = self.line[0]
                if ch == "'":
                    self.handleQuote("'",writer)
                    self.skipquote(writer)
                elif ch == '"':
                    self.handleQuote('"',writer)
                    self.skipquote(writer)                
                elif ch == '{':
                    self.openBrace(writer)
                elif ch == '}':
                    self.closeBrace(writer)
                elif ch == ':':
                    self.openBlock(writer)
                elif ch == '#':
                    writer.printChars(self.line)
                    self.line=""
                else:
                    # should never get here
                    raise Exception()
        else:
            writer.printChars('\n')
                    

   

    # open a new block 
    def openBlock(self,writer):
        match = self.COLONBRACE.match(self.line)
        if match and not self.dictlevel:
            writer.printChars(":")
            writer.pushIndent()
            if match.group(1):
                # text follows :{, if its a comment leave it on the same line
                #  else start a new line and leave the text for processing
                if match.group(1)[0] == '#':
                    writer.printChars(" " + match.group(1))
                    self.line = ""
                else:
                    writer.printChars('\n')
                    writer.printIndent()
                    self.line = match.group(1)
            else:
                self.line = ""
        else:
            writer.printChars(":")
            self.line = self.line[1:]

    # open brace encountered
    def openBrace(self,writer):        
        writer.printChars("{")
        self.line=self.line[1:]
        self.dictlevel = self.dictlevel + 1

    # close brace encountered
    def closeBrace(self,writer):
        if self.dictlevel:
            writer.printChars("}")
            self.line=self.line[1:]
            self.dictlevel = self.dictlevel - 1
        else:
            writer.popIndent()
            self.line = string.lstrip(self.line[1:])
            if (self.line):
                writer.printChars('\n')
                writer.printIndent()

    # skip over all chars until the line is exhausted
    # or the current non-escaped quote sequence is encountered
    def skipquote(self,writer):
        pos = string.find(self.line,self.quotechars)
        if -1 == pos:
            writer.printChars(self.line)
            self.line=""
        elif (pos > 0) and self.line[pos-1] == '\\':
            pos = pos +1
            writer.printChars(self.line[:pos])
            self.line = self.line[pos:]
            self.skipquote(writer)
        else:
            pos = pos + len(self.quotechars)
            writer.printChars(self.line[:pos])
            self.line = self.line[pos:]
            self.inquote = 0

    # Check and handle if current pos is a single or triple quote
    def handleQuote(self,quote,writer):
        self.inquote=1
        triple = quote*3
        if self.line[0:3]==triple:
            self.quotechars=triple
            writer.printChars(triple)
            self.line = self.line[3:]
        else:
            self.quotechars=quote
            writer.printChars(quote)
            self.line = self.line[1:]


### testing
if __name__ == "__main__":
    from ServletWriter import ServletWriter
    # for stand alone testing
    class DummyWriter(ServletWriter):
        def __init__(self):
            self._filehandle = sys.stdout
            self._tabcnt = 0
            self._blockcount = 0 # a hack to handle nested blocks of python code
            self._indentSpaces = ServletWriter.SPACES
            self._useTabs=1
            self._useBraces=0
            self._indent='\t'
            self._userIndent = ServletWriter.EMPTY_STRING
       
    
    test=r"""
     for x in range(10) :{ q={
     'test':x
     }
     print x
     }

     for x in range(10) :{ q={'test':x}; print x} else :{ print "\"done\"" #""}{
     x = { 'test1':{'sub2':{'subsub1':2}} # yee ha
     }
     } print "all done"
     
    """

    p = BraceConverter()
    dw = DummyWriter()

    for line in test.split('\n'):
        p.parseLine(line,dw)
