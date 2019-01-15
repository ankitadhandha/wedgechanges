from CodeGenerator import *
import os, sys
from glob import glob
from types import StringType
from time import asctime, localtime, time
from MiddleKit.Core.ObjRefAttr import objRefJoin


class SQLGenerator(CodeGenerator):
	"""
	This class and its associated mix-ins are responsible for generating:
		- Create.sql
		- InsertSample.sql
		- Info.text

	A subclass and further mix-ins are required for specific databases (since SQL varies from product to product).

	The main method to invoke is generate():

		gen = SomeSQLGenerator()
		gen.readModelFileNamed(filename)
		gen.generate(dirname)

	For subclassers:
		- Subclasses should be named <DATABASE>SQLGenerator where <DATABASE> is the name of the particular database product.
		- A good example of a custom subclass is MySQLSQLGenerator.py. Be sure to take a look at it.
		- Candidates for customization include:
			Klasses
				dropDatabaseSQL()
				createDatabaseSQL()
				useDatabaseSQL()
			StringAttr
			EnumAttr
	"""

	def sqlDatabaseName(self):
		"""
		Returns the name of the database by asking the generator's
		model.
		"""
		return self.model().sqlDatabaseName()

	def configFilename(self):
		filename = self.model().filename()
		if filename is not None:
			filename = os.path.join(filename, 'SQLGenerator.config')
		return filename

	def defaultConfig(self):
		config = CodeGenerator.defaultConfig(self)
		config.update({
			'PreSQL': '',
			'PostSQL': '',
			'DropStatements': 'database'  # database, tables
		})
		return config

	def generate(self, dirname):
		self.requireDir(dirname)
		self.writeInfoFile(os.path.join(dirname, 'Info.text'))
		self._model.writeCreateSQL(self, dirname)
		self._model.writeInsertSamplesSQL(self, dirname)

	def sqlSupportsDefaultValues(self):
		"""
		Subclasses must override to return 1 or 0, indicating their SQL variant supports DEFAULT <value> in the CREATE statement.
		Subclass responsibility.
		"""
		return SubclassResponsibility


class ModelObject:
	pass


class Model:

	def writeCreateSQL(self, generator, dirname):
		"""
		Creates the directory if necessary, sets the klasses' generator, and tells klasses to writeCreateSQL().
		"""
		if not os.path.exists(dirname):
			os.mkdir(dirname)
		assert os.path.isdir(dirname)
		self._klasses.setSQLGenerator(generator)
		self._klasses.writeCreateSQL(generator, os.path.join(dirname, 'Create.sql'))

	def sqlDatabaseName(self):
		"""
		Returns the name of the database (which is either the 'Database'
		setting or self.name()).
		"""
		name = self.setting('Database', None)
		if name is None:
			name = self.name()
		return name

	def writeInsertSamplesSQL(self, generator, dirname):
		if self._filename is not None:
			file = open(os.path.join(dirname, 'InsertSamples.sql'), 'w')
			file.write('use %s;\n\n' % self.sqlDatabaseName())
			self._klasses.writeDeleteAllRecords(generator, file)
			filenames = glob(os.path.join(self._filename, 'Sample*.csv'))
			for filename in filenames:
				lines = open(filename).readlines()
				self.writeInsertSamplesSQLForLines(lines, generator, file)
			file.close()

	def writeInsertSamplesSQLForLines(self, lines, generator, file):
		# @@ 2001-02-04 ce: this method is too long
		#	break into additional methods
		#	some of these methods may even go into other mix-ins
		readColumns = 1
		# @@ 2000-10-29 ce: put in error checking that the column names are valid
		for line in lines:
			fields = line.strip().split(',')
			fields = [self.unquote(field) for field in fields]
			if self.areFieldsBlank(fields):
				continue  # skip blank lines
			if fields[0] and str(fields[0])[0]=='#':
				continue
			if fields[0].endswith(' objects'):
				tableName = fields[0].split()[0]
				klass = self.klass(tableName)
				file.write('\n\n/* %s */\n\n' % fields[0])
				#print '>> table:', tableName
				readColumns = 1
				continue
			if readColumns:
				names = [name for name in fields if name]
				try:
					attrs = [klass.lookupAttr(name) for name in names]
				except KeyError:
					print '>> KeyError'
					print '>> name: ', name
					print '>> names:', ', '.join(names)
					print '>> klass:', klass.name(), '-', klass
					print '>> attrs:', ', '.join([attr.name() for attr in klass.allAttrs()])
					raise
				# @@ 2000-10-29 ce: check that each attr.hasSQLColumn()
				for attr in attrs:
					assert not attr.get('isDerived', 0)
				colNames = [attr.sqlName() for attr in attrs]
				#print '>> cols:', columns
				colSql = ','.join(colNames)
				readColumns = 0
				continue
			values = fields[:len(attrs)]
			i = 0
			for attr in attrs:
				value = values[i]
				value = value.strip()
				#print '>> (%s, %s)' % (value, attr)
				if value=='':
					value = attr.get('Default', None)
					if value is None:
						value = 'NULL'
					else:
						value = attr.sampleValue(value)
				elif value.lower()=='none':
					value = 'NULL'
				else:
					value = attr.sampleValue(value)
