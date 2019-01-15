from ExamplePage import ExamplePage
import string

class RequestInformation(ExamplePage):

	def writeContent(self):
		self.writeln("<p>The following table shows the values for various request variables.")
		self.writeln('<table align=center bgcolor=#EEEEFF border=0 cellpadding=2 cellspacing=2 width=100%>')
		self.dict('HTTPRequest.fields()', self.transaction().request().fields())
		self.dict('HTTPRequest._environ', self.transaction().request()._environ)
		self.dict('Cookies', self.transaction().request().cookies())
		self.writeln('</table>')
		self.transaction().response().setCookie('TestCookieName','CookieValue')
		self.transaction().response().setCookie('TestExpire1','Expires in 1 minutes', expires='+1m')

	def pair(self, key, value):
		valueType = type(value)
		if valueType is type([])  or  valueType is type(()):
			value = string.join(map(lambda x: str(x), value), ', ')
		self.writeln('<tr valign=top><td>%s</td><td>%s</td></tr>' % (key, self.htmlEncode(str(value))))

	def list(self, codeString):
		list = eval(codeString)
		assert type(list) is type([])  or  type(list) is type(())
		self.pair(codeString, list)

	def dict(self, name, dict):
		self.writeln('<tr valign=top><td bgcolor=#9999FF colspan=2>%s</td></tr>' % (name))
		keys = dict.keys()
		keys.sort()
		for name in keys:
			self.writeln('<tr valign=top><td>%s</td><td>%s</td></tr>'
				 % (name, string.replace(self.htmlEncode(str(dict[name])), '\n', '<br>')))
