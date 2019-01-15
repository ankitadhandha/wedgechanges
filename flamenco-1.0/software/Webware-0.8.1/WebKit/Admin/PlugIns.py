from AdminSecurity import AdminSecurity


class PlugIns(AdminSecurity):

	def writeContent(self):
		# @@ 2000-06-02 ce: We should allow a custom admin link for each plug-in (if it provides one)
		# @@ 2000-06-02 ce: We should have a link to the plug-in's docs
		# @@ 2001-01-25 ce: We should pick up more of the plugIn.properties() information
		plugIns = self.application().server().plugIns()
		if plugIns:
			self.writeln('''<p><table align=center border=0 cellspacing=2 cellpadding=2>
<tr bgcolor=black><td align=center colspan=3><font face="Arial, Helvetica" color=white><b>Plug-ins</b></font></td></tr>''')
			for plugIn in plugIns:
				name, dir, ver = plugIn.name(), plugIn.directory(), plugIn.properties()['versionString']
				self.writeln('<tr> %(td)s %(name)s </td> %(td)s %(ver)s </td> %(td)s %(dir)s </td> </tr>' % {
					'name': name,
					'ver': ver,
					'dir': dir,
					'td': '<td bgcolor=#DDDDDD>'
				})
			self.writeln('</table>')
