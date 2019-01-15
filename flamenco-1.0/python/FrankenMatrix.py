# Copyright (c) 2004-2006 The Regents of the University of California.

from app import *
from components import *
from html import *
from InterfaceBase import InterfaceBase, SELF
from query import Query
from time import time, strftime, gmtime, localtime
import os, re, random
import Cookie as CookieEngine
from WebKit.Cookie import Cookie
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
OVERFLOW_LIMIT = 50000
GROUP_LIMIT = 50

class FrankenMatrix(InterfaceBase):
    def title(self):
        return coll.PAGE_TITLE

    def preload(self):
        top=0
        left=0
        if self.form.get('yposition', ''):
            top=self.form.get('yposition', '')
        if self.form.get('xposition', ''):
            left=self.form.get('xposition', '')
        print 'PRELOAD'
        if not self.form.get('yposition', '') and not self.form.get('xposition', ''):
            return ''
        return 'setposition(%s, %s);' % (top, left)

    def more(self, text, facet):
        return self.link(text, action='categorylist', group=facet)

    def heading(self):
        return coll.PAGE_HEADING

    def limitlink(self, *stuff, **attrs):
        if 'count' in attrs:
            if attrs['count'] >= OVERFLOW_LIMIT:
                attrs['action'] = 'overflowlist'
            del attrs['count']
        if 'facet' in attrs:
            attrs['group'] = attrs['facet']
            del attrs['facet']
        return self.link(*stuff, **attrs)

    #Opening game, intro page
    def opening(self, loginerror=None):
        print "opening"
        if self.session.__session__.hasValue('username'):
            if self.session.username=='':
                name='default'

                self.session.username='default'
            else:
                name = str(self.session.username)

        elif self.form.get('username'):
            name = str(self.form.username)
        elif self.request.hasCookie('username'):
            name = str(self.request.cookies()['username'])
        else: #user not yet logged in
            name='default'
        if name=='': name='default'
        if name=='default':
            print loginerror
            #prompt=self.loginbanner(post=self.url())
	    prompt = ''
        else:
            prompt = self.loggedinbox(name)
        if self.session.__contains__('showtooltips'):
            if self.form.get('showtooltip', ''):
                self.session.showtooltips=1 #self.form.get('showtooltip', '')
            elif self.form.get('showtooltipselect', ''):
                self.session.showtooltips=0
        else:
            #set default show tooltip value here as well as middlegamematrix
            self.session.showtooltips=1

        tooltipprompt = postform(tablew(
            trt(td(input(type='checkbox', name='showtooltip', checked='true' and self.session.showtooltips or None, onclick="setscrollxy(this.form); this.form.submit()"),
                  input(type='hidden', name='xposition', value='0'),
                  input(type='hidden', name='yposition', value='0'),
                  input(type='hidden', name='showtooltipselect', value='1'),
                  input(type='hidden', name='task', value=self.task),
               ' Show tooltip previews of subcategories'))), action=self.url())

        self.session.useridx = users.index(name)
        self.session.username = name

        userfacets = coll.facetlist[:]
        if users[self.session.useridx].facets is not None:
            userfacets = users[self.session.useridx].facets.split(', ')
        usersortby = ['name'] * len(userfacets)
        if users[self.session.useridx].sortby is not None:
            usersortby = users[self.session.useridx].sortby.split(', ')
        usercaps = ['none'] * len(userfacets)
        if users[self.session.useridx].caps is not None:
            usercaps = users[self.session.useridx].caps.split(', ')
        OPENING_FACET_TERMS = users[self.session.useridx].opening_facet_terms
        OPENING_FACET_COLUMNS = users[self.session.useridx].opening_facet_columns
        OPENING_TERM_COLUMNS = users[self.session.useridx].opening_term_columns
        matrix = facetmatrix(self.query, self.limitlink, self.openingfacet,
                             columns=OPENING_FACET_COLUMNS, 
                             values=OPENING_FACET_TERMS, 
                             term_columns=OPENING_TERM_COLUMNS, 
                             morelink=self.more, displayfacets=userfacets,
                             sortbylist=usersortby, capslist=usercaps,
                             username=name,
                             showtooltips=self.session.showtooltips)
        header = tablew(trt(
            td(tablew(tr(td(searchbox(self.query, task=self.task))),
                      tr(td(tooltipprompt))), width='39%'),
            td(nbsp, width='1%'),
            td(prompt, width='60%')), space=10)
        if loginerror:
            return tablew(trbl(td(small(loginerror)), c='loginerror'),
                          trt(td(header)), trt(td(matrix)), c='opening')
        else:
            return tablew(self.taskbar(), tr(td(nbsp)),
                          tr(td(header)), tr(td(matrix)), c='opening')

    def openingfacet(self, f, path, link, groups):
        return tip(db.facetprop(f, 'description'), cls('facet', db.name(f)))

    def newsearch(self):
        return link(self.__class__.__name__+'?username='+self.session.username,
                    strong(coll.NEW_SEARCH))

    #Search Results display page
    def middlegame(self):
        print 'middlegame'
        self.session.useridx = users.index(self.session.username)
        #Check to see if processing a "popup" window
        if self.form.get('popuphandle', '') == '1':
            print 'POPUPHANDLE'
            self.popuphandler()
        if self.action.split()[:1] == ['matchlist']:
            return self.matchlist(self.action.split(' ', 1)[1])
        if self.action == 'categorylist':
            facet = self.group or self.facet
            return div(self.query and div(self.paths(facet), c='query'),
                       self.categorylist(facet), c='categorylist')
        if self.group and self.values[self.group]:
            id = self.values[self.group]
            groups = len(db.groups(self.query, self.group, id))
            if groups > GROUP_LIMIT and self.action != 'force':
                self.action = 'overflowlist'
        if self.action == 'overflowlist':
            facet = self.group or self.facet
            if not facet and self.query.getterms():
                facet = self.query.getterms()[0][0]
            id = self.values.get(facet, 0)
            groups = len(db.groups(self.query, facet, id))
            if facet and groups:
                link = flatten(self.link(coll.MIDDLEGAME_TOO_MANY_ITEMS_LINK,
                                         action='force', task=self.task))
                itemcount = '%d %s' % (self.count,
                    plural(self.count, coll.ITEM_NOUN_PLURAL, coll.ITEM_NOUN))
                groupcount = '%d %s' % (groups,
                    plural(groups, coll.GROUP_NOUN_PLURAL, coll.GROUP_NOUN))
                message = coll.MIDDLEGAME_TOO_MANY_ITEMS % {
                    'items': itemcount, 'groups': groupcount, 'link': link,
                    'category': db.name(facet, self.values[facet] or None)}
                return [p, self.paths(facet), p, message,
                        p, self.categorylist(facet)]
        return self.mainmiddlegame()

    def mainmiddlegame(self):
        results = self.itemlisting()
        words = [wordbox(word, self.link, task=self.task)
                 for word in self.query.getwords()]
        terms = [termbox(term, self.link, task=self.task)
                 for term in self.query.getterms()]
        query = [p, tablew(trt(td(words, terms)))]
        matches = ''
        if self.words and not self.query.getterms():
            check = {}
            for word in self.words: check[word] = 1
            qcheck = {}
            for word in self.query.getwords(): qcheck[word] = 1
            if check == qcheck:
                matches = []
                if len(self.words) > 1:
                    matches += [self.matchterms(' '.join(self.words))] 
                matches += [self.matchterms(word) for word in self.words]
        idx = users.index(self.session.username)
        message = (coll.MIDDLEGAME_TERMS, coll.MIDDLEGAME_REMOVE % {
                   'button' : flatten(div('&times;', c='removebox'))})
        idx = users.index(self.session.username)

        facetcolumn = tablew(
            tr(td(searchbox(self.query, task=self.task,
                            selectscope=1, defaultscope='all'))),
            tr(td(coll.MIDDLEGAME_REFINE, c='message')),
            tr(td(self.middlegamematrix())))
        fwidth = '%s%%' % users[idx].facet_column_width
        itemcolumn = tablew(
            trt(td(message, p, query, p, results)))
        iwidth = '%s%%' % users[idx].item_column_width
        return [self.taskbar(), matches, p,
                tablew(trt(td(facetcolumn, width=fwidth, c='facetcolumn'),
                           td(itemcolumn, width=iwidth, c='itemcolumn')))]

    def middlegamematrix(self):
        #default showtooltips value set here as well as opening
        if not self.session.__contains__('showtooltips'):
            self.session.showtooltips = 1
        userfacets = coll.facetlist[:]
        if users[self.session.useridx].facets is not None:
            userfacets = users[self.session.useridx].facets.split(', ')
        usersortby = ['name'] * len(userfacets)
        if users[self.session.useridx].sortby is not None:
            usersortby = users[self.session.useridx].sortby.split(', ')
        usercaps = ['none'] * len(userfacets)
        if users[self.session.useridx].caps is not None:
            usercaps = users[self.session.useridx].caps.split(', ')

        matrix = facetmatrix(self.query, self.limitlink, self.middlegamefacet,
                             columns=1, values=10, term_columns=2,
                             morelink=self.more,
                             column_width_chars=coll.MIDDLEGAME_COLUMN_WIDTH,
                             displayfacets=userfacets, sortbylist=usersortby,
                             capslist=usercaps, username=self.session.username,
                             showtooltips=self.session.showtooltips)

        return tablew(tr(td(matrix)), tr(td(self.historypreview())))


    def middlegamefacet(self, f, path, link, groups):
        name = cls('facet', db.name(f))
        message = tip(coll.MIDDLEGAME_GROUPBY_TOOLTIP + db.name(f), 
                      coll.MIDDLEGAME_GROUPBY)
        grouplink = [' ', link(message, group=f)]
        if self.group == f or not groups:
            grouplink = ''
        if path:
            path = [': ', link('all', term=(f, 0, 0)), ' &gt; '] + path
        return [name, path, grouplink]

    def itemlisting(self):
        name=self.session.username
        if not self.group: group = 0
        elif not self.values[self.group]: group = 1
        elif len(db.groups(
            self.query, self.group, self.values[self.group])) <= 1: group = 0
        else: group = 1
        return group and self.groupeditems(username=name) or self.ungroupeditems(username=name)

    #middlegame display of items grouped by a facet
    def groupeditems(self, username=None):
        print 'GROUPEDITEMS'
        self.sort = None
        head = [strong('%d item%s, ' % (self.count, plural(self.count)),
                       'grouped by ', cls('facet', db.name(self.group))), nbsp,
                '(', self.link(coll.MIDDLEGAME_VIEW_UNGROUPED, group=None), ')']
        groups = db.groups(self.query, self.group, self.values[self.group])
        if len(groups) > GROUP_LIMIT and self.action != 'force':
            return self.redirect(self.url(action='overflowlist'))

        userfacets = coll.facetlist[:]
        if users[self.session.useridx].facets is not None:
            userfacets = users[self.session.useridx].facets.split(', ')
        usersortby = ['name'] * len(userfacets)
        if users[self.session.useridx].sortby is not None:
            usersortby = users[self.session.useridx].sortby.split(', ')
        order = usersortby[userfacets.index(self.group)]

        results = groupitems(self.query, self.group, self.values[self.group],
                             self.link, sort=db.keylist, order=order,
                             links=1, oldquery=self.query)
        return [tablew(tr(td(head))), results]

    #middlegame display of items ungrouped
    def ungroupeditems(self, username=None, sort=None):
        print 'UNGROUPED ITEMS'
        resultinfo = strong(pagecount(self.offset, self.count).capitalize())
        if '' in self.sortkeys:
            self.sortkeys.remove('')
        if not sort: sort = []

        if self.count > 1:
            groupfacets = [
                tip(coll.MIDDLEGAME_GROUPBY_TOOLTIP + db.name(term[0]),
                    self.link(db.name(term[0]), group=term[0]))
                for term in self.query.getterms()]
            if groupfacets:
                resultinfo += [br, 'Group by: ', join(', ', groupfacets)]

            sortkeys = []
            for key in db.keylist:
                if self.sortkeys and self.sortkeys[0] == key:
                    sortkeys += [cls('sel', db.name(key))]
                else:
                    sortkeys += [self.link(db.name(key), sort=key)]
            if sortkeys:
                resultinfo += [br, 'Sort by: ', join(', ', sortkeys)]
        else:
            resultinfo += [coll.MIDDLEGAME_UNGROUPED]
        return [tablew(tr(td(resultinfo)), tr(td(nbsp))),
                pagebar(self.offset, self.count, self.link, head=0),
                listitems(self.query, self.offset,
                          link=self.link, sort=self.sortkeys),
                pagebar(self.offset, self.count, self.link, head=0)]

    def matchterms(self, word, columns=2, max=30):
        pat = re.compile('(%s)' % word, re.I)
        choices = []
        matches = db.termsearch(word)
        if len(matches) > max: matches[max-1:] = [(None, coll.MORE, len(matches))]
        for facet, id, name in matches[:max]:
            if id == coll.MORE:
                choices.append(li(self.link(coll.MORE + coll.NUM_MATCHES % name,
                                            action='matchlist ' + word,
                                            words=self.words)))
                break
            path = db.path(facet, id)
            parts = [db.name(facet), name]
            steps = 2
            while steps < len(path):
                step = db.name(facet, path[-steps])
                if len(' > '.join(parts + [step])) > 50: break
                steps += 1
                parts[1:1] = [step]
            parts[0] = [strong(db.name(facet))]
            if steps < len(path): parts[1:1] = ['...']
            name = pat.sub(flatten(color('#ff0000', '\\1')), name)
            parts[-1] = self.link(name, query=Query(db) + (facet, id, 0))
            choices.append(li(join(' > ', parts)))
        if not choices: return []
        boxtitle = coll.MATCH_CATEGORIES % word
        listing = multicolumn(choices, columns, c='matchbox', space=2)
        return [p, tablew(tr(td(strong(boxtitle), c='querybox')),
                          tr(td(listing)))]


    #Since we use the same endgame for both displaying items and displaying 
    #history items, we need to determine which one a given call is for. Lack of
    #index and query imply a history item view
    def endgame(self):
        if self.form.get('popuphandle', '') == '1':
            self.popuphandler()
        if self.form.get('item', ''):
            itemdisplay = self.itemdisplay()
            queryinfo = self.queryinfo(historyview=1)
            if coll.IMAGE_COLLECTION:
                return [self.taskbar(), p,
                        table(tr(td(itemdisplay)), c='display'), 
                        div(space(300), 
                        table(tr(td(queryinfo))))]
            else:
                return [self.taskbar(), p,
                        tablew(trt(td(queryinfo, width='50%'),
                                   td(nbsp, width='4%'),
                                   td(itemdisplay, width='46%', c='display')))]
        #normal endgame so insert item into store/database

        #check to see if we know the user. If no user specified, store
        # history in the session cookie. Otherwise, store it in the table

        if not self.session.__session__.hasValue('history'):
            self.session.history=[]
        userfacets = coll.facetlist[:]
        userattrs = coll.attrlist[:]
        if self.session.username == 'default':
            #store (item, timestamp) tuple in session
            self.session.history.append(
                (str(self.item), str(self.index), str(time())))
            idx = users.index(self.session.username)
            if users[idx].facets is not None:
                userfacets = users[idx].facets.split(', ')
            if users[idx].attrs is not None:
                userattrs = users[idx].attrs.split(', ')
        else:
            i = user_histories.new()
            user_histories[i].userid = str(users.index(self.session.username))
            user_histories[i].itemidx = str(self.index)
            user_histories[i].timestamp = str(time())
            user_histories[i].item = str(self.item)
            idx = users.index(self.session.username)
            if users[idx].facets:
                userfacets = users[idx].facets.split(', ')
            if users[idx].attrs:
                userattrs = users[idx].attrs.split(', ')

        #itemdisplay must be called before queryinfo
        itemdisplay = self.itemdisplay()
        print "IN ENDGAME"
        print userfacets
        queryinfo = [self.queryinfo(userfacets, userattrs)]

        if coll.IMAGE_COLLECTION:
            return [self.taskbar(), p, table(tr(td(itemdisplay)), c='display'),
                    div(space(300), table(tr(td(queryinfo)), c='info'))]
        else:
            return [self.taskbar(), p, table(trt(td(queryinfo, width=str(int(users[idx].endgame_facet_col_width)-2)+'%', c='info'),
                                      td(nbsp, width='4%'),
                                      td(itemdisplay, width=str(int(users[idx].endgame_item_col_width)-2)+'%'), c='display'))]

    def logoutwindow(self):
        self.session.username='default'
        name = self.__class__.__name__
        return [p, tablew(trt(td("You have been successfully logged out.")),
                          trt(td(nbsp)),
                          trt(td(link(name, "Return to ", name))))]

    #returns (timestamp, item, id, favorites)-tuple of history items
    def historyitems(self):
        i = users.index(self.session.username)
        currenthistory = []
        for x in user_histories.keys():
            x = int(x)
            if str(user_histories[x].userid) == str(users.index(self.session.username)):
                currenthistory.append((user_histories[x].timestamp,
                                       user_histories[x].item,
                                       user_histories[x].id,
                                       user_histories[x].favorites))
        currenthistory.sort()
        currenthistory.reverse()

        return currenthistory 

    #Looks through search table returning searches saved for current user
    def searchitems(self):
        i = users.index(self.session.username)
        currenthistory = []
        for x in user_history_searches.keys():
            x = int(x)
            if str(user_history_searches[x].userid) == \
               str(users.index(self.session.username)):
                currenthistory.append((user_history_searches[x].timestamp,
                                       user_history_searches[x].id,
                                       user_history_searches[x].query,
                                       user_history_searches[x].facetgroup,
                                       user_history_searches[x].searchname))
        currenthistory.sort()
        currenthistory.reverse()
        return currenthistory 

    #displays first <numitems> from history
    def historypreview(self, numpreviews=3):
        result=[]
        count=0
        i=0
        tempitems=[]
        userid = users.index(self.session.username)

        if userid==0:
            if self.session.__session__.hasValue('history'):
                tempitems = [row[0] for row in self.session.history]
                if len(tempitems) > numpreviews:
                    tempitems = tempitems[:numpreviews]
        else:
            tempitems = db.listhistory(uid=userid, limit=(0, numpreviews))

        if coll.IMAGE_COLLECTION:
            result = [[tr(tdc(listhistory([x], self.query, self.offset, 
                              link=self.link))), 
                       tr(tdc(nbsp))]
                         for x in tempitems]

        else:
            result = [[tr(tdc(listhistory([x], self.query, self.offset, 
                              link=self.link, imageonly=1)))]
                          for x in tempitems]

        return tablew(tr(tdc(strong(coll.RECENTLY_VIEWED_ITEMS))),
                      tr(tdc(link(self.__class__.__name__ + '?history=1',
                                  'Go to %s History' %
                                  coll.ITEM_NOUN.capitalize())),
                         c='historylink'), 
                      tr(td(nbsp)), result, c='historybox')

    #takes history items and categorizes them by group
    def grouphistorygame(self, mini=None, imageonly=None, checkboxes=None, 
                         counter=None, perrow=coll.ITEMS_PER_HISTORY_ROW,
                         limit=None):
        groups, result = [],  []
        currenthistory = self.historyitems()
        for timestamp, item, id, favorites in currenthistory:
            entrytime = localtime(float(timestamp))
            if (entrytime[0], entrytime[1], entrytime[2]) not in groups:
                groups.append((entrytime[0], entrytime[1], entrytime[2]))
        if counter is None: counter=0

        for year, month, day in groups:

            groupitems = []
            groupids = []
            count = 0
            for timestamp, item, id, favorites in currenthistory:
                entrytime = localtime(float(timestamp))
                if ((year, month, day) == 
                    (entrytime[0], entrytime[1],entrytime[2]) and item 
                        not in groupitems and favorites=='0'):
                    groupitems.append(item)
                    groupids.append(id)
                    count = count+1
            if not mini:
                result += tablew(tr(td(strftime("%b, %d %Y ", 
                                     (year, month, day, 0, 0, 0, 0, 0, 0)), 
                                    cls('count', count)), c='historygroup'),
                                 tr(td(nbsp, c='historyitem')),

                                 tr(td(listhistory(
                                  groupitems, self.query, self.offset, 
                                  link=self.link, perrow=perrow, 
                                  user=self.session.username, mini=mini, 
                                  imageonly=imageonly, checkboxes=checkboxes, 
                                  ids=groupids, limit=limit)), c='historyitem'), 
                                 tr(td(nbsp)))
            else:

                historytable=listhistory(
                                  groupitems, self.query, self.offset, 
                                  link=self.link, user=self.session.username, 
                                  mini=mini, imageonly=imageonly, perrow=1, 
                                  checkboxes=checkboxes, ids=groupids, 
                                  counter=counter, limit=limit)
                result += tablew(
                                 tr(td(historytable), 
                                   c='historyitem'))     
                counter=counter+len(groupitems)
            if limit:
                limit-=len(groupitems)

        if len(groups) == 0: 
            result+=tr(td(coll.HISTORY_EMPTY), c='historyitem')
        elif mini and (not self.form.get('historyfavoritelimit', '') or
                       (self.form.get('historyfavoritelimit', '') and \
                        not (int(self.form.get('historyfavoritelimit', '')) == 200))):
            result+=tablew(tr(td(self.link('Show All', historyfavoritelimit=200, manage=self.manage))), c='historyitem')
        return tablew(trt(td(result, width='100%')))

    #retrieves saved history items
    def historyfavorites(self, manage=None, perrow=coll.ITEMS_PER_HISTORY_ROW):
        i=1
        groups, result, favoriteitems = [], [], []
        for i in user_history_groups.keys():
            i=int(i)
            if str(user_history_groups[i].userid) == \
               str(users.index(self.session.username)):
                groups.append((user_history_groups[i].timestamp, 
                               user_history_groups[i].groupname, i))
        groups.sort()
        groups.reverse()
        gcount, counter = 0, 0
        for gtime, g, gid in groups:
            if manage:

                result+=tr(td(g, c='favoritegroup'))
                result+=tr(td(input(type='image', name='renamegroup'+str(gid),
                                    src=coll.RENAME_GROUP_SRC, onclick="setscrollxy(this.form); this.form.submit()"),
                              input(type='image', name='copy' + str(gid), 
                                    src=coll.COPY_HERE_SRC, onclick="setscrollxy(this.form); this.form.submit()"),
                              input(type='image', name='delimages'+str(gid), 
                                    src=coll.DELETE_SELECTED_SRC, onclick="setscrollxy(this.form); this.form.submit()"),
                              input(type='image', name='delgroup' + str(gid), 
                                    src=coll.DELETE_GROUP_SRC, onclick="setscrollxy(this.form); this.form.submit()"),


                                     c='favoritegroup'))

                result+=tr(td(nbsp, c='favoriteitem'))
                gcount = gcount+1
            else: result+=tr(td(g, c='favoritegroup'))
            favoriteitems=[]
            favoriteids=[]

            for j in user_histories.keys():
                j=int(j)
                if str(user_histories[j].userid) == \
                 str(users.index(self.session.username)) and \
                 user_histories[j].favorites and \
                 str(gid) == str(user_histories[j].groupid) and \
                 user_histories[j].item:
                    favoriteitems.append(user_histories[j].item)
                    favoriteids.append(j)
            if len(favoriteitems) > 0:
                result+=tr(td(listhistory(favoriteitems, self.query, 
                              self.offset, link=self.link, perrow=perrow, 
                              manage=manage, ids=favoriteids, counter=counter),
                           c='favoriteitem'))
                counter=counter+len(favoriteitems)
            if len(favoriteitems) == 0: result+=tr(td(coll.HISTORY_EMPTY), 
                                                   c='favoriteitem')
            result+=tr(td(nbsp))
        linkloc = self.__class__.__name__+"?"
        if self.form.get('q', ''):
            linkloc+="q="+self.form.get('q', '')
            if self.form.get('group', ''):
                linkloc+="&group="+self.form.get('group', '')
            linkloc+="&"
        if self.form.get('words', ''):
            linkloc+="words="+self.form.get('words', '')+"&"
        if self.form.get('sort', ''):
            linkloc+="sort="+self.form.get('sort', '')+"&"
        if coll.IMAGE_COLLECTION:
            savedwidth='78%'
            historywidth='18%'
        else:
            savedwidth='58%'
            historywidth='38%'

        #counter=0

        if manage:
            if self.task:
                linkloc+='task=%s&manage=1' % self.task
            else:
                linkloc+='manage=1'
            result = tablew(trt(td(
                tablew(
                    trt(td('Saved Images and Groups', 
                           c='title', width=savedwidth), 
                        td(nbsp, width='4%'), 
                        td(coll.RECENTLY_VIEWED_ITEMS,
                           c='title', width=historywidth))),
                postform(
                tablew(trt(td(nbsp, width=savedwidth), td(nbsp, width='4%'), 
                           td(coll.HISTORY_MOST_RECENT, width=historywidth)),
                       trt(td(tablew(
                        trt(td(input(type='text', name='newgroupname', 
                                   value='New Group', size='30'), c='favoritegroup')),

                        trt(td(input(type='image', name='copy' + str(-1), 
                                    src=coll.COPY_HERE_SRC, onclick="setscrollxy(this.form); this.form.submit()"),
                               input(type='hidden', name='task', value=self.form.get('task', '') or None),
                              ), c='favoritegroup'),
                        trt(td(nbsp)),
                        trt(td(input(type='hidden', name='managesave', 
                                   value='1'),
                              input(type='hidden', name='xposition', value='0'),
                              input(type='hidden', name='yposition', value='0'))),
                        trt(td(tablew(result, c='sectionheader'), width=savedwidth)), c='sectionheader')),
                           td(tablew(trt(td(nbsp))), width='4%'),
                td(tablew(trt(td(self.grouphistorygame(
                               mini=1, imageonly=1, checkboxes=1, 
                               counter=counter, perrow=perrow, limit=int(self.form.get('historyfavoritelimit', '') or coll.HISTORY_FAVORITE_ITEM_LIMIT)), 
                              width=historywidth)))))), action=linkloc))))





            return result
        else: 
            return tablew(trt(td(tablew(

                trt(td(coll.HISTORY_SAVED_ITEMS, c='title')),

                trt(postform(result, action=linkloc+'manage=1'))), 
               width=savedwidth)))

    #View of items in history only (does not include saved)
    def historygame(self):
        return tablew(tr(td(nbsp)), tr(td(nbsp)), tr(td(nbsp)), tr(td(self.grouphistorygame())))

    def logoutpage(self):
        self.session.username='default'
        return tablew(tr(td(nbsp)),
                      tr(td(nbsp)),
                      tr(tdc(
            table(#tr(td(nbsp)),
                  #tr(td(nbsp)),
                  tr(tdc('You have been successfully logged out of ', self.__class__.__name__+'.')),
                  #tr(td(nbsp)),
                  tr(td(nbsp)),
                  tr(tdc(link(self.__class__.__name__, 'Start a new search.'))), c='background', width='50%'))))

    #Logout prompt
