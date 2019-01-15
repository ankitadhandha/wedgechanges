from AdminSecurity import AdminSecurity
from Queue import Queue
from WebUtils.Funcs import htmlEncode
import os, string, time


class ServletCache(AdminSecurity):
	"""
	This servlet displays, in a readable form, the internal data
	structure of the application known as the "servlet cache by path".

	This can be useful for debugging WebKit problems and the
	information is interesting in general.
	"""

	def title(self):
		return 'Servlet Cache'

	def writeContent(self):
		cache = self.application()._servletCacheByPath
		self.writeln(htCache(cache))


def sortSplitFilenames(a, b):
	""" This is a utility function for list.sort() that handles list elements that come from os.path.split. We sort first by base filename and then by directory, case insensitive. """
	result = cmp(string.lower(a['base']), string.lower(b['base']))
	if result==0:
		result = cmp(string.lower(a['dir']), string.lower(b['dir']))
	return result


def htCache(cache):
	html = []
	wr = html.append

	keys = cache.keys()
	keys.sort()

	wr('%d unique paths exist in the servlet cache.' % len(keys))

	wr('<p> Click any link to jump to the details for that path.')

	wr('<p> Filenames:')
	wr('<table>')
	wr('<tr> <td> File </td> <td> Directory </td> </tr>')
	paths = []
	for key in keys:
		dir, base = os.path.split(key)
		path = { 'dir': dir, 'base': base, 'full': key }
		paths.append(path)
	paths.sort(sortSplitFilenames)
	# At this point, paths is a list where each element is a tuple
	# of (basename, dirname, fullPathname) sorted first by basename
	# and second by dirname
	for path in paths:
		wr('<tr> <td> <a href=#%s>%s</a> </td> <td> %s </td> </tr>\n' % (id(path['full']), path['base'], path['dir']))
	wr('</table>')

	wr('<p> Full paths:')
	for key in keys:
		wr('<br> <a href=#%s>%s</a>\n' % (id(key), key))

	wr('<p> Details:')
	wr('<table align=center border=0 cellpadding=2 cellspacing=2>\n')

	spacer = '&nbsp;'*8
	for path in paths:
		wr('<tr> <td colspan=2> <br> <a name=%s><strong>%s</strong> - %s</a> </td> </tr>\n' % (id(path['full']), path['base'], path['dir']))
		wr('<tr> <td nowrap>%s</td> <td> ' % spacer)
		wr(htRecord(cache[path['full']]))
		wr('</td> </tr>')
	wr('</table>')

	return string.join(html, '')


def htRecord(record):
	html = []
	wr = html.append
	wr('<table border=0 width=100%>')
	keys = record.keys()
	keys.sort()
	for key in keys:
		htKey = htmlEncode(key)

		# determine the HTML for the value
		value = record[key]
		htValue = None

		# check for special cases where we want a custom display
		if hasattr(value, '__class__'):
			if issubclass(value.__class__, Queue):
				htValue = htQueue(value)
		if key=='timestamp':
			htValue = '%s (%s)' % (time.asctime(time.localtime(value)), str(value))

		# the general case:
		if not htValue:
			htValue = htmlEncode(str(value))

		wr('<tr> <td bgcolor=#EEEEEE> %s </td> <td bgcolor=#EEEEEE> %s </td> </tr>' % (htKey, htValue))
	wr('</table>')
	return string.join(html, '')


def htQueue(queue):
	# @@ 2002-03-21 ce: Could probably do something nicer here in the
	# future, like put a <br> in between each element of the queue.
	return 'Queue: ' + htmlEncode(str(queue.queue))
