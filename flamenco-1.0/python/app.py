# Copyright (c) 2004-2006 The Regents of the University of California.

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import MySQLdb, metadb, store, logging

# Put the instance directory at the front of the path.
from WebKit.AppServer import globalAppServer
sys.path.insert(0, globalAppServer.serverSidePath())

# instance.py, Collection.py, and Lucene/ reside in the instance directory.
from instance import DBHOST, DBUSER, DBPASS, DBNAME
from Collection import Collection

try:
    conn = MySQLdb.connect(host=DBHOST, user=DBUSER, passwd=DBPASS, db=DBNAME)
except MySQLdb.Error:
    # This lets us continue until Page.writeHTML can show an error message.
    class DummyDB:
        rowcount = 0
        def cursor(self): return self
        def execute(self, query): pass
        def fetchone(self): return []
        def fetchall(self): return []
        def close(self): pass
        def ping(self): raise MySQLdb.OperationalError
    conn = DummyDB()

    # Shut down the server so it can restart afresh next time.
    globalAppServer.running = 0

lucenepath = globalAppServer.serverSidePath('Lucene')
db = metadb.DB(conn, os.path.isdir(lucenepath) and lucenepath or None)
coll = Collection(db)

users = store.Store(conn, *'''user name opening_facet_terms
    opening_facet_columns opening_term_columns remember facets attrs
    facet_column_width item_column_width endgame_item_col_width
    endgame_facet_col_width sortby caps display_opening_option
    display_middle_option display_end_option managegame_opening
    showpreviews password email completed_tasks available_tasks'''.split())
user_histories = store.Store(conn, *'''user_history id userid item
    itemidx timestamp favorites groupid user'''.split())
user_history_groups = store.Store(conn, *'''
    user_history_groups id groupname userid timestamp user'''.split())
user_history_searches = store.Store(conn, *'''user_history_searches
    searchname id userid timestamp query facetgroup sort user'''.split())

tasks = store.Store(conn, 'tasks', 'id', 'description')
tasks_questions = store.Store(conn,
    *'tasks_questions id question type optional'.split())
tasks_questions_responses = store.Store(conn, *'''tasks_questions_responses
    id questionid response userid taskid'''.split())
tasks_url = store.Store(conn, 'tasks_url', 'taskid', 'userid', 'url')

log = logging.Log(conn, 'log')
