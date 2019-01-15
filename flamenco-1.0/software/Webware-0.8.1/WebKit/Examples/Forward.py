from ExamplePage import ExamplePage

class Forward(ExamplePage):

	def writeBody(self):
		trans = self.transaction()
		resp = self.response()
		resp.write("<p>This is the Forward servlet speaking. I am now going to include the output of the Welcome servlet via Application's includeURL() method:<br><p>")
#		trans.application().forward(trans, 'Welcome.py')
		trans.application().includeURL(trans, 'Welcome.py')
