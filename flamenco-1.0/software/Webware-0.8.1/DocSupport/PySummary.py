"""
PySummary


A PySummary instance reads a python file and creates a summary of the file which you can access by using it as a string (e.g., %s or str()).

The notion of a "category" is recognized. A category is simply a group of methods with a given name. The default prefix for denoting a category is ##.

"""

import string
from string import find, join, replace, strip
from types import *
import os

class PySummary:

	## Init ##

	def __init__(self):
		self._filename = None
		self._lines = []
		self.invalidateCache()
		if os.path.exists('PySummary.config'):
			self.readConfig('PySummary.config')


	## Config ##

	def readConfig(self, filename):
		self._settings = eval(open(filename).read())
		assert type(self._settings) is DictType


	## Reading files ##

	def readFileNamed(self, filename):
		self._filename = filename
		file = open(filename)
		self.readFile(file)
		file.close()

	def readFile(self, file):
		self.invalidateCache()
		for line in file.readlines():
			if line and line[-1]=='\n':
				line = line[:-1]
			sline = strip(line)
			if not sline:
				continue
			try:
				if sline[:6]=='class ' and sline[6]!='_':
					self._lines.append(Line('class', line))
				elif sline[:4]=='def ' and (sline[4]!='_' or sline[5]=='_'):
					self._lines.append(Line('def', line))
				elif sline[:3]=='## ':
					self._lines.append(Line('category', line))
			except IndexError:
				pass


	## Reports ##

	def text(self):
		return self.render('text')

	def html(self):
		return self.render('html')

	def render(self, format):
		filename = self._filename
		span = format=='html'
		settings = self._settings[format]
		res = []
		res.append(settings['file'][0] % locals())
		for line in self._lines:
			type = line.type()
			res.append(settings[type][0])
			if span:
				res.append('<span class=Line_%s>' % type)
			res.append(apply(getattr(line, format)))  # e.g., line.format()
			if span:
				res.append('</span>')
			res.append('\n')
			res.append(settings[type][1])
		res.append(settings['file'][1] % locals())
		res = join(res, '')
		res = replace(res, '\t', settings['tabSubstitute'])
		return res


	## As strings ##

	def __repr__(self):
		return self.text()

	def __str__(self):
		return self.html()


	## Self utility ##

	def invalidateCache(self):
		self._text = None
		self._html = None


class Line:

	def __init__(self, type, contents):
		self._type = type
		self._text = contents
		self._html = None

	def type(self):
		return self._type

	def text(self):
		return self._text

	def html(self):
		if self._html is None:
			if self._type=='class' or self._type=='def':
				delimiters = {'class': ':', 'def': '('}
				delimiter = delimiters[self._type]
				ht = self._text
				start = find(ht, self._type) + len(self._type) + 1
				end = find(ht, delimiter, start)
				ht = '%s<span class=Name_class>%s</span>%s' % (
					ht[:start], ht[start:end], ht[end:])
			else:
				ht = self._text
			self._html = ht
		return self._html

	def __str__(self):
		return self.contents()


def test():
	print 'Testing on self...'
	sum = PySummary()
	sum.readFileNamed('PySummary.py')
	open('PySummary.py.sum.text', 'w').write(sum.text())
	open('PySummary.py.sum.html', 'w').write(sum.html())
	print 'Wrote PySummary.py.sum.* files.'
	print 'Finished.'


if __name__=='__main__':
	test()
