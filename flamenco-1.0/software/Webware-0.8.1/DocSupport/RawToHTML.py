"""
RawToHTML.py

This script inputs a .raw file and outputs a .html file of the same base name.

The .raw files are basically HTML files that can contain Python dictionaries, which get processed by this script to produce HTML in their place. That HTML could be a table, a series of bullet points, etc. and is based on the content of the dictionary.

This technique comes in handy when style sheets won't go far enought. For example, you may have several blurbs in your document that have all the same content components. Until you actually write these blurbs and experiment with their look and feel, you might not know whether you want to use <table> et al, <dd> et al or something else.


EXAMPLES

For an example, see ../Docs/StyleGuidelines.raw.


RULES

There are some rules to help this script recognize the Python dictionaries without confusing them with ordinary HTML content.

* The dictionary starts with a single curly brace on a line by itself in column 1 (e.g., no preceding white space).
* The immediate line after words starts with a single or double quote optionally preceded by white space.
* The dictionary ends with a single curly brace on a line by itself in column 1.

* htForDict() can return an string containing HTML, or a list of strings.


FUTURE

* Add a verbose option.

* Provide for the class definitions to be outside this script (in findClass()).

* Consider if this would be useful as a generate "templating" component (along with additional features).

"""


import os, string, sys
from glob import glob
from types import *


class Convention:
	"""
	This class is on the "raw-to-HTML" classes and is specifically for ../Docs/StyleGuidelines.raw.
	"""

	def __init__(self, processor):
		pass

	def htForDict(self, dict):
		self._dict = dict
		self._results = []
		for key in ['what', 'why', 'examples', 'negatives', 'exceptions']:
			self.part(key)
		return self._results

	def part(self, key):
		if self._dict.has_key(key):
			value = self._dict[key]
			if key=='examples' or key=='negatives' or key=='exceptions':
				self._results.append('<div class=%s>%s: <code>%s</code></div>\n' % (
					key, string.capitalize(key), value))
			else:
				self._results.append('<div class=%s>%s</div>\n' % (key, value))


class RawToHTML:

	def __init__(self):
		self._translators = {}

	def main(self, args):
		for filename in args[1:]:
			if '*' in filename:
				# Help out Windows command line users
				filenames = glob(filename)
				for filename in filenames:
					self.processFile(filename)
			else:
				self.processFile(filename)

	def error(self, msg):
		# @@ 2000-10-08 ce: raise an exception
		print msg
		sys.exit(1)

	def createTranslator(self, className):
		""" Returns a translator by instantiating a class for the given name out of globals(). A subclass could override this (or a future version of this class could change this) to do something more sophisticated, like locate the class in the current directory or DocSupport. Used by processString(). """
		pyClass = globals()[className]
		return pyClass(self)

	def translator(self, className):
		""" Returns the translator for the given class name, invoking createTranslator() if necessary. """
		translator = self._translators.get(className, None)
		if translator is None:
			translator = self.createTranslator(className)
			self._translators[className] = translator
		return translator

	def processFile(self, filename):
		targetName = os.path.splitext(filename)[0] + '.html'
		contents = open(filename).read()
		results = self.processString(contents)
		open(targetName, 'w').write(results)

	def processString(self, contents):
		lines = string.split(contents, '\n')
		numLines = len(lines)
		i = 0
		results = []
		while i<numLines:
			line = lines[i]
			if line and line[0]=='{' and len(string.strip(line))==1:
				start = i
				while 1:
					i = i + 1
					if i==numLines:
						self.error('Unterminated Python dictionary starting at line %d.' % (start+1))
					line = lines[i]
					if line and line[0]=='}' and len(string.strip(line))==1:
						end = i
						break
				dictString = string.join(lines[start:end+1])
				try:
					dict = eval(dictString)
				except:
					self.error('Could not evaluate dictionary starting at line %d.' % (start+1))
				translator = self.translator(dict['class'])
				ht = translator.htForDict(dict)
				if type(ht)==ListType:
					results.extend(ht)
				else:
					results.append(ht)
			else:
				results.append(line)
			i = i + 1
		return string.join(results, '\n')


if __name__=='__main__':
	RawToHTML().main(sys.argv)
