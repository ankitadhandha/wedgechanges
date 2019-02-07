# Copyright (c) 2004-2006 The Regents of the University of California.

from app import db, coll
from html import *
from string import capitalize, capwords

def searchbox(query, value='', facet='', task=None,
              selectscope=0, defaultscope='all'):
    entry = [input(type='text', size='14', name='words', value=value or None),
             nbsp, input(type='submit', value='search'),
             input(type='hidden', name='q', value=query.serialize()),
             input(type='hidden', name='facet', value=facet)]
    if task:
        entry += [input(type='hidden', name='task', value=task)]
    if selectscope:
        scopes = []
        for scope, description in [('all', 'all items'),
                                   ('current', 'in current results')]:
            button = input(type='radio', name='in', value=scope, id=scope,
                           checked=(scope == defaultscope) and 1 or None)
            scopes += [button, label(description, for_=scope), nbsp*2]
        contents = trb(td(entry)), trb(td(scopes))
    else:
        contents = trb(td(entry, input(type='hidden', name='in', value='all')))
    return form(table(contents), c='search')

def pagecount(offset, count, perpage=coll.ITEMS_PER_UNGROUPED_PAGE):
    if count <= perpage:
        return '%d result%s' % (count, plural(count))
    if offset + 1 == count:
        return 'item %d of %d results' % (offset + 1, count)
    else:
        return 'items %d to %d of %d results' % (offset + 1,
            min(offset + perpage, count), count)

def pagebar(offset, count, link,
            perpage=coll.ITEMS_PER_UNGROUPED_PAGE, head=1, boxes=12, **attrs):
    heading = head and center(pagecount(offset, count, perpage)) or ''
    if count <= perpage: return heading
    offsets = range(0, count, perpage)
    while len(offsets) > boxes:
        if offsets.index(offset) >= len(offsets)/2: offsets[1:2] = []
        else: offsets[-2:-1] = []
    prev, next = offset - perpage, offset + perpage
    cells, last = [], 0
    for i in offsets:
        if i > last + perpage: cells += td('...')
        number = div(i + 1, style='width: %dpx' % min(count - i, perpage))
        if i != offset: number = link(number, offset=i)
        cells += td(number, c='offset' + (i == offset and ' sel' or ''))
        last = i
    return [heading, table(trb(cells), space=1, c='pagebar', **attrs)]

def grouplist(query, facet, parent, link, columns=3):
    groups = db.groups(query, facet, parent)
    groups.sort()
    rows = int((len(groups) + columns - 1) / columns)
    cells = []
    for col in range(columns):
        list = []
        for row in range(rows):
            i = col * rows + row
            if i >= len(groups): break
            name, id, count = groups[i]
            list += [link(esc(name), term=(facet, id, 0)), ' ',
                     cls('count', '(%d)' % count), br]
        cells += td(list)
    return [p, tablew(trt(cells))]

def groupitems(query, facet, parent, link, links=0, buttons=0,
               perpage=coll.ITEMS_PER_GROUPED_PAGE,
               pergroup=coll.ITEMS_PER_GROUP, perrow=coll.ITEMS_PER_ROW,
               sort=None, order=None, **args):
    groups = db.groups(query, facet, parent, order=order)
    parents = db.parentlist(facet, [id for name, id, count in groups])

    totalcount = 0
    for name, id, count in groups:
        totalcount += count
    if totalcount <= perpage: limit = None
    elif len(groups) == 1: limit = perpage
    else: limit = pergroup

    rows = []
    for name, id, count in groups:
        term = (facet, id, 0)
        head = cls('grouphead', name or 'none')
        if links: head = link(head, term=term)
        rows.append((head, term, buttons and id and count > 1, count, limit))
    term = (facet, parent, 1)
    count = db.count(query + term)
    if count:
        name = [big(nbsp), groups and '(others)' or '(all)']
        rows.append((name, term, buttons and count > 1, count, pergroup))

    results = []
    for head, term, refine, count, limit in rows:
        q = query + term
        items = db.list(q, limit=limit, sort=sort)
        #if user clicks on all _number_ items, go to ungrouped view
        more = limit and count > limit and link(
            'all %d items...' % count, term=term, group=None)
        listing = itemtable(items, more=more, link=link, query=q, **args)
        if refine:
            tip = 'look only within these %d items' % count
            button = link(img(coll.DETAIL_SRC, alt=tip), term=term)
        else: button = nbsp
        results += [p, tablew(tr(td(head, nbsp, cls('count', '(%d)' % count),
                                    nbsp*2, button, c='facetbox')),
                              tr(td(listing, c='valuebox')),
                              c='facet_' + facet)]
    return results

