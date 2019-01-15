from SecurePage import SecurePage

class SecureCountVisits(SecurePage):
	def writeContent(self):
		count = self.session().value('num_visits', 0)+1
		self.session().setValue('num_visits', count)
		if count>1:
			plural = 's'
		else:
			plural = ''
		self.writeln("<p> You've been here %d time%s." % (count, plural))
		self.writeln('<p> This page records your visits using a session object. Every time you RELOAD or revisit this page, the counter will increase. If you close your browser, then your session will end and you will see the counter go back to 1 on your next visit.')
		self.writeln('<p> Try hitting RELOAD now.')
		user = self.getLoggedInUser()
		if user:
			self.writeln('<p> Authenticated user is %s.' % user)
		self.writeln('<p> <a href="SecureCountVisits">Revisit this page</a> <a href="SecureCountVisits?logout=1">Logout</a>')
