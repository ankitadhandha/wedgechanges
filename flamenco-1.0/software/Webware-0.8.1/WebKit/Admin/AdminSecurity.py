import string, types
from AdminPage import AdminPage

# Set this to 0 if you want to allow everyone to access secure pages with no login
# required.  This should instead come from a config file.
require_login = 1

if not require_login:
	class AdminSecurity(AdminPage):
		def writeHTML(self):
			session = self.session()
			request = self.request()
			# Are they logging out?
			if request.hasField('logout'):
				# They are logging out.  Clear all session variables.
				session.values().clear()
			# write the page
			AdminPage.writeHTML(self)

else:
	class AdminSecurity(AdminPage):
		def writeHTML(self):
			session = self.session()
			request = self.request()
			trans = self.transaction()
			app = self.application()
			# Get login id and clear it from the session
			loginid = session.value('loginid', None)
			if loginid: session.delValue('loginid')
			# Are they logging out?
			if request.hasField('logout'):
				# They are logging out.  Clear all session variables.
				session.values().clear()
				request.fields()['extra'] = 'You have been logged out.'
				app.forward(trans, 'LoginPage')
				return
			elif request.hasField('login') and request.hasField('username') and request.hasField('password'):
				# They are logging in.  Clear session
				session.values().clear()
				# Check if this is a valid user/password
				username = request.field('username')
				password = request.field('password')
				if self.isValidUserAndPassword(username, password) and request.field('loginid', 'nologin')==loginid:
					# Success; log them in and send the page
					session.setValue('authenticated_user_admin', username)
					AdminPage.writeHTML(self)
				else:
					# Failed login attempt; have them try again
					
					request.fields()['extra'] = 'Login failed.  Please try again. (And make sure cookies are enabled.)'
					app.forward(trans, 'LoginPage')
					return
			# They aren't logging in; are they already logged in?
			elif session.value('authenticated_user_admin', None):
				# They are already logged in; write the HTML for this page.
				AdminPage.writeHTML(self)
			else:
				# They need to log in.
				session.values().clear()
				app.forward(trans, 'LoginPage')
				return

		def isValidUserAndPassword(self, username, password):
			# Replace this with a database lookup, or whatever you're using for
			# authentication...
			adminPassword = self.application().setting('AdminPassword')
			if username == 'admin' and adminPassword and \
			   password == adminPassword:
				return 1
			else:
				return 0