def listitems(query, offset=0, perpage=coll.ITEMS_PER_UNGROUPED_PAGE,
              perrow=coll.ITEMS_PER_ROW, sort=None, maxnumdisplay=None, **args):
    print "SORT"
    print sort
    if maxnumdisplay is None:
        return itemtable(db.list(query, (offset, perpage), sort),
                     perrow, query=query, offset=offset, **args)
    else:
        result = []
        numresults = len(db.list(query, (offset, perpage), sort))
        for i in range(maxnumdisplay):
            if i < numresults:
                result.append(db.list(query, (offset, perpage), sort)[i])
        #print len(result)
        return itemtable(result, perrow, query=query, offset=offset, **args)

#given a list of items, puts themin an itemtable
def listhistory(items, query=None, index=None, 
                perrow=coll.ITEMS_PER_HISTORY_ROW, checkboxes=None, ids=None, 
                counter=None, limit=None, **args):
    return itemtable(items, perrow=perrow, history=1, checkboxes=checkboxes, 
                     ids=ids, counter=counter, limit=limit, **args)

def itemtable(items, perrow=coll.ITEMS_PER_ROW, more=None, offset=0, 
              history=None, user=None, manage=None, mini=None, imageonly=None, 
              checkboxes=None, ids=None, counter=None, limit=None, **args):
    
    if limit:
                
        tablelen=min(len(items), limit)
    else:
        tablelen=len(items)
                
    if checkboxes or manage and counter is not None:
        if coll.IMAGE_COLLECTION:
            cells = [td(coll.itemlisting(items[i], i+offset, history=history, 
                                         mini=mini, imageonly=imageonly, **args), 
                     input(type='checkbox',
                           name='checked%d' % (counter + i), 
                           value=ids[i]), c='itemlisting')
                     for i in range(tablelen)]
        else:
            #print "ITEMTABLE"
            #print range(len(items))
            
            cells = [
                     trt(td(input(type='checkbox',
                                  name='checked%d' % (counter + i), 
                                  value=ids[i])),
                         td(coll.itemlisting(items[i], i + offset,
                                             history=history, mini=mini,
                                             imageonly=imageonly, **args),
                            c='itemlisting'))
                     for i in range(tablelen)]
    else:
        cells = [td(coll.itemlisting(items[i], i + offset, history=history, 
                                     imageonly=imageonly, **args),
                    c='itemlisting')
                 for i in range(tablelen)]
    rows = []
    for i in range(0, len(cells), perrow):
        rows += trb(cells[i:i + perrow])
    if more: rows += tr(tdr(more, colspan=perrow))
    
    return tablew(rows, pad=2)

def groupselect(query, facet, group):
    count = db.count(query)
    if not count: return ''
    select, option = mktag('select'), mktag('option')
    options = []
    for f in [''] + db.facetlist:
        name = f and db.name(f) or '(none)'
        if f == group: options += option(name, value=f, selected=1)
        else: options += option(name, value=f)
    return form('%d item%s selected.  Group by: ' % (count, plural(count)),
                input(type='hidden', name='q', value=query.serialize()),
                input(type='hidden', name='facet', value=facet),
                select(options, name='group'), input(type='submit', value='go'))

def linepath(facet, id, link):
    output = cls('facet', db.name(facet), ': ')
    output += link('any', term=(facet, 0, 0))
    for step in db.path(facet, id):
        text = cls('value', db.name(facet, step))
        if step != id: text = link(text, term=(facet, step, 0))
        output += [' &gt; ', text]
    return output

def indentpath(facet, id, query, link, links=0, buttons=0):
    path = db.path(facet, id)
    steps = [(0, small(db.name(facet).upper()))] + [
        (step, esc(db.name(facet, step))) for step in path]
    output = []
    indent = 0
    for step, text in steps:
        sel = (step == id) and ' sel' or ''
        term = (facet, step, 0)
        if links and not sel: text = link(text, term=term)
        if indent > 20: output += space(indent-20)
        if indent > 0: output += img(coll.ANGLE_SRC)
        output += [cls('value' + sel, text)]
        if step and buttons:
            count = db.count(query + term)
            if count > 1:
                output += [nbsp] + cls('count', '(%d)' % count)
                tip = 'look only within these %d items' % count
                icon = img(coll.DETAIL_SRC, alt=tip, align='absmiddle')
                output += [nbsp, link(icon, term=term)]
        output += [br]
        indent += 20
    return output

def facetlist(link, facet):
    links = []
    for f in db.facetlist:
        links.append(cls('facet' + (f == facet and ' sel' or ''), db.name(f)))
    return join(' | ', links)

def facetheading(f, path, link):
    return [link(cls('facet', db.name(f)), facet=f, term=(f, 0, 0)), path]

