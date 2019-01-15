"""
FUTURE

* Parameterize the database and everything else. Currently hard coded to MySQL, user=test, password=test.

* We don't really test performance here. e.g., we don't do benchmarks to see if DBPool actually helps or not.

"""


import sys
sys.path.insert(1, '..')
from DBPool import DBPool


def Test(iterations=15):
	try:
		dbModuleName = 'MySQLdb'
		dbModule = __import__(dbModuleName)
		pool = DBPool(dbModule, 10, host='localhost', user='test', passwd='test', db='test')
		for i in range(iterations):
			db = pool.getConnection()
			cursor = db.cursor()
			cursor.execute("select * from test")
			print i, cursor.fetchall()
			db.close()
	except:
		import traceback
		traceback.print_exc()
		print 'You need the MySQLdb adapter and a test database for this example'


if __name__=='__main__':
	Test()
