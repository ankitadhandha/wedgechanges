from WebKit.Page import Page
import os, string, sys
try:
	from cStringIO import StringIO
except:
	from StringIO import StringIO


class Colorize(Page):
	"""
	Syntax highlights python source files.  Set a variable 'filename' in the request so I know which file to work on.
	This also demonstrates forwarding.  The View servlet actually forwards it's request here.
	"""

	def respond(self, transaction):
		"""
		write out a syntax hilighted version of the file.  The filename is an attribute of the request object
		"""
		res = transaction._response
		req = self.request()
		if not req.hasField('filename'):
			res.write("No filename given to syntax color!")
			return
		filename = req.field('filename')
		filename = self.request().serverSidePath(os.path.basename(filename))
		if not os.path.exists(filename):
			res.write("The requested file, %s, does not exist in the proper directory" % os.path.basename(filename))
##			res.write(filename+" does not exist.")
			return

		from WebKit.DocSupport import py2html
		from WebKit.DocSupport import PyFontify

		myout=StringIO()
		realout=sys.stdout
		sys.stdout=myout

		py2html.main((None,'-stdout','-format:rawhtml','-files',filename))

		results = myout.getvalue()
		results = string.replace(results, '\t', '    ')  # 4 spaces per tab
		res.write(results)

		sys.stdout = realout
