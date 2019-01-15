from WebKit.Page import Page
from WebKit.Application import Application
from string import replace, split, strip
import os


class Servlet(Page):
	"""
	Test of extra path info.
	"""

	def writeBody(self):
		self.writeln('<p><center><font size=+1>WebKit Testing Servlet</font></center> <p>')

		req = self.request()
		self.writeln("<p>serverSidePath=%s</p>" % req.serverSidePath())
		self.writeln("<p>extraURLPath=%s</p>" % req.extraURLPath())
