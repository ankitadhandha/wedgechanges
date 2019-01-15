# Copyright (c) 2004-2006 The Regents of the University of California.

from Page import Page
from app import db, coll, log, users, user_history_groups, user_histories, tasks
from query import Query
from html import *
from components import donebox

import time
import re
import Cookie as CookieEngine
from WebKit.Cookie import Cookie
SELF = []                            # unique sentinel value

class InterfaceBase(Page):
    """A base class for interfaces that (a) have an opening, middle game,
       endgame, and historygame; (b) allow only one value to be selected per facet."""

    def url(self, query=SELF, term=None, add=None, remove=None, action=None,
            facet=SELF, group=SELF, sort=SELF, offset=SELF, index=SELF,
            words=None, oldquery=None, count=None, history=None, 
            searchhistory=None, item=None, searchsave=None, favesave=None,
            groupid=None, manage=None, managesearch=None, managesave=None,
            renamegname=None, help=None, logout=None, createaccount=None,
            managestart=None, task=SELF, taskcomplete=None,
            historyfavoritelimit=None, morelike=None):
        if query is SELF: query = self.query
        elif offset is SELF: offset = 0
        if term:
            terms = []
            for f, id, leaf in query.getterms():
                if f != term[0]: terms.append((f, id, leaf))
            if term[1]: terms.append(term)
            query, offset = Query(query.db, terms, query.words), 0
        if add: query, offset = query + add, 0
        if remove: query, offset = query - remove, 0
        if facet is SELF: facet = self.facet
        if group is SELF: group = self.group
        if sort is SELF: sort = self.sort
        if offset is SELF: offset = self.offset
        if index is SELF: index = self.index
        if task is SELF: task = self.task
        if historyfavoritelimit is SELF:
            historyfavoritelimit = self.historyfavoritelimit
        
        params = []
        if query: params.append('q=' + query.serialize())
        if oldquery: params.append('oldq=' + oldquery.serialize())
        if action: params.append('action=' + urlenc(action))
        if facet: params.append('facet=' + facet)
        if group: params.append('group=' + group)
        if sort: params.append('sort=' + sort)
        if offset: params.append('offset=' + str(offset))
        if index is not None: params.append('index=' + str(index))
        if history is not None: params.append('history=1')
            
        if searchhistory is not None: params.append('searchhistory=1')
        if searchsave is not None: params.append('searchsave=1')
        if favesave is not None: params.append('favesave=1')
        if manage is not None: params.append('manage=1')
        if task: params.append('task=' + task)
        if morelike is not None: params.append('morelike=1')
        if taskcomplete is not None: params.append('taskcomplete=1')
        if managestart is not None: params.append('managestart=1')
        if createaccount is not None: params.append('createaccount=1')
        if managesearch is not None: params.append('managesearch=1')
        if managesave is not None: params.append('managesave=1')
        if groupid is not None: params.append('groupid=1')
        if renamegname is not None: params.append('renamegname='+renamegname)
        if historyfavoritelimit is not None:
            params.append('historyfavoritelimit='+str(historyfavoritelimit))
        
        if help is not None: params.append('help=1')
        if logout is not None: params.append('logout=1')
        
        if item is not None: params.append('item=' + str(item))
        if words:
            params.append(
                'words=' + urlenc(' '.join(['"%s"' % word for word in words])))
        url = self.__class__.__name__
        if history is not None and item is not None:
            if task is not None:
                return url+'?item=%s&task=%s' % (item, task)
            return url+ '?item=%s' % item
        
        #print "INSIDE URL\n"
        #print self.session.username
        #print self.form.get('username', '')

        if not self.session.__contains__('username'):
            self.session.username='default'
        username=self.session.username
        if not users.__contains__(username):
            username='default'

        #append username to parameters to allow users to link to flamenco
        # pages. username=default means generic user. lack of username in
        # form means the user is logged in. If session cookie not available,
        # user will need to login again. For this reason, do not append
        # username to parameters on login pages
        #print favesave
        #print searchsave
        #print self.form.get('favesave', '')
        #print self.form.get('searchsave', '')
        if self.form.get('favesave', '') is None and \
               self.form.get('searchsave', '') is None and \
               username=='default':
            print "username is default"
            params.append('username=default')

        if params: url += '?' + '&'.join(params)
        return url

    def prepare(self):
	self.ip = self.request.remoteAddress()
        self.query = Query(db, text=self.form.get('q', ''))
        self.group = self.form.get('group', '')
        if 'oldq' in self.form:
            self.oldquery = Query(db, text=self.form.get('oldq', ''))
        else:
            self.oldquery = None
        self.item = self.form.get('item', '')
        self.history = self.form.get('history', '')
        self.searchhistory = self.form.get('searchhistory', '')
        self.searchsave = self.form.get('searchsave', '')
        self.favesave = self.form.get('favesave', '')
        self.manage = self.form.get('manage', '')
        self.task = self.form.get('task', '')
        self.taskcomplete = self.form.get('taskcomplete', '')
        self.managestart = self.form.get('managestart', '')
        self.createaccount = self.form.get('createaccount', '')
        self.managesearch = self.form.get('managesearch', '')
        self.managesave = self.form.get('managesave', '')
        self.renamegname = self.form.get('renamegname', '')

        self.logout = self.form.get('logout', '')
        self.help = self.form.get('help', '')
        self.searchname = self.form.get('searchname', '')
        self.groupid = self.form.get('groupid', '')
        self.action = self.form.get('action', '')
        self.facet = self.form.get('facet', '')

        self.sort = self.form.get('sort', '')
        self.sortkeys = db.keylist[:]
        if self.sort:
            self.sortkeys.remove(self.sort)
            self.sortkeys[:0] = [self.sort]
        self.offset = int(self.form.get('offset', '0'))
        self.index = None
        if 'index' in self.form:    
            self.index = int(self.form.index)
        if self.form.get('survey'):
            log.log(self, 'survey', closer=self.form.closer, ipaddr=self.ip,
                    expected=self.form.expected, useful=self.form.useful)
        if self.form.get('in') == 'all':
            self.query = Query(db)
        self.words = []
        if self.form.get('words', '').strip():
            self.words = []
            quoted = re.compile(r'"([^"]*)"')
            words = self.form.words.strip()
            while words:
                match = quoted.match(words)
                if match:
                    self.words.append(match.group(1))
                    words = words[match.end():].strip()
                else:
                    if words[:1] == '"': words = words[1:]
                    bits = words.strip().split(' ', 1) + ['']
                    self.words.append(bits[0])
                    words = bits[1].strip()
            for word in self.words: self.query += word
        self.values = {}
        for facet in db.facetlist:
            self.values[facet] = 0
        for facet, id, leaf in self.query.getterms():
            self.values[facet] = id
        if self.index is not None:
            self.results = db.list(self.query, sort=self.sortkeys)
            self.item = self.results[self.index]
            self.count = len(self.results)
        else:
            self.count = db.count(self.query)

    def body(self, out):
        out.write(self.page())

    def page(self):
        loginerror=None
        if self.session.__session__.hasValue('username') and users.__contains__(str(self.session.username)):
            
            userid=users.index(str(self.session.username))
        else:
            self.session.username='default'
            userid=users.index(str(self.session.username))

        if self.taskcomplete:
            log.log(self, 'taskcomplete', self.action, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            
            return div(self.taskcompleted())
        if self.logout:
            
            self.session.history=[]
            self.session.facets=''
            self.session.sortby=''
            self.session.attrs=''
            self.session.username='default'
            
            cookie = Cookie('username', 'default')

            cookie.setPath('/')
#            return self.request.cookies()
            
            
            t=time.gmtime(time.time())
            t = (t[0]-10,) + t[1:]
            t = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT", t)
            cookie.setExpires(t)
            self.response.addCookie(cookie)
            
                
            log.log(self, 'logoutwindow', self.action, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            #return div(self.opening(), c='opening')
            return div(self.logoutwindow())

        #check for new account creation
        elif self.form.get('createaccount', '') and not self.form.get('accountformfilled', ''):
            log.log(self, 'notloggedin', 'accountformfilled=0', userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.notloggedin(post=self.url(manage='1' and self.form.get('manage', '') or None,
                                                      managestart='1' and self.form.get('managestart', '') or None)), c='popupwindow')
            

        #check if its a login/create request
        elif self.form.get('username', ''):
            if self.form.get('createaccount', ''):
                creationerror=''
                #create account request
                if self.form.get('accountformfilled', ''):      
                    name, password='', '' 
                    if not (self.form.get('username', '') and \
                       self.form.get('password', '') and \
                       self.form.get('password2', '') and \
                       self.form.get('email', '')):
                       creationerror='Error: Please fill in all fields'
                    else:                
                        name=self.form.get('username', '')
                        if users.__contains__(name):
                            creationerror='Error: That username is already taken'
                        if not self.form.get('password', '') == \
                            self.form.get('password2', ''):
                            creationerror='Error: Passwords did not match'
                        elif len(name) < 4:
                            creationerror='Error: Name too short'
                        elif len(name) > 12:
                            creationerror='Error: Name too long'
                    #passes error checking. create new user
                    if creationerror=='':
                        idx = users.new()
                        users[idx].name = name
                        users[idx].password=self.form.get('password', '')
                        users[idx].email=self.form.get('email', '')
                        print "passes errory checking; create new user"
                        print self.form.get('username', '')
                        print self.form.get('password', '')
                        print self.form.get('password2', '')
                        print self.form.get('email', '')
    
                    else:
                        log.log(self, 'notloggedin', creationerror, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                        
                        return div(self.notloggedin(creationerror=creationerror, post=self.url(manage='1' and self.form.get('manage', '') or None,
                                                                                               managestart='1' and self.form.get('managestart', '') or None,
                                                                                               createaccount='1' and self.form.get('createaccount', '') or None)), c='popupwindow')
        
            #is login request, check for valid user
            name=self.form.get('username', '')
            if users.__contains__(name):
                idx=users.index(name)
                password=self.form.get('password', '')
                print "Login request"
                if users[idx].password==password:
                    self.session.username=name
                    print self.session.username
                    if not users.__contains__(name):

                        if self.form.get('popuphandle', ''):
                            #log managegame activity in FrankenMatrix
                            #log.log(self, 'managegame', self.task, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl, detail='login request')
                            
                            return div(self.managegame(post=self.url(manage='1')), c='managegame')
                        
                    else:
                        idx=users.index(name)
                        if users[idx].password==password:
                            self.session.username=name
                            if users[idx].remember=='1':
                                name=self.form.get('username', '')
                                cookie = Cookie('username', name)
                                cookie.setPath('/')
                                t=time.gmtime(time.time())
                                t = (t[0]+10,) + t[1:]
                                t = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT", t)
                                cookie.setExpires(t)
                                self.response.addCookie(cookie)
                else:
                    #existing user, wrong password
                    error='Error: Incorrect password for given username'
                    self.session.username='default'
                    if self.form.get('createaccount', ''):
                        log.log(self, 'notloggedin', error, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                        
                        return div(self.notloggedin(post=self.url(
                            manage='1' and self.form.get('manage', '') or None,
                            managestart='1' and self.form.get('managestart', '') or None)), c='popupwindow')
                    
                    log.log(self, 'notloggedin', error, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                    return div(self.notloggedin(post=self.url(
                        manage='1' and self.form.get('manage', '') or None,
                        managestart='1' and self.form.get('managestart', '') or None),loginerror=error), c='popupwindow')
            else:
                self.session.username='default'
                error='Error: Specified username does not exist'
                #user doesnt exist
                if self.form.get('createaccount', ''):
                    log.log(self, 'notloggedin', error, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                    return div(self.notloggedin(post=self.url(
                        manage='1' and self.form.get('manage', '') or None,
                            managestart='1' and self.form.get('managestart', '') or None)), c='popupwindow')
                log.log(self, 'notloggedin', error, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                
                return div(self.notloggedin(post=self.url(
                    manage='1' and self.form.get('manage', '') or None,
                    managestart='1' and self.form.get('managestart', '') or None), loginerror=error), c='popupwindow')
            #add entry regardless of new user or not
            # dump session history
            # into the user_history table
            #entries from session history in format(item, index, timestamp)    
            if self.session.__session__.hasValue('history'):
                print "Dumping session history"
                print self.session.history
                
                for entry in self.session.history:
                    i = user_histories.new()
                    user_histories[i].userid = str(idx)
                    user_histories[i].itemidx = entry[1]
                    user_histories[i].timestamp = entry[2]
                    user_histories[i].item = entry[0]
                    #user_histories[i].groupid = str(groupid)
                self.session.history=[]

#cookie section
#            if self.form.get('rememberme', '') and \
#               self.form.get('rememberme', '') == '1':
                #set the cookie
#                name=self.form.get('username', '')
#                cookie = Cookie('username', name)
#                cookie.setPath('/')
#                t=time.gmtime(time.time())
#                t = (t[0]+10,) + t[1:]
#                t = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT", t)
#                cookie.setExpires(t)
#                
#                self.response.addCookie(cookie)
#                idx=users.index(name)
#                users[idx].remember='1'
#cookie section



#cookie section
        #not login, not logout, check for cookie
        #elif self.request.hasCookie('username') and \
        #         self.session.__session__.hasValue('username') and \
        #         self.session.username == 'default':
#        elif self.request.hasCookie('username') and not self.session.__contains__('username'):
            #return self.request.cookie('username').expires()
#            return 'cookie detected'
            #cookie detected
#            print "Cookies"
#            print self.request.cookies()
#            self.session.username=self.request.cookies()['username']
#            
#            if self.session.username=='':
#                self.session.username='default'
#                self.session.history=[]
#                self.session.facets=''
#                self.session.sortby=''
#                self.session.attrs=''
#cookie section

        if not self.session.__session__.hasValue('username'):
            
            print "user not logged in\n\n\n"
            #return "user has not logged in, but is accessing protected content"
            
            self.session.username='default'
            self.session.history=[]
            self.session.facets=''
            self.session.sortby=''
            self.session.attrs=''
        if not users.__contains__(self.session.username):
            self.session.username='default'
        #print "username set to default"
        if self.searchsave:
            log.log(self, 'savesearch', self.action, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.searchsavewindow(), c='popupwindow')

        elif self.favesave:
            log.log(self, 'savefavorite', self.action, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.favesavewindow(), c='popupwindow')


        #manage=1 means wants to access myflamenco, possible login
        #manage=1 createaccount=1 means access myflamenco after create
        #manage=1 createaccount=1 managestart=1 means start managegame to certain page
        
        elif self.manage:
            print 'entering managegame section'
            #as long as this is not handling a login request, we can assume
            #that this returns the managegame section, so set self.manage
            # to proper opening section
            if self.form.get('managestart', ''):
                if self.form.get('username', ''):
                    name=self.form.get('username', '')
                    if users.__contains__(name):
                        idx=users.index(name)
                        self.manage=users[idx].managegame_opening
                        
                elif self.session.__contains__('username'):
                    name=self.session.username
                    if users.__contains__(name):
                        idx=users.index(name)
                        self.manage=users[idx].managegame_opening
            print self.manage
            if int(self.form.get('manage', ''))==7:
                self.manage=1
            #log managegame activity in FrankenMatrix
            #log.log(self, 'managegame', 'manage', userid=userid, ipaddr=self.ip,
            #        query=str(self.query), sort=self.sort, groupby=self.group,
            #        facet=self.facet, count=self.count, offset=self.offset,
            #        indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.managegame(), c='managegame') 

        elif self.help:
            log.log(self, 'helpgame', self.action, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.helpgame(), c='helpgame')

        elif self.renamegname:
            if self.renamegname:
                name='renamegroup'
            else:
                name='newgroup'
            log.log(self, name, self.action, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.managehandler(), c='managehandler')

        elif self.history:
            #history game
            log.log(self, 'historygame', self.action, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.historygame(), c='historygame')
  
        elif self.index is not None or self.item:
            if self.form.get('morelike', ''):
                event='morelike'
            else: event=self.action
            log.log(self, 'endgame', event, userid=userid, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, groupby=self.group,
                    facet=self.facet, count=self.count, offset=self.offset,
                    indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.endgame(), c='endgame')

        elif self.query or self.action:
            if self.form.get('morelike', ''):
                event='morelike'
            else: event=self.action
            log.log(self, 'middle', event, userid=userid,
                    groupby=self.group, ipaddr=self.ip,
                    query=str(self.query), sort=self.sort, offset=self.offset,
                    facet=self.facet, count=self.count, prevurl=self.prevurl)
            print 'QUERY'
            print self.query
            print self.query.serialize()
            return div(self.middlegame(), c='middlegame')
  
        else:
            print "username, apss"
            print self.form.get('username', '')
            print self.form.get('password', '')
            loginerror=None
            if self.form.get('username', ''):
                name=self.form.get('username', '')
                if not users.__contains__(name):
                    loginerror= ' Error: Invalid Username/Password pair. Please try again'
                    log.log(self, 'opening', self.action, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                    return div(self.opening(loginerror=loginerror), c='opening')
                idx = users.index(name)
                if not users[idx].password==password:
                    print 'loginerr'
                    print self.session.username
                    self.session.username='default'
                    loginerror= ' Error: Invalid Username/Password pair. Please try again'
                    log.log(self, 'opening', self.action, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
                    return div(self.opening(loginerror=loginerror), c='opening')
            
            #self.session.username='default'
            log.log(self, 'opening', self.action, userid=userid, ipaddr=self.ip, query=str(self.query), sort=self.sort, groupby=self.group, facet=self.facet, count=self.count, offset=self.offset, indx=self.index, item=self.item, prevurl=self.prevurl)
            return div(self.opening(loginerror=loginerror), c='opening')

    def subheading(self):
        return [donebox(), br, Page.subheading(self)]

    def link(self, *stuff, **attrs): return link(self.url(**attrs), *stuff)

    def opening(self): raise NotImplementedError
    def middlegame(self): raise NotImplementedError
    def endgame(self): raise NotImplementedError
    def historygame(self): raise NotImplementedError
    def searchhistorygame(self): raise NotImplementedError
    
    def favesavehandler(self): raise NotImplementedError
    def managegame(self): raise NotImplementedError
    def managehandler(self): raise notImplementedError
    def helpgame(self): raise notImplementedError
    def loginbox(self): raise NotImplementedError
    def logoutwindow(self): raise NotImplementedError
    def createaccoutnwindow(self): raise NotImplementedError
    def taskcompleted(self): raise NotImplementedError

    #prevent bots from crawling flamenco generated pages. allow only on opening page; Flamenco with no parameters
    def metatag(self):
        if self.request.fields():
            return 'name="robots" content="noindex,nofollow"'
        return 'name="robots" content="index,nofollow"'
    
    def questions(self):
        return ''
        if not (self.session.get('userid') and self.session.get('taskid')):
            return ''
        radio = deftag(input, type='radio')
        cells = []
        for name in 'closer expected useful'.split():
            cells += td(name, ':', br,
                        [[radio(name=name, value=value), nbsp, value, nbsp]
                         for value in 'yes somewhat no'.split()])
        hidden = deftag(input, type='hidden')
        state = [hidden(name='q', value=self.query.serialize())]
        if self.facet: state.append(hidden(name='facet', value=self.facet))
        if self.group: state.append(hidden(name='group', value=self.group))
        if self.offset: state.append(hidden(name='offset', value=self.offset))
        ident = users[self.session.userid].name
        ident += ' (%s)' % tasks[self.session.taskid].name
        submit = input(type='submit', name='survey', value='record answers')
        return form(tablew(tr(cells, td(ident, br, submit, state)),
                           pad=4, bgcolor='#e0e0e0'))
