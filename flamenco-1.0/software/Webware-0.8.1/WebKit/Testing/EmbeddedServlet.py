from WebKit.Page import Page


class EmbeddedServlet(Page):
	"""
	This servlet serves as a test for "extra path info"-style URLs such as:

		http://localhost/WebKit.cgi/Servlet/Extra/Path/Info

	Where the servlet is embedded in the URL, rather than being the last component.
	This servlet simply prints it's fields.
	"""

	def writeBody(self):
		fields = self.request().fields()
		self.writeln('<center><b>EmbeddedServlet</b></center>')
		self.writeln('<pre>%s</pre>' % self.__class__.__doc__)
		self.writeln('<hr>\n<p>Fields: %d\n<p>' % len(fields))
		for key, value in fields.items():
			self.writeln('<br> %s = %s' % (self.htmlEncode(key), self.htmlEncode(value)))
		self.writeln('<p><hr>')

		
