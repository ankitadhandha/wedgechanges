# Copyright (c) 2004-2006 The Regents of the University of California.

import WebKit.AppServer, WebKit.Session, WebKit.Page, UserDict, MySQLdb, app
from html import *

class DictWrapper(UserDict.UserDict):
    def __repr__(self):
        return '<%s at %x>' % (self.__class__.__name__, id(self))
    def __contains__(self, name): return self.has_key(name)
    def __iter__(self): return iter(self.keys())
    def __len__(self): return len(self.keys())
    def clear(self):
        for name in self: del self[name]
    def keys(self): return self.__delegate__.keys()
    def values(self): return self.__delegate__.values()
    def items(self): return self.__delegate__.items()
    def has_key(self, name): return self.__delegate__.has_key(name)
    def update(self, dict):
        for key in dict: self[key] = dict[key]

    def __cmp__(self): raise TypeError, 'cannot compare %r' % self
    def copy(self): raise TypeError, 'cannot copy %r' % self
    def popitem(self): raise TypeError, 'cannot pop from %r' % self

class SessionWrapper(DictWrapper):
    getters = {'__start__': WebKit.Session.Session.creationTime,
               '__access__': WebKit.Session.Session.lastAccessTime,
               '__id__': WebKit.Session.Session.identifier,
               '__timeout__': WebKit.Session.Session.timeout}
    setters = {'__timeout__': WebKit.Session.Session.setTimeout}

    def __init__(self, session):
        self.__dict__['__session__'] = session
        self.__dict__['__delegate__'] = session._values
    def __getitem__(self, name): return self.__session__.value(name)
    def __setitem__(self, name, value): self.__session__.setValue(name, value)
    def __delitem__(self, name):
        if name in self: self.__session__.delValue(name)

    def __getattr__(self, name):
        if name in self.getters: return self.getters[name](self.__session__)
        else: return self[name]

    def __setattr__(self, name, value):
        if name in self.setters:
            self.setters[name](self.__session__, value)
        elif name in self.getters:
            raise TypeError, 'read-only attribute ' + name
        else: self[name] = value

    def __delattr__(self, name):
        if name in self.getters:
            raise TypeError, 'permanent attribute ' + name
        else: del self[name]

class FormWrapper(DictWrapper):
    def __init__(self, form):
        self.__dict__['__form__'] = form
        self.__dict__['__delegate__'] = form
    def __getitem__(self, name):
        value = self.__form__[name]
        if type(value) is type([]):
            if len(value) == 1: value = value[0]
            else: raise TypeError, 'multiple values in field "%s"' % name
        return str(value)
    def __getattr__(self, name): return self[name]

    def getlist(self, name):
        if self.__form__.has_key(name):
            value = self.__form__[name]
            if type(value) is type([]): return map(str, value)
            else: return [str(value)]

    def __setitem__(self, name, value): raise TypeError, 'read-only object'
    def __delitem__(self, name): raise TypeError, 'read-only object'
    def __setattr__(self, name, value): raise TypeError, 'read-only object'
    def __delattr__(self, name): raise TypeError, 'read-only object'
    def clear(self): raise TypeError, 'read-only object'
    def update(self): raise TypeError, 'read-only object'

class OutputWrapper:
    def __init__(self, out):
        self.out = out

    def write(self, *args):
        if len(args) == 1: args = args[0]
        if type(args) in (type([]), type(())):
            for item in args: self.write(item)
        else:
            self.out.write(str(args))

class Page(WebKit.Page.Page):
    def awake(self, transaction):
        WebKit.Page.Page.awake(self, transaction)
        self.response = transaction.response()
        self.response.setHeader('content-type', 'text/html; charset=iso-8859-1')
        self.out = OutputWrapper(self.response)
        self.request = transaction.request()
        self.prevurl = self.request._environ.get('HTTP_REFERER',
            self.request._environ.get('HTTP_REFERRER'))
        self.session = SessionWrapper(transaction.session())
        self.form = FormWrapper(self.request.fields())

    def writeHTML(self):
        try:
            app.conn.ping() # If the connection has gone away, abort.
            self.prepare()
            self.header(self.out)
            self.body(self.out)
            self.footer(self.out)
        except MySQLdb.Error, error:
            if error.args[0] in(2006,):
                conn = MySQLdb.connect(host=DBHOST, user=DBUSER, passwd=DBPASS, db=DBNAME)
                #app.conn.ping(True)
                #app.cursor = app.conn.cursor
            elif error.args[0] in (1037, # out of memory
                                 1040, # too many connections
                                 1041, # out of resources
                                 1053, # shutdown in progress
                                 1078, # aborting on signal
                                 2002, # cannot connect to local
                                 2003, # cannot connect to host
                                 #2006, # server gone away
                                 2013, # lost connection during query
                                ):
                # These errors can often be resolved by restarting the server.
                print >>self.out, '''
<!doctype html public "-//W3C//DTD HTML 3.2 Final//EN">
<html><head><link rel=stylesheet type="text/css" href="FlamencoStyle">
<title>%s: Database Error</title></head><body>
<div class="title"><h1>Database Error</h1></div>
<div class="body">The MySQL database connection is missing.
Please restart the MySQL database server and reload this page.
<p>
Error message: <code>%s</code>
</div></body></html>''' % (self.title(), esc(repr(error.args)))
                # Shut down the application so it can restart afresh next time.
                from WebKit.AppServer import globalAppServer
                globalAppServer.running = 0
            else:
                # For other database errors, show a normal error page.
                raise

    def prepare(self):
        pass

    def header(self, out):
        print >>out, '''<!doctype html public "-//W3C//DTD HTML 3.2 Final//EN">
<html><head><link rel=stylesheet type="text/css" href="FlamencoStyle">
<meta %s><title>%s</title></head><body onload="%s">%s
''' % (self.metatag(), self.title(), self.preload(), bodyprefix)
        out.write(self.pagetop())
        
    def pagetop(self):
        return div(h1(self.heading()), h2(self.subheading()), c='title')

    def preload(self):
        return ''

    def heading(self):
        return 'Heading'

    def subheading(self):
        return 'Subheading'

    def body(self, out):
        print >>out, '<p>This is a generic page.'

    def footer(self, out):
        print >>out, '</body></html>'

    def preAction(self, name):
        self.header()

    def postAction(self, name):
        self.footer()

    def redirect(self, url):
        self.response.sendRedirect(url)
