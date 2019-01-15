# Copyright (c) 2004-2006 The Regents of the University of California.


"""A simple class for managing records of text fields into a SQL database."""

import sys

def esc(value):
    return "'" + value.replace('\\', r'\\').replace('\'', r'\''
                     ).replace('\t', r'\t').replace('\n', r'\n') + "'"

class Store:
    def __init__(self, sqlconnection, table, key, *fields):
        self.conn = sqlconnection
        self.table = table
        self.key = key
        self.fields = [key] + list(fields)
        if (table,) in self.execute('show tables'):
            existing = [row[0] for row in self.execute('describe ' + table)]
            if 'id' not in existing or key not in existing:
                raise TypeError, 'table %r has incompatible layout' % table
            for field in fields:
                if field not in existing:
                    self.execute('alter table %s add column %s text' %
                                 (table, field))
        else:
            specs = ['id int(9) primary key',
                      '%s varchar(100), unique key (%s)' % (key, key)]
            specs += ['%s text' % field for field in fields]
            self.execute('create table %s (%s)' % (table, ', '.join(specs)))

    def __getitem__(self, id):
        if id in self:
            return Record(self, id)
        else:
            raise IndexError, 'no record with id %r in this store' % id

    # the two things being set must be from the same store
    def __setitem__(self, id, item):
        if id in self:
            for f in self.fields:
                if f is not self.key:
                    self[id].__setattr__(f, str(item.__getattr__(f)))
        else:
            raise IndexError, 'no record with id %r in this store' % id

    def __delitem__(self, id):
        if id in self:
            self.execute('delete from %s where id = %s' % (self.table, id))
        else:
            raise IndexError, 'no record with id %r in this store' % id

    def deletegroup(self, field, value):
        self.execute("delete from %s where %s = '%s'" % (self.table, field, value))

    def __len__(self):

        return int(self.execute('select count(*) from %s' % self.table)[0][0])

    def __contains__(self, id):
        if type(id) is type(1):
            return len(self.execute('select id from %s where id = %d' %
                                    (self.table, id)))
        if type(id) is type(''):
            return len(self.execute('select id from %s where %s = %s' %
                                    (self.table, self.key, esc(id))))
        raise TypeError, 'argument %r to "in" operator has illegal type' % id

    def __iter__(self):
        return iter(self.keys())

    def new(self):
        id = self.execute('select max(id) from %s' % self.table)[0][0] or 0
        self.execute('insert into %s (id) values (%d)' % (self.table, id + 1))
        return int(id + 1)

    def keys(self):
        return [id for (id,) in self.execute('select id from %s' % self.table)]

    def index(self, value):
        return int(self.execute('select id from %s where %s = %s' %
                                (self.table, self.key, esc(value)))[0][0])

    def execute(self, sql):
        if sql[:6] == 'insert' or sql[:6] == 'update':
            print "STORE QUERY"
            print sql
        cursor = self.conn.cursor()
        sys.last_query = sql
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        return results

class Record:
    def __init__(self, store, id):
        self.__dict__['store'] = store
        self.__dict__['id'] = id

    def __getattr__(self, name):
        if name in self.store.fields:
            return self.store.execute('select %s from %s where id = %d' %
                                      (name, self.store.table, self.id))[0][0]
        else:
            raise NameError, 'no field named %r in this store' % name

    def __setattr__(self, name, value):
        if name in self.store.fields:
            self.store.execute('update %s set %s = %s where id = %d' %
                               (self.store.table, name, esc(str(value)), self.id))
        else:
            raise NameError, 'no field named %r in this store' % name

def test(*args):
    import MySQLdb
    conn = MySQLdb.connect(db='development', user='root', passwd='root')
    return Store(conn, *args)
