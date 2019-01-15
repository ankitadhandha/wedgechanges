from AdminPage import AdminPage
from AdminSecurity import AdminSecurity
import sys


class AppControl(AdminSecurity):

	def writeContent(self):

		action = self.request().field("action",None)
		if action == None:
			if not self.application().server().isPersistent():
				self.write('<b>You are running the <i>OneShot</i> version WebKit. None of the options below are applicable.</b> <p>')
			self.write( """
		<form method=post>
		<table cellspacing = '0' cellpadding = '0'>
			<tr>
				<td><input type=submit name="action" value="Shutdown"></td>
			</tr>
			<tr>
				<td><input type=submit name="action" value="ClearCache"></td>
				<td>Clear the Servlet instance cache in Application and the class caches of each servlet factory</td>
			</tr>
			<tr>
				<td><input type=submit name="action" value="Reload"></td>
				<td>Reload the selected modules.  Be Careful!</td>
			</tr>
		""")
			mods = sys.modules.keys()
			mods.sort()
			for i in mods:
				self.write("""<tr><td colspan=2><input type=checkbox name=reloads value="%s"> %s </td></tr>""" % (i,i))

			self.write("""
			</table>
			</form>
			""")

		elif action == "ClearCache":
			self.write("""<p>Clearing Application instance cache...""")
			self.application().flushServletCache()
			self.write("Done")
			self.write("Clearing Servlet factory class caches...")
			for i in self.application()._factoryList:
				self.write("<p>Clearing: %s..." % i.__class__)
				i.flushCache()
				self.write("Done")
			self.write("""<p>
			Cache Flushed
			<p>Click here to view the Servlet cache: <a href="ServletCache">Servlet Cache </a>
			""" \
					   )

		elif action == "Reload":
			self.write("""<p>Reloading selected modules.  Any existing classes will continue to use the old module definitions, as will any functions/variables imported using 'from'.  Use ClearCache to clean out any Servlets in this condition.<p>""")

			reloadnames = self.request().field("reloads",None)
			if not type(reloadnames) == type([]):
				reloadnames = [reloadnames,]
			for i in reloadnames:
				if i and sys.modules.get(i,None):
					self.write("<br>Reloading %s, %s" % (i, self.htmlEncode(str(sys.modules[i]))))
					try:
						reload(sys.modules[i])
					except Exception, e:
						self.write("<br><font color='red'>Could not reload %s, error was %s</font>" % (i,e))
			self.write("<p>Done")

		elif action == "Shutdown":
			self.write("<B> Shutting down the Application server")
			self.application().server().initiateShutdown()
			self.write("<p>Good Luck!</b>")

