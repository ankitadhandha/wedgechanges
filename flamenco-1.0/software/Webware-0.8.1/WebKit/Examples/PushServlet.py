"""
This is a test servlet for the buffered output streams of the app servers.
This probably won't work with the cgi adapters. At least on apache, the data
doesn't seem to get flushed.
This will not have the expected functionality on Internet Explorer, as it does
not support the x-mixed-replace content type. Opera does, though.
"""

from WebKit.Page import Page
from time import sleep
import random
import string

MSIEString = """<html><body bgcolor=white>Microsoft Internet Explorer does not support server side push with x-mixed-replace content.
<p>Your browser identified itself as %s.
<p>Sorry.</body></html>"""

class PushServlet(Page):
	
	boundary = "MyRandomBoundryIsThisStringAndNumber" + str(random.randint(1000,10000000))
	
	def respond(self, transaction):
		browser = self.request().serverDictionary()['HTTP_USER_AGENT']
		if string.find(browser,'MSIE') and not string.find(browser,'Opera'):
			self.write(MSIEString % self.request().serverDictionary()['HTTP_USER_AGENT'])
			return
		self.response().streamOut().autoCommit(1) #this isn't necessary, but it's here as an example
		self.initialHeader()
		for i in range(1,6):
			self.sendBoundary()
			self.sendLF()
			self.writeContent(i)
			self.sendLF()
			self.response().flush() #send the currently buffered output now.
			sleep(2)
		

	def initialHeader(self):
		self.response().setHeader("Content-type","multipart/x-mixed-replace; boundary=" + self.boundary)

	def sendBoundary(self):
		self.write("--"+self.boundary)

	def sendLF(self):
		self.write("\r\n")
		

	def writeContent(self,count):
		self.write("Content-type: text/html\r\n\r\n")
		self.write("<HTML><BODY><h1 align=center>")
		self.write("Count = %s<p>This won't work in IE.  You'll just see '5'." % count)
		self.write("</h1></body></html>")
