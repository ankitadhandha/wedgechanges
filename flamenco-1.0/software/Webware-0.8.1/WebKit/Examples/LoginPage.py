from ExamplePage import ExamplePage
from MiscUtils.Funcs import uniqueId
import string, types

class LoginPage(ExamplePage):
	def title(self):
		return 'Log In'

	def htBodyArgs(self):
		return ExamplePage.htBodyArgs(self) + ' onload="document.loginform.username.focus();"' % locals()

	def writeContent(self):
		self.write('''
<center>
	<table border="0" cellpadding="0" cellspacing="0" bgcolor="#ffffff" width="300">
''')

		extra = self.request().field('extra', None)
		if not extra and self.request().isSessionExpired() and not self.request().hasField('logout'):
			extra = 'You have been automatically logged out due to inactivity.'
		if extra:
			self.write('<tr><td align="left">%s</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td></tr>' % self.htmlEncode(extra))
		
		# Create a "unique" login id and put it in the form as well as in the session.
		# Login will only be allowed if they match.
		loginid = uniqueId(self)
		self.session().setValue('loginid', loginid)

		action = self.request().field('action', '')
		if action:
			action = 'action="%s"' % action

		self.write('''
		<tr>
			<td align="left">Please log in (use Alice or Bob as the username and password):</td>
		</tr>
		<tr>
			<td>
				<form method="post" name="loginform" %s>
					<table border="0" width="100%%" cellpadding="3" cellspacing="0" bgcolor="#cecece" align="left">
						<tr><td>&nbsp;</td><td>&nbsp;</td></tr>
						<tr>
							<td align="right">Username</td>
							<td><input type="TEXT" name="username"></td>
						</tr>
						<tr>
							<td align="right">Password</td>
							<td><input type="PASSWORD" name="password"></td>
						</tr>
						<tr>
							<td>&nbsp;</td>
							<td><input type="submit" name="login" value="Login"></td>
						</tr>
						<tr><td>&nbsp;</td><td>&nbsp;</td></tr>
					</table>
					<input type="hidden" name="loginid" value="%s">''' % (action, loginid))

		# Forward any passed in values to the user's intended page after successful login,
		# except for the special values used by the login mechanism itself
		for name, value in self.request().fields().items():
			if name not in 'login loginid username password extra logout'.split():
				if isinstance(value, types.ListType):
					for valueStr in value:
						self.write('''<input type="hidden" name="%s" value="%s">'''
								   % (self.htmlEncode(name), self.htmlEncode(valueStr)))
				else:
					self.write('''<input type="hidden" name="%s" value="%s">'''
							   % (self.htmlEncode(name), self.htmlEncode(value)))
		self.write('''
				</form>
			</td>
		</tr>
	</table>
</center>
''')
