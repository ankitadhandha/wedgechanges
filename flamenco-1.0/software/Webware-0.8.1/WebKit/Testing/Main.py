from WebKit.Page import Page
from WebKit.Application import Application
from string import replace, split, strip
import os


class Main(Page):
	"""
	Read TestCases.data and display them.

	TO DO
		* Reload TestCases.data only load when modified (by checking mod date).
	"""

	def error(self, msg):
		raise Exception, msg

	def writeBody(self):
		self.writeln('<p><center><font size=+1>WebKit Testing</font></center> <p>')
		self.writeTestCases()
		self.writeNotes()

	def writeTestCases(self):
		wr = self.writeln
		req = self.request()
		filename = self.serverSidePath('TestCases.data')
		self._cases = self.readFileNamed(filename)
		wr('''
			<table align=center border=0 cellpadding=3 cellspacing=0>
			<tr> <td align=center colspan=4 bgcolor=black><font color=white><b>Test Cases</b></font></td> </tr>
			<tr> <td> # </td> <td> URLs </td> <td> &nbsp; </td> <td> Expectation </td> </tr>
		''')

		caseNum = 1
		for case in self._cases:
			# For each URL, fix it up and make a name. Put in urls list.
			urls = []
			for url in case['URLs']:
				url = req.adapterName() + url
				urlName = self.htmlEncode(url)
				urls.append((url, urlName))

			expectation = case['Expectation'] #self.htmlEncode(case['Expectation'])
			bgcolor = ['EEEEEE', 'DDDDDD'][caseNum % 2]
			wr('<tr bgcolor=%s> <td> %d. </td>  <td>' % (bgcolor, caseNum))
			for url, urlName in urls:
				wr('<a href=%s>%s</a><br>' % (url, urlName))
			wr('''</td>
				<td> &nbsp; &gt&gt &nbsp; </td>
				<td> %s </td>
				</tr>
				''' % (expectation))
			caseNum = caseNum + 1
		wr('</table>')


	def readFileNamed(self, filename):
		""" Returns a list of test cases, each of which is a dictionary, as defined the given file. See TestCases.data for information on the format. """
		f = open(filename)
		cases = self.readFile(f)
		f.close()
		return cases

	def readFile(self, file):
		return self.readContent(file.read())

	def readContent(self, content):
		lines = split(content, '\n')
		lines = map(lambda line: strip(line), lines)
		lineNum = 1
		cases = []
		urls = []
		for line in lines:
			if line and line[0]!='#':
				if line[-1]=='\\':
					# continuation line; means there are multiple URLs for this case
					urls.append(strip(line[:-1]))
				else:
					parts = split(line, '-->')
					if len(parts)!=2:
						self.error('Invalid line at %d.' % lineNum)
					urls.append(strip(parts[0]))
					cases.append({
						'URLs': urls,
						'Expectation': strip(parts[1]),
					})
					urls = [] # reset list of URLs
			lineNum = lineNum + 1
		return cases

	def writeNotes(self):
		self.writeln('<p> <b>Notes</b>')
		rawNotes = """
Test all links in all pages of all contexts (Examples, Admin, Testing, etc.), including links found in the headers and footers of the pages.

Test functionality of interactive pages, like CountVisits and ListBox.

Test each link more than once.

Test with multiple adapters (WebKit.cgi, OneShot.cgi, etc.)

Application's serverSideInfoForRequest() method is fairly involved. It supports a variety of functionalities as described in it's doc string: <pre>%(serverSideInfoForRequestDoc)s</pre>
"""
		doc = Application.serverSideInfoForRequest.__doc__
		doc = replace(doc, '\t', '    ')
		fields = {
			'serverSideInfoForRequestDoc': doc,
		}
		lines = split(rawNotes, '\n')
		lines = map(lambda line: strip(line), lines)
		self.writeln('<ul>')
		for line in lines:
			if line:
				self.writeln('<li> ' + (line % fields))
		self.writeln('</ul>')
