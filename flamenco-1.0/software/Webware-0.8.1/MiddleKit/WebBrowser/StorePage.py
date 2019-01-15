import os, sys
from MiddleKit.Run.MySQLObjectStore import MySQLObjectStore


from SitePage import SitePage


class StorePage(SitePage):

	## Init ##

	def __init__(self):
		SitePage.__init__(self)
		self._store = None


	## Access ##

	def modelFilename(self):
		req = self.request()
		filename = req.field('modelFilename', None)
		if filename:
			self.response().setCookie('modelFilename', filename)
		else:
			filename = req.cookie('modelFilename', None)
		return filename

	def store(self):
		if not self._store:
			self.saveFieldsToCookies()
			modelFilename = self.modelFilename()

			# MK will need access to the Python classes for the model.
			# We expect to find them with the actual model file,
			# so we update sys.path appropriately:
			extraDir = os.path.dirname(modelFilename)
			if extraDir not in sys.path:
				sys.path.insert(1, extraDir)

			req = self.request()
			self._store = MySQLObjectStore(host=req.value('host'), user=req.value('user'), passwd=req.value('password'))
			self._store.readModelFileNamed(modelFilename)
			self._store.connect()
		return self._store


	## Writing page parts ##

	def writeTopBar(self):
		names = os.path.split(self.modelFilename())
		self.writeln('<a href=SelectModel class=SelectLink>SELECT</a> <span class=StatusBar>%s - %s</span>' % (names[1], names[0]))
		req = self.request()
		self.writeln('<br> <a href=SelectDatabase class=SelectLink>SELECT</a> <span class=StatusBar>db=%s, host=%s, user=%s</span>' % (req.value('database'), req.value('host'), req.value('user')))

	def writeSideBar(self):
		self.writeKlasses()

	def writeKlasses(self):
		# @@ 2000-11-27 ce: move this to MixIns???
		curClassName = self.request().field('class', None)
		klasses = self.store().model().klasses()
		names = klasses.keys()
		names.sort()
		modelFilename = self.urlEncode(self.modelFilename())
		for name in names:
			urlName = self.urlEncode(name)
			if name==curClassName:
				style = 'CurClassLink'
			else:
				style = 'ClassLink'
			self.writeln('<a href=BrowseObjects?class=%s class=%s> %s </a> <br>\n' % (name, style, urlName))

	def writeContent(self):
		self.writeln('Woops. Forgot to override writeContent().')
