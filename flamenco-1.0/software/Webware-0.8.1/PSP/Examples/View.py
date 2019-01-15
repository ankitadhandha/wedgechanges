import string
#from WebKit.Page import Page
from PSP.Examples.PSPExamplePage import PSPExamplePage
import os

class View(PSPExamplePage):
	"""

	"""

	def writeContent(self):
		req = self.request()
		if req.hasField('filename'):
			self.writeln('<p>', self.__class__.__doc__)

			filename = req.field('filename')
			basename = os.path.basename(filename)
			filename = self.request().serverSidePath(basename)
			if not os.path.exists(filename):
				self.write("No such file %s exists" % basename)
				return

			text = open(filename).read()

			text = string.replace(text,"<","&lt;")
			text = string.replace(text,">","&gt;")
			text = string.replace(text,'\n',"<br>")

			self.write(text)
			
