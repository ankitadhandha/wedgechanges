#!/usr/bin/env python
"""
Used to generate the config section for CGIWrapper.html from Config.list
"""


import re, string


def toc(filename='Config.list'):
	f = open(filename)
	contents = f.read()
	f.close()
	list = eval(contents)
	for item in list:
		name, default, descr = item
		print '<p><dl>'
		if len(default)<20:
			print '<dt><font face="Arial, Helvetica"><b>%s</b></font>' % name
			print '&nbsp; <code> = %s</code></dt>' % default
			print '<dd>'
			print '%s' % descr
			print '</dd>'
		else:
			print '<dt><font face="Arial, Helvetica"><b>%s</b></font></dt>' % name
			print '<dd>'
			print '<code>= %s</code>' % default
			print '<br> <hr> %s' % descr
			print '</dd>'		
		print '</dl></p>'
		print

def main():
	# header
	print '<html> <head><title>Config</title></head> <body>'
	print '<p>'
	toc()
	print '</body></html>'
	

if __name__=='__main__':
	main()