#    def logoutwindow(self):
#        #self.session.__session__.invalidate()
#        self.session.username='default'
#        
#        cookie = Cookie('username', 'default')
#        cookie.setPath('/')
#        self.response.addCookie(cookie)
#        
#        return self.loginbox(post=self.__class__.__name__)

    #The actual display of the login
    def loginbanner(self, post='', loginerror=None):
        action = post or self.__class__.__name__
        fieldrow = tr(td('Username ', input(type='text', name='username', 
                                            value='default', size=12)),
                      td('Password ', input(type='password', name='password',
                                            size=12)),
                      td(input(type='submit', value='Log In')))
        rows = [fieldrow,
                tr(td(self.link('Create a New Account', createaccount=1),
                      c='newaccount', colspan=3))]
        if loginerror:
            rows.insert(0, tr(td(loginerror, c='loginerror')))
        return postform(tablew(rows), action=action, c='login')

    def loginbox(self, post=''):
        return postform(table(
            tr(tdc(
            table(
                  tr(tdc(strong("LOG IN"))),
                  tr(td(nbsp)),
                  tr(tdc(
            table(

                        tr(tdc(tablew(tr(tdc(strong('USERNAME  '),
                              tr(tdc(input(type='text', name='username', 
                                    value=self.form.get('username', '') or 'default',size='20')))))))),

                        tr(tdc(tablew(tr(tdc(strong('PASSWORD  '),
                               tr(tdc(input(type='password', name='password',
                                     size='20')))))))),


                        tr(tdc(input(type='image', src=coll.LOGIN_SRC))),
                          width='60%', c='loginbg'))),
                      width='100%'))),
            tr(td(nbsp)),
            tr(tdc('You must be logged in to utilize History and Setting features. This will allow you to customize the appearance of your browsing experience. Additionally, you will be able to take advantage of features such as history logging and item/search saving.*', width='50%')),
                     width='100%'), action=post or self.__class__.__name__)

    def loggedinbanner(self):
        if self.session.username == 'default':
            return []
        return tablew(tr(td('You are currently logged in as', ' ',
                            strong(self.session.username)), c='loginheader'), c='loginbg')

    #Display for when user is already logged in
    def loggedinbox(self, name='default'):
        classname = self.__class__.__name__
        return tablew(tr(td('Welcome to ', classname, ' ', strong(name), '!'),
                         td(small('If this is not you, please ',
                                  link(classname + '?logout=1',
                                       'click here', '.'))),
                         c='loginheader'))


    def helpgame(self):
        result = []
        returnlink = tablew(tr(td(self.link(coll.HELP_RETURN_MY_FLAMENCO, manage=1))))
        result+=tr(td(nbsp))
        result+=tr(tdw(coll.HELP_HISTORY_DESCRIPT))
        result+=tr(td(nbsp)), tr(td(nbsp)), tr(td(nbsp))
        result = tablew(result)

        saveditems=tablew(tr(td(coll.HISTORY_SAVED_ITEMS), c='title'),
                          tr(td(nbsp)),
                          tr(td(nbsp), c='favoritegroup'),
                          tr(td(coll.HELP_GROUP_NAME), c='favoritegroup'),
                          tr(td(nbsp), c='favoritegroup'),
                          tr(td(nbsp), c='favoriteitem'),
                          tr(td(nbsp), c='favoriteitem'),
                          tr(td(nbsp)),
                          tr(td(coll.HELP_SAVE_DESCRIPT)),
                          tr(td(nbsp)), tr(td(nbsp)))

        savedsearches=tablew(tr(td(coll.HISTORY_SEARCH_SAVED), c='title'),
                             tr(td(nbsp)),
                             tr(td(nbsp), c='searchname'),
                             tr(td(coll.HISTORY_SEARCH_NAME), c='searchname'),
                             tr(td(nbsp), c='searchname'),
                             tr(td(nbsp), c='searchbody'),
                             tr(td(nbsp), c='searchbody'),
                             tr(td(nbsp)),
                             tr(td(coll.HELP_SEARCH_DESCRIPT)),
                             tr(td(nbsp)), tr(td(nbsp)))

        history=tablew(tr(td(coll.HISTORY_ITEM_HISTORY), c='title'),
                       tr(td(nbsp)),
                       tr(td(coll.HISTORY_DATE_VIEWED), c='historygroup'),
                       tr(td(nbsp), c='historyitem'),
                       tr(td(nbsp), c='historyitem'),
                       tr(td(nbsp)),
                       tr(td(coll.HELP_HISTORY)),
                       tr(td(nbsp)), tr(td(nbsp)))
        return tablew(tr(td(nbsp)), tr(td(returnlink)), tr(td(nbsp)), 
                      tr(td(result)), tr(td(saveditems)), 
                      tr(td(savedsearches)), tr(td(history)), 
                      tr(td(returnlink)))

    #manage=1 means view saved searches
    #manage=2 means view saved items
    #manage=3 means view items history
    #manage=4 means edit options
    #session vars for editoptions must be loaded on every managegame section
    # not equal to 4, in order to "trick" the user into not seeing
    # changes in uncommit category ordering

    def managegame(self):
        print "MANAGEGAME"
        #print self.session.history
        #print self.session.username
        linkloc = self.__class__.__name__+"?"
        helpheader = [coll.HELP_HEADER, link(linkloc+'help=1', 'here.')]

        if self.session.__session__.hasValue('username'):
            userid=users.index(self.session.username)
        else:
            userid=-1
        if self.form.get('q', ''):
            linkloc+="q="+self.form.get('q', '')
            if self.form.get('group', ''):
                linkloc+="&group="+self.form.get('group', '')
            linkloc+="&"
        if self.form.get('words', ''):
            linkloc+="words="+self.form.get('words', '')+"&"
        if self.form.get('sort', ''):
            linkloc+="sort="+self.form.get('sort', '')+"&"
        if self.form.get('index', ''):
            linkloc+="index="+self.form.get('index', '')+"&"
        if self.form.get('item', ''):
            linkloc+="item="+self.form.get('item', '')+"&"
        if self.form.get('task', ''):
            print 'TASK DETECTED IN MANAGEGAME'
            linkloc+="task="+self.form.get('task', '')+"&"
        linkloc+='manage='

        #if self.form.get('username', ''):
        #    self.session.username=self.form.get('username', '')
        username=self.form.get('username', '')
        password=self.form.get('password', '')
        if username and not self.form.get('createaccount', ''):
            idx=users.index(username)
            if not users[idx].password == password:
                loginerror=' *Invalid Username/Password pair. Please try again'
                log.log(self, 'login attempt', loginerror, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                return self.notloggedin(post=linkloc+'1', loginerror=loginerror)
        if not self.session.__session__.hasValue('username') or \
            str(self.session.username) == 'default':

            log.log(self, 'loginwindow', self.task, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
            return self.notloggedin(post=linkloc+'1&managestart=1')

        print self.session.username

        handleresult = []
        if self.form.get('managesave', ''):
            manage=1       
            handleresult = self.managehandler()
            if not handleresult == []:
                return handleresult
        elif self.form.get('managesearch', ''):
            manage=2
            handleresult = self.managehandler()
            if not handleresult == []:
                return handleresult

        elif self.form.get('popuphandle', ''):
            self.searchhistory=None
            self.popuphandle=None



            #handling a search save, return to middlegame
            if self.searchname:
                i = user_history_searches.new()
                user_history_searches[i].searchname = self.searchname
                user_history_searches[i].userid = str(
                    users.index(self.session.username))
                user_history_searches[i].timestamp = str(time())

                user_history_searches[i].query = str(self.query)
                user_history_searches[i].facetgroup=str(self.group)
                log.log(self, 'searchsave', 'id=%s' % i, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                return div(self.middlegame(), c='middlegame');
            #handling a group rename, return to managegame, group view
            elif self.form.get('gname', ''):
                gid = int(self.form.get('gid', ''))
                oldname=user_history_groups[gid].groupname
                user_history_groups[gid].groupname = self.form.get('gname', '')

                self.manage=1
                log.log(self, 'group rename', 'id=%s, old=%s, new=%s' % (gid, oldname, self.form.get('gname', '')), userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

            #handling a search rename, return to managegame, search view
            elif self.form.get('sname', ''):
                sid = int(self.form.get('sid', ''))
                user_history_searches[sid].searchname = self.form.get(
                    'sname', '')
                self.manage=2
                log.log(self, 'search rename', 'id=%s' % sid, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)


            #handling a new group, return to managegame, grouped view
            elif self.form.get('newgroupname', ''):
                i = user_history_groups.new()
                user_history_groups[i].timestamp = str(time())
                user_history_groups[i].userid = str(
                    users.index(self.session.username))
                user_history_groups[i].groupname = self.form.get(
                    'newgroupname', '')
                self.manage=1
                log.log(self, 'new group', 'id=%s' % i, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)


            #handling saved item, return to endgame
            else:
                if self.form.get('cancelbutton', ''):
                    old = int(max(user_histories.keys()))
                    i = user_histories.new()
                    user_histories[i] = user_histories[old]
                    user_histories[i].favorites = str(1)
                    if self.form.get('groupname', '') and \
                           self.form.get('groupname', '')=='newname' and \
                           self.form.get('savetogroupname', ''):
                    #return self.form.get('groupname', '')
                        j = user_history_groups.new()
                        user_history_groups[j].timestamp = str(time())
                        user_history_groups[j].userid = str(user_histories[i].userid)
                        user_history_groups[j].groupname = self.form.get(
                          'savetogroupname', '')
                        user_histories[i].groupid = j
                    else:
                        user_histories[i].groupid=user_history_groups.index(str(
                            self.form.get('groupname', '')))
                    log.log(self, 'save item', 'historyid=%s, groupid=%s' % (i, user_histories[i].groupid), userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                return div(self.endgame(), c='endgame');



        #load necessary session variables from user table to support
        # interactive edit options page
        #also need to load if this is the startup managegame page and user
        # has it configured to this page
#        if str(self.manage) != '5' or self.form.get('username', ''):
        if not self.form.get('changefacets', ''):        
            print "MANAGE !=5"
            print self.session.username

            idx = users.index(self.session.username)
            self.session.facets = users[idx].facets

            self.session.sortby = users[idx].sortby
            self.session.caps = users[idx].caps
        if not self.form.get('changeattrs', ''):
            idx = users.index(self.session.username)
            self.session.attrs=users[idx].attrs

        if str(self.manage) != '6':
            idx = users.index(self.session.username)
            self.session.attrs = users[idx].attrs

        #handle different managegame sections/cases

        if str(self.manage)=='2':
            result = td(self.searchsaves(manage=1))
            viewstr = self.viewbar(searches=0, linkloc=linkloc)
            helpheader= 'The Saved Searches section allows you to re-run searches you have found interesting. You will need to save these searches before you can run them from this section. Save searches by using the icons in the top right after performing a search.'
        elif str(self.manage)=='3':
            result = self.grouphistorygame()
            result = tablew(tr(td(coll.RECENTLY_VIEWED_ITEMS, c='title')),
                            tr(td(nbsp)),
                            tr(td(result)))
            viewstr = self.viewbar(history=0, linkloc=linkloc)
            helpheader= 'The Recently Viewed Images section allows you to view images you have have recently looked at, organized by date. The system will delete these images after a while so you need not manage them. To keep images you find interesting, refer to the Saved Images and Groups section.'
        elif str(self.manage)=='4':
            if self.help:
                result = self.managehelp()
            else:
                result = self.editoptions(linkloc=linkloc)
            viewstr = self.viewbar(options=0, linkloc=linkloc)
            helpheader='The Edit Options section allows you to configure the appearance of various sections of the interface, including Display Layout, History and Settings Starting Page and other Miscellaneous Settings. Changes take place immediately.'

        elif str(self.manage)=='5':
            if self.help:
                result = self.managehelp()
            else:
                if not self.session.__session__.hasValue('facets'):
                    id = users.index(self.session.username)
                    self.session.facets=users[id].facets
                result = self.changefacets(linkloc=linkloc)
            viewstr = self.viewbar(facets=0, linkloc=linkloc)
            helpheader='The Edit Visible Categories section allows you to change display features of the categories while browsing. More detailed instructions are below.'

        elif str(self.manage)=='6':
            if self.help:
                result=self.managegamehelp()
            else:

                if not self.session.__session__.hasValue('attrs'):
                    id = users.index(self.session.username)
                    self.session.attrs=users[id].attrs
                result=self.changeattrs(linkloc=linkloc)
            viewstr=self.viewbar(attrs=0, linkloc=linkloc)
            helpheader='The Edit Visible Attributes section allows you to change which attributes are shown while browsing. Attributes are item properties that are not organized into categories. These are displayed in the Item Display page.'
        elif str(self.manage)=='7':
            result=self.tasks()
            viewstr=self.viewbar(tasks=0, linkloc=linkloc)
            helpheader='This section allows you to select a task that you plan to complete from "Available Tasks." First select a task to attempt, and then choose the interface you wish to use by clicking on either the Use Denali or the Use Shasta button. The first few tasks will tell you which interface to use, allowing you to familiarize yourself with both. After that, you will be free to choose whichever interface you like to complete the tasks. Alternatively, you can view "Completed Tasks." Once you finish a task, you will need to return to this page to select a new task. Should you finish all the available tasks, wait for more tasks to be released. New tasks tend to be released on Sunday night, so check back then. '
        else: #if self.manage=='1':
            result = td(self.historyfavorites(manage=1)) 
            viewstr = self.viewbar(saved=0, linkloc=linkloc)
            helpheader='The Saved Images and Groups section allows you to save images you find interesting while browsing, so you can refer to them later. You can organize these saved images into groups. Create a new group by specifying the desired group name and clicking the "Copy Selected Here" icon below. Any images that have their corresponding checkboxes checked will be copied into this new group. Save images while browsing by using the Save Image button at the top right of the screen at the appropriate time.'
        if self.form.get('task', ''):
            print 'task detected in manage'
        return table(self.taskbar(),
                  trt(td(nbsp)), 
                  trt(td(tablew(trt(td(table(tr(td(helpheader, c='introbox'))),
                                       width='60%'),
                                    td(tablew(tr(td(nbsp, width='5%'))), width='40%'))))),
                  tr(td(tablew(trt(td(nbsp))))),
                  tr(td(tablew(trt(td(nbsp)), tr(td(nbsp)),
                               tr(td(viewstr), c='viewbg'), 
                               trt(td(nbsp))), tr(result, td(nbsp)))))

    def managehelp(self):
        idx = users.index('default')
        return table(
                     tr(td('Display Options Help', colspan=4, c='title')),
                     tr(td(nbsp)),
                   table(
                     tr(td(nbsp, width='3%'), td(nbsp, width='60%'), td(nbsp, width='20%'), td(nbsp, width='17%')),

                     trt(td('Opening Page Layout',
                           colspan=2, c='sectionheader'),
                         td(strong('default value'), colspan=2)),
                     tr(td(nbsp),                       
                        td(strong('Number of terms to display per category')),
                        td(users[idx].opening_facet_terms,
                                 size='1')),

                     tr(td(nbsp*2),
                        td(strong('Number of columns')),
                        td(users[idx].opening_facet_columns,
                                 size='1')),
                     tr(td(nbsp*2),
                        td(strong('Number of columns to display per category')),
                        td(users[idx].opening_facet_columns)),


                     tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)),
                     tr(td('Search Results Page Layout', colspan=4, c='sectionheader')),
                     tr(td(nbsp*2), 
                        td(strong('Search Results Category Column Width %')),
                        td(users[idx].facet_column_width)),


                     tr(td(nbsp*2),
                        td(strong('Search Results Item Column Width %')),
                        td(users[idx].item_column_width)),


                     tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)),
                     tr(td('Item Display Layout', colspan=4, c='sectionheader')),
                     tr(td('General Preferences', colspan=4, c='sectionheader')),
                     tr(td(nbsp*2),
                        td(strong('Remember my username and password when I login'))),


                     tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)),
                     tr(td(input(type='image', src=coll.SUBMIT_SRC, name='changeoptions'), nbsp,
                           input(type='image', src=coll.CANCEL_SRC), colspan=4)),
                     tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)), width='70%'),
                 tr(td(
                 table(
                     trt(td(a(name='categories'), width='40%'), td(nbsp, width='20%'), td(nbsp, width='40%')),
                     trt(td('Displayed Categories', c='title'), td(nbsp), td('Removed Categories', c='title')),
                     trt(td('(click on the arrows to change display order of categories)')),
                     trt(td(nbsp), td(nbsp), td(nbsp)),
                     #trt(td(matrix), td(nbsp), td(missingmatrix)),
                     trt(td(nbsp), td(nbsp), td(nbsp)),
                     width='70%'))))





    def viewbar(self, saved=1, searches=1, history=1, options=1, facets=1, attrs=1, editopts=0, tasks=1, linkloc=''):
        #bar = [td('View: ', c='viewbg')]
        bar = [td(nbsp*4, c='viewbg')]
        bottom = ''
        buttons=[td(nbsp*4, c='viewbg')]

        if saved:
            bar+=tdc(link(linkloc+str(1), coll.SAVED_ITEMS_AND_GROUPS, style='text-decoration:none'), c='favoritebg')

        else:
            bar+=tdc(coll.SAVED_ITEMS_AND_GROUPS, c='favoritebg')
            bottom = 'favoritebg' 
        bar+=td(nbsp*2)

        if history:
            bar+=tdc(link(linkloc+str(3), coll.RECENTLY_VIEWED_ITEMS, style='text-decoration:none'), c='historybg')
        else:
            bar+=tdc(coll.RECENTLY_VIEWED_ITEMS, c='historybg')
            bottom='historybg'
        bar+=td(nbsp*2)



        if searches:
            bar+=tdc(link(linkloc+str(2), 'Saved Searches', style='text-decoration:none'), c='searchbg')
        else:
            bar+=tdc("Saved Searches", c='searchbg')
            bottom='searchbg'
        bar+=td(nbsp*2)

        if options:
            bar+=tdc(link(linkloc+str(4), 'Edit Options', style='text-decoration:none'), c='optionsbg')
        else:
            bar+=tdc("Edit Options", c='optionsbg')
            bottom='optionsbg'
        bar+=td(nbsp*2)
        if facets:
            bar+=tdc(link(linkloc+str(5), 'Edit Visible Categories', style='text-decoration:none'), c='facetsbg')
        else:
            bar+=tdc("Edit Visible Categories", c='facetsbg')
            bottom='facetsbg'
        bar+=td(nbsp*2)
        if attrs:
            bar+=tdc(link(linkloc+str(6), 'Edit Visible Attributes', style='text-decoration:none'), c='attrsbg')

        else:
            bar+=tdc("Edit Visible Attributes", c='attrsbg')
            if (not saved and not searches and not history and not options and not facets and not attrs):
                bottom=''
            else:
                bottom='attrsbg'
        bar+=td(nbsp*2)
        bar+=tdc(nbsp)

        bar+=tdc(nbsp, width='30%')
        idx=users.index(self.session.username)        

        if editopts:
            buttons+=[tdc(input(type='radio', name='myflamencostart', value='1', checked=users[idx].managegame_opening==1 and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()")),
                  td(nbsp*2),
                  tdc(input(type='radio', name='myflamencostart', value='3', checked=users[idx].managegame_opening==3 and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()")),
                  td(nbsp*2),
                  tdc(input(type='radio', name='myflamencostart', value='2', checked=users[idx].managegame_opening==2 and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()")),
                  td(nbsp*2),
                  tdc(input(type='radio', name='myflamencostart', value='4', checked=users[idx].managegame_opening==4 and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()")),
                  td(nbsp*2),
                  tdc(input(type='radio', name='myflamencostart', value='5', checked=users[idx].managegame_opening==5 and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()")),
                  td(nbsp*2),
                  tdc(input(type='radio', name='myflamencostart', value='6', checked=users[idx].managegame_opening==6 and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()")),
                  td(nbsp*2)]
            buttons+=[tdc(nbsp)]
            bottom=''
            return tr(td(tablew(tr(bar),
                                tr(buttons),
                            tr(td(nbsp, colspan=14), c=bottom),

                            c='editoptsviewbar')))
        return tr(td(tablew(tr(bar),
                            tr(td(nbsp, colspan=14), c=bottom),
                            c='viewbar')))

    #log actions from managegame here
    #handles responses to interaction with managegame
    def managehandler(self):
        if self.session.__session__.hasValue('username'):
            userid=users.index(self.session.username)
        else:
            userid=-1
        result = []
        if self.form.get('managesearch', ''):
            for i in user_history_searches.keys():
                if self.form.get('delsearch%s.x' % str(i), ''):
                    user_history_searches.__delitem__(int(i))
                    self.manage=2
                    log.log(self, 'delete search', 'id=%s' % i, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

                    return []
                elif self.form.get('renamesearch%s.x' % str(i), ''):
                    if self.form.get('xposition', ''):
                        xposition=self.form.get('xposition', '')
                    else:
                        xposition=300
                    if self.form.get('yposition', ''):
                        yposition=self.form.get('yposition', '')
                    else:
                        yposition=300
                    print "rename search"
                    print xposition
                    print yposition
                    log.log(self, 'rename search', self.task, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                    return self.renamesearchwindow(int(i), xposition, yposition)
            self.manage=2

        elif self.form.get('managesave', ''):
            #create group entry point
            #handle implicit creation of group through copy

            if self.form.get('createnewgroup') or \
               self.form.get('copy'+str(-1)+'.x', ''):
                i = user_history_groups.new()
                user_history_groups[i].timestamp = str(time())
                user_history_groups[i].userid = str(
                    users.index(self.session.username))
                user_history_groups[i].groupname = self.form.get(
                    'newgroupname', '')
                copyhereitems=[]
                if self.form.get('copy'+str(-1)+'.x', ''):
                    for j in range(len(user_histories)):
                        if self.form.get('checked'+str(j), ''):
                            old = int(self.form.get('checked'+str(j)))
                            x = user_histories.new()
                            user_histories[x]=user_histories[old]
                            #must be favorite if we're copying
                            user_histories[x].favorites = str(1)
                            user_histories[x].groupid = i
                            copyhereitems.append(user_histories[x].item)
                self.manage=1
                log.log(self, 'creategroup', 'gid=%s, gname=%s, copyhere=%s' % (i, user_history_groups[i].groupname, ', '.join(copyhereitems)), userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

                return []


            for i in user_history_groups.keys():
                copyhereitems=[]
                if self.form.get('copy'+str(i)+'.x', ''):
                    #check boxes not numbered by id, but counter

                    for j in range(len(user_histories)):
                        if self.form.get('checked'+str(j), ''):
                            old = int(self.form.get('checked'+str(j)))
                            x = user_histories.new()
                            user_histories[x]=user_histories[old]
                            #must be favorite if we're copying
                            user_histories[x].favorites = str(1)
                            user_histories[x].groupid = i
                            copyhereitems.append(user_histories[x].item)
                    log.log(self, 'copyhere', 'gid=%s, copyhere=%s' % (i, ', '.join(copyhereitems)), userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

                elif self.form.get('delimages'+str(i)+'.x', ''):
                    delhereitems=[]
                    for j in range(len(user_histories)): 
                        if self.form.get('checked' + str(j), '') and \
                           user_histories[int(self.form.get(
                               'checked'+str(j), ''))].favorites=='1' and \
                           i == user_histories[int(
                               self.form.get('checked' + str(j), ''))].groupid:
                            delhereitems.append(user_histories[int(self.form.get('checked'+str(j), ''))].item)
                            user_histories.__delitem__(self.form.get(
                             'checked' + str(j), ''))
                    log.log(self, 'delimages', 'gid=%s, delitems=%s' % (i, ', '.join(delhereitems)), userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

                elif self.form.get('delgroup'+str(i)+'.x', ''):

                    user_histories.deletegroup('groupid', i)
                    user_history_groups.__delitem__(int(i))
                    log.log(self, 'delgroup', 'gid=%s' % i, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                elif self.form.get('renamegroup%s.x' % str(i), ''):
                    xposition=self.form.get('xposition', '') or 0
                    yposition=self.form.get('yposition', '') or 0
                    log.log(self, 'renamegroup', 'gid=%s' % i, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

                    return self.renamegroupwindow(int(i), xposition, yposition)

        self.manage = 1
        return []

    #returns saved searches from current user's history
    def searchsaves(self, manage=None):
        i=0      
        savedsearches = self.searchitems()

        result = []
        for timestamp, id, query, facetgroup, searchname in savedsearches:
            self.query = Query(db, text=query)
            self.group = facetgroup
            entrytime = localtime(float(timestamp))
            entrydate = strftime("%b, %d %Y ", (
                            entrytime[0], entrytime[1], entrytime[2], 
                            0, 0, 0, 0, 0, 0))
            searchlink = self.__class__.__name__+"?q="+str(self.query)
            if self.group:
                searchlink += "&group="+str(self.group)
            if self.form.get('task', ''):
                searchlink+="&task="+str(self.form.get('task', ''))
            if manage:
                header = td(
                            input(type='image', src=coll.DELETE_SEARCH_SRC, name='delsearch' + str(id), onclick="setscrollxy(this.form); this.form.submit()"), 


                            input(type='image', src=coll.RENAME_SEARCH_SRC, name='renamesearch' + str(id), onclick="setscrollxy(this.form); this.form.submit()"))

                i=i+1
            else: header=td(nbsp)
            result += tablew(tr(td(link(searchlink, searchname), 
                                   c='searchname'),
                                tdr(link(searchlink, coll.HISTORY_SEARCH_RUN), 
                                    c='searchname')),
                             tr(td(entrydate, c='date'), td(nbsp, c='date')),
                             tr(header, td(nbsp), c='searchname'),
                             tr(td(nbsp), td(nbsp), c='searchbody'),
                             c='sectionheader')
            words = [wordbox(word, self.link, path=0, button=0) 
                     for word in self.query.getwords()]
            terms = [termbox(term, self.link, path=0, button=0) 
                     for term in self.query.getterms()]
            result += tablew(trt(td(strong(coll.HISTORY_SEARCH_TERMS), 
                                    width='20%'), 
                                 td(strong(coll.HISTORY_SAMPLE+
                                            coll.ITEM_TYPE_PLURAL+':'), 
                                    width='80%'), c='searchbody'),
                             trt(td(nbsp, width='20%'), 
                                 td(nbsp, width='80%'), c='searchbody'),
                             trt(td(words, terms, width='20%'), 
                                 td(listitems(self.query, self.offset, 
                                               link=self.link, 
                                               sort=self.sortkeys,
                                               maxnumdisplay=3), 
                                    width='80%'), c='searchbody'))
            result += tablew(tr(td(nbsp)))
        result+=tablew(tr(td(input(type='hidden', name='xposition', value='0'),
                             input(type='hidden', name='yposition', value='0'),
                             input(type='hidden', name='managesearch',
                                   value='1',),
                             input(type='hidden', name='task', value=self.task))))
        if len(savedsearches)==0: 
            result+=tablew(tr(td(coll.HISTORY_EMPTY), c='searchbody'))
        return tablew(tr(td(coll.HISTORY_SEARCH_SAVED, c='title')), 
                      tr(td(nbsp)),
                      tr(td(coll.HISTORY_SEARCH_SAMPLE)), 
                      tr(td(nbsp)), 
                      postform(result, 
                               action=self.__class__.__name__+'?manage=2&task='+self.form.get('task', '')))

    #handle managegame logging here for response to windows
    #currently only handles searchsaves and favorite saves
    def popuphandler(self):
        if self.session.__session__.hasValue('username'):
            userid=users.index(self.session.username)
        else:
            userid=-1
        self.searchhistory=None
        self.popuphandle=None
        #handling a search save, return to middlegame
        print "in popuphandle"
        if self.searchname:
            print 'self.searchname'
        if self.form.get('submitbutton.x', ''):
            print 'submitbutton.x'
        if self.searchname and self.form.get('submitbutton.x', ''):
            i = user_history_searches.new()
            user_history_searches[i].searchname = self.searchname
            user_history_searches[i].userid = str(
                users.index(self.session.username))
            user_history_searches[i].timestamp = str(time())
            user_history_searches[i].sort = str(self.sort)
            #if self.words:
            #    user_history_searches[i].query = str(self.query)
            #else:
            #    user_history_searches[i].query = str(self.query)
            if self.__class__.__name__=='Floogle' and self.words:
                user_history_searches[i].query=' '.join(self.words)

            else:
                user_history_searches[i].query = str(self.query)
            user_history_searches[i].facetgroup=str(self.group)
            log.log(self, 'searchsave', 'id=%s' % i, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

        elif self.form.get('cancelbutton.x', ''):
            return []
        #handling a group rename, return to managegame, group view
        elif self.form.get('gname', ''):
            gid = int(self.form.get('gid', ''))
            oldname=user_history_groups[gid].groupname
            user_history_groups[gid].groupname = self.form.get('gname', '')
            user_history_groups[gid].timestamp = str(time())
            self.manage=1
            log.log(self, 'group rename', 'id=%s, old=%s, new=%s' % (gid, oldname, self.form.get('gname', '')), userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

            return div(self.managegame(), c='managegame')

        #handling a search rename, return to managegame, search view
        elif self.form.get('sname', ''):
            sid = int(self.form.get('sid', ''))
            user_history_searches[sid].searchname = self.form.get('sname', '')
            self.manage=2
            log.log(self, 'search rename', 'id=%s' % sid, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

            return div(self.managegame(), c='managegame')

        #handling saved image, return to endgame
        else:
            print 'SAVE IMAGE'
            old = int(max(user_histories.keys()))
            i = user_histories.new()
            user_histories[i] = user_histories[old]
            user_histories[i].favorites = str(1)
            if self.form.get('savetogroupname', '') and \
               self.form.get('groupname', '') and \
               str(self.form.get('groupname', ''))=='newname':
                j = user_history_groups.new()
                user_history_groups[j].timestamp = str(time())
                user_history_groups[j].userid = str(user_histories[i].userid)
                user_history_groups[j].groupname = self.form.get(
                    'savetogroupname', '')
                user_histories[i].groupid = j
            else:
                user_histories[i].groupid=int(self.form.get('groupname', ''))
            log.log(self, 'save item', 'historyid=%s, groupid=%s' % (i, user_histories[i].groupid), userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)

        return []

    def notloggedin(self, post='', creationerror='', loginerror=''):
        createpost=post
        if post.find('createaccount') == -1:
            if createpost.find(self.__class__.__name__)==len(createpost)-len(self.__class__.__name__):
                createpost+='?createaccount=1'
            else:
                createpost+='&createaccount=1'
        else:
            loc=post.find('&createaccount')
            if loc==-1:
                loc=post.find('createaccount')
                post=post[:loc]+post[loc+len('createaccount=1'):]
            else:
                post=post[:loc]+post[loc+len('&createaccount=1'):]

        if not loginerror:
            return [tablew(trt(tdc(nbsp)),

                           trt(tdc(tablew(tr(tdc(nbsp)),
                                   trt(td(self.loginbox(post=post), width='50%'),
                                       td(self.createaccountwindow(post=createpost, error=creationerror), width='50%')),
                                   tr(tdc(nbsp)),
                                          tr(td(nbsp)),
                                   tr(td(small(strong('*Disclaimer: ')),
                                         small('By creating an account, you acknowledge that your search history will be logged (unless you choose to turn this off). This information will be used strictly for research and will serve an educational purpose only.'), colspan=2)),
                                         tr(td(nbsp))))))]

        return [table(tr(tdc(nbsp)),

                          tr(tdc(tablew(tr(tdc(nbsp)),

                                   trt(tdc(nbsp)),
                                   trt(tdc(loginerror, c='loginerror')),
                                   trt(td(self.loginbox(post=post), width='50%'),
                                       td(self.createaccountwindow(post=createpost, error=creationerror), width='50%')),
                                   tr(tdc(nbsp)),
                                       tr(tdc(nbsp)),
                                       tr(tdc(strong('*Disclaimer: '),
                       'By creating an account, you acknowledge that your search history will be logged (unless you choose to turn this off). This information will be used strictly for research and will serve an educational purpose only.')),
                                       tr(td(nbsp))))))]

    #response for when user clicks save favorite from endgame
    #since done from endgame, image has already been saved, so find it, 
    #mark it, then return this endgame        
    def favesavehandler(self):
        print "FAVESAVEHANDLER"
        i = max(user_histories.keys())
        user_histories[i].favorites=str(1)
        if self.form.get('savetogroupname', ''):
             j = user_history_groups.new()
             user_history_groups[j].timestamp = str(time())
             user_history_groups[j].userid = str(self.session.username)
             user_history_groups[j].groupname = self.form.get(
                 'savetogroupname','')
             user_histories[i].groupid = j
        else: 
            user_histories[i].groupid = str(user_history_groups.index(
                self.form.get('groupname', '')))
        return self.endgame()

    def renamegroupwindow(self, groupid, xposition=0, yposition=0):
        currentgroups=[trt(td(coll.HISTORY_GROUPS_CURRENT)), tr(td(nbsp))]
        for i in user_history_groups.keys():
            i=int(i)
            if str(user_history_groups[i].userid) == str(users.index(
                self.session.username)):
                currentgroups+= tr(td(user_history_groups[i].groupname))
        currentgroups+=tr(td(nbsp))
        linkloc = self.__class__.__name__+"?"
        if self.form.get('q', ''):
            linkloc+="q="+self.form.get('q', '')
            if self.form.get('group', ''):
                linkloc+="&group="+self.form.get('group', '')
            linkloc+="&"
        if self.form.get('words', ''):
            linkloc+="words="+self.form.get('words', '')+"&"
        if self.form.get('sort', ''):
            linkloc+="sort="+self.form.get('sort', '')+"&"

        if self.form.get('task', ''):
            linkloc+="task="+self.form.get('task', '')+"&"
        headerinfo = [tr(td(nbsp)), tr(td(nbsp)), 
                      tr(tdc(coll.HISTORY_RENAME_GROUPS, c='title')), 
                      tr(td(nbsp)), tr(tdc(strong(coll.HISTORY_GROUPS_OLD))), 
                      tr(tdc(str(user_history_groups[groupid].groupname),
                             c='groupname')),
                      tr(td(nbsp)), tr(tdc(strong(coll.HISTORY_GROUPS_NEW)))]
        formcontents = [input(type='text', name='gname', size='30'), br, 
                        input(type='hidden', name='gid', value=groupid), br, 
                        input(type='submit', value='OK'),
                        input(type='hidden', name='task', value=self.form.get('task', '')),
                        input(type='hidden', name='popuphandle', value='1'),
                        input(type='hidden', name='xposition', value=xposition),
                        input(type='hidden', name='yposition', value=yposition)]
        formcontents = postform(formcontents, 
                  action=linkloc+'manage=1')
        return tablew(headerinfo, tr(tdc(formcontents)))


    def changeattrs(self, linkloc=''):
        idx=users.index(self.session.username)
        print "SELF SESSION ATTRS"

        userattrs = coll.attrlist
        if users[self.session.useridx].attrs is not None:
            userattrs = users[self.session.useridx].attrs.split(', ')
        print userattrs
        print "USERATTRS"
        i=0

        if len(userattrs)==0:
            for attr in db.attrlist:
                if self.form.get('addattr_%s.x' % attr, ''):
                    print "attr added"
                    userattrs.append(attr)
                    i=len(userattrs)

        while i < len(userattrs):
            attr = userattrs[i]
            print 'checkattrs'
            if self.form.get('moveup_attr_%s.x' % attr, ''):
                print 'moveup'
                oldidx = userattrs.index(attr)-1
                if oldidx >= 0:                      
                    oldattr = userattrs[oldidx]                   

                    userattrs[oldidx] = attr                     
                    userattrs[oldidx+1] = oldattr
                    i=len(userattrs) #break out
            elif self.form.get('movedown_attr_%s.x' % attr, ''):
                print 'movedown'
                oldidx = userattrs.index(attr)+1
                if oldidx < len(userattrs):
                    oldattr = userattrs[oldidx]

                    userattrs[oldidx] = attr
                    userattrs[oldidx-1] = oldattr
                    i=len(userattrs) #break out

            elif self.form.get('removeattr_%s.x' % attr, ''):
                userattrs.remove(attr)
                i=len(userattrs)
            else:
                for attr in db.attrlist:
                    if self.form.get('addattr_%s.x' % attr, ''):
                        print "attr added"
                        userattrs.append(attr)
                        i=len(userattrs)
            i=i+1

        print "session attrs"
        print self.session.attrs
        print userattrs
        self.session.attrs = ', '.join(userattrs)
        print self.session.attrs
        #now that attrs and sortby stuff should be correctly modified,
        # save if necessary
        #if self.form.get('changeattrs', ''):
        users[idx].attrs = ', '.join(userattrs)
        #elif self.form.get('cancelchangeattrs.x', ''):
        #    userattrs=users[idx].attrs.split(', ')

        if not userattrs==[]:
            attrlist=[]
            attrlist.append(tablew(tr(td(input(type='hidden', name='changeattrs', value='1'),
                                             input(type='hidden', name='xposition', value='0'),
                                             input(type='hidden', name='yposition', value='0'))))),
            for attr in userattrs:
                attrlist.append(tablew(tr(td(tablew(tr(td(tablew(
                    trt(td(strong(db.name(attr)), c='attrbox'), width='93%'),
                    trt(td(nbsp), c='attrbox'),
                    trt(
                        td('move attribute:', nbsp*3,
                           input(type='image', src=coll.ARROW_DOWN_SRC, name='movedown_attr_'+attr, onclick="setscrollxy(this.form); this.form.submit()"),
                           nbsp*3,
                           input(type='image', src=coll.ARROW_UP_SRC, name='moveup_attr_'+attr, onclick="setscrollxy(this.form); this.form.submit()"),
                           nbsp*10,
                           'hide attribute:', nbsp*3,
                           input(type='image', src=coll.RIGHT_ARROW_SRC, name='removeattr_'+attr, onclick="setscrollxy(this.form); this.form.submit()", alt='Hide Attribute'),
                           c='attrbox')),
                    c='attr_'+attr)))))),
                                       tr(td(nbsp))))

            result=attrlist
#            result = [tablew(tr(td(tablew(tr(td(tablew(
#                    trt(td(input(type='image', src=coll.ARROW_UP_SRC, name='moveup_attr_'+attr), width='7%'),
#                       td(strong(db.name(attr)), c='attrbox'), width='93%'),
#                    trt(td(nbsp),
#                        td(nbsp, c='attrbox')),
#                    trt(td(input(type='image', src=coll.ARROW_DOWN_SRC, name='movedown_attr_'+attr)),
#                       td(input(type='submit', value='Make Attribute Hidden', 
#                                name='removeattr_'+attr, c='attr_'+attr), c='attrbox'))))),
#                    c='attr_'+attr),
#                           tablew(tr(td(nbsp))))))
#                      for attr in userattrs]
        else:
            print 'result'
            result=[]
        button=[]

        matrix = button+[tablew(tr(td(nbsp)))]+result+button  
        missingattrs = []

        print "ATTRS"
        print db.attrlist
        for attr in db.attrlist:
            if attr not in userattrs: missingattrs.append(attr)
        print missingattrs

        missingmatrix = [table(
                    trt(td(nbsp, width='5%'),
                       td(strong(db.name(attr)), width='95%', c='attrbox')),

                    trt(td(nbsp),
                       td(input(type='image', name='addattr_'+attr, src=coll.LEFT_ARROW_SRC, alt='Show attribute', c='attrbutton2', onclick="setscrollxy(this.form); this.form.submit()"), nbsp*3, 'show attribute', c='attrbox')),
                    trt(td(nbsp), td(nbsp)),


                    c='attr_'+attr, width='90%')
                  for attr in missingattrs]

        return postform(#tablew(tr(td(

#                 tr(td(
                 tablew(
                     #tr(td(a(name='categories'), width='40%'), td(nbsp, width='20%'), td(nbsp, width='40%')),
                     tr(td('Visible Attributes', width='48%', c='title'), td(nbsp, width='4%'), td('Hidden Attributes', width='48%', c='title')),
                     tr(td('(Click on the up and down arrows to change display order of attributes or on right arrows to hide them. Changes take place immediately.)'),
                        td(nbsp), td('(Click on the left arrows to make attributes shown)')),
                     tr(td(nbsp), td(nbsp), td(nbsp)),
                     trt(td(matrix), td(nbsp), td(missingmatrix)),
                     tr(td(nbsp), td(nbsp), td(nbsp))), action=linkloc+'6')

    def changefacets(self, linkloc=''):
        print 'CHANGEFACETS'
        idx = users.index(self.session.username)

        userfacets = coll.facetlist[:]
        if users[self.session.useridx].facets is not None:
            userfacets = users[self.session.useridx].facets.split(', ')
        usersortby = ['name'] * len(userfacets)
        if users[self.session.useridx].sortby is not None:
            usersortby = users[self.session.useridx].sortby.split(', ')
        usercaps = ['none'] * len(userfacets)
        if users[self.session.useridx].caps is not None:
            usercaps = users[self.session.useridx].caps.split(', ')

        i=0

        if len(userfacets)==0:
            for facet in db.facetlist:
                if self.form.get('addfacet_%s.x' % facet, ''):
                    userfacets.append(facet)
                    usersortby.append('name')
                    usercaps.append('first word')
                    i=len(userfacets)

        while i < len(userfacets):
            facet = userfacets[i]

            if self.form.get('moveup_%s.x' % facet, ''):
                  oldidx = userfacets.index(facet)-1
                  if oldidx >= 0:                      
                      oldfacet = userfacets[oldidx]                   

                      userfacets[oldidx] = facet                     
                      userfacets[oldidx+1] = oldfacet
                      i=len(userfacets) #break out
            elif self.form.get('movedown_%s.x' % facet, ''):

                oldidx = userfacets.index(facet)+1
                if oldidx < len(userfacets):
                    oldfacet = userfacets[oldidx]

                    userfacets[oldidx] = facet
                    userfacets[oldidx-1] = oldfacet
                    i=len(userfacets) #break out

            elif self.form.get('removefacet_%s.x' % facet, ''):
                print 'remove facet: %s' % facet
                print 'CAPS2'
                print usercaps
                removeidx=userfacets.index(facet)
                userfacets.remove(userfacets[removeidx])
                usersortby.remove(usersortby[removeidx])
                usercaps.remove(usercaps[removeidx])
                print usercaps
                i=len(userfacets)
            else:
                for facet in db.facetlist:
                    if self.form.get('addfacet_%s.x' % facet, ''):
                        userfacets.append(facet)
                        usersortby.append('name')
                        usercaps.append('first word')
                        i=len(userfacets)
            i=i+1


        self.session.facets = ', '.join(userfacets)

        print "CHECK sortbys"
        for facet in userfacets:
            print facet
            if self.form.get('sortby_' + facet, ''):
                print "sortby for facet: " + facet + " " + self.form.get('sortby_' + facet, '')
                if str(self.form.get('sortby_' + facet, ''))=='number of items':
                    usersortby[userfacets.index(facet)] = 'count desc'
                else:
                    usersortby[userfacets.index(facet)] = str(
                        self.form.get('sortby_' + facet, ''))

        print usersortby


        self.session.sortby = ', '.join(usersortby)        
        self.session.caps=', '.join(usercaps)
        users[idx].facets = ', '.join(userfacets)
        users[idx].sortby = ', '.join(usersortby)
        users[idx].caps = ', '.join(usercaps)
        print "USERFACETS"
        print self.form.get('xposition', '')


        print userfacets
        if userfacets==[]:
            categorylist=[tablew(tr(td(nbsp)))]
        else:
            categorylist=[]
            categorylist.append(tablew(tr(td(input(type='hidden', name='changefacets', value='1'),
                                             input(type='hidden', name='xposition', value='0'),
                                             input(type='hidden', name='yposition', value='0'))))),                    
            for facet in userfacets:
                sortkey = str(usersortby[userfacets.index(facet)])
                sortlabels = {'name': 'name', 'count desc': 'number of items'}
                sortoptions = [option(sortlabels.get(value, value), value=value,
                                      selected=(sortkey == value or None))
                               for value in ['name', 'count desc']]
                categorylist.append(
                  tablew(tr(td(tablew(tr(td(tablew(
                   trt(td(nbsp),
                       td(strong(db.name(facet)), c='facetbox'), width='93%'),
                    trt(td(nbsp),
                        td('sort items by:', nbsp*3,
                           select(sortoptions, name='sortby_'+facet,
                                  onchange="setscrollxy(this.form); this.form.submit()"),
                           c='facetbox')),
                    trt(td(nbsp),
                        td('move category:', nbsp*3,
                           input(type='image', src=coll.ARROW_DOWN_SRC, name='movedown_'+facet, onclick="setscrollxy(this.form); this.form.submit()"),
                           nbsp*3,
                           input(type='image', src=coll.ARROW_UP_SRC, name='moveup_'+facet, onclick="setscrollxy(this.form); this.form.submit()"),
                           nbsp*10,
                           'hide category:', nbsp*3,
                           input(type='image', src=coll.RIGHT_ARROW_SRC, name='removefacet_'+facet, onclick="setscrollxy(this.form); this.form.submit()", alt='Hide Category'),

                           c='facetbox')),


                    c='facet_'+facet))), c='changefacetsbox'))),
                  tr(td(nbsp))))
                           #td(tablew(tr(td(nbsp)))))))))))                           
                   #                        td(input(type='submit', value='Make Category Hidden', 
#                                name='removefacet_'+facet, c='facet_'+facet), c='facetbox')),     

        buttons=[]
        matrix=buttons+[tablew(tr(td(nbsp)))]+categorylist+buttons             
        missingfacets = []

        for facet in db.facetlist:
            if facet not in userfacets:
                missingfacets.append(facet)

        missingmatrix = [table(
                    trt(td(nbsp, width='5%'),
                       td(strong(db.name(facet)), width='95%', c='facetbox')),

                    trt(td(nbsp),
                       td(input(type='image', src=coll.LEFT_ARROW_SRC, alt='Show category', name='addfacet_'+facet, onclick="setscrollxy(this.form); this.form.submit()", c='facetbutton2'), nbsp*3, 'show category', c='facetbox')),
                    trt(td(nbsp), td(nbsp)),


                    c='facet_'+facet, width='90%')
                  for facet in missingfacets]

        hi=0

        return postform(#tablew(tr(td(
                 tablew(
                     #trt(td(a(name='categories'), width='40%'), td(nbsp, width='20%'), td(nbsp, width='40%')),
                     trt(td('Visible Categories', width='48%', c='title'), td(nbsp, width='4%'), td('Hidden Categories', width='48%', c='title')),
                     tr(td('(Click on the up and down arrows to change display order of categories or on right arrows to hide them. Changes take place immediately.)'),
                        td(nbsp), td('(Click on the left arrows to make categories visible)')),
                     tr(td(nbsp), td(nbsp), td(nbsp)),
                     #tr(td(postform(input(type='image', src=coll.SUBMIT_SRC, name='changefacets'),
         #   input(type='image', src=coll.CANCEL_SRC), action=linkloc+'5'))),
          #           tr(td(nbsp), td(nbsp), td(nbsp)),
                     trt(td(matrix), td(nbsp), td(missingmatrix)),
                     tr(td(nbsp), td(nbsp), td(nbsp))), action=linkloc+'5')



#    def editoptions(self, linkloc=''):
#        idx=users.index(self.session.username)
#
#        if self.form.get('changeoptions.x', ''):
#            
#            users[idx].opening_facet_terms = int(self.form.get('openingfacetterms', ''))
#            users[idx].opening_facet_columns = self.form.get('openingfacetcols', '')
#            users[idx].opening_term_columns = self.form.get('openingtermcols', '')
#            
#            if self.form.get('rememberme', ''):
#                users[idx].remember='1'
#                
#            else:
#                users[idx].remember='0'
#                remembermebox = input('checkbox', name='rememberme')
#            #users[idx].middle_category_result = self.form.get('categoryresultratio', '')
#            ratio = str(self.form.get('categoryresultratio', ''))
#            
#            users[idx].facet_column_width = ratio[:ratio.find(':')]
#            users[idx].item_column_width = ratio[ratio.find(':')+1:]
#
#            ratio = str(self.form.get('categoryitemratio', ''))
#            
#            users[idx].endgame_facet_col_width = ratio[:ratio.find(':')]
#            users[idx].endgame_item_col_width = ratio[ratio.find(':')+1:]
#            
#
#        if str(users[idx].remember)=='1':
#            remembermebox = input(type='checkbox', name='rememberme',
#                                  checked=1)
#        else: remembermebox = input(type='checkbox', name='rememberme')
#        
#        return postform(
#            table(
#            tr(td('Display Options for %s' % self.session.username, colspan=4, c='title')), tr(td(nbsp))),
#            table(
#            tr(td(nbsp, width='3%'), td(nbsp, width='60%'), td(nbsp, width='20%'), td(nbsp, width='17%')),

#            tr(td(nbsp*2),
#               tdr('Opening Page Layout', nbsp*5, c='sectionheader'),
#                  c='sectionheader'),
#            tr(td(nbsp*2),                       
#               tdr(strong('Number of terms to display per category', nbsp*5)),
#               td(select([option(val, selected=(str(val)==str(users[idx].opening_facet_terms) and 'true' or None), value=val)
#                          for val in ['6', '8', '10', '12', '14', '16']], name='openingfacetterms'))),
#            

#            tr(td(nbsp*2),
#               tdr(strong('Number of columns', nbsp*5)),
#               td(select([option(val, selected=(str(val)==str(users[idx].opening_facet_columns) and 'true' or None), value=val)
#                          for val in ['1', '2', '3', '4']], name='openingfacetcols'))),
#            tr(td(nbsp*2),
#               tdr(strong('Number of columns to display per category', nbsp*5)),
#               td(select([option(val, selected=(str(val)==str(users[idx].opening_term_columns) and 'true' or None), value=val)
#                          for val in ['1', '2', '3', '4']], name='openingtermcols'))),


#            tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)),
#            tr(td(nbsp*2),
#               tdr('Search Results Page Layout', nbsp*5, c='sectionheader')),


#            tr(td(nbsp*2),
#               tdr(strong('Category Column Width:Results Column Width', nbsp*5)),
#               td(select([option(val, selected=(str(val)[:str(val).find(':')]==str(users[idx].facet_column_width) and \
#                                                str(val)[str(val).find(':')+1:]==str(users[idx].item_column_width) and 'true' or None), value=val)
 #                         for val in ['30:70', '60:40', '50:50', '40:60']], name='categoryresultratio'))),


 #           tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)),
 #           tr(td(nbsp*2),
 #              tdr('Item Display Layout', nbsp*5, c='sectionheader')),
 #            
 #           tr(td(nbsp*2),
 #              tdr(strong('Related Category Listing Width:Item Listing Width', nbsp*5)),
 #              td(select([option(val, selected=(str(val)[:str(val).find(':')]==str(users[idx].endgame_facet_col_width) and \
 #                                               str(val)[str(val).find(':')+1:]==str(users[idx].endgame_item_col_width) and 'true' or None), value=val)
 #                         for val in ['60:40', '50:50', '40:60']], name='categoryitemratio'))),
 #           tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)),
 #           tr(td(nbsp*2),
 #              tdr('General Preferences', nbsp*5, c='sectionheader')),
 #         
 #           tr(td(nbsp*2),
 #              tdr(strong('Remember my username and password when I login', nbsp*5)),
 #              td(remembermebox)),
 #           
 #           tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)),
 #           tr(td(nbsp*2),
 #              tdr(input(type='image', src=coll.SUBMIT_SRC, name='changeoptions'), nbsp),
 #              td(input(type='image', src=coll.CANCEL_SMALL_SRC))),
 #           tr(td(nbsp), td(nbsp), td(nbsp), td(nbsp)), width='85%'),
 #           action=linkloc+'4')




 # editoptions allows the user to change the Flamenco Layout for opening,
 # middle and endgames. Rather than offering the user a multitude of choices
 # for different viewing options, screenshots are used to provide the user
 # with a grouped selection of viewing options.
 # For reference:
 # 
 #  Opening game:
 #                                   option1    option2    option3
 #   items per category               12         20         10
 #   # of columns of categories        2          1          3
 #   #columns per category             2          3          1
 #
 #  Middlegame:
 #                                         option1    option2    option3
 #   Ratio of categories:search results     40:60      50:50      60:40
 #
 #  Endgame:
 #                                         option1    option2    option3
 #   Ratio of itemdisplay:itemlisting       40:60      50:50      60:40
 #
 #
 #  The option number for a given mode of interaction will be stored in
 #   the user table along with the specific values associated with each
 #   option. However, integrity is only maintained when changing these
 #   options through this function. That is, should the values of a given
 #   display attribute be changed without changing the option, the actual
 #   display achieved by the system will change accordingly; there is no
 #   integrity checking.
    def editoptions(self, linkloc=''):

        idx=users.index(self.session.username)
        print 'editoptions'
        if self.form.get('myflamencostart', ''):

            preview=self.form.get('myflamencostart', '')
            print preview
            users[idx].managegame_opening=str(preview)
        if self.form.get('rememberme', ''):
            users[idx].remember='1'
        else:
            users[idx].remember='0'
        if self.form.get('showpreviews', ''):
            users[idx].showpreviews='1'
        else:
            users[idx].showpreviews='0'
        if self.form.get('openingformat', ''):
            print 'openingformat'
            openingformat=self.form.get('openingformat', '')
            users[idx].display_opening_option=openingformat
            if openingformat=='1':
                users[idx].opening_facet_terms=12
                users[idx].opening_facet_columns=2
                users[idx].opening_term_columns=2
            elif openingformat=='2':
                users[idx].opening_facet_terms=20
                users[idx].opening_facet_columns=1
                users[idx].opening_term_columns=3

            else:
                users[idx].opening_facet_terms=10
                users[idx].opening_facet_columns=3
                users[idx].opening_term_columns=1

        if self.form.get('middleformat', ''):
            print 'middle'
            middleformat=self.form.get('middleformat', '')
            users[idx].display_middle_option=middleformat
            if middleformat=='1':
                users[idx].item_column_width=60
                users[idx].facet_column_width=40
            elif middleformat=='2':
                users[idx].item_column_width=50
                users[idx].facet_column_width=50
            else:
                users[idx].item_column_width=40
                users[idx].facet_column_width=60

        if self.form.get('endformat', ''):
            print 'end'
            endformat = self.form.get('endformat', '')
            users[idx].display_end_option=endformat
            if endformat=='1':
                users[idx].endgame_item_col_width=60
                users[idx].endgame_facet_col_width=40
            elif endformat=='2':
                users[idx].endgame_item_col_width=50
                users[idx].endgame_facet_col_width=50
            else:
                users[idx].endgame_item_col_width=40
                users[idx].endgame_facet_col_width=60

        if self.form.get('changeemail', ''):
            users[idx].email=self.form.get('newemail', '')
        passworderror=''

        if self.form.get('changepassword', ''):
            oldpass, newpass1, newpass2= '', '', ''

            if self.form.get('oldpass', ''):
                oldpass=self.form.get('oldpass', '')
            if self.form.get('newpass1', ''):
                newpass1=self.form.get('newpass1', '')
            if self.form.get('newpass2', ''):
                newpass2=self.form.get('newpass2', '')

            if oldpass=='':
                passworderror='Error: Enter old password'
            elif not oldpass==users[idx].password:
                passworderror="Error: Old password does not match records"
            elif (newpass1=='' or newpass2=='') or not (newpass1==newpass2):
                passworderror="Error: Re-enter new passwords"
            else:
                users[idx].password=newpass1
                passworderror='Password successfully changed'
        if self.form.get('emailpassword', ''):
            #send password
            passworderror='Email containing password sent to %s' % users[idx].email
            cmd='/usr/sbin/sendmail -fkevinli@sims.berkeley.edu ' % users[idx].email
            print cmd
            fd=os.popen(cmd, 'w', 16384)
            x=fd.write('Username= %s\nPassword= %s\n' % (users[idx].name, users[idx].password))
            print x
            r=fd.close()
            print 'Email containing password sent.'
            print r
        instructions = 'Select from the following representative screenshots to configure display options for your browsing experience.'

        submitbutton = td(
            input(type='hidden', name='xposition', value='0'),
            input(type='hidden', name='yposition', value='0'))


        openingoption=users[idx].display_opening_option
        middleoption=users[idx].display_middle_option
        endoption=users[idx].display_end_option
        return postform(tablew(tr(td(
            table(trt(td('Edit Options for %s' % self.session.username, colspan=3, c='title'))),


            table(tr(td(nbsp))),


            table(tr(td(submitbutton))),


            tablew(tr(td(nbsp)),
                  tr(td(nbsp)),
                  tr(td(nbsp)))))),


            tablew(tr(td(
            tablew(tr(td(strong('Set Starting View for History and Settings'), colspan=2)), width='80%', c='previewtable'),
            tablew(tr(td(self.viewbar(saved=0, searches=0, history=0, options=0, facets=0, attrs=0, editopts=1, tasks=None))), 
                   tr(td(nbsp))))),
                   width='80%', border='1', bordercolor='#000000'),
            tablew(tr(td(nbsp)), tr(td(nbsp)), tr(td(nbsp))),
            #tablew(tr(td(tablew(tr(td(strong('Miscellaneous Account Features'), colspan=2)),
                  #tr(tdc(input(type='checkbox', name='rememberme', checked=users[idx].remember=='1' and 'true' or None, onclick="setscrollxy(this.form); this.form.submit()"), width='10%'),
                    # td("Remember my username on this computer so I don't have to log in next time. (Requires Cookies)", width='80%')), c='previewtable'))),
                 # width='90%', border='1', bordercolor='#000000', c='previewtable'),

                  #      tablew(tr(td(nbsp)), tr(td(nbsp)), tr(td(nbsp))),
            tablew(tr(td(tablew(tr(td(strong('E-mail Address Information'), colspan=2)),
                               tr(td('Current e-mail address:  ', width='20%'), td(users[idx].email, width='80%')),
                               tr(td('New e-mail address:  ', width='20%'), td(input(type='text', name='newemail'), width='80%')),
                               tr(td(input(type='submit', name='changeemail', value='Change Email', onclick="setscrollxy(this.form); this.form.submit()"))), c='previewtable'))), border='1', bordercolor='#000000', width='80%', c='previewtable'),
                        tablew(tr(td(nbsp)), tr(td(nbsp)), trbl(td(passworderror, c='loginerror'))),

                        tablew(tr(td(tablew(tr(td(strong('Password Information'), colspan=2)),
                               tr(td('Old password:  ', width='20%'), td(input(type='password', name='oldpass'), width='80%')),
                               tr(td('New Password:  ', width='20%'), td(input(type='password', name='newpass1'), width='80%')),
                               tr(td('Re-type New Password:  ', width='20%'), td(input(type='password', name='newpass2'), width='80%')),
                               tr(td(input(type='submit', name='changepassword', value='Change Password', onclick="setscrollxy(this.form); this.form.submit()"))),
                               tr(td(input(type='submit', name='emailpassword', value='Email me my password', onclick="setscrollxy(this.form); this.form.submit()"))), c='previewtable'))), border='1', bordercolor='#000000', width='80%', c='previewtable'),

                        tablew(tr(td(nbsp)),
                               tr(td(nbsp))),
                        tablew(

            tr(td(tablew(tr(td(strong('Display Layout'))),
                        tr(td(nbsp)),
                        tr(td(instructions))), colspan=4)),
            tr(tdc(strong('Opening Page'), c='sectionheader'),
               tdc(tablew(
                         tr(tdc(img(coll.PREVIEW_OPENING1_SRC, width='200', height='126'))),
                         tr(tdc('3-column view')),
                         tr(tdc(input(type='radio', name='openingformat', value='1', checked='true' and openingoption==1 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')),
               tdc(table(tr(tdc(img(coll.PREVIEW_OPENING2_SRC))),
                         tr(tdc('1-column view')),

                         tr(tdc(input(type='radio', name='openingformat', value='2', checked='true' and openingoption==2 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')),
                   tdc(table(tr(tdc(img(coll.PREVIEW_OPENING3_SRC))),
                             tr(tdc('2-column view')),
                             tr(tdc(input(type='radio', name='openingformat', value='3', checked='true' and openingoption==3 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')), c='openingoptionbg'),

             tr(tdc(strong('Search Results'), c='sectionheader'),
                tdc(table(tr(tdc(img(coll.PREVIEW_MIDDLE1_SRC))),
                          tr(tdc('40% category listing : 60% result listing')),
                          tr(tdc(input(type='radio', name='middleformat', value='1', checked='true' and middleoption==1 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')),
                tdc(table(tr(tdc(img(coll.PREVIEW_MIDDLE2_SRC))),
                          tr(tdc('50% category listing : 50% result listing')),
                        tr(tdc(input(type='radio', name='middleformat', value='2', checked='true' and middleoption==2 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')),
                tdc(table(tr(tdc(img(coll.PREVIEW_MIDDLE3_SRC))),
                          tr(tdc('60% category listing : 40% result listing')),
                          tr(tdc(input(type='radio', name='middleformat', value='3', checked='true' and middleoption==3 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')), c='middleoptionbg'),

            tr(tdc(strong('Item Display'), c='sectionheader'),
               td(table(tr(tdc(img(coll.PREVIEW_END1_SRC))),
                        tr(tdc('40% category listing : 60% item listing')),
                        tr(tdc(input(type='radio', name='endformat', value='1', checked='true' and endoption==1 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')),
               td(table(tr(tdc(img(coll.PREVIEW_END2_SRC))),
                        tr(tdc('50% category listing : 50% item listing')),
                        tr(tdc(input(type='radio', name='endformat', value='2', checked='true' and endoption==2 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')),
               td(table(tr(tdc(img(coll.PREVIEW_END3_SRC))),
                        tr(tdc('60% category listing : 40% item listing')),
                        tr(tdc(input(type='radio', name='endformat', value='3', checked='true' and endoption==3 or None, onclick="setscrollxy(this.form); this.form.submit()"))), c='singleoptionbox')), c='endoptionbg'),       
               width='80%', border='1', bordercolor='#000000', c='previewtable')

                       , action=linkloc+'4')


    def createaccountwindow(self, error='', post=''):

        print 'createaccountwindow'
        print self.form.get('username', '')
        print error

        return tablew(trt(tdc(error), c='loginerror'),
                      trt(tdc(strong("CREATE NEW ACCOUNT"))),
                      trt(tdc(nbsp)),

                      trt(tdc(
                postform(
                table(

                tr(tdc(tablew(tr(tdc(strong('USERNAME'))),
                              tr(tdc('(4-12 characters)')),


                              tr(tdc(input(type='text', name='username', 
                                           value=self.form.get('username', '') or 'default',size='20')))))),

                tr(tdc(tablew(tr(tdc(strong('PASSWORD'))),

                              tr(tdc('(4-12 characters)')),
                              tr(tdc(input(type='password', name='password', value='',
                             size='20')))))),
                tr(tdc(tablew(tr(tdc(strong('RE-TYPE PASSWORD  '),
                       tr(tdc(input(type='password', name='password2', value='',
                             size='20')))))))),
                tr(tdc(tablew(tr(tdc(strong('E-MAIL ADDRESS  '),
                       tr(tdc(input(type='text', name='email', value='',
                             size='20'),
                       input(type='hidden', name='accountformfilled', value='1')))))))),
                tr(tdc(input(type='image', src=coll.CREATE_SRC))),
                width='70%', c='loginbg'), action=post or self.__class__.__name__),


                trt(tdc('To create an account, please enter the following information. E-mail address is necessary for retrieving lost passwords and will be kept strictly confidential.*', width='50%')),
                   )),
                      width='100%')


    def seemore(self):
        return []

    def renamesearchwindow(self, searchid, xposition=0, yposition=0):
        print "RENAME SEARCH POSITIONS"
        print xposition
        print yposition

        currentsearches=[trt(td(coll.HISTORY_SEARCHES_CURRENT)), tr(td(nbsp))]
        for i in user_history_searches.keys():
            i = int(i)
            currentsearches+=tr(td(nbsp))

        headerinfo = [tr(tdc(coll.HISTORY_SEARCH_RENAMING, c='title')), 
                      tr(tdc(strong(coll.HISTORY_SEARCH_OLD))), 
                      tr(tdc(str(user_history_searches[searchid].searchname))),
                      tr(tdc(strong(coll.HISTORY_SEARCH_NEW)))]
        formcontents = [input(type='text', name='sname', size='30'), br, 
                        input(type='hidden', name='sid', value=searchid), br, 
                        input(type='submit', value='OK'),
                        input(type='hidden', name='task', value=self.task),
                        input(type='hidden', name='popuphandle', value='1'),
                        input(type='hidden', name='xposition', value=str(xposition)),
                        input(type='hidden', name='yposition', value=str(yposition))]
        formcontents = postform(formcontents, 
                  action=self.__class__.__name__+'?manage=2&task='+self.form.get('task', ''))
        return tablew(tr(td(nbsp)),
                      tr(td(nbsp)),
                      tr(tdc(table(headerinfo, tr(tdc(formcontents)),
                                   width='40%', c='renamebg'))))

    def favesavewindow(self):
        if not self.session.__session__.hasValue('username') or \
           str(self.session.username) == 'default':
            return self.notloggedin(post=self.url(favesave=1))

        i=1
        formcontents=[]
        firstradio=1
        for i in user_history_groups.keys():
            i=int(i)
            if str(user_history_groups[i].userid) == str(users.index(
                self.session.username)):
                if firstradio:
                    firstradio=0 
                    formcontents+=input(
                        type='radio', name='groupname', checked='true', 
                        value=i)
                else:
                    formcontents+=input(
                        type='radio', name='groupname', 
                        value=i)
                formcontents+=[user_history_groups[i].groupname]
                formcontents+=br
        if firstradio:
            firstradio=0
            formcontents+=[input(type='radio', name='groupname', 
                                 checked='true', value='newname'),
                           input(type='text', name='savetogroupname', 
                                 value='New Group', size='30'), br*2]
        else:
            formcontents+=[input(type='radio', name='groupname', 
                                 value='newname'),
                           input(type='text', name='savetogroupname', 
                                 value='New Group', size='30'), br*2]
        formcontents+=[input(type='image', name='submitbutton', src=coll.SAVE_SMALL_SRC),
                       input(type='image', name='cancelbutton', src=coll.CANCEL_SMALL_SRC),
                       input(type='hidden', name='popuphandle', value='1')]

        previewitem = [db.list(self.query, sort=db.keylist)[self.index]]
        previewpic = tr(tdc(listhistory(
            previewitem, self.query, self.offset, link=self.link, 
            user=self.session.username)))
        action=self.__class__.__name__+'?q=' + \
                        str(self.query) + '&group=' + str(self.group) + \
                        '&index=' + str(self.index)
        if self.task:
            action+='&task='+str(self.task)
        result = tablew(tr(td(nbsp)), tr(td(nbsp)), previewpic, tr(td(nbsp)), 
                       tr(td([coll.HISTORY_SAVE_GROUP_SELECT, br,
                              postform(formcontents,
                        action=action)])), width='80%')
        return self.taskbar(), tablew(
                 tr(td(nbsp)), tr(td(nbsp)), tr(td(nbsp)),
                 tr(tdc(strong(coll.SAVE_IMAGE_ALT))), tr(td(nbsp)),
                 tr(tdc(
                   tablew(tr(tdc(result)), c='favoriteitem', width='40%'))),
                 width='100%')

    def searchsavewindow(self):

        defaultname = ''

        if not self.session.__session__.hasValue('username') or \
           str(self.session.username) == 'default':
            return self.notloggedin(post=self.url()+'&searchsave=1')


        for x in self.query.getterms():
            facet, value, leaf = x
            defaultname+=str(db.name(facet, value) + ' ')
        for x in self.query.getwords():
           defaultname+=str(x)+ ' '

        if self.__class__.__name__=='Floogle' and self.form.get('words', ''):
            defaultname=self.form.get('words', '')
        defaultname=defaultname.strip()
        formcontents = [input(type='text', name='searchname', 
                              value=defaultname, size='50'),
                        input(type='hidden', name='q', 
                              value=self.form.get('q', '')),
                        input(type='hidden', name='words',
                              value=self.form.get('words', '')) ]
        if self.group:
            formcontents+=input(type='hidden', name='group', 
                                value=self.form.get('group', '')),
        formcontents+=[br*2, input(type='image', name='submitbutton', src=coll.SAVE_SMALL_SRC, tabindex=0),
                       input(type='image', name='cancelbutton', 
                             src=coll.CANCEL_SMALL_SRC, tabindex=1), 
                       input(type='hidden', name='popuphandle', value='1')]
        searchpreview=[]
        if self.__class__.__name__=='Floogle' and self.form.get('words', ''):
            words = [wordbox(word, self.link, task=self.task) for word in self.form.get('words', '').split(' ')]
        else:
            words = [wordbox(word, self.link, task=self.task) for word in self.query.getwords()]
        if self.__class__.__name__=='Flamenco':
            terms = [termbox(term, self.link, task=self.task) for term in self.query.getterms()]
        else: terms=[]
        searchpreview += tr(td(words, terms), td(nbsp))
        searchpreview += tr(td(nbsp))
        action=self.__class__.__name__+'?'
        if self.query:
            print "QUERY"
            print self.query
            #return self.query
            action+='q='+str(self.query)+'&'
        if self.words:
            action+='words='+'&'.join(self.words)
        if self.group:
            action+='&group='+str(self.group)
        if self.sort:
            action+='&sort='+str(self.sort)
        if self.task:
            action+='&task='+str(self.task)
        result = table(tr(td(nbsp)), searchpreview,
                       tr(td([p, coll.HISTORY_SEARCH_SAVE_PROMPT, 
                postform(formcontents, action=action)])),
#                         action=self.__class__.__name__+"?&" + ('q=' + 
#                                self.query+'&' or '') + ('words=' and self.words or '') + 
#                                '&'.join(self.words) +
#                                '&group=' + str(self.group) + ('&sort=' and self.sort or '') + 
#                                str(self.sort))])),
                       tr(td(nbsp)),
                       tr(td('To return to your search without saving, click the Cancel button.')), width='80%')
        return self.taskbar(), tablew(
                 tr(td(nbsp)), tr(td(nbsp)),
                 tr(tdc(strong(coll.SAVE_SEARCH_ALT))), tr(td(nbsp)),
                 tr(tdc(
                   tablew(tr(tdc(result)),
                     c='searchbody', width='40%'))),
                 width='100%')

    def itemdisplay(self):
        if not self.index is None:
            prev = next = []
            if self.index > 0:
                prev = [td(self.link(img(coll.LEFT_ARROW_SRC, alt=coll.LEFT_ARROW_ALT), index=self.index-1, oldquery=self.oldquery, task=self.task)),
                        td(self.link('previous', index=self.index - 1,
                                oldquery=self.oldquery, task=self.task))] #c='box'
            if self.index < self.count - 1:
                next = [tdr(self.link('next', index=self.index + 1,
                                 oldquery=self.oldquery, task=self.task)), #c='box'
                        tdr(self.link(img(coll.RIGHT_ARROW_SRC, alt=coll.RIGHT_ARROW_ALT), index=self.index+1, oldquery=self.oldquery, task=self.task))]
            back = self.link('back to results', index=None, offset=self.offset,
                              query=self.oldquery or self.query, task=self.task)
            head = tablew(tr(tdc(
                 'Item ', self.index + 1, ' of ', self.count, ' (', back, ')')))
            nav = tablew(tr(prev, td(width='100%'), next, c='pagebar'), space=2)
        item = coll.itemdisplay(self.item, self.request)
        if not self.index is None:
            return [head, nav, item, p]
        return item



    def queryinfo(self, facetlist=None, attrlist=None, historyview=None):
        if facetlist is None:
            facetlist = db.facetlist
        if attrlist is None:
            attrlist = db.attrlist
        self.index = None
        boxes = [termbox(term, self.link, task=self.task)
                 for term in self.query.getterms()
            ] + [wordbox(term, self.link, task=self.task)
                 for term in self.query.getwords()]
        metadata = db.metadata(self.item)
        refine, expand = [], []
        for f in facetlist:
            if metadata[f]:
                terms = coll.queryinfo_terms(f, metadata[f])
                refineterms = []
                for name, term in terms:
                    q = self.query + term
                    refineterms.append(
                        (self.link(esc(name), query=q, index=None, group=f, task=self.task),
                         cls('count', ' (%d)' % db.count(q))))
                facetname = cls('facet', db.name(f) + ':' + nbsp*2)
                refine.append(trbl(td(facetname), td(join(', ', refineterms))))
                expandterms = []
                for name, term in terms:
                    q = Query(db) + term
                    expandterms.append(
                        (self.link(esc(name), query=q, index=None, group=f, task=self.task),
                         cls('count', ' (%d)' % db.count(q))))
                expand.append(trbl(td(join(', ', expandterms))))
        for a in attrlist:
            if metadata[a]:
                name = cls('attribute', db.name(a) + ':' + nbsp*2)
                refine.append(trbl(td(name), td(metadata[a])))
        return [p, tablew(tr(td('Current search:'))),
                p, boxes,
                p, cls('metaheading',
                coll.MIDDLEGAME_REFINE_SEARCH),
                p, tablew(refine), p, '<hr>',
                p, cls('metaheading',
                coll.MIDDLEGAME_SEE_ALL), p, tablew(expand)]

    def paths(self, facet):
        paths = []
        for f in db.facetlist:
            if self.values[f]:
                paths += termbox((f, self.values[f], 0), self.link,
                    c='termbox' + (f == facet and ' current' or ''),
                    xbutton=self.values[f], task=self.task)
        return paths

    def categorylist(self, facet):
        message = ['Subcategories in ', cls('facet', db.name(facet)),
                   facetpath(facet, self.values[facet]), ':']
        groups = db.groups(self.query, facet, self.values[facet])
        if len(groups) == 1:
            [(name, id, count)] = groups
            return self.redirect(self.url(self.query + (facet, id, 0)))
        groups.sort()
        def entry(name, id, count):
            return [self.link(name, term=(facet, id, 0)), ' ',
                    cls('count', '(%d)' % count), br]
        if len(groups) < 50:
            return [div(message, c='message'),
                    multicolumn([entry(*group) for group in groups], 2)]
        letters = list(alphabet) + ['other']
        sections = {}
        for letter in letters:
            sections[letter] = []
        for name, id, count in groups:
            letter = (name or '')[:1].upper()
            if letter not in alphabet: letter = 'other'
            sections[letter].append(entry(name, id, count))

        message += [br, '(jump to ', join(' - ', [
            link('#' + x, x) for x in letters if sections[x]]), ')']
        if len(groups) > 500:
            return [div(message, c='message'),
                    [[p, a(strong('- %s -' % letter), name=letter),
                      multicolumn(sections[letter], 3)] for letter in letters]]

        for letter in letters:
            if sections[letter]:
                heading = [a(strong('- %s -' % letter), name=letter), br]
                blank = [nbsp, br]
                sections[letter] = [heading] + sections[letter] + [blank]
        lengths = map(len, [sections[letter] for letter in letters])
        total, left, ltotal = sum(lengths), 0, 0
        while abs(ltotal*2 + lengths[left]*2 - total) < abs(ltotal*2 - total):
            ltotal += lengths[left]
            left += 1
        tdcol = deftag(td, width="50%", c='column')
        return [div(message, c='message'),
                tablew(trt(tdcol([sections[x] for x in letters[:left]]),
                           tdcol([sections[x] for x in letters[left:]])))]

    def matchlist(self, word, columns=2):
        pat = re.compile('(%s)' % word, re.I)
        results = []
        facets = {}
        for facet in db.facetlist: facets[facet] = []
        for facet, id, name in db.termsearch(word):
            facets[facet].append((db.name(facet, id), id))
        for facet in db.facetlist:
            if not facets[facet]: continue
            facets[facet].sort()
            items = []
            for name, id in facets[facet]:
                parts = [db.name(facet, id) for id in db.path(facet, id)]
                name = pat.sub(flatten(color('#ff0000', '\\1')), name)
                parts[-1] = self.link(name, query=Query(db) + (facet, id, 0))
                items.append([join(' > ', parts), br])
            if len(items) < 5: items += [''] * (5 - len(items))
            heading = cls('facet', db.name(facet))
            listing = multicolumn(items, columns=columns)
            results += [p, tablew(tr(td(heading, c='querybox')),
                                  tr(td(listing, c='matchbox')))]
        backlink = self.link('back to results', words=self.words, task=self.task)
        return [p, self.taskbar(), p, tablew(tr(td('All terms matching keyword "%s":' % word),
                             tdr(backlink))), results]

    def tasks(self):
        if self.session.username == 'default':
            return []
        else:
            userid = users.index(self.session.username)
            availableids = users[userid].available_tasks.split(', ')
            #assume availableids are in theproper order; that is, set1 then set2
            #availableids.sort()
            available='No available tasks'
            completedids = users[userid].completed_tasks.split(', ')
            completed='No completed tasks'
            availableresult = []
            completedresult = []
            #first set of tasks
            first=''
            firsttasks=['1', '2', '3', '4', '5']
            secondtasks=['22', '23', '24', '25']
            thirdtasks=['26', '27', '28', '29']
            fourthtasks=['30', '31']

            for id in firsttasks:
                if id in availableids:
                    first=id
                    break
            #second set of tasks
            second=''
            if '22' not in availableids or \
               '23' not in availableids or \
               '24' not in availableids:
                for x in ['22', '23', '24']:
                    if x in availableids:
                        availableids.remove(x)
                oneofthree=0
            else:
                oneofthree=1

            for id in secondtasks:
                if id in availableids:
                    second=id
                    break

            #third set of tasks
            third1, third2='', ''
            if '26' not in availableids or \
               '27' not in availableids:
                for x in ['26', '27']:
                    if x in availableids:
                        availableids.remove(x)
                oneoftwo1=0
            else:
                oneoftwo1=1

            if '28' not in availableids or \
               '29' not in availableids:
                for x in ['28', '29']:
                    if x in availableids:
                        availableids.remove(x)
                oneoftwo2=0
            else:
                oneoftwo2=1

            for id in ['26', '27']:
                if id in availableids:
                    third1=id
                    break


            for id in ['28', '29']:
                if id in availableids:
                    third2=id
                    break

            fourth=''
            if '30' not in availableids or \
               '31' not in availableids:
                for x in ['30', '31']:
                    if x in availableids:
                        availableids.remove(x)
                oneoftwo3=0
            else:
                oneoftwo3=1            
            for id in fourthtasks:
                if id in availableids:
                    fourth=id
                    break


            if not availableids == ['']:

                counter = 1
                for taskid in availableids:
                    #print taskid
                    #print taskid=='5'
                    #print completedids
                    #print completedids==['1', '2', '3', '4']
                    if not taskid=='5' or \
                       (taskid=='5' and completedids==['1', '2', '3', '4']):

                        if first=='' and taskid in secondtasks:
                            availableresult+=trt(
                                td(strong('First set of Tasks (posted 8/12/04) complete.'), colspan=2), c='taskset')
                            first='-1'

                        if taskid==first:
                            availableresult+=trt(
                                td(strong('First Set of Tasks (posted 8/12/04)'), colspan=2), c='taskset')
                            if not taskid=='5':
                                availableresult+=trt(
                                    td('After completing the tasks currently listed for this set, a fifth task will appear', colspan=2), c='taskset')
                        elif taskid==second:
                            availableresult+=trt(
                                td(strong('Second Set of Tasks (posted 8/17/04)'), colspan=2), c='taskset')
                            if oneofthree:
                                availableresult+=trt(
                                    td('Of the following three tasks, you only need to complete one. You must complete the fourth task.', colspan=2), c='taskset')
                        elif taskid==third1:
                            if second=='':
                                availableresult+=trt(
                                td(strong('Second Set of Tasks (posted 8/17/04) complete.'), colspan=2), c='taskset')
                                second='-1'
                            availableresult+=trt(
                                td(strong('Third Set of Tasks (posted 8/23/04)'), colspan=2), c='taskset')
                            if oneoftwo1:
                                availableresult+=trt(
                                    td('Of the following two tasks, you only need to complete one.', colspan=2), c='taskset')

                        elif taskid==third2:
                            if second=='':
                                availableresult+=trt(
                                    td(strong('Second Set of Tasks (posted 8/17/04) complete.'), colspan=2), c='taskset')
                                second='-1'
                            if not oneoftwo1:
                                availableresult+=trt(
                                td(strong('Third Set of Tasks (posted 8/23/04)'), colspan=2), c='taskset')
                            if oneoftwo2:
                                availableresult+=trt(
                                    td('Of the following two tasks, you only need to complete one.', colspan=2), c='taskset')

                        elif taskid==fourth:
                            if second=='':
                                availableresult+=trt(
                                    td(strong('Second Set of Tasks (posted 8/17/04) complete.'), colspan=2), c='taskset')
                                second='-1'
                            if third1=='' and third2=='':
                                availableresult+=trt(
                                td(strong('Third Set of Tasks (posted 8/23/04) complete.'), colspan=2), c='taskset')
                                third1='-1'
                                third2='-1'
                            if oneoftwo3:
                                availableresult+=trt(
                                    td(strong('Fourth Set of Tasks (posted 8/28/04)'), colspan=2), c='taskset')
                                availableresult+=(trt(
                                    td('Of the following two tasks, you only need to complete one.', colspan=2), c='taskset'))


                        print 'inside'
                        availableresult+=trt(
                        tdc(input(type='radio', name='task',
                                  value=taskid, checked=1 and self.task==taskid or None, onclick="setscrollxy(this.form); this.form.submit()"), width='2%'),
                        td(tasks[int(taskid)].description))
                        counter+=1
                if second=='':
                    availableresult+=trt(
                                td(strong('Second Set of Tasks (posted 8/17/04) complete.'), colspan=2), c='taskset')

                if third1=='' and third2=='':
                    availableresult+=trt(
                                td(strong('Third Set of Tasks (posted 8/23/04) complete.'), colspan=2), c='taskset')

                if fourth=='':
                    availableresult+=trt(
                        td(strong('Fourth Set of Tasks (posted 8/28/04) complete.'), colspan=2), c='taskset')


                denali=tdc(link('Flamenco?task='+self.task, img(coll.PIC_URL_BASE+'use_denali.gif')))
                shasta=tdc(link('Floogle?task='+self.task, img(coll.PIC_URL_BASE+'use_shasta.gif')))
                x=random.randint(1, 2)
                if x==1:
                    left=denali
                    lefticon=tdc(link('Flamenco?task='+self.task, img(coll.DENALI_SRC)))
                    right=shasta
                    righticon=tdc(link('Floogle?task='+self.task, img(coll.SHASTA_SRC)))
                else:
                    left=shasta
                    lefticon=tdc(link('Floogle?task='+self.task, img(coll.SHASTA_SRC)))
                    right=denali
                    righticon=tdc(link('Flamenco?task='+self.task, img(coll.DENALI_SRC)))

                availableresult+=tr(tdc(tablew(
                    tr(td(nbsp, colspan=5)),
                    tr(td(nbsp, width='15%'), left,
                       tdc(nbsp),
                       right, td(nbsp, width='15%')),
                    tr(td(nbsp, colspan=5)),
                    tr(td(nbsp), lefticon,
                       tdc(nbsp, width='5%'),
                       righticon, td(nbsp)),
                    tr(td(input(type='hidden', name='xposition', value='0'),
                          input(type='hidden', name='yposition', value='0')))), colspan=2))






            if not completedids == ['']:

                counter = 1
                for taskid in completedids:
                    completedresult+=tr(td(nbsp*2, counter, '. ', tasks[int(taskid)].description, colspan=2))
                    counter+=1
            if availableresult == []:
                availableresult=tr(td(nbsp, width='2%'), td(available))
            availableresult=postform(availableresult, action='Flamenco?manage=7')
            if completedresult == []:
                completedresult=tr(td(nbsp*2, completed, colspan=2))
        return table(trt(td('Available Tasks', colspan=2, c='title')),
                      availableresult,
                      #trt(td(nbsp)),
                      trt(td('Completed Tasks', colspan=2, c='title')),
                      completedresult, width='80%', c='tasksitem')

    def taskbar(self):
        return []

        if self.session.username=='default':
            return []
        description=''
        id=users.index(self.session.username)
        available = users[id].available_tasks.split(', ')
        if available==['']: available=[]

        if not self.form.get('task', ''):
            description = 'No task selected. To select a task, click on the History and Settings button in the upper right and go to View Tasks.'
        else:
            if not self.task in available:
                description = 'No task selected'
            else: description = tasks[int(self.task)].description
        if self.form.get('task', '') and not self.form.get('task', '')=='None':
            donebutton=img(coll.PIC_URL_BASE+'done_button.gif')
        else:
            donebutton=img(coll.PIC_URL_BASE+'done_button_grey.gif')
        return tablew(tr(td(strong('Current Task: '), description, colspan=2)),
                      tr(td(small('Click the done button when you feel you have completed the task.')), td(self.task and self.link(donebutton,task=self.task, taskcomplete=1) or donebutton)),

                      c='tasksitem')

    def taskcompleted(self):
        error=''
        errorstyle=''
        if self.session.username=='default':
            return ['You are not logged in. Please login and try again.']
        message, questions='', ''
        userid = users.index(self.session.username)
        available = users[userid].available_tasks.split(', ')

        completed = users[userid].completed_tasks.split(', ')
        if available==['']:
            available=[]
        if completed==['']:
            completed=[]
        taskid=self.task
        questions = db.listquestions(taskid)
        questionresult=[]
        feedbackentry=''
        if not self.task in available and not self.form.get('feedbacksubmit.x', ''):
            message= 'This task is not a valid task for you to submit. Please select a task from your History and Settings page and try again.'
        else:
            error=''
            for keyid in questions:

                if not self.form.get('question'+str(keyid)):
                    if not tasks_questions[int(keyid)].optional=='1':
                        error='Please answer all the required questions.'
                        errorstyle='taskerror'

            if not self.form.get('feedbacksubmit.x', ''):
                error=''
            if self.form.get('feedbacksubmit.x', '') and not error and taskid in available:

                message='Feedback received. Thank you!'


                if not error:
                    timestamp=str(time())
                    for keyid in questions:
                        i=tasks_questions_responses.new()
                        tasks_questions_responses[i].questionid=keyid
                        tasks_questions_responses[i].response=self.form.get('question'+str(keyid), '')
                        tasks_questions_responses[i].userid=userid
                        tasks_questions_responses[i].taskid=taskid
     #                   tasks_questions_responses[i].timestamp=timestamp

                    #dump user tables
                    log.dumpusertables(userid, taskid, timestamp)


#                if taskid in available:
                    available.remove(taskid)
                    completed.append(taskid)
                    if available==[]:
                        users[userid].available_tasks=''
                    else:
                        users[userid].available_tasks = ', '.join(available)
                    if completed==[]:
                        users[userid].completed_tasks=''
                    else:
                        users[userid].completed_tasks = ', '.join(completed)
                    message+=' Task completed. '



            else:
                taskquestions=[]
                questionresult=[]

                for keyid in questions:
                    keyid=int(keyid)
                    taskquestions.append((tasks_questions[keyid].type, keyid, tasks_questions[keyid].question))
                questionnumber=1
                taskquestions.sort()
                taskquestions.reverse()
                radioset=0
                for type, keyid, question in taskquestions:
                    if type=='radio' and radioset==0:
                        questionresult+=table(tr(td(nbsp)),
                                              tr(td(strong('Consider the following set of statements. Mark 1 if you Disagree Strongly with the statement, 7 if you Agree Strongly with the statement, and 4 for Neutral.'), colspan=3)),
                                               tr(td(nbsp)),
                                               tr(td(strong('Strongly Disagree'), width='33%'),
                                                  tdc(strong('Neutral'), width='33%'),
                                                  tdr(strong('Strongly Agree'), width='33%')), tr(td(nbsp)), width='50%')
                        radioset=1

                    questiontype=tasks_questions[keyid].type
                    if questionnumber%2==0 and questiontype=='radio':
                        style='taskcompletebg'
                    elif questiontype=='radio':
                        style='taskcompletebg2'
                    else:
                        style=''

                    questionresult+=table(tr(td(questionnumber, '. ', question)), width='50%', c=style)
                    questionnumber=questionnumber+1


                    if questiontype=='radio':
                        radios = tr([tdc(input(type='radio', value=i+1, name='question'+str(keyid), checked=((self.form.get('question'+str(keyid), '')==str(i+1)) and '1' or None))) for i in range(7)])
                        vals = tr([tdc(i+1) for i in range(7)])
                        questionresult+=table(radios, vals,
                                               tr(td(nbsp)), c=style, width='50%')

                    elif questiontype=='textarea':


                        questionresult+=tr(td(textarea(self.form.get('question'+str(keyid), '') or '', cols='60', rows='6', name='question'+str(keyid)))),
                        questionresult+=tr(td(nbsp))


                strquestions=[]
                for question in questions:
                    strquestions.append(str(question))
                questions=', '.join(strquestions)
                questionresult = tablew(tr(td(strong(tasks[int(self.task)].description))), tr(td(nbsp)),
                                        tr(td('Please answer the following questions about the task you just completed to receive credit for this task.')),
                                   tr(td(nbsp)),
                                   questionresult,
                                   tr(td(table(
                    tr(td(nbsp)),
                    tr(td(input(type='hidden', name='questions', value=questions), input(type='image', src=coll.SUBMIT_SRC, name='feedbacksubmit'), nbsp, self.link(img(coll.CANCEL_SRC), task=self.task, taskcomplete=None))), tr(td(nbsp))))))



        return postform(tablew(tr(td(error or message), c=errorstyle),
                               tr(td(nbsp)),
                               tr(td(questionresult)),
                               tr(td(nbsp)),

                               tr(td(nbsp)),
                               tr(td(feedbackentry))),
                        action=self.__class__.__name__+'?task='+self.task+'&taskcomplete=1')