#					print 'Attr: %s, Value: %s' % (attr,value)
				if type(value) is not StringType:
					print 'attr:', attr
					print 'value:', value
					print 'type of value:', type(value)
					assert type(value) is StringType
				assert value  # value cannot be blank
				values[i] = value
				i += 1
			#print
			#values = [self.valueFilter(value) for value in values]
			values = ', '.join(values)
			stmt = 'insert into %s (%s) values (%s);\n' % (tableName, colSql, values)
			file.write(stmt)

	def unquote(self, string):
		""" Removes preceding and trailing quotes. This is a utility method for writeInsertSamplesSQLForLines(). """
		if string:
			if string.startswith('"') and string.endswith('"'):
				string = string[1:-1]
		return string

	def areFieldsBlank(self, fields):
		""" Utility method for writeInsertSamplesSQLForLines(). """
		if len(fields)==0:
			return 1
		for field in fields:
			if field:
				return 0
		return 1


class Klasses:

	def sqlGenerator(self):
		return generator

	def setSQLGenerator(self, generator):
		self._sqlGenerator = generator

	def auxiliaryTableNames(self):
		""" Returns a list of table names in addition to the tables that hold objects. One popular user of this method is dropTablesSQL(). """
		return ['_MKClassIds']

	def writeKeyValue(self, out, key, value):
		""" Used by willCreateWriteSQL(). """
		key = key.ljust(12)
		out.write('# %s = %s\n' % (key, value))

	def writeCreateSQL(self, generator, out):
		""" Writes the SQL to define the tables for a set of classes. The target can be a file or a filename. """
		if type(out) is StringType:
			out = open(out, 'w')
			close = 1
		else:
			close = 0
		self.willWriteCreateSQL(generator, out)
		self._writeCreateSQL(generator, out)
		self.didWriteCreateSQL(generator, out)
		if close:
			out.close()

	def willWriteCreateSQL(self, generator, out):
		# @@ 2001-02-04 ce: break up this method
		wr = out.write
		kv = self.writeKeyValue
		wr('/*\nStart of generated SQL.\n\n')
		kv(out, 'Date', asctime(localtime(time())))
		kv(out, 'Python ver', sys.version)
		kv(out, 'Op Sys', os.name)
		kv(out, 'Platform', sys.platform)
		kv(out, 'Cur dir', os.getcwd())
		kv(out, 'Num classes', len(self._klasses))
		wr('\nClasses:\n')
		for klass in self._model._allKlassesInOrder:
			wr('\t%s\n' % klass.name())
		wr('*/\n\n')

		sql = generator.setting('PreSQL', None)
		if sql:
			wr('/* PreSQL start */\n' + sql + '\n/* PreSQL end */\n\n')

		dbName = generator.sqlDatabaseName()
		drop = generator.setting('DropStatements')
		if drop=='database':
			wr(self.dropDatabaseSQL(dbName))
			wr(self.createDatabaseSQL(dbName))
			wr(self.useDatabaseSQL(dbName))
		elif drop=='tables':
			wr(self.useDatabaseSQL(dbName))
			wr(self.dropTablesSQL())
		else:
			raise Exception, 'Invalid value for DropStatements setting: %r' % drop

	def dropDatabaseSQL(self, dbName):
		"""
		Returns SQL code that will remove the database with the given name.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def dropTablesSQL(self):
		"""
		Returns SQL code that will remove each of the tables in the database.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def createDatabaseSQL(self, dbName):
		"""
		Returns SQL code that will create the database with the given name.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def useDatabaseSQL(self, dbName):
		"""
		Returns SQL code that will use the database with the given name.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def _writeCreateSQL(self, generator, out):
		for klass in self._model._allKlassesInOrder:
			klass.writeCreateSQL(self._sqlGenerator, out)
		self.writeClassIdsSQL(generator, out)

	def writeClassIdsSQL(self, generator, out):
		wr = out.write
		wr('''\
create table _MKClassIds (
	id int not null primary key,
	name varchar(100)
);
''')
		wr('insert into _MKClassIds (id, name) values\n')
		id = 1
		values = []
		for klass in self._model._allKlassesInOrder:
			values.append('\t(%s, %r)' % (id, klass.name()))
			klass.setId(id)
			id += 1
		wr(',\n'.join(values))
		wr(';\n\n')

	def didWriteCreateSQL(self, generator, out):
		sql = generator.setting('PostSQL', None)
		if sql:
			out.write('/* PostSQL start */\n' + sql + '\n/* PostSQL end */\n\n')
		out.write('show tables\n\n')
		out.write('/* end of generated SQL */\n')

	def writeDeleteAllRecords(self, generator, file):
		"""
		Writes a delete statement for each data table in the model. This is used for InsertSamples.sql to wipe out all data prior to inserting sample values.
		SQL generators rarely have to customize this method.
		"""
		wr = file.write
		if 0:
			# Woops. Our only auxiliary table is _MKClassIds, which we
			# *don't* want to delete. In the future we will likely
			# have other aux tables for lists and relationships. When
			# that happens, we'll need more granularity regarding
			# aux tables.
			names = self.auxiliaryTableNames()[:]
			names.reverse()
			for tableName in names:
				wr('delete from %s;\n' % tableName)
		klasses = self._model._allKlassesInOrder[:]
		klasses.reverse()
		for klass in klasses:
			if not klass.isAbstract():
				wr('delete from %s;\n' % klass.sqlTableName()) # dr 7-12-02: changed from klass.name()
		wr('\n')



