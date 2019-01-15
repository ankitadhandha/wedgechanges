from types import *

True, False = 1==1, 0==1

class HTTPError(Exception):

    def __init__(self, code, codeMessage, internal=None, path=None,
                 *args):
        Exception.__init__(self, *args)
        self._code = code
        self._codeMessage = codeMessage
        self._internal = internal
        self._path = path

    def code(self, servlet=None):
        return self._code

    def codeMessage(self, servlet=None):
        return self._codeMessage

    def html(self, servlet=None):
        return '''
<html><head><title>%(title)s</title></head>
<body>
<h1>%(title)s</h1>
%(body)s
</body></html>''' % {
            "title": self.htmlTitle(servlet),
            "body": self.htmlBody(servlet),
            }

    def title(self, servlet=None):
        return self.codeMessage()

    def htTitle(self, servlet=None):
        return self.title(servlet)

    def htBody(self, servlet=None):
        body = self.htmlBoilerplate()
        if self._args:
            body += ''.join(['<p>%s</p>\n' % str(l) for l in self._args])
        return 'An error has occurred.'

    def headers(self, servlet=None):
        return {}

    def title(self, servlet=None):
        return self.codeMessage()

    def htDescription(self, servlet=None):
        return 'An error has occurred'

class NotImplementedError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 501, 'Not Implemented', *args, **kw)

class ForbiddenError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 403, 'Forbidden', *args, **kw)

class AuthenticationRequiredError(HTTPError):
    def __init__(self, realm=None, *args, **kw):
        if not realm:
            realm = 'Password required'
        assert realm.find('"') == -1, 'Realm must not contain "'
        self._realm = realm
        HTTPError.__init__(self, 401, 'Authentication Required', *args, **kw)

    def code(self, servlet=None):
        if servlet and servlet.useHTTPAuthentication():
            return HTTPError.code(self, servlet)
        else:
            return 200

    def codeMessage(self, servlet=None):
        if servlet and servlet.useHTTPAuthentication():
            return HTTPError.codeMessage(self, servlet)
        else:
            return 'OK'

    def htDescription(self, servlet=None):
        if servlet and servlet.useHTTPAuthentication():
            return HTTPError.codeMessage(servlet)
        else:
            return servlet.loginBox(focus=True)
        
    def headers(self, servlet=None):
        return {'WWW-Authenticate': 'Basic realm="%s"' % self._realm}

## These are for spelling mistakes.  I'm unsure about their benefit.
AuthenticationRequired = AuthenticationRequiredError
AuthorizationRequiredError = AuthenticationRequiredError
AuthorizationRequired = AuthenticationRequiredError

class MethodNotAllowedError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 405, 'Method Not Allowed', *args, **kw)

class ConflictError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 409, 'Conflict', *args, **kw)

class UnsupportedMediaTypeError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 415, 'Unsupported Media Type', *args, **kw)

class InsufficientStorageError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 507, 'Insufficient Storage', *args, **kw)

class PreconditionFailedError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 412, 'Precondition Failed', *args, **kw)

class MovedPermanentlyError(HTTPError):
    def __init__(self, location=None, *args, **kw):
        self._location = location
        HTTPError.__init__(self, 301, 'Moved Permanently', *args, **kw)
    def location(self):
        return self._location
    def headers(self, servlet=None):
        return {'Location': self.location()}

class TemporaryRedirectError(MovedPermanentlyError):
    def __init__(self, location=None, *args, **kw):
        self._location = location
        HTTPError.__init__(self, 307, 'Temporary Redirect', *args, **kw)

TemporaryRedirect = TemporaryRedirectError

class BadRequestError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 400, 'Bad Request', *args, **kw)

class NotFoundError(HTTPError):
    def __init__(self, *args, **kw):
        HTTPError.__init__(self, 404, 'Not Found', *args, **kw)

_registry = {}
def register(context, variables):
    global _registry
    mine = globals()
    dict = {}
    _registry[context] = dict
    for var, value in variables.items():
        if mine.has_key(var) \
           and type(mine) is ClassType \
           and issubclass(value, mine[var]):
            _registry[var] = value

def exception(context, exceptionName):
    global _registry
    if not exceptionName.endswith('Error'):
        exceptionName = exceptionName + 'Error'
    dict = _registry.get(context, {})
    return dict.get(exceptionName, globals()[exceptionName])
