# This file must be present so Webware can import this directory as a package.
# This file also customizes the display of error messages in Flamenco.

import sys
from WebKit.ExceptionHandler import ExceptionHandler
from html import *

class FlamencoHandler(ExceptionHandler):
    def write(self, *stuff):
        self.html.append(stuff)

    def privateErrorPage(self):
        etype, evalue, etb = self._exc
        self.html = []
        self.write('<html><head><title>Error</title></head><body>')
        self.writeTitle('Error')
        self.write(p, 'An error has occurred on this page: ',
                   blockquote(code(strong(esc(str(etype))), ': ',
                                   esc(str(evalue)))))
        if hasattr(sys, 'last_query'):
            self.write(p, 'The last database query was: ',
                       blockquote(code(sys.last_query)))
        self.writeFancyTraceback()
        try:
            self._tra._session.writeExceptionReport(self)
        except:
            pass
        self.write('</body></html>')
        return flatten(self.html)

def contextInitialize(app, path):
    app._exceptionHandlerClass = FlamencoHandler
