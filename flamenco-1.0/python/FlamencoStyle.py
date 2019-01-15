# Copyright (c) 2004-2006 The Regents of the University of California.

from Style import Style
from css import *
from app import db

colours = {}
for facet in db.facetlist:
    hue = float(db.facetprop(facet, 'hue'))
    value = float(db.facetprop(facet, 'value'))
    colours[facet] = dsv(hue, 0.5, value)

khaki = dsv(36, 0.5, 0.95)
greyorange = (orange*grey).lighten(0.8)
greyyellow = (yellow*grey).lighten(0.8)
greykhaki = khaki.lighten(0.7)
greygreen = (green*grey).lighten(0.8)

class FlamencoStyle(Style):
    def tasks(self):
        return [rule('.tasksbg', bg=light(red)),
                rule('.taskstablebg', bg=light(red), padding='5px'),
                rule('.tasksitem', bg=light(red.desaturate(), 0.7), padding='8px'),
                rule('.taskcompletebg', bg=light(grey.desaturate(), 0.9), padding='5px'),
                rule('.taskcompletebg2', bg=light(blue.desaturate(), 0.4), padding='5px'),
                rule('.taskerror', fg=red),
                rule('.taskset', style='italic')]
    
    def title(self): # style rules for the title box
        return [within('.title',
                       rule('', fg='#fd4', bg='#248', padding='16px'),
                       rule('h1', size='20px', weight='bold', margin='0'),
                       rule('h2', size='10px', weight='normal', margin='0'),
                       rule('a', color='#fd4', decoration='none'),
                       rule('h1 a', decoration='none')),
                rule('div.body', padding='16px'),
                rule('.loginerror', fg=red),
                rule('.loginheader', bg=light(grey), padding='5px'),
                within('.powered',
                       rule('', float='right', size='11px')),
                within('.login',
                       rule('', float='right', size='11px'),
                       rule('.user', weight='bold')),
                within('.toolbar',
                       rule('', float='right', size='11px'),
                       rule('a', decoration='none'),
                       rule('div.button', display='inline', padding='3px',
                            fg='#000', bg='#c0c8e0',
                            margin='0px 1px', border='1px solid',
                            border_color='#fff #77a #77a #fff'),
                       rule('div.button.disabled', fg=light(grey), bg=grey,
                            border='1px solid grey'))]

    def tips(self): # style rules for tool tips
        return [rule('.tip', padding='1px', border='1px solid #888',
                             bg='#ffe', family='tahoma, ' + sans, size='10px')]

    def facets(self): # style rules for facet names and boxes
        return [rule('.facet_' + facet + ' .facetbox', padding='3px 5px',
                     bg=light(colours[facet].desaturate(), 0.2))
                for facet in db.facetlist
           ] + [rule('.facet', xform='uppercase', weight='bold', size='90%'),
                rule('.opening .facetbox', size='14px'),
                rule('.middlegame .facetbox', size='12px', padding='2px 5px')]

    def values(self): # style rules for facet values
        return [rule('.facet_' + facet + ' .valuebox', padding='5px',
                     bg=light(colours[facet].desaturate(), 0.7))
                for facet in db.facetlist
           ] + [rule('.value', fg='#4040ff'),
                rule('.value.sel', fg=black),
                rule('.count', size='10px')]

    def query(self): # style rules for query term boxes
        return [rule('.facet_' + facet + ' .termbox',
                     bg=light(colours[facet].desaturate(), 0.2),
                     border='1px solid ' + colours[facet].darken(0.3),
                     padding='3px 4px', marginb='3px')
                for facet in db.facetlist
           ] + [within('.termbox',
                       rule(bg=light(grey), padding='3px 4px', marginb='3px',
                            border='1px solid ' + dark(grey)),
                       rule('a', fg='#e00', decoration='none'),
                       rule('.arrow', fg=grey),
                       rule('.removebox', marginl='5px')),
                rule('div.removebox', display='inline', 
                     weight='bold', size='11px',
                     fg='#e00', bg='#eee', border='1px solid #aaa',
                     padding='0 3px 2px 3px', vertical_align='1px'),
                ]

    def pagebar(self): # style rules for the pagebar
        return [rule('.offset', size='10px', fg='#223e71', bg='#e0c0d0',
                                padding='3px 0 0 1px'),
                rule('.offset.sel', weight='bold', fg=white, bg='#936')]

    def opening(self): # style rules for the opening
        return [rule('.matrix .column', padding='0 11px 0 0'),
                rule('.matrix .column:first-child', padding='0 11px'),
                rule('.valuebox .column', padding='0'),
                rule('.valuebox .column:first-child', padding='0')]

    def middlegame(self): # style rules for the middle game
        return [rule('.groupheadbox', bg='#d0b0d0'),
                rule('.grouphead', weight='bold'),
                rule('.resultbox', bg='#f0f0ff'),
                rule('.search', padding='11px', bg='#ddd'),
                rule('.search td', text_align='center'),
                rule('.search table', margin='auto'),
                rule('.facetcolumn', padding='0 11px'),
                rule('.facetcolumn .message', padding='5px 0'),
                rule('.facetcolumn .matrix', padding='0 0 16px'),
                rule('.itemcolumn', padr='11px'),
                rule('.itemlink', size='100%'),
                rule('.facetlink', size='100%'),
                rule('.metadatatitle', size='100%', weight='bold'),
                rule('.metadata', size='11px'),
                rule('.metadata2', size='100%', style='italic'),
                #rule('.metadata .missing', fg=light(grey), family=serif),
                rule('.historybox', bg=white, border='1px solid ' + black),
                rule('.historylink', size='100%', style='italic'),
                within('.categorylist',
                       rule('', padding='11px'),
                       rule('.query', padding='5px'),
                       rule('td.column', padding='5px'),
                       rule('.message', padding='5px'))]

    def endgame(self): # style rules for the end game
        return [rule('.metasubhead', fg='#b0b0b0', size='11px'),
                rule('.display', float='left', margin='0 16px 16px'),
                rule('.info', margin='0 16px'),
                rule('.info .minwidth', width='300px'),
                within('.metadata',
                       rule('.morelikebg', bg=light(grey.desaturate(), 0.8)),
                       rule('.facet', xform='uppercase', size='10px'),
                       rule('.attribute', xform='uppercase', size='10px'),
                       rule('.facetrepeat', fg=grey),
                       rule('.value', size='11px', fg='#8080ff'),
                       rule('.count', size='9px', fg=grey),
                       rule('.arrow', size='80%', fg=grey),
                       rule('.sel .value', size='11px', fg=blue),
                       rule('.sel .count', size='9px', fg=black)),
                
                rule('.attribute', weight='bold'),
                rule('.title', weight='bold', size='110%', fg=black),
                rule('.valuebox', bg='#f8f4f8', size='11px'),
                rule('.metadata1', size='100%', style='italic'),
                rule('.itembox', bg=light(blue.desaturate(), 0.85),
                     border='0px solid '+black, padding='8px')]

    def historygame(self): #style rules for the history page
        return [rule('.historygroup', weight='bold', 
                     bg=light(orange.desaturate(), 0.2)),
                rule('.metadata2', size='100%', style='italic'),
                rule('.historyitem', bg=light(orange.desaturate(), 0.7)),
                rule('.count', size='smaller', style='italic', weight='normal')]

    def popuphandler(self): #style rules for the search history page
        return [rule('.searchheader', size='115%', weight='bold', 
                     bg=light(khaki.desaturate(), 0.2)),
                rule('.date', size='80%', bg=light(khaki.desaturate(), 0.2)),
                rule('.searchbody', bg=light(khaki.desaturate(), 0.7)),
                rule('.count', size='smaller', style='italic', weight='normal'),
                rule('.favoritegroup', weight='bold', 
                     bg=light(yellow.desaturate(), 0.2)),
                rule('.favoriteitem', bg=light(yellow.desaturate(), 0.7)),
                rule('.groupname', style='italic', weight='normal', size='100%'),
                rule('.searchname', style='italic', weight='normal', size='100%')]

    def popupwindow(self):
        return [rule('.loginbg', bg=light(grey.desaturate(), 0.7),
                     padding='15px'),
                rule('.error', size='110%', fg=red),
                rule('.searchheader', size='115%', weight='bold', 
                     bg=light(khaki.desaturate(), 0.2)),
                rule('.date', size='80%', bg=light(khaki.desaturate(), 0.2)),
                rule('.searchbody', bg=light(khaki.desaturate(), 0.7), padding='10px'),
                rule('.count', size='smaller', style='italic', weight='normal'),
                rule('.favoritegroup', weight='bold', 
                     bg=light(yellow.desaturate(), 0.2)),
                rule('.favoriteitem', bg=light(yellow.desaturate(), 0.7))]

    def managegame(self):
        return [rule('.loginerror', fg=red),
                rule('.loginbg', bg=light(grey.desaturate(), 0.7),
                     padding='15px'),
                rule('.renamebg', bg=light(grey.desaturate(), 0.7),
                     padding='10px'),
                rule('.sectionheader', padding='8px'),
                rule('.searchheader', size='115%', weight='bold', 
                     bg=light(khaki.desaturate(), 0.2)),
                rule('.date', weight='bold', size='100%', bg=light(khaki.desaturate(), 0.2)),
                rule('.searchbody', padding='8px', bg=light(khaki.desaturate(), 0.7)),
                rule('.count', size='smaller', style='italic', weight='normal'),
                rule('.favoritegroup', style='italic', weight='bold', 
                     bg=light(yellow.desaturate(), 0.2)),
                rule('.favoriteitem', bg=light(yellow.desaturate(), 0.7)),
                rule('.historygroup', weight='bold', 
                     bg=light(orange.desaturate(), 0.2),
                     padding='5px'),
                rule('.historyitem', padding='8px', bg=light(orange.desaturate(), 0.7)),
                rule('.metadata2', size='100%', style='italic'),
                rule('.count', size='smaller', style='italic', weight='normal'),
                rule('.title', size='125%', weight='bold', fg=black),
                rule('.groupname', style='italic', weight='normal', size='100%'),
                rule('.searchname', style='italic', weight='bold', size='100%',
                     bg=light(khaki.desaturate(), 0.2)),
                rule('.introbox', bg=white, border='1px solid ' + black, 
                     padding='10px'),
                rule('.favoritebutton', bg=greyyellow, fg=black),
                rule('.favoritebutton2', bg=greyyellow, fg=black, width='1.2in'),
                rule('.favoritebutton3', bg=greyyellow, fg=black, width='2in'),
                rule('.favoritebutton4', bg=greyyellow, fg=black, width='1.75in'),
                rule('.favoritebutton5', bg=greyyellow, fg=black, width='1.1in'),
                rule('.favoritebutton6', bg=greyyellow, fg=black, width='1.3in'),
                rule('.searchbutton', bg=greykhaki, fg=black),
                rule('.searchbutton2', bg=greykhaki, fg=black, width='1.6in'),
                rule('.searchbutton3', bg=greykhaki, fg=black, width='1.7in'),

                rule('.changefacetsbox', padding='0px'),

                rule('.singleoptionbox', padding='5px'),
                
                rule('.previewtable', padding='10px'),
                rule('.editoptionsdisplay', size='110%'),
                rule('.favoritebg', bg=light(yellow)),
                rule('.searchbg', bg=light(khaki)),
                rule('.historybg', bg=light(orange)),
                rule('.optionsbg', bg=light(greygreen)),
                rule('.facetsbg', bg=light(blue)),
                rule('.attrsbg', bg=light(grey)),
                
                rule('.attrbox', bg=light(grey), padding='5px'),
                rule('.openingoptionbg', bg=light(yellow.desaturate(), 0.5),
                     padding='5px'),
                rule('.middleoptionbg', bg=light(orange.desaturate(), 0.7)),
                rule('.endoptionbg', bg=light(red.desaturate(), 0.7)),
                rule('.viewbar', size='105%'),
                rule('.editoptsviewbar', size='105%')]
                     

    def helpgame(self):
        return [rule('.title', size='125%', weight='bold', fg=black),
                rule('.favoritegroup', style='italic', weight='bold', 
                     bg=light(yellow.desaturate(), 0.2)),
                rule('.favoriteitem', bg=light(yellow.desaturate(), 0.7)),
                rule('.historygroup', weight='bold', 
                     bg=light(orange.desaturate(), 0.2)),
                rule('.historyitem', bg=light(orange.desaturate(), 0.7)),
                rule('.searchname', style='italic', weight='bold', size='100%',
                     bg=light(khaki.desaturate(), 0.2)),

                rule('.searchbody', bg=light(khaki.desaturate(), 0.7)),
                rule('.loginbg', bg=light(grey.desaturate(), 0.7))]

    def stylesheet(self):
        return [rule('body, td', family=sans, margin=0, size='12px'),
                self.tasks(),
                self.title(),
                self.tips(),
                self.facets(),
                self.values(),
                self.query(),
                within('.opening', self.opening()),
                within('.middlegame', self.middlegame()),
                within('.endgame', self.endgame()),
                within('.pagebar', self.pagebar()),
                within('.historygame', self.historygame()),
                within('.popuphandler', self.popuphandler()),
                within('.popupwindow', self.popupwindow()),
                within('.managegame', self.managegame()),
                within('.managehandler', self.managegame()),
                within('.helpgame', self.helpgame()),

                rule('.matchbox', bg='#efefff', size='80%'),
                rule('.donebox', bg='#8080c0', padding='3px'),
                rule('.donebox A', fg=white)]
