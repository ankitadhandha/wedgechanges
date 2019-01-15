from ExamplePage import ExamplePage
import string

class Introspect(ExamplePage):

	def writeContent(self):
		self.writeln("<p>The following table shows the values for various Python expressions, all of which are related to <i>introspection</i>. That is to say, all the expressions examine the environment such as the object, the object's class, the module and so on.")
		self.writeln('<table align=center bgcolor=#EEEEFF border=0 cellpadding=2 cellspacing=2 width=100%>')
		self.pair('locals().keys()', locals().keys())
		self.list('globals().keys()')
		self.list('dir(self)')
		self.list('dir(self.__class__)')
		self.list('self.__class__.__bases__')
		self.list('dir(self.__class__.__bases__[0])')
		self.writeln('</table>')

	def pair(self, key, value):
		valueType = type(value)
		if valueType is type([])  or  valueType is type(()):
			value = string.join(map(lambda x: str(x), value), ', ')
		self.writeln('<tr valign=top><td>%s</td><td>%s</td></tr>' % (key, self.htmlEncode(str(value))))

	def list(self, codeString):
		list = eval(codeString)
		assert type(list) is type([])  or  type(list) is type(())
		self.pair(codeString, list)
