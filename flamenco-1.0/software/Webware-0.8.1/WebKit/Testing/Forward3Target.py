from WebKit.Page import Page

class Forward3Target(Page):

	def writeContent(self):
		self.writeln('<p> servlet %s</p>' % self.__class__.__name__ )
		self.writeln('<pre>%s</pre>' % self.request().getstate() )
			
