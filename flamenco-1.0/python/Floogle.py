# Copyright (c) 2004-2006 The Regents of the University of California.

from InterfaceBase import InterfaceBase
from Flamenco import Flamenco
from app import *
from components import *
from html import *
from query import Query
import re

class Floogle(Flamenco):
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
            prompt=self.loginbanner(post=self.url())
        else:
            prompt = self.loggedinbox(name)
                
        self.session.useridx = users.index(name)
        self.session.username = name
        
        userfacets = coll.facetlist
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
                
        return tablew(tr(td(self.taskbar(), colspan=2)), tr(td(nbsp)),
                      tr(td(prompt, width='60%'), td(nbsp)),
                      tr(td(nbsp)), tr(td(strong("Enter keywords to search the collection for: "))),
                      tr(td(nbsp)), tr(td(searchbox(query=self.query, task=self.task))), width='100%')


    #def opening(self, loginerror=None):
#	return [p, strong("Enter keywords to search the collection for: "), 
#                p, searchbox(query=self.query)]
    def newsearch(self, inresults=0, value=''):
	return tablew(tr(td(searchbox(query=self.query, selectscope=inresults, value=value))))
    
    def middlegame(self):
        if self.form.get('popuphandle', ''):
            self.popuphandler()
        
	result = self.searchresults()
        
        #return [self.taskbar(), p,
        #        table(self.loggedinbanner(), width='60%'), p, self.newsearch(value=str(self.query).replace('/', ' ')), br*2, self.pagelinks(self.offset), br*2,
	#	table(result), br*3, self.pagelinks(self.offset), br*2, 
        #        self.newsearch(value=str(self.query).replace('/', ' '))]
        return [self.taskbar(), p,
                table(self.loggedinbanner(), width='60%'), p, self.newsearch(value=' '.join(self.words)), br*2, self.pagelinks(self.offset), br*2,
		table(result), br*3, self.pagelinks(self.offset), br*2, 
                self.newsearch(value=' '.join(self.words))]
    
    	
    def searchresults(self, sort=None):
        return [tablew(tr(td(strong(pagecount(self.offset, self.count).capitalize()))), 
		       tr(td(listitems(self.query, self.offset, link=self.link,
                                       sort=self.sortkeys))))]

    def pagelinks(self, offset):
        if self.count==0:
            return []
	result = []
	totalnumpages = self.count/coll.ITEMS_PER_UNGROUPED_PAGE + 1
	tempoffset = offset
	decapagecounter = 0
	morepages=0
	while(tempoffset/(10*coll.ITEMS_PER_UNGROUPED_PAGE) > 0):
	    tempoffset = tempoffset - 10*coll.ITEMS_PER_UNGROUPED_PAGE
	    decapagecounter = decapagecounter + 1
	if totalnumpages > (decapagecounter + 1) * 10: #this means there's a "next10"
	    pagerange = range(decapagecounter*10, (decapagecounter+1)*10)
	    morepages=1
	else: pagerange = range(decapagecounter*10, totalnumpages) 
	for x in pagerange:    
	    if ((x * coll.ITEMS_PER_UNGROUPED_PAGE <= offset) and 
                ((x+1) * coll.ITEMS_PER_UNGROUPED_PAGE > offset)): 
                result += td(x+1)
	    else: result += td(self.link(x + 1, offset = x*coll.ITEMS_PER_UNGROUPED_PAGE))
	    result += td(nbsp*2)
	result += td(nbsp*2)

	
