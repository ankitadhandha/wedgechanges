import string, sys, traceback
from Funcs import htmlEncode


# @@ 2000-04-10 ce: change these so they're general args to the tags rather than just the colors
HTMLForExceptionOptions = {
	'table.bgcolor':        '#F0F0F0',
	'default.fgcolor':      '#000000',
	'row.location.fgcolor': '#0000AA',
	'row.code.fgcolor':     '#FF0000'
}


def HTMLForException(excInfo=None, options=None):
	""" Returns an HTML string that presents useful information to the developer about the exception. The first argument is a tuple such as returned by sys.exc_info() which is in fact, invoked if the tuple isn't provided. """
	# @@ 2000-04-17 ce: Maybe excInfo should default to None and get set to sys.excInfo() if not specified. If so, then clean up other code.

	# Get the excInfo if needed
	if excInfo is None:
		excInfo = sys.exc_info()

	# Set up the options
	if options:
		opt = HTMLForExceptionOptions.copy()
		opt.update(options)
	else:
		opt = HTMLForExceptionOptions

	# Create the HTML
	res = [
		'<table bgcolor=%s width=100%% cellpadding=4><tr><td>\n' % opt['table.bgcolor'],
		'<pre><font color=%s>' % opt['default.fgcolor']
		]
	out = apply(traceback.format_exception, excInfo)
	for line in out:
		if string.find(line, 'File ')!=-1:
			parts = string.split(line, '\n')
			parts = map(lambda s: htmlEncode(s), parts)
			parts[0] = '<font color=%s>%s</font>' % (opt['row.location.fgcolor'], parts[0])
			parts[1] = '<font color=%s>%s</font>' % (opt['row.code.fgcolor'], parts[1])
			line = string.join(parts, '\n')
			res.append(line)
		else:
			res.append(htmlEncode(line))
	if out:
		if res[-1][-1]=='\n':
			res[-1] = string.rstrip(res[-1])
	res.extend([
		'</font></pre>',
		'</td></tr></table>\n'
		])
	return string.join(res, '')
