from ExamplePage import ExamplePage
from types import StringType


class PlugInInspector(ExamplePage):
	"""
	This example is not public yet.
	And this should probably just be axed and something
	real added in Admin/PlugIns.
	"""

	def writeContent(self):
		wr = self.writeln
		for pi in self.application().server().plugIns():
			wr('<b>%s</b>' % self.htmlEncode(repr(pi)))
			for item in dir(pi):
				wr('<br> %s == %s' % (item, self.htmlEncode(str(getattr(pi, item)))))
			self.writeln('<hr>')
