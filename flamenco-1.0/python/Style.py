# Copyright (c) 2004-2006 The Regents of the University of California.

import WebKit, Page

class Style(WebKit.Page.Page):
    """Stylesheet base class.  To create a dynamic stylesheet, write a
    subclass implementing the 'stylesheet()' method."""

    def awake(self, transaction):
        WebKit.Page.Page.awake(self, transaction)
        self.response = transaction.response()
        self.response.setHeader('Content-Type', 'text/css')
        self.request = transaction.request()
        self.out = Page.OutputWrapper(self.response)
        self.session = Page.SessionWrapper(transaction.session())

    def writeHTML(self): # poor method name chosen by WebKit API
        self.body(self.out)

    def body(self, out):
        out.write(self.stylesheet())

    def stylesheet(self):
        return '// This is just a generic stylesheet.\n'

    def redirect(self, url):
        self.response.redirect(url)
