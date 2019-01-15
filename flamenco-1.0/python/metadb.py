# Copyright (c) 2004-2006 The Regents of the University of California.


"""This is the Flamenco back-end.  No user interface stuff should go here."""

import time, sys, re

# ----------------------------------------------------------- SQL utilities
def explain(cursor, sql):
    sys.last_query = 'explain ' + sql
    cursor.execute('explain ' + sql)
    itable, itype, ikeys, ikey, ikeylen, iref, irows, iextra = map(
        [spec[0].lower() for spec in cursor.description].find,
        'table rows type key key_len possible_keys ref extra'.split())
    for row in cursor.fetchall():
        row.append('')
        print '%10s:%6s %-8skey %s(%s) [%s] on %s, %s' % (
            row[itable], row[irows], row[itype], row[ikey],
            row[ikeylen], row[ikeys], row[iref], row[iextra])

def execute(cursor, sql):
    start = time.time()
    sys.last_query = sql
    cursor.execute(sql)
    duration = time.time() - start
    if duration > 0.05:
        print '---- query:', sql
        print 'rows: %d, time: %.2f sec' % (cursor.rowcount, duration)
        sys.stdout.flush()

def escape(text):
    return text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')

def tablename(name_as_alias):
    return name_as_alias.split()[-1]

# --------------------------------------------------------- RDBMS interface
class ResultIterator:
    def __init__(self, cursor): self.cursor = cursor
    def __len__(self): return int(self.cursor.rowcount)
    def __iter__(self): return self

    def next(self):
        record = self.cursor.fetchone()
        if record is not None: return record
        self.cursor.close()
        raise StopIteration

class CachedSQLDatabase:
    def __init__(self, sqlconnection):
        self.conn = sqlconnection
        self.cache = {}

    def select(self, fields, tables,
               conditions=[], group=[], having=[], order=[], limit=None):
        if type(fields) is type(''): fields = [fields]
        if type(tables) is type(''): tables = [tables]
        if type(conditions) is type(''): conditions = [conditions]
        if type(group) is type(''): group = [group]
        if type(having) is type(''): having = [having]
        if type(order) is type(''): order = [order]
        for list in tables, conditions, group, having:
            list.sort()
        where = conditions and (' where ' + ' and '.join(conditions)) or ''
        group = group and (' group by ' + ', '.join(group)) or ''
        having = having and (' having ' + ' and '.join(having)) or ''
        order = order and (' order by ' + ', '.join(order)) or ''
        limit = limit and (' limit %s,%s' % limit) or ''
        return self.query('select ' + ', '.join(fields) +
                          ' from ' + ', '.join(tables) +
                          where + group + having + order + limit)

    def query(self, sql):
        #if sql in self.cache:
        #    print '---- cached:', sql
        #    return self.cache[sql]
        print sql
        sys.stdout.flush()
        cursor = self.conn.cursor()
        execute(cursor, sql)
        if cursor.rowcount < 500:
            self.cache[sql] = cursor.fetchall()
            cursor.close()
            return self.cache[sql]
        else:
            return ResultIterator(cursor)

# -------------------------------------------------------- metadb interface
def textmatch(field, value):
    if ' ' in value:
        parts = value.split()
        conditions = ["%s like '%% %s %%'" % (field, value)]
        conditions += ["match (%s) against ('%s')" % (field, part)
                       for part in parts if len(part) > 3]
        return ' and '.join(conditions)
    elif len(value) < 4:
        return "%s like '%% %s %%'" % (field, value)
    else:
        return "match (%s) against ('%s')" % (field, value)

