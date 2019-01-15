from ExamplePage import ExamplePage


class CountVisits(ExamplePage):

	def writeContent(self):
		count = self.session().value('count', 0)+1
		self.session().setValue('count', count)
		if count>1:
			plural = 's'
		else:
			plural = ''
		if self.request().isSessionExpired():
			self.writeln('<p> Your session has expired.')
		self.writeln("<p> You've been here %d time%s." % (count, plural))
		self.writeln('<p> This page records your visits using a session object. Every time you RELOAD or revisit this page, the counter will increase. If you close your browser, then your session will end and you will see the counter go back to 1 on your next visit.')
		self.writeln('<p> Try hitting RELOAD now.')
