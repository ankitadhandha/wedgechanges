#!/usr/bin/env python
"""
A quick, hacky script to contruct a class hierarchy list from a set of python files.
"""


import os, re, string, string, sys, time
from glob import glob
from types import *


def EmptyString(klass):
	return ''


class Klass:
	""" Represents a Python class for our purposes. """
	def __init__(self, name, filename=''):
		self._name = name
		self._bases = []
		self._derived = []
		self._filename = filename

	def addBase(self, klass):
		assert isinstance(klass, Klass)
		if klass not in self._bases:
			self._bases.append(klass)
		klass.addDerived(self)

	def addDerived(self, klass):
		assert isinstance(klass, Klass)
		if klass not in self._derived:
			self._derived.append(klass)

	def name(self):
		return self._name

	def filename(self):
		return self._filename

	def setFilename(self, filename):
		self._filename = filename

	def printHier(self, file=sys.stdout, indent=0, indentString='    ', prefix='', func=EmptyString, filenamePrefix=' (', filenamePostfix=')', multipleBasesMarker='*'):
		filename = self._filename
		if os.path.splitext(filename)[0]==self._name:
			filename = ''
		if len(self._bases)<2:
			star = ''
		else:
			star = multipleBasesMarker
		file.write('%s%s%s%s%s%s%s%s\n' % (prefix, func(self), indentString*indent, self._name, star, filenamePrefix, filename, filenamePostfix))
		indent = indent + 1
		for klass in self._derived:
			klass.printHier(file, indent, indentString, prefix, func, filenamePrefix, filenamePostfix)

	def __repr__(self):
		return '<%s, %s>' % (self.__class__.__name__, self._name)


class ClassHier:
	def __init__(self):
		self._splitter = re.compile(r"[(,):]")
		self._klasses = {}
		self._verbose = 0
		self._filesToIgnore = []

	def addFilesToIgnore(self, list):
		self._filesToIgnore.extend(list)

	def readFiles(self, filename):
		filenames = glob(filename)
		for name in filenames:
			self.readFile(name)

	def readFile(self, name):
		if name in self._filesToIgnore:
			if self._verbose:
				print 'Skipping %s...' % name
			return
		if self._verbose:
			print 'Reading %s...' % name
		lines = open(name).readlines()
		lineNum = 1
		for line in lines:
			if len(line)>8 and \
			   line[:5]=='class' and \
			   line[5] in ' \t' and \
			   string.find(line, ':')!=-1:
				self.readLine(line, name, lineNum)
			lineNum = lineNum + 1
		if self._verbose:
			print

	def readLine(self, line, filename=None, lineNum=None):
		# strip comments
		comment = string.find(line, '#')
		if comment!=-1:
			line = line[:comment]

		# split into words
		names = self._splitter.split(line[5:])

		# strip white space
		names = map(lambda part: string.strip(part), names)

		# get rid of empty strings
		names = filter(None, names)

		# special case:  class foo(fi): pass
		if names[-1]=='pass':
			del names[-1]

		# check for weirdos
		for name in names:
			if ' ' in name  or  '\t' in name:
				if name is not None:
					if lineNum is not None:
						print '%s:%s:' % (filename, lineNum),
					else:
						print '%s:' % (filename),
				print 'strange result:', names
				if not self._verbose:
					print 'Maybe you should set self._verbose to 1 and try again.'
				sys.exit(1)

		if self._verbose:
			print names

		# create the klasses as needed
		for name in names:
			if not self._klasses.has_key(name):
				self._klasses[name] = Klass(name)

		# connect them
		klass = self._klasses[names[0]]
		klass.setFilename(filename)
		for name in names[1:]:
			klass.addBase(self._klasses[name])

	def roots(self):
		roots = []
		for klass in self._klasses.values():
			if len(klass._bases)==0:
				roots.append(klass)
		return roots

	def printHier(self, file=sys.stdout):
		roots = self.roots()
		roots.sort(lambda a, b: cmp(a._name, b._name))
		for klass in roots:
			klass.printHier(file=file)

	def printHierForWeb(self, file=sys.stdout):
		if type(file) is StringType:
			file = open(file, 'w')
			close = 1
		else:
			close = 0
		file.write('<table cellpadding=2 cellspacing=0 style="font-family: Arial, Helvetica, sans-serif; font-size: 14;">\n')
		file.write('<tr> <td><b>Summary</b></td> <td><b>Source</b></td> <td><b>Class</b></td> <td><b>File</b></td> </tr>\n')
		roots = self.roots()
		roots.sort(lambda a, b: cmp(a._name, b._name))
		for klass in roots:
			klass.printHier(file=file, prefix='<tr>', func=self.links, indentString = '&nbsp;'*6, filenamePrefix='</td><td>', filenamePostfix='</td></tr>\n')
		file.write('</table>')
		if close:
			file.close()

	def printListForWeb(self, file=sys.stdout):
		if type(file) is StringType:
			file = open(file, 'w')
			close = 1
		else:
			close = 0
		file.write('<table cellpadding=2 cellspacing=0 style="font-family: Arial, Helvetica, sans-serif; font-size: 14;">\n')
		file.write('<tr> <td><b>Summary</b></td> <td><b>Source</b></td> <td><b>Class</b></td> <td><b>File</b></td> </tr>\n')
		classes = self._klasses.values()
		classes.sort(lambda a, b: cmp(a._name, b._name))
		for klass in classes:
			file.write('<tr> %s %s </td>  <td>%s</td> </tr>\n' % (self.links(klass), klass.name(), klass.filename()))
		file.write('</table>')
		if close:
			file.close()

	def links(self, klass):
		""" In support of printForWeb(). """
		filename = klass.filename()
		links = []

		# summary file
		if os.path.exists('Docs/Source/Summaries/%s.html' % filename):
			links.append('<td> <a href="Summaries/%s.html">summary</a> </td>' % filename)
		else:
			links.append('<td> &nbsp; </td>')

		# source file
		docFilename = 'Docs/Source/Files/%s.html' % filename
		if os.path.exists(docFilename):
			links.append('<td> <a href="Files/%s.html">source</a> </td>' % filename)
		else:
			links.append('<td> &nbsp; </td>')

		# finish up
		links.append('<td>')
		return string.join(links, '')


def main(args):
	ch = ClassHier()
	ch.addFilesToIgnore(['zCookieEngine.py', 'WebKitSocketServer.py', '_on_hold_HierarchicalPage.py', 'fcgi.py']) # whoa! look at that hard-coding!
	for filename in args:
		ch.readFiles(filename)
#	ch.printHier()
	ch.printForWeb()


if __name__=='__main__':
	main(sys.argv[1:])
