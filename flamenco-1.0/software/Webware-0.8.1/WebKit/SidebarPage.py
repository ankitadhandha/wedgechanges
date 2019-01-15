from Page import Page


class SidebarPage(Page):
	"""
	SidebarPage is an abstract superclass for pages that have a sidebar (as well as a header and "content well"). Sidebars are normally used for navigation (e.g., a menu or list of links), showing small bits of info and occasionally a simple form (such as login or search).

	Subclasses should override cornerTitle(), writeSidebar() and writeContent() (and title() if necessary; see Page).

	The utility methods menuHeading() and menuItem() can be used by subclasses, typically in their implementation of writeSidebar().

	WebKit itself uses this class: Examples/ExamplePage and Admin/AdminPage both inherit from it.

	TO DO
	-----
	* Use of MenuBar.gif needs reconsideration.
	* Consider using a DIV tag to set the min width of the menu bar.
	* Use style sheets.
	* After style sheets, consider removal of startMenu() and endMenu().
	* It's not easy to customize, via subclasses:
		* what's between <head> and </head>
		* the corner
		* the colors
		* the spacer
	"""


	## Init ##

	def __init__(self):
		Page.__init__(self)
		self._indentBase = '&nbsp; ' # used in menuItem()


	## Content methods ##

	def writeBodyParts(self):
		# begin
		wr = self.writeln
		wr('<table border=0 cellpadding=0 cellspacing=0 width=100%>')

		# banner
		self.writeBanner()

		# sidebar
		wr('<tr> <td bgcolor="#EEEEEF" valign=top nowrap>')
		self.writeSidebar()
		wr('</td>')

		# spacer
		wr('<td> &nbsp;&nbsp;&nbsp; </td>')

		# content
		wr('<td valign=top width=90%><p><br>')
		self.writeContent()
		wr('</td>')

		# end
		wr('</tr> </table>')

	def writeBanner(self):
		# header
		title = self.title()
		startFont1 = '<font face="Tahoma, Arial, Helvetica, sans-serif" color=white size=+1>'
		endFont1 = '</font>'
		startFont2 = '<font face="Tahoma, Arial, Helvetica, sans-serif" color=white size=+2><b>'
		endFont2 = '</b></font>'
		cornerTitle = self.cornerTitle()
		self.writeln('''
			<tr>
				<td align=center bgcolor="#000000">%(startFont1)s%(cornerTitle)s%(endFont1)s</td>
				<td align=center bgcolor="#00008B" colspan=2>&nbsp;<br>%(startFont2)s%(title)s%(endFont2)s<br>&nbsp;</td>
			</tr>''' % locals())

	def writeSidebar(self):
		self.startMenu()
		self.writeln('Woops. Someone forgot to override writeSidebar().')
		self.endMenu()

	def cornerTitle(self):
		return ''


	## Menu ##

	def startMenu(self):
		self.writeln('<table border=0 cellpadding=0 cellspacing=4><tr><td nowrap><font face=Arial size=-1>')
		self._wroteHeading = 0

	def menuHeading(self, title):
		if self._wroteHeading:
			self.write('<br>')
		self.writeln('<b>%s</b><br>' % title)
		self._wroteHeading = 1

	def menuItem(self, title, url=None, suffix=None, indentLevel=1):
		if suffix:
			suffix = suffix + ' '
		else:
			suffix = ''
		indent = self._indentBase*indentLevel
		if url is not None:
			self.writeln(' %s<a href="%s">%s</a> %s<br>' % (
				indent, url, title, suffix))
		else:
			self.writeln(' %s%s %s<br>' % (indent, title, suffix))

	def endMenu(self):
		self.writeln('</font></td></tr></table>')


	## WebKit sidebar sections ##

	def writeWebKitSidebarSections(self):
		""" This method (and consequently the methods it invokes) are provided for WebKit's example and admin pages. It writes sections such as contexts, e-mails, exits and versions. """
		self.writeContextsMenu()
		self.writeWebwareEmailMenu()
		self.writeWebwareExitsMenu()
		self.writeVersions()

	def writeContextsMenu(self):
		self.menuHeading('Contexts')
		adapterName = self.request().adapterName()
		ctxs = self.application().contexts().keys()
		ctxs = filter(lambda ctx: ctx!='default', ctxs)
		ctxs.sort()
		for ctx in ctxs:
			self.menuItem(ctx, '%s/%s/' % (adapterName, ctx))

	def writeWebwareEmailMenu(self):
		self.menuHeading('E-mail')
		self.menuItem('webware-discuss', 'mailto:webware-discuss@lists.sourceforge.net')

	def writeWebwareExitsMenu(self):
		self.menuHeading('Exits')
		self.menuItem('Webware', 'http://webware.sourceforge.net')
		self.menuItem('Python', 'http://www.python.org')

	def writeVersions(self):
		app = self.application()
		self.menuHeading('Versions')
		self.menuItem('WebKit ' + app.webKitVersionString())
		self.menuItem('Webware ' + app.webwareVersionString())
		import string, sys
		self.menuItem('Python ' + string.split(sys.version)[0])

	def writeContent(self):
		self.writeln('Woops, someone forgot to override writeContent().')


	## Deprecated ##

	def writeMenuBarMinWidthImage(self):
		""" DEPRECATED: SidebarPage.writeMenuBarMinWidthImage() deprecated on 1/26/01 in ver 0.5. HTML's nowrap is used instead. """
		# To ensure a minimum width of the sidebar
		# Technique learned from www.python.org in 6/2000
		self.deprecated(self.writeMenuBarMinWidthImage)
		self.writeln('<img width=175 height=1 src=MenuBar.gif>')
