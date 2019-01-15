from ExamplePage import ExamplePage
import MySQLdb


class DB(ExamplePage):

    def writeContent(self):
        self.writeln('<P>Welcome to the DBPool example!</P>')
        pool = self.getCan('DBPoolCan', 'DBPool', 'application',
                           MySQLdb, 5, host='localhost',
                           user='test', passwd='test',
                           db='test')
        con = pool.getConnection()
        cursor = con.cursor()
        cursor.execute("select name from test")
        for name in cursor.fetchall():
            self.writeln('%s<br>' % name)
        db.close()
