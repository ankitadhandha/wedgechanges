from AdminPage import AdminPage
import string, types, random
from time import time, localtime

class LoginPage(AdminPage):
	def writeContent(self):
		if self.loginDisabled():
			self.write(self.loginDisabled())
			return
		self.write('''
<center>
	<table border="0" cellpadding="0" cellspacing="0" bgcolor="#ffffff" width="300">
''')

		extra = self.request().field('extra', None)
		if extra:
			self.write('<tr><td align="left">%s</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td></tr>' % self.htmlEncode(extra))

		self.write('''
		<tr>
			<td align="left">Please log in to view Administration Pages.  The username is admin.  The password is set in the WebKit/Configs/Application.config file.</td>
		</tr>
		<tr>
			<td>
				<form method="post">
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
''')
		for (key, value) in self.request().fields().items():
			if string.lower(key) not in ('username','password','login','logout','loginid'):
				if isinstance(value, types.ListType):
					for v in value:
						self.writeln('<input type="hidden" name="%s" value="%s">' % (key, v))
				else:
					self.writeln('<input type="hidden" name="%s" value="%s">' % (key, value))
		# Create a "unique" login id and put it in the form as well as in the session.
		# Login will only be allowed if they match.
		loginid = string.join(map(lambda x: '%02d' % x, localtime(time())[:6]), '') + str(random.randint(10000, 99999))
		self.writeln('<input type="hidden" name="loginid" value="%s">' % loginid)
		self.session().setValue('loginid', loginid)
		self.write('''
				</form>
			</td>
		</tr>
	</table>
</center>
''')