#only show next link if there are subsequent pages
	if not (offset+coll.ITEMS_PER_UNGROUPED_PAGE > self.count):
	    result += td(self.link(img(coll.RIGHT_ARROW_SRC), 
                                   offset=offset+coll.ITEMS_PER_UNGROUPED_PAGE))
	if offset >= coll.ITEMS_PER_UNGROUPED_PAGE:
	    result = td(self.link(img(coll.LEFT_ARROW_SRC), 
                        offset=offset - coll.ITEMS_PER_UNGROUPED_PAGE),
                        nbsp*4) + result

	result2 = [tdwr("     ", width='50%'), tdw("     ", width='50%')]
	if decapagecounter > 0: 
	    result2[0] = td(self.link(strong("Prev 10"), 
                              offset=(decapagecounter - 1) * 
                                     coll.ITEMS_PER_UNGROUPED_PAGE*10),
                                     nbsp*5, width='50%')
	if morepages: result2[1] = tdr(self.link(strong("Next 10"), 
                                       offset=(decapagecounter + 1) * 
                                              coll.ITEMS_PER_UNGROUPED_PAGE * 10), width='50%')
	return tablew(tr(tdc(table(tr(tdc('Result Page:', nbsp*5, result))))), 
                                   tr(td(nbsp)), 
                                   tr(tdc(table(tr(td(nbsp, width='20%'), result2[0], result2[1]), width='45%'))))

    def itemdisplay(self):
        prev = next = []
        if self.index > 0:
            prev = [td(self.link(img(coll.LEFT_ARROW_SRC), index=self.index-1,
                                 oldquery=self.oldquery)),
                    td(self.link('previous', index=self.index - 1,
                                 oldquery=self.oldquery))]
        if self.index and self.index < self.count - 1:
            next = [tdr(self.link('next', index=self.index + 1,
                                  oldquery=self.oldquery)),
                    tdr(self.link(img(coll.RIGHT_ARROW_SRC),
                                  index=self.index+1, oldquery=self.oldquery))]
        back = self.link('back to results', index=None, offset=self.offset,
                         query=self.oldquery or self.query)
        if self.index:
            head = tablew(tr(tdc(
                'item ', self.index + 1, ' of ', self.count, ' (', back, ')')))
        else:
            head=tablew(tr(tdc(nbsp)))
        nav = tablew(tr(prev, td(width='100%'), next, c='pagebar'), space=2)
        item = coll.itemdisplay(self.item, self.request)
        return [head, nav, item, p]

    def queryinfo(self, historyview=None):
        self.index = None
        words = self.query.getwords()
        metadata = db.metadata(self.item)
        refine, expand = [], []
        linknames=[]
	for f in coll.facetlist:
            if metadata[f]:
                name = db.name(f) + ':' + nbsp*2
                terms = coll.queryinfo_terms(f, metadata[f])
		refine.append(trbl(td(strong(name)), 
                                   td(join(', ', [namey for namey, term in terms]))))
		for namey, term in terms:
		    linknames.append(str(namey))
	linknames.sort(nocapscomp) #need to fix this so it's not caps sensitive
	for keyword in linknames:
	    expand.append(trbl(td(join(', ',
		[link(self.__class__.__name__+'?words=' + keyword+'&task='+self.task, keyword)]))))

        for a in coll.attrlist:
            #fix for -1 values in db; if -1, replace value with N/A
            if metadata[a]:
                name = cls('attribute', db.name(a) + ':' + nbsp*2)
                value = metadata[a]
                if value==-1:
                    value='N/A'
                refine.append(trbl(td(name), td(value)))
	querystring = ""
	for keyword in words: querystring = querystring + ' ' + str(keyword)
	#for part in range(len(words)): querystring = querystring + words[part] + " "
        return [p, tablew(tr(tdr(self.newsearch(inresults=0, value=str(self.query).replace('/', ' '))))), p, 
                tablew(tr(td('Current search: ' + querystring))),
                p,
                p, cls('metaheading',
                'Details about this image:'),
                p, table(refine), p, '<hr>',
                p, cls('metaheading',
                'Perform search on relevant keywords:'), p, table(expand), 
                tablew(tr(td(nbsp)),
                       tr(tdr(self.newsearch(inresults=0, value=str(self.query).replace('/', ' ')))))]
	

