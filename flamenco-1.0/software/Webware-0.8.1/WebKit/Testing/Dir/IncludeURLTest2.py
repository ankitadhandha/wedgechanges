from WebKit.Page import Page
from WebKit.Testing.IncludeURLTest import IncludeURLTest

class IncludeURLTest2(IncludeURLTest):
	"""
	This is the second part of the URL test code.  It gets included
	into the IncludeURLTest, and calls methods on other servlets to
	verify the references continue to work.
	"""

	def writeBody(self):
		self.writeln('<b>IncludeURLTest class = %s, module= %s</b>' %
			     (self.__class__.__name__,
			      self.__module__))
		self.writeln('<pre>%s</pre>' % self.__class__.__doc__)

		self.writeStatus()
		self.cmos("/","serverSidePath",
			  "Expect to see the serverSidePath of the Testing/Main module.")
	pass
