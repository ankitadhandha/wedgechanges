import os, string, time
from ExamplePage import ExamplePage

class Colors(ExamplePage):
	"""
	This class is a good example of caching. The color table that
	this servlet creates never changes, so the servlet caches this in
	the _htColorTable attribute. The original version of this
	example did no caching and was 12 times slower.
	"""

	def __init__(self):
		ExamplePage.__init__(self)
		self._htColorTable = None

	def awake(self, trans):
		""" Set _bgcolor and _bgcolorArg according to our fields. """
		ExamplePage.awake(self, trans)
		self._bgcolor = ''
		self._bgcolorArg = ''
		req = self.request()
		if req.hasField('bgcolor'):
			self._bgcolor = string.strip(req.field('bgcolor'))
			if self._bgcolor!='':
				self._bgcolorArg = 'bgcolor=' + self._bgcolor

	def htBodyArgs(self):
		""" Overridden to throw in the custom background color that the user can specify in our form. """
		return 'color=black ' + self._bgcolorArg

	def writeContent(self):
		self.write('''
			<center>
			<form>
				bgcolor: <input type=next name=bgcolor value="%s">
				<input type=submit value=Go>
			</form>
			</center>
		''' % (self._bgcolor))

		self.write(self.htColorTable())

	def htColorTable(self):
		if self._htColorTable is None:
			colorTable = ['<p><table align=center>']

			space = '&nbsp;'*10
			gamma = 2.2  # an approximation for today's CRTs, see "brightness =" below

			numSteps = 8
			steps = map(lambda x: float(x), range(numSteps))
			denominator = float(numSteps-1)
			for r in steps:
				r = r/denominator
				for g in steps:
					g = g/denominator
					colorTable.append('<tr>\n')
					for b in steps:
						b = b/denominator
						color = '#%02x%02x%02x' % (r*255, g*255, b*255)
						# Compute brightness given RGB
						brightness = (0.3*r**gamma + 0.6*g**gamma + 0.1*b**gamma)**(1/gamma)
						# We then use brightness to determine a good font color for high contrast
						if brightness<0.5:
							textcolor = 'white'
						else:
							textcolor = 'black'
						colorTable.append('<td bgcolor=%s> <br> <font color=%s>%s</font> </td>\n' % (color, textcolor, color))
					colorTable.append('</tr>\n')

			colorTable.append('</table>\n')
			self._htColorTable = string.join(colorTable, '')
		return self._htColorTable
