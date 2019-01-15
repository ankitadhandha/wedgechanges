

"""
This module defines a subClass of the standard python cgi.FieldStorage class with an extra method that will allow a FieldStorage to parse a query string even in a POST request.
"""


import cgi, os, urllib, string

class FieldStorage(cgi.FieldStorage):

	def __init__(self, fp=None, headers=None, outerboundary="",
                 environ=os.environ, keep_blank_values=0, strict_parsing=0):
		self._environ = environ
		self._strict_parsing = strict_parsing
		self._keep_blank_values = keep_blank_values
		cgi.FieldStorage.__init__(self, fp, headers, outerboundary, environ, keep_blank_values, strict_parsing)
	
	def parse_qs(self):
		"""
		Explicitly parse the query string, even if it's a POST request
		"""
		self._method = string.upper(self._environ['REQUEST_METHOD'])
		if self._method == "GET" or  self._method == "HEAD":
##			print __file__, "bailing on GET or HEAD request"
			return  #bail because cgi.FieldStorage already did this
		self._qs = self._environ.get('QUERY_STRING', None)
		if not self._qs:
##			print __file__, "bailing on no query_string"
			return  ##bail if no query string


		name_value_pairs = string.splitfields(self._qs, '&')
		dict = {}
		for name_value in name_value_pairs:
			nv = string.splitfields(name_value, '=')
			if len(nv) != 2:
				if self._strict_parsing:
					raise ValueError, "bad query field: %s" % `name_value`
				continue
			name = urllib.unquote(string.replace(nv[0], '+', ' '))
			value = urllib.unquote(string.replace(nv[1], '+', ' '))
			if len(value) or self._keep_blank_values:
				if dict.has_key (name):
					dict[name].append(value)
					##print "appending"
				else:
					dict[name] = [value]
					##print "no append"

		# Only append values that aren't already in the FieldStorage's keys;
		# This makes POSTed vars override vars on the query string
		if not self.list:
			# This makes sure self.keys() are available, even
			# when valid POST data wasn't encountered.
			self.list = [] 
		keys = self.keys()
		for key, values in dict.items():
			if key not in keys:
				for value in values:
					self.list.append(cgi.MiniFieldStorage(key,value))
##					print "adding %s=%s" % (str(key),str(value))
			


		
