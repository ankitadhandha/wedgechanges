from SQLObjectStore import SQLObjectStore
import MySQLdb
from MySQLdb import Warning


class MySQLObjectStore(SQLObjectStore):
	"""
	MySQLObjectStore does the obvious: it implements an object store backed by a MySQL database.

	MySQL notes:
		* MySQL home page: http://www.mysql.com.
		* MySQL version this was developed and tested with: 3.22.34 & 3.23.27
		* The platforms developed and tested with include Linux (Mandrake 7.1) and Windows ME.
		* The MySQL-Python DB API 2.0 module used under the hood is MySQLdb by Andy Dustman. http://dustman.net/andy/python/MySQLdb/

	The connection arguments passed to __init__ are:
		- host
		- user
		- passwd
		- port
		- unix_socket
		- client_flag

	You wouldn't use the 'db' argument, since that is determined by the model.

	See the MySQLdb docs or the DB API 2.0 docs for more information.
	  http://www.python.org/topics/database/DatabaseAPI-2.0.html
	"""

	def newConnection(self):
		args = self._dbArgs.copy()
		args['db'] = self._model.sqlDatabaseName()
		return self.dbapiModule().connect(**args)

	def retrieveLastInsertId(self, conn, cur):
		return cur.insert_id()
		# The above is more efficient.
		# conn, cur = self.executeSQL('select last_insert_id();', conn)
		# return cur.fetchone()[0]

	def dbapiModule(self):
		return MySQLdb

	def _executeSQL(self, cur, sql):
		try:
			cur.execute(sql)
		except MySQLdb.Warning, e:
			if not self.setting('IgnoreSQLWarnings', 0):
				raise

# Mixins

class StringAttr:
	def sqlValue(self, value):
		""" MySQL provides a quoting function for string -- use it. """
		if value is None:
			return 'NULL'
		else:
			return "'" + MySQLdb.escape_string(value) + "'"
