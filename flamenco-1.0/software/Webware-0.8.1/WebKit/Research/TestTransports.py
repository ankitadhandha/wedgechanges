#!/usr/bin/env python
"""
TestTransports.py

In order to get a raw request from a WebKit adaptor (such as CGIAdaptor or FCGIAdaptor) a very simple dictionary has to be transferred (normally via a TCP/IP socket) to the AppServer. What is the most efficient way to do the transfer?
	* repr() and eval()
	* pickle
	* marshal

Note that eval() is pretty much out anyway since it's not as secure as the other forms (arbitrary python code could be sneaked into the raw request).

The results:

    pickle: 41.95
   cPickle: 12.14
 repr/eval:  5.57
   marshal:  0.49


marshal wins.
"""

import cPickle, pickle, marshal, sys
from time import time

dict = {'format': 'CGI', 'time': 957828183.321, 'environ': {'DOCUMENT_ROOT': '/home/httpd/html', 'SERVER_ADDR': '127.0.0.1', 'HTTP_ACCEPT_ENCODING': 'gzip', 'SERVER_PORT': '80', 'PATH_TRANSLATED': '/home/httpd/html/Hello', 'REMOTE_ADDR': '127.0.0.1', 'SERVER_SOFTWARE': 'Apache/1.3.9  (NetRevolution Advanced Extranet Server/Linux-Mandrake) PHP/3.0.13 mod_perl/1.21 mod_fastcgi/2.2.4', 'HTTP_ACCEPT_LANGUAGE': 'en', 'GATEWAY_INTERFACE': 'CGI/1.1', 'SERVER_NAME': 'localhost.localdomain', 'HTTP_CONNECTION': 'Keep-Alive', 'HTTP_USER_AGENT': 'Mozilla/4.7 [en] (X11; I; Linux 2.2.14-15mdk i686)', 'HTTP_ACCEPT_CHARSET': 'iso-8859-1,*,utf-8', 'HTTP_ACCEPT': 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, image/png, */*', 'REQUEST_URI': '/~echuck/Projects/Webware/WebKit/WebKit.cgi/Hello', 'PATH': '/usr/local/bin:/usr/bin:/bin', 'QUERY_STRING': '', 'SERVER_PROTOCOL': 'HTTP/1.0', 'PATH_INFO': '/Hello', 'HTTP_HOST': 'localhost.localdomain', 'REQUEST_METHOD': 'GET', 'SCRIPT_NAME': '/~echuck/Projects/Webware/WebKit/WebKit.cgi', 'SERVER_ADMIN': 'root@localhost', 'SCRIPT_FILENAME': '/home/echuck/public_html/Projects/Webware/WebKit/WebKit.cgi', 'REMOTE_PORT': '1552'}, 'input': ''}


def bench(title, encode, decode, reps=1000, validate=0):
	"""
	title - descriptive string for output
	encode - function that takes a dictionary and returns it encoded as a string
	decode - function that takes string and returns the dictionary encoded within
	"""
	start = time()
	for i in xrange(reps):
		s = encode(dict)
		d = decode(s)
		if validate:
			assert d==dict, 'Decoded dictionary is not the same as encoded dictionary!'
	duration = time() - start
	print '%10s: %5.2f' % (title, duration)
	sys.stdout.flush()
	
	
def main():
	bench('pickle', lambda d, encode=pickle.dumps: encode(d), lambda s, decode=pickle.loads: decode(s))
	bench('cPickle', lambda d, encode=cPickle.dumps: encode(d), lambda s, decode=cPickle.loads: decode(s))
	bench('repr/eval', lambda d: repr(d), lambda s: eval(s))
	bench('marshal', lambda d, encode=marshal.dumps: encode(d), lambda s, decode=marshal.loads: decode(s))

if __name__=='__main__':
	main()
