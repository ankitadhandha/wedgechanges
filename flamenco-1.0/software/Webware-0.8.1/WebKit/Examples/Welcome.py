from ExamplePage import ExamplePage

class Welcome(ExamplePage):

	def writeContent(self):
		self.writeln('<p> Welcome to WebKit %s!' % self.application().webKitVersionString())
		self.writeln('''<p> Along the side of this page you will see various links that will take you to:

		<ul>
			<li> The different WebKit examples.
			<li> The source code of the current example.
			<li> The local WebKit documentation.
			<li> Whatever contexts have been configured. Each context represents a distinct set of web pages, usually given a descriptive name.
			<li> External sites, such as the Webware home page.
		</ul>

		<p> The <b>Admin</b> context is particularly interesting because it takes you to the administrative pages for the WebKit AppServer where you can review logs, configuration, plug-ins, etc.
''')
		req = self.request()
		extraURLPath = req.extraURLPath()
		if extraURLPath and extraURLPath != '/':
			self.writeln('''
			<p>extraURLPath information was found on the URL,
			and a servlet was not found to process it.
			Processing has been delegated to this servlet.</p>''')

			self.writeln('<ul>')
			self.writeln('serverSidePath of this servlet is: <tt>%s</tt><br>' % req.serverSidePath() )
			self.writeln('extraURLPath data is: <tt>%s</tt><br>' % extraURLPath )
			self.writeln('</ul>')
				    
			
