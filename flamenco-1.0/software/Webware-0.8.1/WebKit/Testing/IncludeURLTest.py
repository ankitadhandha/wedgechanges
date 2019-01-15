from WebKit.Page import Page,NoDefault

class IncludeURLTest(Page):
	"""
	This test will test out the callMethodOfServlet and includeURL
	redirection.  the forward() method works similar to these but is
	not tested here.  The following operations are performed:

	The form fields are displayed, as seen by this servlet.

	The request environment of this servlet is displayed.

	The writeStatus method on the servlet IncludeURLTest2 which is
	found in the Dir subdirectory under Testing is called.

	The title method is called on several other servlets to demonstrate
	calling methods on servlets in different areaes relative to here.

	Finally, the top level page of this context is included with includeURL.

	A 'Test Complete' message is displayed at the very end.

	"""

	def writeBody(self):
		fields = self.request().fields()
		self.writeln('<b>IncludeURLTest class = %s, module= %s</b>' %
			     (self.__class__.__name__,
			      self.__module__))
		self.writeln('<pre>%s</pre>' % self.__class__.__doc__)
		self.writeln('<hr>\n<p>Number of fields in the request.fields(): %d\n<p>' % len(fields))
		for key, value in fields.items():
			self.writeln('<br> %s = %s' % (self.htmlEncode(key), self.htmlEncode(value)))
		self.writeln('<p><hr>')
		self.writeStatus()

		self.cmos("/Dir/IncludeURLTest2","writeStatus",
			  "Expect to see the status written by IncludeURLTest2 which is the same format as the above status, only relative to /Dir/IncludeURLTest2")
		self.cmos("Dir/IncludeURLTest2","serverSidePath",
			  "This returns the serverSide Path of the Dir/IncludeURLTest2 servlet.  Notice that there is no leading '/' which means this test is relative to the current directory and not the root of the context. Since we are the current directory and siteRoot are the same, it should work.")
		self.cmos("/","name",
			  "This returns the name of the module at the top of this context which is Main")
		self.cmos("/Main","serverSidePath",
			  "This returns the serverSidePath of the servlet accessed at the top of this context.")
		self.cmos("Main","serverSidePath",
			  "This returns the serverSidePath of the servlet accessed 'Main' and should be the same as the servlet accessed through '/' in the test above.")

		self.writeln("<hr><b>Including Dir/IncludeURLTest2</b><br>")
		self.write("<ul>")
		self.includeURL("Dir/IncludeURLTest2")
		self.write("</ul>")
		
		self.writeln("<hr><b>Including the URL '/' which is the root of the context %s</b><br>" % self.request().contextName())
		self.write("<ul>")
		self.includeURL("/Main")
		self.write("</ul>")
		self.writeln("<hr><p>%s Test Complete" % self.__class__.__name__)


	def writeStatus(self):
		w = self.w
		req = self.request()

		self.writeln("<hr>")
		self.writeln("<b>%s Request Status:</b><br>" % self.__class__.__name__)
		self.writeln("<pre>")
		w( "serverSidePath():       %s" % req.serverSidePath() )
		w( "contextName():          %s" % req.contextName() )
		w( "serverSideContextPath():%s" % req.serverSideContextPath() )
		w( "extraURLPath():         %s" % req.extraURLPath() )
		w( "urlPath():              %s" % req.urlPath() )
		w( "adapterName():          %s" % req.adapterName() )
		w( "-- environment --" )
		w( "REQUEST_URI:            %s" % req._environ["REQUEST_URI"] )
		w( "PATH_INFO:              %s" % req._environ["PATH_INFO"] )
		w( "SCRIPT_NAME:            %s" % req._environ["SCRIPT_NAME"] )
		w( "SCRIPT_FILENAME:        %s" % req._environ["SCRIPT_FILENAME"] )
		self.writeln('</pre>')


	def cmos(self,url,method,desc):
		a = self.application()
		t = self.transaction()
		self.write('<hr>')
		self.write('Calling callMethodOfServlet(t, "%s", "%s")<br>%s' %
			   (url,method, desc) )
		self.write("<ul>")
		x = a.callMethodOfServlet(t, url, method )
		self.writeln("</ul>")
		self.writeln("callMethodOfServlet returned \"<tt>%s</tt>\"" % (self.htmlEncode(str(x))))

	def w( self, msg ):
		self.writeln( self.htmlEncode(msg) )
		
	
