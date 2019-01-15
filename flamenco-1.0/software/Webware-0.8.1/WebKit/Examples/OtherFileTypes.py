from ExamplePage import ExamplePage


class OtherFileTypes(ExamplePage):
	
	def writeBody(self):
		self.writeLink('test.text')
		self.writeLink('test.html')

	def writeLink(self, link):
		self.write('<p> <a href="Tests/%s">%s</a>\n' % (link, link))
