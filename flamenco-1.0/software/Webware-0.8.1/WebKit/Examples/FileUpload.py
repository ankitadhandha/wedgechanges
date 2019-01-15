

from WebKit.Examples.ExamplePage import ExamplePage
import string, os, stat
from WebUtils import Funcs

class FileUpload(ExamplePage):
	"""
	This servlet shows how to handle uploaded files.

	The process is fairly self explanatory.  You use a form like the one below in the
	writeContent method.  When the form is uploaded, the request field with the name you
	gave to the file selector form item will be an instance of the FieldStorage class from
	the standard python module "cgi".  The key attributes of this class are shown in the
	example below.  The most important things are filename, which gives the name of the
	file that was uploaded, and file, which is an open file handle to the uploaded file.
	The uploaded file is temporarily stored in a temp file created by the standard module.
	You'll need to do something with the data in this file.  The temp file will
	be automatically deleted.  If you want to save the data in the uploaded file read it
	out and write it to a new file, db, whatever.
	"""

	def writeContent(self):
		self.write("""
		<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
  <head>
    <title>Upload Test</title>
  </head>

  <body>
    <h1>Upload Test</h1>
	<p>%s
	<p>

<form action="FileUpload.py" method=POST enctype="multipart/form-data">
<input type="FILE" name="filename">
<p>
<input type="SUBMIT" name="_action_" value="fileupload">
</form>
  </body>
</html>

		""" % (Funcs.htmlEncode(self.__doc__)))


	def fileupload(self, trans):

		f = self.request().field('filename')

		contents = f.file.read()

		self.write("""<html><head></head><body bgcolor='#DDDDEE'>
		Here's the file you submitted:
		<hr>
		name:%s<p>
		type:%s<p>
		type_options:%s<p>
		disposition:%s<p>
		disposition_options:%s<p>
		headers:%s<p>
		size: %s<p>
		contents:<hr>%s </body>
		""" % (f.filename, f.type, f.type_options, f.disposition, f.disposition_options, f.headers, len(contents), Funcs.htmlEncode(contents) ) )

	def actions(self):
		return ExamplePage.actions(self) + ['fileupload']

	def title(self):
		return "File Upload Example"


