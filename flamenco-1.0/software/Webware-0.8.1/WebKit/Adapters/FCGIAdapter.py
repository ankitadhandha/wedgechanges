#!/usr/bin/env python

"""
FCGIAdapter.py

FCGI Adapter for the WebKit application environment.

Note: FCGI for Webware is not available on Windows.

This script is started by the Web Server and is kept running.
When a request comes through here, this script collects information
about the request, puts it into a package, and then invokes the
WebKit Application to handle it.

Original CGI implementaion by Chuck Esterbrook.

FastCGI Implementation by Jay Love. Based on threaded fcgi example "sz_fcgi" provided by "Andreas Jung"



SETUP

To use this adapter, you must have a fastcgi capable web server.

For Apache, you'll need to add the following lines to your httpd.conf file, or
put them in another file and include that file in httpd.conf

#I have the file in my cgi-bin directory, but you might as well put it in html.
#the -host is the port it communicates on
FastCgiExternalServer ../cgi-bin/FCGIWebKit.py -host localhost:33333 # the path is from the SERVER ROOT

<Location /FCGIWebKit.py>  #or whatever name you chose for the file above
 SetHandler fastcgi-script
 Options ExecCGI FollowSymLinks
</Location>


You could also take an extension oriented approach in Apache using '.fcgi':

	AddHandler fastcgi-script fcgi


And then using, in your URLs, 'WebKit.fcgi' which is a link to this file. e.g.,:

	http://localhost/Webware/WebKit/WebKit.fcgi/Introspect



FUTURE

(*) There are some interesting lines at the top of fcgi.py:

# Set various FastCGI constants
# Maximum number of requests that can be handled
FCGI_MAX_REQS=1
FCGI_MAX_CONNS = 1

# Boolean: can this application multiplex connections?
FCGI_MPXS_CONNS=0

Do these need to be adjusted in order to realize the full benefits of FastCGI?

(*) Has anyone measured the performance difference between CGIAdapter and FCGIAdapter? What are the results?

JSL- It's twice as fast as straight CGI



CHANGES

* 2000-05-08 ce:
	* Fixed bug in exception handler to send first message to stderr, instead of stdout
	* Uncommented the line for reading 'address.text'
	* Switched from eval() encoding to marshal.dumps() encoding in accordance with AppServer
	* Increased rec buffer size from 8KB to 32KB
	* Removed use of pr() for feeding app server results back to webserver. Figure that's slightly more efficient.
	* Added notes about how I set this up with Apache to what was already there.

*2001-03-14 jsl:
    * Fixed problem with post data

"""

##"""Set WebKitDir to the directory where WebKit is located"""
WebKitDir = '/data/Linux/python/Webware/WebKit'





import fcgi, time
from marshal import dumps, loads
from socket import *
import string
import os
import sys

timestamp = time.time()


_AddressFile='address.text'


HTMLCodes = [
	['&', '&amp;'],
	['<', '&lt;'],
	['>', '&gt;'],
	['"', '&quot;'],
]

def HTMLEncode(s, codes=HTMLCodes):
	""" Returns the HTML encoded version of the given string. This is useful to display a plain ASCII text string on a web page. (We could get this from WebUtils, but we're keeping CGIAdapter independent of everything but standard Python.) """
	for code in codes:
		s = string.replace(s, code[0], code[1])
	return s

if os.name != 'posix':
	print "This adapter is only available on UNIX"
	sys.exit(1)

fcgi._startup()
if not fcgi.isFCGI():
	print "No FCGI Environment Available"
	print "This module cannot be run from the command line"
	sys.exit(1)



addrfile=os.path.join(WebKitDir, _AddressFile)
(host, port) = string.split(open(addrfile).read(), ':')
port = int(port)

os.chdir(WebKitDir)
sys.path.append(os.path.abspath(os.path.join(WebKitDir, "..")))

from Adapter import Adapter

class FCGIAdapter(Adapter):
	def run(self):
		"""Block waiting for new request"""
		while fcgi.isFCGI():
			req=fcgi.FCGI()
			self.FCGICallback(req)

	def FCGICallback(self,req):
		"""This function is called whenever a request comes in"""
		import sys

		try:
			# Transact with the app server
			response = self.transactWithAppServer(req.env, req.inp.read(), host, port)

			# deliver it!
			req.out.write(response)
			req.out.flush()
		except:
			import traceback

			# Log the problem to stderr
			stderr = req.err
			stderr.write('[%s] [error] WebKit.FCGIAdapter: Error while responding to request (unknown)\n' % (
				time.asctime(time.localtime(time.time()))))
			stderr.write('Python exception:\n')
			traceback.print_exc(file=stderr)

			# Report the problem to the browser
			output = apply(traceback.format_exception, sys.exc_info())
			output = string.join(output, '')
			output = HTMLEncode(output)
			self.pr('''Content-type: text/html

<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)
		req.Finish()
		return

	#easy print function
	def pr(self,*args):
		"""just a quick and easy print function"""
		try:
			req=self.req
			s=''
			for i in args: s=s+str(i)
			req.out.write(s+'\n')
			req.out.flush()
		except:
			pass



#print "Starting"	
fcgiloop = FCGIAdapter(WebKitDir)
fcgiloop.run()



