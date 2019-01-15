import os, string
from AdminSecurity import AdminSecurity
from MiscUtils.DataTable import DataTable


class DumpCSV(AdminSecurity):

	def filename(self):
		""" Overidden by subclasses to specify what filename to show. """
		return None

	def awake(self, trans):
		AdminSecurity.awake(self, trans)
		self._filename = self.filename()

	def shortFilename(self):
		return os.path.splitext(os.path.split(self._filename)[1])[0]

	def title(self):
		return 'View ' + self.shortFilename()

	def writeContent(self):
		if not os.path.exists(self._filename):
			self.writeln('<p> File does not exist.')
			return

		table = DataTable(self._filename)

		if len(table)==1:
			plural = ''
		else:
			plural = 's'
		self.writeln('<p>%d row%s' % (len(table), plural))
		self.writeln('<br><table align=center border=0 cellpadding=2 cellspacing=2>')


		# Head row gets special formatting
		self._headings = map(lambda col: string.strip(col.name()), table.headings())
		self._numCols = len(self._headings)
		self.writeln('<tr bgcolor=black>')
		for value in self._headings:
			self.writeln('<td><font face="Arial, Helvetica" color=white><b> ', value, ' </b></font></td>')
		self.writeln('</tr>')

		# Data rows
		rowIndex = 1
		for row in table:
			self.writeln('<tr bgcolor=#EEEEEE>')
			colIndex = 0
			for value in row:
				if colIndex<self._numCols: # for those cases where a row has more columns that the header row.
					self.writeln('<td> ', self.cellContents(rowIndex, colIndex, value), ' </td>')
				colIndex = colIndex + 1
			self.writeln('</tr>')
			rowIndex = rowIndex + 1

		self.writeln('</table>')

	def cellContents(self, rowIndex, colIndex, value):
		""" This is a hook for subclasses to customize the contents of a cell based on any criteria (including location). """
		return value
