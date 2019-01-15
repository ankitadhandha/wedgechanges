import FixPath
from DataTable import *
import string
from StringIO import StringIO


# @@ 2000-12-04 ce: We don't test the feature where record like objects, that respond to hasValueForKey() and valueForKey(), can be added to a table (as opposed to a sequence, dictionary or TableRecord instance).

def heading(title):
	print 'Testing %s...' % title


def testSource(name, src, headings, data):
	heading(name)
	dt = DataTable()
	lines = split(src, '\n')
	dt.readLines(lines)
	assert [col.name() for col in dt.headings()]==headings
	i = 0
	while i<len(dt):
		match = data[i]
		if dt[i].asList()!=match:
			print 'mismatch'
			print 'i        :', i
			print 'expected :', match
			print 'got      :', dt[i]
			raise AssertionError
		i = i + 1


def test01():
	print 'Simple tests...'

	heading('Create table')
	t = DataTable()

	heading('Headings 1')
	t = DataTable()
	t.setHeadings([TableColumn('name'), TableColumn('age:int'), TableColumn('rating:float')])

	heading('Headings 2')
	t = DataTable()
	t.setHeadings(['name', 'age:int', 'rating:float'])

	heading('Adding and accessing data')
	a = ['John', '26', '7.2']
	b = ['Mary', 32, 8.3]
	t.append(a)
	t.append(b)
	assert t[-1].asList()==b
	assert t[-2].asDict()=={'name':'John', 'age':26, 'rating':7.2}
	assert t[-1]['name']=='Mary'
	assert t[-2]['name']=='John'

	heading('Printing')
	print t

	heading('Writing file (CSV)')
	answer = '''\
name,age,rating
John,26,7.2
Mary,32,8.3
'''
	out = StringIO()
	t.writeFile(out)
	results = out.getvalue()
	assert results==answer, '\n%r\n%r\n' % (results, answer)

	heading('Accessing rows')
	for row in t:
		assert row['name']==row[0]
		assert row['age']==row[1]
		assert row['rating']==row[2]
		for item in row:
			pass

	heading('Default type')
	t = DataTable(defaultType='int')
	t.setHeadings(list('xyz'))
	t.append([1, 2, 3])
	t.append([4, 5, 6])
	assert t[0]['x'] - t[1]['z'] == -5

	# Basics
	src = '''\
"x","y,y",z
a,b,c
a,b,"c,d"
"a,b",c,d
"a","b","c"
"a",b,"c"
"a,b,c"
"","",""
"a","",
'''
	headings = ['x', 'y,y', 'z']
	data = [
		['a', 'b', 'c'],
		['a', 'b', 'c,d'],
		['a,b', 'c', 'd'],
		['a', 'b', 'c'],
		['a', 'b', 'c'],
		['a,b,c', '', ''],
		['', '', ''],
		['a', '', '']
	]
	testSource('Basics', src, headings, data)


	# Comments
	src = '''\
a:int,b:int
1,2
#3,4
5,6
'''
	headings = ['a', 'b']
	data = [
		[1, 2],
		[5, 6],
	]
	testSource('Comments', src, headings, data)

	# Multiline records
	src = '''\
a
"""Hi
there"""
'''
	headings = ['a']
	data = [
		['"Hi\nthere"'],
	]
	testSource('Multiline records', src, headings, data)

	# MiddleKit enums
	src = '''\
Class,Attribute,Type,Extras
#Foo,
,what,enum,"Enums=""foo, bar"""
,what,enum,"Enums='foo, bar'"
'''
	headings = 'Class,Attribute,Type,Extras'.split(',')
	data = [
		['', 'what', 'enum', 'Enums="foo, bar"'],
		['', 'what', 'enum', "Enums='foo, bar'"],
	]
	testSource('MK enums', src, headings, data)


	heading('Unfinished multiline record')
	try:
		DataTable().readString('a\n"1\n')
	except DataTableError:
		pass  # just what we were expecting
	else:
		raise Exception, 'Failed to raise exception for unfinished multiline record'


def main():
	print 'Testing DataTable.py'
	test01()
	print 'Done.'


if __name__=='__main__':
	main()
