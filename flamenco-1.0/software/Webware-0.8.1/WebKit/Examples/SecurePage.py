import string, types
from MiscUtils.Configurable import Configurable
from ExamplePage import ExamplePage

class SecurePage(ExamplePage, Configurable):
	"""
	This class is an example of how to implement username and password-based
	security using WebKit.  Use a SecurePage class like this one as the
	base class for any pages that you want to require login.  Modify
	the isUserNameAndPassword method to perform validation in whatever
	way you desire, such as a back-end database lookup.  You might also
	want to modify loginUser so that it automatically brings in additional
	information about the user and stores it in session variables.

	You can turn off security by creating a config file called SecurePage.config
	in the Configs directory with the following contents:

		{
			'RequireLogin': 0
		}

	To-Do: Integrate this functionality with the upcoming UserKit.
		   Make more of the functionality configurable in the config file.

	"""

	def __init__(self):
		ExamplePage.__init__(self)
		Configurable.__init__(self)

	def awake(self, trans):
		# Awaken our superclass
		ExamplePage.awake(self, trans)

		if self.setting('RequireLogin'):
			# Handle four cases: logout, login attempt, already logged in, and not already logged in.
			session = trans.session()
			request = trans.request()
			app = trans.application()
			# Get login id and immediately clear it from the session
			loginid = session.value('loginid', None)
			if loginid:
				session.delValue('loginid')
			# Are they logging out?
			if request.hasField('logout'):
				# They are logging out.  Clear all session variables and take them to the
				# Login page with a "logged out" message.
				session.values().clear()
				request.setField('extra', 'You have been logged out.')
				request.setField('action', string.split(request.urlPath(), '/')[-1])
				app.forward(trans, 'LoginPage')
			elif request.hasField('login') and request.hasField('username') and request.hasField('password'):
				# They are logging in.  Clear session
				session.values().clear()
				# Get request fields
				username = request.field('username')
				password = request.field('password')
				# Check if they can successfully log in.  The loginid must match what was previously
				# sent.
				if request.field('loginid', 'nologin')==loginid and self.loginUser(username, password):
					# Successful login.
					# Clear out the login parameters
					request.delField('username')
					request.delField('password')
					request.delField('login')
					request.delField('loginid')
				else:
					# Failed login attempt; have them try again.
					request.setField('extra', 'Login failed.  Please try again.')
					app.forward(trans, 'LoginPage')
			# They aren't logging in; are they already logged in?
			elif not self.getLoggedInUser():
				# They need to log in.
				session.values().clear()
				# Send them to the login page
				app.forward(trans, 'LoginPage')
		else:
			# No login is required
			session = self.session()
			request = self.request()
			# Are they logging out?
			if request.hasField('logout'):
				# They are logging out.  Clear all session variables.
				session.values().clear()
			# write the page
			ExamplePage.writeHTML(self)


	def respond(self, trans):
		"""
		If the user is already logged in, then process this request normally.  Otherwise, do nothing.
		All of the login logic has already happened in awake().
		"""
		if self.getLoggedInUser():
			ExamplePage.respond(self, trans)
  
	def isValidUserAndPassword(self, username, password):
		# Replace this with a database lookup, or whatever you're using for
		# authentication...
		users = [('Alice', 'Alice'), ('Bob', 'Bob')]
		return (username, password) in users

	def loginUser(self, username, password):
		# We mark a user as logged-in by setting a session variable called
		# authenticated_user to the logged-in username.
		#
		# Here, you could also pull in additional information about this user
		# (such as a user ID or user preferences) and store that information
		# in session variables.
		if self.isValidUserAndPassword(username, password):
			self.session().setValue('authenticated_user', username)
			return 1
		else:
			self.session().setValue('authenticated_user', None)
			return 0

	def getLoggedInUser(self):
		# Gets the name of the logged-in user, or returns None if there is
		# no logged-in user.
		return self.session().value('authenticated_user', None)

	def defaultConfig(self):
		return {'RequireLogin': 1}

	def configFilename(self):
		return 'Configs/SecurePage.config'
