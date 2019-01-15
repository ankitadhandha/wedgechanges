
"""
A bunch of utility functions for the PSP generator.

--------------------------------------------------------------------------
   (c) Copyright by Jay Love, 2000 (mailto:jsliv@jslove.net)

	Permission to use, copy, modify, and distribute this software and its
	documentation for any purpose and without fee or royalty is hereby granted,
	provided that the above copyright notice appear in all copies and that
	both that copyright notice and this permission notice appear in
	supporting documentation or portions thereof, including modifications,
	that you make.

	THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD TO
	THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
	FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
	INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
	FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
	NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
	WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

		This software is based in part on work done by the Jakarta group.

"""

import string
import copy

"""various utility functions"""



def removeQuotes(st):
	return string.replace(st,"%\\\\>","%>")

def isExpression(st):
	OPEN_EXPR = '<%='
	CLOSE_EXPR = '%>'
	
	if ((st[:len(OPEN_EXPR)] == OPEN_EXPR) and (st[-len(CLOSE_EXPR):] == CLOSE_EXPR)):
		return 1
	return 1

def getExpr(st):
	OPEN_EXPR = '<%='
	CLOSE_EXPR = '%>'
	length = len(st)
	if ((st[:len(OPEN_EXPR)] == OPEN_EXPR) and (st[-len(CLOSE_EXPR):] == CLOSE_EXPR)):
		retst = st[len(OPEN_EXPR):-(len(CLOSE_EXPR))]
	else:
		retst=''
	return retst


def checkAttributes(tagtype, attrs, validAttrs):

	#missing check for mandatory atributes
	#see line 186 in JSPUtils.java

	pass
	