class Klass:

	def writeCreateSQL(self, generator, out):
		if not self.isAbstract():
			name = self.name()
			wr = out.write
			sqlIdName = self.sqlIdName()
			wr('create table %s (\n' % self.sqlTableName())
			wr(self.primaryKeySQLDef(generator))
			if generator.model().setting('DeleteBehavior', 'delete') == 'mark':
				wr(self.deletedSQLDef(generator))
			first = 1
			sqlAttrs = []
			nonSQLAttrs = []
			for attr in self.allAttrs():
				if attr.hasSQLColumn():
					sqlAttrs.append(attr)
				else:
					nonSQLAttrs.append(attr)
			for attr in sqlAttrs:
				if first:
					first = 0
				else:
					wr(',\n')
				attr.writeCreateSQL(generator, out)
			self.writeIndexSQLDefs(wr)
			for attr in nonSQLAttrs:
				attr.writeCreateSQL(generator, out)
				wr('\n')
			wr(');\n\n\n')

	def primaryKeySQLDef(self, generator):
		"""
		Returns a one liner that becomes part of the CREATE statement for creating the primary key of the table. SQL generators often override this mix-in method to customize the creation of the primary key for their SQL variant. This method should use self.sqlIdName() and often ljust()s it by self.maxNameWidth().
		"""
		return '    %s int not null primary key,\n' % self.sqlIdName().ljust(self.maxNameWidth())

	def deletedSQLDef(self, generator):
		"""
		Returns a one liner that becomes part of the CREATE statement for creating the deleted timestamp field of the table.
		This is used if DeleteBehavior is set to "mark".
		"""
		return '    %s datetime,\n' % ('deleted'.ljust(self.maxNameWidth()))

	def sqlIdName(self):
		name = self.name()
		if name:
			name = name[0].lower() + name[1:] + 'Id'
		return name

	def maxNameWidth(self):
		return 30   # @@ 2000-09-15 ce: Ack! Duplicated from Attr class below

	def writeIndexSQLDefs(self, wr):
		for attr in self.allAttrs():
			if attr.get('isIndexed', 0) and attr.hasSQLColumn():
				wr(',\n')
				wr('\tindex (%s)' % attr.sqlName())
		wr('\n')


	def sqlTableName(self):
		"""
		Can be overiddent to allow for table names that do not conflict with SQL
		reserved words. dr 08-08-2002 - MSSQL uses [tablename]
		"""
		return '%s' % self.name()


class Attr:

	def sqlName(self):
		return self.name()

	def hasSQLColumn(self):
		""" Returns true if the attribute has a direct correlating SQL column in it's class' SQL table definition. Most attributes do. Those of type list do not. """
		return not self.get('isDerived', 0)

	def sampleValue(self, value):
		""" Returns a string suitable for a SQL insert statement including any necessary SQL syntax. Subclasses should override to perform type checking and handle any special capabilities.
		The invoker of this method already strips preceding and trailing whitespace, as well detects blanks as NULLs.
		"""
		# @@ 2001-02-20 ce: restructure this
			# sqlValue() instead of sampleValue()
			# w.s. stripping, blanks as default value, none as NULL
			# make _sqlValue()
		return value

	def writeCreateSQL(self, generator, out):
		if self.hasSQLColumn():
			name = self.sqlName().ljust(self.maxNameWidth())
			if self.isRequired():
				notNullSQL = ' not null'
			else:
				notNullSQL = self.sqlNullSpec()
			if generator.sqlSupportsDefaultValues():
				defaultSQL = self.createDefaultSQL()
				if defaultSQL:
					defaultSQL = ' ' + defaultSQL
			else:
				defaultSQL = ''
			out.write('\t%s %s%s%s' % (name, self.sqlType(), notNullSQL, defaultSQL))
		else:
			out.write('\t/* %(Name)s %(Type)s - not a SQL column */' % self)

	def sqlNullSpec(self):
		return ''

	def createDefaultSQL(self):
		default = self.get('Default', None)
		if default is not None:
			default = default.strip()
			if default.lower()=='none':  # kind of redundant
				default = None
			return 'default ' + self.sampleValue(default)
		else:
			return ''

	def maxNameWidth(self):
		return 30  # @@ 2000-09-14 ce: should compute that from names rather than hard code

	def sqlType(self):
		raise AbstractError, self.__class__

	def sqlColumnName(self):
		""" Returns the SQL column name corresponding to this attribute, consisting of self.name() + self.sqlTypeSuffix(). """
		if not self._sqlColumnName:
			self._sqlColumnName = self.name() # + self.sqlTypeSuffix()
		return self._sqlColumnName


