# Copyright (c) 2004-2006 The Regents of the University of California.


from Page import Page
from html import repr
from app import db, coll

class Test(Page):
    def body(self, out):
        print >>out, '''
<form><input name=query size=60 value="%s"><input type=submit></form>
''' % self.form.get('query', 'select item from ...')
        if 'query' in self.form:
            results = db.db.query(self.form.query)
            print >>out, '<p>results: %d<p>' % len(results)
            count = 0
            for (item,) in results:
                print >>out, coll.itemlisting(item)
                count += 1
                if count == 30: break
        print >>out, html.repr(db.facets)
        print >>out, html.repr(db.attrs)
