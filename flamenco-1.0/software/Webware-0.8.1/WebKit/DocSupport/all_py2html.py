#!/usr/bin/env python

import os, string, sys
from glob import glob


for filename in glob('../../*.py'):
	targetname = os.path.split(filename)[1] + '.html'
	cmd = 'py2html.py -header:header.html -footer:footer.html -stdout %s > %s' % (filename, targetname)
	print os.system(cmd)