class BoolAttr:

	def sqlType(self):
		# @@ 2001-02-04 ce: is this ANSI SQL? or at least common SQL?
		return 'bool'

	def sampleValue(self, value):
		value = value.upper()
		if value=='FALSE' or value=='NO':
			value = 0
		elif value=='TRUE' or value=='YES':
			value = 1
		else:
			value = int(value)  # will throw exception if value is weird
		assert value==0 or value==1
		return str(value)


class IntAttr:

	def sqlType(self):
		return 'int'

	def sampleValue(self, value):
		int(value) # raises exception if value is invalid
		return value


class LongAttr:

	def sqlType(self):
		# @@ 2000-10-18 ce: is this ANSI SQL?
		return 'bigint'

	def sampleValue(self, value):
		long(value) # raises exception if value is invalid
		return value


class FloatAttr:

	def sqlType(self):
		return 'double precision'
		# @@ 2001-02-04 ce: this (8,8) stuff is bad,]
		# but haven't come up with solution yet

	def sampleValue(self, value):
		float(value) # raises exception if value is invalid
		return value


class DecimalAttr:

	def sqlType(self):
		# the keys 'Precision' and 'Scale' are used because all the
		# SQL docs I read say:  decimal(precision, scale)
		precision = self.get('Precision', None)
		if precision is None:
			if self.klass().klasses()._model.setting('UseMaxForDecimalPrecision'):  # that setting is for backwards compatibility
				precision = self.get('Max', None)
				if not precision:
					precision = None
			if precision is None:
				precision = 11
		scale = self.get('Scale', None)
		if scale is None:
			scale = self.get('numDecimalPlaces', 3)
		return 'decimal(%s,%s)' % (precision, scale)

	def sampleValue(self, value):
		return value


class StringAttr:

	def sqlType(self):
		"""
		Subclass responsibility.
		Subclasses should take care that if self['Max']==self['Min'] then the "char" type is preferred over "varchar".
		Also, most (if not all) SQL databases require different types depending on the length of the string.
		"""
		raise AbstractError, self.__class__

	def sampleValue(self, value):
		if value=="''":
			value = ''
		elif value.find('\\')!=-1:
			if 1:
				value = eval('"""'+str(value)+'"""')
				value = repr(value)
				value = value.replace('\\011', '\\t')
				value = value.replace('\\012', '\\n')
				return value
		value = repr(value)
		#print '>> value:', value
		return value


class AnyDateTimeAttr:

	def sqlType(self):
		return self['Type']  # e.g., date, time and datetime

	def sampleValue(self, value):
		return repr(value)


class ObjRefAttr:

	def sqlName(self):
		return self.name() + 'Id'

	# @@ 2001-02-04 ce: Is this standard SQL?
	#def sqlType(self):
	#	return 'bigint unsigned /* %s */' % self['Type']

	def sampleValue(self, value):
		""" Obj ref sample data format is "Class.serialNum", such as "Thing.3". If the Class and period are missing, then the obj ref's type is assumed. """
		parts = value.split('.')
		if len(parts)==2:
			className = parts[0]
			objSerialNum = parts[1]
		else:
			className = self.className()
			objSerialNum = value
		# @@ 2000-11-24 ce: check that we're pointing to a legal class
		klass = self.klass().klasses()._model.klass(className)
		klassId = klass.id()
		objRef = objRefJoin(klassId, objSerialNum)
		return str(objRef)


class ListAttr:

	def sqlType(self):
		raise Exception, 'Lists do not have a SQL type.'

	def hasSQLColumn(self):
		return 0

	def sampleValue(self, value):
		# @@ 2000-11-24 ce: need specific extension?
		# @@ 2001-02-04 ce: ^^^ what does that mean???
		raise Exception, 'Lists are implicit. They cannot have sample values.'
