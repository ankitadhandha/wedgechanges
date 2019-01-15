# Copyright (c) 2004-2006 The Regents of the University of California.

from Page import Page
from css import *
from html import *

class Palette(Page):
    def body(self, out):
        sat = float(self.form.get('sat', '0.5'))
        links = []
        for i in range(11):
            s = '%.1f' % (i/10.0)
            if s == str(sat): links += td(strong(s))
            else: links += td(link('Palette?sat=' + s, s))
        links = table(tr(td('saturation:'), links), space=5)
        rows = []
        for hue in range(0, 360, 10):
            row = []
            for value in [0.6, 0.7, 0.8, 0.9]:
                c = dsv(hue, sat, value)
                facetbox = c.desaturate()
                valuebox = light(c.desaturate())
                termbox = c.desaturate()
                termborder = c.saturate().darken()
                group = table(tr(td(strong('facet'), bgcolor=facetbox)),
                              tr(td('values', bgcolor=valuebox)), pad=2)
                style = 'border: 1px solid %s; ' % termborder
                style += 'padding: 3px; margin-bottom: 3px'
                term = table(tr(td(strong('Query'), ': term', bgcolor=termbox)),
                             style=style, pad=3)
                label = tdr(small('hue %d' % hue, br, 'value %.1f' % value))
                row += [td(table(tr(label, td(group), td(term)), space=3))]
            rows.append(tr(row))
        out.write(links, table(rows))
