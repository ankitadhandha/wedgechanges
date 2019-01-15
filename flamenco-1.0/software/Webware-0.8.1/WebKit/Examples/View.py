import string, os
from ExamplePage import ExamplePage


class View(ExamplePage):
	"""
	For each WebKit example, you will see a sidebar with various menu items, one of which is "View source of <i>Example</i>". This link points to the View servlet and passes the filename of the current servlet. The View servlet then loads that file's source code and displays it	in the browser for your viewing pleasure.
	<p> BTW, if the View servlet isn't passed a filename, it prints the	View's doc string which you are reading right now.
	"""

	def writeContent(self):
		req = self.request()
		if not req.hasField('filename'):
			self.writeln('<p>', self.__class__.__doc__)
		else:
			trans = self.transaction()
			fn = req.field('filename')
			if os.sep in fn:
				self.write("Cannot request a file outside of this directory %s" % fn)
				return
			fn = self.request().serverSidePath(fn)
			self.request().fields()['filename'] = fn
			trans.application().forward(trans, "Colorize.py")
