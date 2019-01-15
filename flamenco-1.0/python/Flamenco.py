# Copyright (c) 2004-2006 The Regents of the University of California.

from FrankenMatrix import *

def indent(rows, reservefirst=0):
    result, lastpath = [], []
    for path, leaf in rows:
        for i in range(len(path)):
            if lastpath[:i+1] != path[:i+1]:
                result.append((i, path[i], (path[i] == 0) and -1 or None))
        indent, dir, lastleaf = result[-1]
        if lastleaf:
            result.append((indent + (dir > -1), -1, leaf))
        else:
            result[-1] = (indent, dir, leaf)
        lastpath = path
    return result

def connect(rows):
    rows = rows[:]
    rows.reverse()
    pipes = []
    result = []
    for indent, dir, leaf in rows:
        pipes += [None]*(indent - len(pipes))
        if indent: pipes[indent-1] = pipes[indent-1] or 'ell'
        result.append((pipes[:indent] + [dir], leaf))
        pipes = pipes[:indent-1] + ['pipe']
    result.reverse()
    return result

def facettree(db, facet, values, term=lambda d, f, v: db.name(f, v or None),
              tab=17, stub=7, pipes='#d8d8d8', bars='#d8d8d8', facetvalue={}):
    paths = [list(db.path(facet, value)) for value in values]
    paths = [([0] + path[:-1], path[-1]) for path in paths]
    paths.sort()
    #return connect(indent(paths))
    rows = []
    tinysp = small(small(nbsp))

    checkboxcounter=0
    for dir, leaf in connect(indent(paths)):
        top, middle, bottom = [], [], []
        indented = 0
        for step in dir:
            if step in ['pipe', 'ell', None]:
                width = indented and tab or (tab - stub)
                top.append(td(space(width), width=width, rowspan=3))
                indented = 1
            if step == 'pipe':
                top.append(td(space(1), bgcolor=pipes, width=1, rowspan=3))
            elif step == 'ell':
                top.append(td(space(1, 7), bgcolor=pipes, width=1))
                middle.append(td(space(1), bgcolor=pipes, width=1))
                bottom.append(td(space(1, 7), width=1))
            elif step not in [-1, None]:
                if indented:
                    top.append(td(space(stub, 7), width=stub))
                    middle.append(td(space(stub), bgcolor=pipes, width=stub))
                    bottom.append(td(space(stub, 7), width=stub))
                # IE understands "nowrap", Opera understands <nobr>
                top.append(td(indented and tinysp or '', '<nobr>',
                              term(db, facet, step), '</nobr>', tinysp,
                              width=0, rowspan=3, nowrap=1))
        if leaf > 0:
            top.append(td(space(stub, 7), width="100%"))
            middle.append(td(space(stub), bgcolor=bars, width="100%"))
            bottom.append(td(space(stub, 7), width="100%"))
            top.append(td(space(4, 7), c='valuebox'))
            middle.append(td(space(4), bgcolor=bars))
            bottom.append(td(space(4, 7), c='valuebox'))
        else:
            top.append(td(space(stub, 7), width="100%", rowspan=3))
            top.append(td(space(4, 7), c='valuebox', rowspan=3))
        left = tablew(tr(top, height="50%"),
                      tr(middle, height=1),
                      tr(bottom, height="50%"), height="100%")
        
        if leaf == -1:
            right = cls('facetrepeat', term(db, facet, 0))
            more=''
            #rows.append(tr(td(left, height="100%"), td(right, c='valuebox'), td(more, c='morelikebg')))
        else:
            checkboxvalue=None
            if checkboxcounter in facetvalue.keys():
                checkboxvalue=facetvalue[checkboxcounter]
            
            right = leaf and cls('sel', tinysp, term(db, facet, leaf)) or ''
            more=leaf and input(type='checkbox', name=facet+'_%s' % str(checkboxcounter), value=leaf, checked=(str(checkboxvalue)==str(leaf)) and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()") or ''
            checkboxcounter=checkboxcounter+1
            
            #rows.append(tr(td(left, height="100%"), td(right, c='valuebox'), th(more, rowspan=3, c='morelikebg')))
        
        rows.append(tr(td(left, height="100%"), td(right, c='valuebox'), tdc(more, c='morelikebg')))
    
    return rows

class Flamenco(FrankenMatrix):
    def title(self):
        return '%s (%s)' % (coll.PAGE_TITLE, self.__class__.__name__)

    def pagetop(self):
        result = []
        showsearchsave, showfavesave, showreturntosearch = None, None, None
        if self.form.get('manage', ''):
            if self.form.get('q', '') or self.form.get('words', ''):
                showreturntosearch=1
        elif self.form.get('q', '') or self.form.get('words', ''):
            if self.form.get('index', '') and not self.form.get('taskcomplete', ''):
                showfavesave=1
                showreturntosearch=1
            elif not self.form.get('searchsave', '') and \
                     not self.form.get('item', '') and \
                     not self.form.get('taskcomplete', ''):
                showsearchsave=1
        toolbar = self.toolbar(showsearchsave, showfavesave, showreturntosearch)
        login = ''
        powered = '&nbsp;&nbsp;Powered by <a href=http://flamenco.berkeley.edu>Flamenco</a>'
        if self.session.username and self.session.username != 'default':
            login = ['Logged in as ', cls('user', self.session.username), '.']
        return div(div(powered, c='powered'), div(login, c='login'), h1(coll.PAGE_HEADING),
                   div(toolbar, c='toolbar'), h2(coll.PAGE_SUBHEADING),
                   c='title')

    def toolbar(self, searchsave=1, favesave=1, returntosearch=1):
        result = []

        if coll.USER_PERSONALIZATION:
            if self.form.get('username', ''):
                self.session.username = self.form.get('username', '')

            if self.index is not None:
                if not self.manage:
                    result += self.link(div('Save Item', c='button'),
                                        favesave=1, words=self.words,
                                        oldquery=self.oldquery)
            elif searchsave and not self.logout: 
                result += self.link(div('Save Search', c='button'),
                                    words=self.words, oldquery=self.oldquery)
            else:
                result += div('Save Search', c='button disabled')
            
            if self.query and not self.logout:
                result += self.link(div('History and Settings', c='button'),
                                    facet=None, offset=None, words=self.words,
                                    oldquery=self.oldquery,
                                    manage=1, managestart=1)
            elif not self.logout:
                result += self.link(div('History and Settings', c='button'),
                                    query=None, facet=None, group=None,
                                    sort=None, offset=None, index=None,
                                    manage=1, managestart=1)
            else:
                result += div('History and Settings', c='button disabled')

            if returntosearch and not self.logout:
                result += self.link(div('Return to Search', c='button'),
                                    facet=None, offset=None, words=self.words,
                                    oldquery=self.oldquery,
                                    index=[SELF, None][not self.manage])
            else:
                result += div('Return to Search', c='button disabled')

        result += self.link(div('New Search', c='button'),
                            query=None, facet=None, group=None,
                            sort=None, offset=None, index=None)

        if ((self.form.get('username', '') and
             self.form.get('username', '') == 'default') or
            (self.session.__session__.hasValue('username') and
             self.session.username == 'default') or self.logout):
            result += div('Logout', c='button disabled')
        else:
            result += self.link(div('Logout', c='button'), logout=1)
        return tdr(result, c='toolbar')

    def relatedlink(self, db, facet, value):
        if value == 0:
            return cls('facet', db.name(facet))
        term = cls('value', db.name(facet, value))
        query = Query(db) + (facet, value, 0)
        return [self.link(term, query=query, group=facet), nbsp,
                cls('count', '(%d)' % db.count(query))]

    def queryinfo(self, facetlist=None, attrlist=None, historyview=0):
        if facetlist is None:
            facetlist = db.facetlist
        if attrlist is None:
            attrlist = db.attrlist
        self.index = None
        boxes = [termbox(term, self.link) for term in self.query.getterms()
            ] + [wordbox(term, self.link) for term in self.query.getwords()]
        metadata = db.metadata(self.item)
        facets = []
        for facet in facetlist:
            if not metadata[facet]: continue
            facetvals={}
            for i in range(20):
                value = self.form.get('%s_%d' % (facet, i), '')
                if value:
                    facetvals[i] = value
                      
            facets.append(facettree(
                db, facet, metadata[facet], self.relatedlink,
                facetvalue=facetvals or {}))
            facets.append(tr(td(space(4,4))))
        attrs = []
        for attr in attrlist:
            if not metadata[attr]: continue
            name = cls('attribute', db.name(attr))
            # fix for -1 attribute value; set to N/A
            value = metadata[attr]
            if value == -1:
                value = 'N/A'
            attrs.append(trt(td(name, ':', nbsp), td(nbsp, value)))

        terms = []
        for facet in facetlist:
            for i in range(20):
                value = self.form.get('%s_%d' % (facet, i), '')
                if value:
                    terms.append((facet, int(value), 0))
        if terms:
            query=Query(db, terms=terms)
            count=db.count(query)
            morelikelink=self.link('Find Similar Items (%s)' % count)
        else:
            query=None
            count=None
            morelikelink='Find Items Similar to This One...'
        if count:
            morelikelink=input(type='submit', value='Find Similar Items (%s)' % count)
        else:
            morelikelink=input(type='submit', value='Find Similar Items')
        subhead = tr(td(nobr(coll.ENDGAME_MORE_GENERAL),
                        nbsp*3, c='metasubhead'),
                     td(coll.ENDGAME_ITEM_INFO, c='metasubhead'), td())

        extrainfo = [input(type='hidden', name='xposition', value='0'),
                     input(type='hidden', name='yposition', value='0'),
                     input(type='hidden', name='showtooltipselect', value='1'),
                     input(type='hidden', name='morelike', value='1'),
                     input(type='hidden', name='task', value=None)]
    
        result = []
        if not historyview:
            result += [cls('metaheading', coll.ENDGAME_CURRENT_SEARCH), p, boxes]
        index = None
        if not query:
            index = self.form.get('index')
        button = postform(tablew(tr(tdr(morelikelink))),
                          action=self.url(query=query or self.query,
                                          morelike='1', index=index))
        detail = postform(table(subhead, facets, attrs), extrainfo,
                          action=self.url(index=self.form.get('index')))
        result += [p, cls('metaheading', coll.ENDGAME_LINK_RELATED),
                   p, cls('metadata', button),
                   p, cls('metadata', detail)]
        return result
