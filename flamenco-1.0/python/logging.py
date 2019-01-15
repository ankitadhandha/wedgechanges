# Copyright (c) 2004-2006 The Regents of the University of California.

"""Logging facility."""

import sys

def esc(value):
    return "'" + value.replace('\\', r'\\').replace('\'', r'\''
                     ).replace('\t', r'\t').replace('\n', r'\n') + "'"

class Log:
    def __init__(self, sqlconnection, table):
        self.conn = sqlconnection
        self.table = table

    def log(self, interface, event, detail='', userid=0, **fields):
        #userid = interface.session.get('userid', 0)
        taskid = interface.session.get('taskid', 0)
        names = ['interface', 'userid', 'taskid', 'event', 'detail']
        values = [esc(interface.__class__.__name__),
                  str(userid), str(taskid), esc(event), esc(detail)]
        for name, value in fields.items():
            names.append(name)
            if type(value) is type(''): value = esc(value)
            if value is None: value = 'NULL';
            values.append(str(value))
        self.execute('insert into %s (%s) values (%s)' %
                     (self.table, ', '.join(names), ', '.join(values)))

    def execute(self, sql):
        print "LOGGING SQL"
        print sql
        results = ()
        cursor = self.conn.cursor()
        sys.last_query = sql
        cursor.execute(sql)
        #DB2 can't do fetchall on non select queries so check query type
        if sql[:6] == 'select':
            results = cursor.fetchall()
        cursor.close()
        return results


    #record user tables for 2004 study, for when people submit task
    def dumpusertables(self, userid, task, timestamp):
#        self.execute("insert into user_dump values ('6', 'kevin', '12', '2', '2', '0', 'date, artist, heaven_earth, location, media2, objects, occupations, shapes_colors_scenes, themes, built_places', '50', '50', '60', '40', 'new', 'title, count desc, title, title, title, title, title, title, title, title', 'first word, first word, first word, first word, first word, first word, first word, first word, first word, first word', 'name, artist_detail, media_detail, culture, item, rec_no, description', '1', '2', '1', '7', '0', 'asdf', '3', '', '3', '1091747518.24')")
        for table in ['user', 'user_history', 'user_history_groups', 'user_history_searches']:
            if table=='user':
                results = self.execute('select * from %s where id=%s' % (table, userid))
            else:
                results = self.execute('select * from %s where userid=%s' % (table, userid))
            
            if not results==():
                for row in results:
                    content=[]
                
                    for x in row:
                        content.append('"'+str(x)+'"')
                    content.append('"'+ task+'"')
                    content.append('"'+timestamp+'"')
                
                    content = ', '.join(content)
                
                
                    query="insert into %s values (%s)" % (table+'_dump', content)
                    print query
                    self.execute(query)

        
    
