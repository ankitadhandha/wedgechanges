import string, sys, traceback
from Funcs import htmlEncode


# @@ 2000-04-10 ce: change these so they're general args to the tags rather than just the colors
HTMLForExceptionOptions = {
	'table.bgcolor':        '#F0F0F0',
	'default.fgcolor':      '#000000',
	'row.location.fgcolor': '#0000AA',
	'row.code.fgcolor':     '#FF0000'
}

def ExpansiveHTMLForException(context=5, options=None):
	from WebUtils import cgitb
	if options:
		opt = HTMLForExceptionOptions.copy()
		opt.update(options)
	else:
		opt = HTMLForExceptionOptions
	return cgitb.html(context=context, options=opt)