class DB:
    def __init__(self, sqlconnection, luceneindex=None):
        self.db = CachedSQLDatabase(sqlconnection)
        if luceneindex:
            import lucene
            self.lucene = lucene.Lucene(luceneindex)
        else: self.lucene = None
        self.itemfields = [row[0] for row in self.db.query('describe items')
                                  if row[0] != 'item']
        self.attrs, self.attrlist = {}, []
        self.facets, self.facetlist, self.facetprops = {}, [], {}
        self.keys, self.keylist = {}, []
        self.depth, self.names = {}, {}
        for attr, name in self.db.select(['ident', 'name'], 'attrs'):
            self.attrlist.append(attr)
            self.attrs[attr] = name
        for key, name in self.db.select(['ident', 'name'], 'sortkeys'):
            self.keylist.append(key)
            self.keys[key] = name
        for (facet, name) in self.db.select(['ident', 'name'], 'facets'):
            self.facetlist.append(facet)
            self.facets[facet] = name
            fields = [row[0] for row in self.db.query('describe ' + facet)]
            numbers = [name[1:] for name in fields if name[1:2] in '123456789']
            self.depth[facet] = max(map(int, numbers))
            self.names[facet] = {}
            for id, name in self.db.select(['id', 'name'], facet):
                self.names[facet][id] = name
        columns = [row[0] for row in self.db.query('describe ' + 'facets')]
        for values in self.db.select(columns, 'facets'):
            props = {}
            for name, value in zip(columns, values):
                props[name] = value
            facet = props['ident']
            self.facetprops[facet] = props
        self.pathcache = {}
        self.parentcache = {}
        self.childrencache = {}

    def __clauses(self, query):
        conditions = []
        tables = []
        def first():
            return tablename(tables[0])
        def itemjoin(table):
            if tables:
                conditions.append(
                    '%s.item = %s.item' % (tablename(table), first()))
            tables.append(table)
        seq = 0
        for facet, value, leaf in query.getterms():
            seq += 1
            item_table = 'item_%s_%d' % (facet, seq)
            itemjoin('item_%s as %s' % (facet, item_table))
            if type(value) is type(''):
                seq += 1
                table = '%s_%d' % (facet, seq)
                tables.append('%s as %s' % (facet, table))
                conditions.append('%s.id = %s.id' % (item_table, table))
                conditions.append(textmatch(table + '.name', value))
            else:
                conditions.append('%s.id = %d' % (item_table, value))
            if leaf:
                conditions.append('%s.leaf = 1' % item_table)

        if self.lucene and query.getwords():
            terms = []
            for word in query.getwords():
                word = word.lower()
                if re.match('^[A-Za-z0-9]+$', word):
                    terms.append('+all:%s*' % word) # single word, prefix ok
                else:
                    terms.append('+all:"%s"' % word) # phrase of words
            items = self.lucene.search(' '.join(terms))
            itemlist = ', '.join(["'%s'" % item for item in items]) or 'null'
            if 'items' not in tables:
                itemjoin('items')
            conditions.append('%s.item in (%s)' % (first(), itemlist))
        else:
            for word in query.getwords():
                seq += 1
                table = 'text_%d' % seq
                tables.append('text as ' + table)
                if len(tables) > 1:
                    conditions.append('%s.item = %s.item' % (table, tablename(tables[0])))
                conditions.append(textmatch(table + '.text', word))
        return tables, conditions

    def facetprop(self, facet, name):
        return self.facetprops[facet][name]

    def name(self, facet, id=None):
        if id is not None:
            return self.names[facet].get(id, '[%s:%s]' % (facet, id))
        elif facet in self.facets: return self.facets[facet]
        elif facet in self.attrs: return self.attrs[facet]
        elif facet in self.keys: return self.keys[facet]

    def count(self, query):
        tables, conditions = self.__clauses(query)
        result = self.db.select('count(*)', tables or ['items'], conditions)
        try: len(result)
        except: # aieee!
            return 0
        return len(result) and result[0][0]

    def list(self, query, limit=None, sort=None):
        tables, conditions = self.__clauses(query)
        if type(limit) is not type(()): limit = limit and (0, limit)
        if sort and 'items' not in tables:
            tables.append('items')
            conditions.append('items.item = %s.item' % tablename(tables[0]))
        tables = tables or ['items']
        order = ['items.' + key for key in sort or []]
        rows = self.db.select('%s.item' % tablename(tables[0]), tables,
                              conditions, limit=limit, order=order)
        return [item for (item,) in rows]

    def lists(self, query, facet, ids, limit):
        results = {}
        for id in ids:
            results[id] = self.list(query + (facet, id, 0), (0, limit))
        return results

    def groups(self, query, facet, parent=0, limit=None, order=None):
        # This can often hit the cache, but is much slower if not cached.
        # It should be fast (if we force joining on child first), but
        # MySQL seems to choose the wrong join order.
        # if (facet, parent, 0) in query.getterms():
        #     query = query - (facet, parent, 0)
        columns = ['child.id', 'count(*) as count', 'child.name as name']
        tables, conditions = self.__clauses(query)
        if tables:
            conditions.append('map.item = %s.item' % tablename(tables[0]))
        tables.append('item_%s as map' % facet)
        tables.append('%s as child' % facet)
        conditions.append('map.id = child.id')
        conditions.append('child.parent = %d' % parent)
        if type(limit) is not type(()):
            limit = limit and (0, limit)
        if order not in ['count', 'count desc', 'name', 'name desc']:
            order = None

        groups = []
        for id, count, name in self.db.select(columns, tables, conditions,
            group='child.id', having='count > 0', limit=limit, order=order):
            if id:
                groups.append((name, id, count))
        return groups

    def termsearch(self, words):
        if type(words) is not type([]): words = [words]
        conditions = []
        for word in words:
            conditions.append("name like '%" + escape(word) + "%'")
        results = []
        for facet in self.facets:
            results += [(facet, int(id), name) for (id, name) in
                        self.db.select(['id', 'name'], facet, conditions)]
        return results

    def parentlist(self, facet, idlist):
        if not idlist: return []
        ids = ', '.join([str(id) for id in idlist])
        return [id for (id,) in self.db.select(
            'distinct parent', facet, 'parent in (%s)' % ids)]

    def path(self, facet, id):
        if facet not in self.pathcache:
            self.pathcache[facet] = {0: []}
        cache = self.pathcache[facet]
        if id not in cache:
            fields = ['p%d' % (i+1) for i in range(self.depth[facet])]
            ids = self.db.select(fields + ['level'], facet, 'id = %d' % id)[0]
            cache[id] = ids[:int(ids[-1])]
        return cache[id]

    def parent(self, facet, id):
        if facet not in self.parentcache:
            self.parentcache[facet] = {}
        cache = self.parentcache[facet]
        if id not in cache:
            cache[id] = self.db.select('parent', facet, 'id = %d' % id)[0][0]
        return cache[id]

    def children(self, facet, id=0):
        if facet not in self.childrencache:
            self.childrencache[facet] = {}
        cache = self.childrencache[facet]
        if id not in cache:
            cache[id] = [child for (child,) in
                self.db.select('id', facet, 'parent = %d' % id)]
        return cache[id]

    def counts(self, facet, idlist=None, limit=None):
        dict = {}
        if not idlist:
            condition = []
        else:
            condition = 'id in (%s)' % ', '.join([str(id) for id in idlist])
        if type(limit) is not type(()): limit = limit and (0, limit)
        for id, count in self.db.select(['id', 'count'], facet, condition,
            order='count desc', limit=limit): dict[id] = count
        return dict

    def metadata(self, item):
        idents = []
        metadata = {}
        for facet in self.facets:
            table = 'item_' + facet
            ids = self.db.select('id', table,
                ['%s.item = "%s"' % (table, item), 'leaf = 1'])
            metadata[facet] = [id for (id,) in ids if id]
        idents += self.attrs.keys()
        record = self.db.select(idents, 'items', 'item = "%s"' % item)[0]
        for i in range(len(record)):
            metadata[idents[i]] = record[i]
        return metadata

    #returns list of first "limit" items in history for this guy
    def listhistory(self, uid=0, limit=0):
        table = 'user_history'
        return [row[0] for row in
                 self.db.select('item', table, "userid='%s'" % uid,
                                order='timestamp desc', limit=limit)]

    def listquestions(self, task=1):
        return [row[0] for row in
                self.db.select('questionid', 'tasks_questions_relation',
                               "taskid=%s" % task, order='questionid')]
