#!/usr/bin/env python

# If the Webware installation is located somewhere else,
# then set the WebwareDir variable to point to it.
# For example, WebwareDir = '/Servers/Webware'
WebwareDir = None

# If you used the MakeAppWorkDir.py script to make a separate
# application working directory, specify it here.
AppWorkDir = None

try:
	import os, sys
	if not WebwareDir:
		WebwareDir = os.path.dirname(os.path.dirname(os.getcwd()))
	sys.path.insert(1, WebwareDir)
	webKitDir = os.path.join(WebwareDir, 'WebKit')
	if AppWorkDir is None:
		AppWorkDir = webKitDir
	else:
		sys.path.insert(1, AppWorkDir)

	try:
		import WebKit.Adapters.CGIAdapter
	except ImportError:
		cgiAdapter = os.path.join(webKitDir, 'Adapters/CGIAdapter.py')
		if not os.path.exists(cgiAdapter):
			sys.stdout.write("""\
Content-type: text/html

<html><body>
<p>ERROR
<p>I can't find the file %s.
<p>If that file really doesn't exist, then you need to edit WebKit.cgi so
that WebwareDir points to the actual Webware installation directory.
<p>If that file does exist, then its permissions probably need to be modified
with chmod so that WebKit.cgi can read it.  You may also need to modify
the permissions on parent directories.
""" % cgiAdapter)
		else:
			raise
	else:
		WebKit.Adapters.CGIAdapter.main(AppWorkDir)
except:
	import string, sys, traceback
	from time import asctime, localtime, time

	sys.stderr.write('[%s] [error] WebKit: Error in adapter\n' % asctime(localtime(time())))
	sys.stderr.write('Error while executing script\n')
	traceback.print_exc(file=sys.stderr)

	output = apply(traceback.format_exception, sys.exc_info())
	output = string.join(output, '')
	output = string.replace(output, '&', '&amp;')
	output = string.replace(output, '<', '&lt;')
	output = string.replace(output, '>', '&gt;')
	output = string.replace(output, '"', '&quot;')
	sys.stdout.write('''Content-type: text/html

<html><body>
<p>ERROR
<p><pre>%s</pre>
</body></html>\n''' % output)

