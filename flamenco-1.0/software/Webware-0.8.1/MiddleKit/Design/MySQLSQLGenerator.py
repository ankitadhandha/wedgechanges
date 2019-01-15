from SQLGenerator import SQLGenerator


class MySQLSQLGenerator(SQLGenerator):

	def sqlSupportsDefaultValues(self):
		return 1


class Klasses:

	def dropDatabaseSQL(self, dbName):
		return 'drop database if exists %s;\n' % dbName

	def dropTablesSQL(self):
		sql = []
		names = self.auxiliaryTableNames()[:]
		names.reverse()
		for tableName in names:
			sql.append('drop table if exists %s;\n' % tableName)
		klasses = self._model._allKlassesInOrder[:]
		klasses.reverse()
		for klass in klasses:
			sql.append('drop table if exists %s;\n' % klass.name())
		sql.append('\n')
		return ''.join(sql)

	def createDatabaseSQL(self, dbName):
		return 'create database %s;\n' % dbName

	def useDatabaseSQL(self, dbName):
		return 'use %s;\n\n' % dbName


class Klass:

	def primaryKeySQLDef(self, generator):
		return '    %s int not null primary key auto_increment,\n' % self.sqlIdName().ljust(self.maxNameWidth())


class EnumAttr:

	def sqlType(self):
		enums = ['"%s"' % enum for enum in self.enums()]
		enums = ', '.join(enums)
		enums = 'enum(%s)' % enums
		return enums

	def sampleValue(self, value):
		assert value in self._enums, 'value = %r, enums = %r' % (value, self._enums)
		return repr(value)


class StringAttr:

	def sqlType(self):
		# @@ 2000-11-11 ce: cache this
		if not self.get('Max', None):
			return 'varchar(100) /* WARNING: NO LENGTH SPECIFIED */'
		max = int(self['Max']) # @@ 2000-11-12 ce: won't need int() after using types
		if max>65535:
			return 'longtext'
		if max>255:
			return 'text'
		if self.has_key('Min') and self['Min'] and int(self['Min'])==max:
			return 'char(%s)' % max
		else:
			return 'varchar(%s)' % max


class ObjRefAttr:

	def sqlType(self):
		# @@ 2001-02-04 ce: Is this standard SQL? If so, it can be moved up.
		return 'bigint unsigned /* %s */' % self['Type']
