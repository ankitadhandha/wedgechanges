from SQLObjectStore import SQLObjectStore
from mx import ODBC # DR: 07-12-02 The ODBC.Windows module is flawed
ODBC.Windows.threadsafety = ODBC.Windows.threadlevel # mx.ODBC.Windows has a threadlevel, not a threadsafety, even though DBABI2.0 says its threadsafety (http://www.python.org/topics/database/DatabaseAPI-2.0.html)

class MSSQLObjectStore(SQLObjectStore):
	_threadSafety = ODBC.Windows.threadsafety
	"""
	MSSQLObjectStore does the obvious: it implements an object store backed by a MSSQL database.

	The connection arguments passed to __init__ are:
		- host
		- user
		- passwd
		- port
		- unix_socket
		- client_flag

	You wouldn't use the 'db' argument, since that is determined by the model.
	"""

	def dbapiConnect(self):
		"""
		Returns a DB API 2.0 connection. This is a utility method invoked by connect(). Subclasses should implement this, making use of self._dbArgs (a dictionary specifying host, username, etc.).
		Subclass responsibility.
		MSSQL 2000 defaults to autocommit ON (at least mine does)
		if you want it off, do not send any arg for clear_auto_commit or set it to 1
		# self._db = ODBC.Windows.Connect(dsn='myDSN',clear_auto_commit=0)
		"""
		return apply(ODBC.Windows.Connect, (), self._dbArgs)

	def retrieveLastInsertId(self, conn, cur):
		conn, cur = self.executeSQL('select @@IDENTITY', conn)
		return int(cur.fetchone()[0])

	def newConnection(self):
		args = self._dbArgs.copy()
#		args['database'] = self._model.sqlDatabaseName()
		return self.dbapiModule().connect(**args)

	def dbapiModule(self):
		return ODBC.Windows

class Klass:

	def sqlTableName(self):
		"""
		Returns "[name]" so that table names do not conflict with SQL
		reserved words.
		"""
		return '[%s]' % self.name()

class Attr:

	def sqlColumnName(self):
		""" Returns the SQL column name corresponding to this attribute, consisting of self.name() + self.sqlTypeSuffix(). """
		if not self._sqlColumnName:
			self._sqlColumnName = self.name() + self.sqlTypeSuffix()
		return '[' + self._sqlColumnName + ']'


class StringAttr:

	def sqlValue(self, value):
		if value is None:
			return 'NULL'
		else:
			# do the right thing
			value = value.replace("'","''")
			return "'" + value + "'"
