# Copyright (c) 2004-2006 The Regents of the University of California.

"""HTML generation utilities."""

import pydoc
from urllib import quote as urlenc, unquote as urldec
repr, esc = pydoc.html.repr, pydoc.html.escape

def flatten(stuff):
    if type(stuff) in (type([]), type(())): return ''.join(map(flatten, stuff))
    else: return str(stuff)

def join(sep, list):
    return zip(list, [sep]*(len(list)-1) + [''])
    if len(list) <= 1: return list
    result = list[:1]
    for item in list[1:]: result += [sep, item]
    return result

_rename={'pad': 'cellpadding', 'space': 'cellspacing', 'c': 'class'}.get
def _attrs(d): return ''.join([' %s="%s"' % (_rename(k, k), d[k])
                               for k in d if d[k] is not None])

def mktag(name, br=''): return lambda *stuff, **attrs: \
    ['<%s%s%s>' % (name, _attrs(attrs), br), stuff, '</%s>' % name, br]

for t in 'select option i strong big small code span label a textarea'.split():
    globals()[t] = mktag(t)
for t in 'h1 h2 h3 h4 h5 h6 table tr td th div form ul li blockquote'.split():
    globals()[t] = mktag(t, '\n')

def link(url, *stuff, **attrs): return a(href=url, *stuff, **attrs)
def textbox(name, cols, rows, *stuff, **attrs):
    return textarea(name=name, cols=cols, rows=rows, *stuff, **attrs)
def cls(c, *stuff, **attrs): return span(c=c, *stuff, **attrs)
def color(col, *stuff, **attrs):
    return span(style='color: %s' % col, *stuff, **attrs)
def input(**attrs): return ['<input%s>' % _attrs(attrs)]
def img(src, **attrs): return ['<img src="%s"%s>' % (src, _attrs(attrs))]
#def space(w, h=1): return div(nbsp, style='display: inline; background-color: #f00; width: %dpx; height: %dpx; font-size: 1px;' % (w, h))
#def space(w, h=1): return img(src='http://orange.sims.berkeley.edu/projects/flamenco/pics/pixel.gif', width=w, height=h, border=0)
def space(w, h=1): return img(src='pixel.gif', width=w, height=h, border=0)



def deftag(tag, **defaults):
    def result(*stuff, **attrs):
        dict = defaults.copy()
        dict.update(attrs)
        return tag(*stuff, **dict)
    return result

postform = deftag(form, method='post')
img = deftag(img, border=0)
table = deftag(table, pad=0, space=0, border=0)
tablew = deftag(table, width='100%')
tdc = deftag(td, align='center')
tdr = deftag(td, align='right')
trt = deftag(tr, valign='top')
trbl = deftag(tr, valign='baseline')
trb = deftag(tr, valign='bottom')
tdwr = deftag(td, align='right', width = '100%')
tdw = deftag(td, width='100%')
center = deftag(div, align='center')
p, br, nbsp = '\n<p>', '<br>\n', '&nbsp;'

def multicolumn(items, columns=3, rows=None, **attrs):
    cells = []
    if not rows:
        rows = (len(items) + columns - 1) / columns
    cellattrs = {'width': str(100/columns) + '%', 'c': 'column'}
    cell = []
    for item in items:
        cell.append(item)
        if len(cell) == rows:
            cells.append(td(cell, **cellattrs))
            cell = []
    if cell:
        cells.append(td(cell, **cellattrs))
    return tablew(trt(cells), **attrs)

def multicolumnbullet(items, columns=3, rows=None, **attrs):
    cells = []
    if not rows: rows = (len(items) + columns - 1) / columns
    if columns: width = {'width': str(100/columns) + '%'}
    cell = []
    for item in items:
        cell.append(li(item))
        if len(cell) == rows:
            cells.append(td(cell, **width))
            cell = []
    if cell: cells.append(td(cell, **width))
    return tablew(trt(ul(cells)), **attrs)

bodyprefix = '''<div style="display: none; position: absolute; width: 200px"
id="tooltip"></div><script type="text/javascript"><!--
d = document; b = d.body; w = window; dom = d.documentElement;

if (dom) { t = d.getElementById('tooltip'); s = t.style; }
function find(e) { ex = 0; ey = 0; eh = e.offsetHeight; ew = e.offsetWidth;
    while (e) { ex += e.offsetLeft; ey += e.offsetTop; e = e.offsetParent; } }
function show(e) { find(e); s.left = ex + 80; s.top = ey + eh + 5; s.display = ''; }
function hide() { s.display = 'none'; } 
function opensearchsave(page){
   winpops=window.open(page,"","width=425,height=275,status,scrollbars,resizable,")
}

function setscrollxy(form) {

   form.xposition.value=document.body.scrollLeft;
   form.yposition.value=document.body.scrollTop;
   }

function setposition(top, left) {
    document.body.scrollTop=top;
    document.body.scrollLeft=left;
    }

//-->

</script>'''

def plural(number, plural='s', singular=''):
    return number != 1 and plural or singular

def jsesc(text): return "'%s'" % text.replace('\\', '\\\\').replace(
    "'", "\\'").replace('"', '\\x22').replace('\n', '\\n')

_tipcount = 0
def tip(tip, anchor, c='tip'):
    global _tipcount; _tipcount += 1
    id = 'anchor%d' % _tipcount
    over = 'if (dom) { t.innerHTML=%s; show(d.getElementById(\'%s\')) }' % (
        jsesc(flatten(div(tip, c=c))), id)
    return span(anchor, id=id, onmouseover=over, onmouseout='if (dom) hide();')

def nobr(text): return text.replace(' ', '&nbsp;').replace('\n', '&nbsp;')
def abbrev(text, max):
    if len(text) > max: return tip(text, nobr(text[:max][:-2]) + '...')
    return nobr(text)
