#!/usr/bin/env python
"""
Used to generate the config sections for WebKit.html.
"""

import re, string, sys


def toc(filename):
	f = open(filename)
	contents = f.read()
	f.close()
	list = eval(contents)
	for item in list:
		name, default, descr = item
		print '<p><dl class=config>'
		if len(default)<20:
			print '<dt class=config><span class=setting>%s</span>' % name
			print '&nbsp; <code> = %s</code></dt>' % default
			print '<dd class=config>'
			print '%s' % descr
			print '</dd>'
		else:
			print '<dt class=config><span class=setting>%s</span>' % name
			print '&nbsp; <code> = </code></dt>'
			print '<dd class=config>'
			print '<code>%s</code>' % string.strip(default)
			print '<br> %s' % descr
			print '</dd>'
		print '</dl></p>'
		print

def main(filename):
	# header
	print '''
<html>
	<head>
		<title>Config</title>
		<link rel=stylesheet href=StyleSheet.css type=text/css>
	</head>
<body>
<p>
'''
	toc(filename)
	print '''
</body>
</html>'''


if __name__=='__main__':
	for filename in sys.argv[1:]:
		main(filename)