def facetpath(f, id, link=None, tips=0):
    path = []
    for step in db.path(f, id):
        sel = (step == id) and ' sel' or ''
        text = cls('value' + sel, db.name(f, step))
        if not sel and link:
            text = link(text, term=(f, step, 0))
            if tips:
                text = tip('include items classified under "%s"' %
                           db.name(f, step), text)
        if sel and tips:
            text = tip('all current results are classified under "%s"' %
                       db.name(f, step), text)
        path += [cls('arrow', ' &gt; '), text]
    return path[1:]

def facetmatrix(query, link, fhead=facetheading, morelink=lambda t, f: t,
                columns=2, values=10, expand=None, term_columns=2,
                column_width_chars=1000, displayfacets=db.facetlist,
                sortbylist=None, capslist=None, username=None,
                showtooltips=1):

    parent = {}
    columns = int(columns)
    values = int(values)

    for facet in db.facetlist: parent[facet] = 0
    for facet, id, leaf in query.getterms(): parent[facet] = id
    height = int((len(db.facetlist) + columns - 1) / columns)
    facets = []

    for i in range(len(displayfacets)):
        f = displayfacets[i]
        order = sortbylist[i]
        caps = capslist[i]
        
        numcols = int(term_columns)
        if expand is None or f in expand:
            names = db.groups(query, f, parent[f], limit=values+1, order=order)
            widths = [len(value[0].strip()) for value in names[:values - 1]]
            if widths and max(widths) > column_width_chars:
                numcols = 1
            more = (len(names) > values)
            separator = term_columns and br or ', '
            links = []
            for name, id, count in names:
                if count > 0:
#                   if caps == 'first word': modname=capitalize(name.lower())
#                   elif caps == 'all words': modname=capwords(name.lower())
#                   else: modname=name.lower()
                    term = [link(name, facet=f, term=(f, id, 0),
                                 count=count), nbsp,
                            cls('count', '(%s)' % count), separator]
                    if showtooltips:
                        subcats = db.db.select('name', f, 'parent=%s' % id)
                        if subcats:
                            subtip = ['Subcategories:',
                                   div(join(br, [row[0] for row in subcats]),
                                       c='subcategories')]
                        else:
                            subtip = '(no subcategories)'
                    
                        links.append(tip(subtip, term))
                    else:
                        links.append(term)
            #links = [[link(esc(capitalize(name.lower())), 
            #               facet=f, term=(f, id, 0), count=count),
            #          nbsp, '(', cls('count', count), ')', separator]
            #          for name, id, count in names if count > 0]
            if more: links[values:] = [[morelink('more...', f), separator]]
            if links: links[-1][-1:] = []
        else: links = [] 
        if numcols:
            links = multicolumn(links, numcols, c='facetlink')
        heading = fhead(f, facetpath(f, parent[f], link), link, names)
        
        #print heading
        active = parent[f] and ' active' or ''
        facets.append([p, tablew(tr(td(heading, c='facetbox')),
                                 tr(td(links, c='valuebox')),
                                 c='facet_' + f + active)])
    return multicolumn(facets, columns, c='matrix')

def termbox(term, link, c='termbox', path=1, button=1, **attrs):
    facet, value, leaf = term
    name = cls('facet', db.name(facet))
    xbutton = tip(coll.X_ALT, div('&times;', c='removebox'))
    xbutton = button and link(xbutton, remove=term) or ''

    #xbutton = button and tip(coll.X_ALT, div(link('&times;', remove=term), c='removebox')) or ''
    if path:
        path = facetpath(facet, value, link, tips=1)
        if path and not button:
            all = link('all', term=(facet, 0, 0))
            label = [name, ': ', all , cls('arrow', ' &gt; '), path]
        else: label = [name, ': ', path]
    else: label = [name, ': ', cls('value sel', db.name(facet, value))]
    return div(table(tr(td(label), td(xbutton)), c=c, **attrs),
               c='facet_' + facet)

def wordbox(word, link, c='termbox', button=1, **attrs):
    if button:
        xbutton = tip(coll.X_ALT, div('&times;', c='removebox'))
        xbutton = link(xbutton, remove=word)
    else: xbutton=[]
    label = cls('term', 'keyword', ' "' + esc(word) + '"')
    label = tip('only showing items matching keyword "%s"' % word, label)
    return table(tr(td(label), td(xbutton)), c=c, **attrs)

def donebox():
    content = link('Survey', 'Please give us feedback!', target='_new')
    return table(tr(td(content)), c='donebox')

#caps insensitive comparison function for usew ith Floogle
def nocapscomp(x, y): return cmp(str(x[0]).lower(), str(y[0]).lower())

def userfacets(username):
    #print userfacets
    facets = db.db.select(['facets'], 'user', "name='%s'" % username)
    result = []
    for facetname in facets[0][0].split(', '):
        result.append(db.name(facetname))
    return result
