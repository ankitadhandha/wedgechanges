"""
FixPath.py

Enhance sys.path so that we're guaranteed to import the MiddleKit that
we reside in. This is particularly important for Webware developers
that might have more than one Webware source tree on their file system.
"""


# We're located at .../MiddleKit/Run/Tests/Test.py.
import os, sys
if sys.path and sys.path[0]=='':
	index = 1
else:
	index = 0
sys.path.insert(index, os.path.abspath('../..'))
import MiddleKit
