#!/usr/bin/env python

__real_import__ = __builtins__.__import__

def custom_import(name, globals=None, locals=None, fromlist=[]):
	__real_import__(name, globals, locals, fromlist)
	print 'Hi'

__builtins__.__import__ = custom_import

import sys

print 'Done.'


# see ihooks.py
# see knee.py
# see imp
