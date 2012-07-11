from __future__ import print_function, division
import calendar
import datetime
import email.utils
import functools
import hashlib
import httplib
from logging import getLogger
import re
import tornado
from tornado.httpserver import HTTPServer
from tornado.stack_context import StackContext
from sandal.encoding import to_str
from .argument import normalize_arguments
from .argument import tunnel_put_and_delete
from .context import HTTPContext
from .context import require_current_http_context_being
from .context import get_current_http_response
from .error import handle_exception
from .xsrf import prevent_xsrf

LOGGER = getLogger(__name__)

def create_http_server(handler, prevents_xsrf=True, **kwargs):
    return HTTPServer(HTTPHandler(handler, prevents_xsrf=prevents_xsrf), **kwargs)


class HTTPHandler(object):
    def __init__(self, handler, prevents_xsrf=True):
        self.handler = handler
        self.prevents_xsrf = prevents_xsrf

    def __call__(self, request):
        http_context = HTTPContext(request, HTTPResponse(request))
        with create_stack_context(require_current_http_context_being, http_context=http_context):
            with create_stack_context(handle_exception):
                with normalize_arguments():
                    with tunnel_put_and_delete():
                        if self.prevents_xsrf:
                            with prevent_xsrf():
                                self.handler()
                        else:
                            self.handler()
        if request.files:
            LOGGER.debug('handled file upload to {}'.format(request.uri))
        else:
            LOGGER.debug('handled {}'.format(request))


def create_stack_context(context_manager, *args, **kwargs):
    return StackContext(functools.partial(context_manager, *args, **kwargs))


def set_http_status_code(status_code):
    get_current_http_response().status_code = status_code


class HTTPResponse(object):
    def __init__(self, request):
        self._headers_written = False
        self._finished = False
        self.request = request
        self.connection = self.request.connection
        self.clear()

    @property
    def finished(self):
        return self._finished

    @property
    def headers(self):
        return self._headers

    @property
    def headers_written(self):
        return self._headers_written

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, status_code):
        assert status_code in httplib.responses
        if self.headers_written:
            LOGGER.warn('setting status code to {} is too late, as heads already written'.format(status_code))
        self._status_code = status_code

    def clear(self):
        self._headers = {
            'Server': 'TornadoServer/%s' % tornado.version,
            'Content-Type': 'text/html; charset=utf-8',
            }
        if not self.request.supports_http_1_1():
            if self.request.headers.get('Connection') == 'Keep-Alive':
                self.set_header('Connection', 'Keep-Alive')
        self._write_buffer = []
        self._status_code = 200

    def set_header(self, name, value):
        if self.headers_written:
            LOGGER.warn('setting header {} to {} is too late, as heads already written'.format(name, value))
        if isinstance(value, datetime.datetime):
            t = calendar.timegm(value.utctimetuple())
            value = email.utils.formatdate(t, localtime=False, usegmt=True)
        elif isinstance(value, int) or isinstance(value, long):
            value = str(value)
        else:
            value = to_str(value)
            # If \n is allowed into the header, it is possible to inject
            # additional headers or split the request. Also cap length to
            # prevent obviously erroneous values.
            safe_value = re.sub(r'[\x00-\x1f]', ' ', value)[:4000]
            if safe_value != value:
                raise ValueError('Unsafe header value %r', value)
        self._headers[to_str(name)] = value

    def write(self, chunk):
        assert not self._finished
        chunk = to_str(chunk)
        self._write_buffer.append(chunk)

    def flush(self):
        chunk = ''.join(self._write_buffer)
        self._write_buffer = []
        if not self._headers_written:
            self._headers_written = True
            headers = self._generate_headers()
        else:
            headers = ''

        # Ignore the chunk and only write the headers for HEAD requests
        if self.request.method == 'HEAD':
            if headers: self.connection.write(headers)
            return

        if headers or chunk:
            self.connection.write(headers + chunk)

    def finish(self, no_keep_alive=False):
        assert not self._finished

        # Automatically support ETags and add the Content-Length header if
        # we have not flushed any content yet.
        if not self._headers_written:
            if (self._status_code == 200 and self.request.method == 'GET' and
                'Etag' not in self._headers):
                hasher = hashlib.md5()
                for part in self._write_buffer:
                    hasher.update(part)
                etag = '"%s"' % hasher.hexdigest()
                inm = self.request.headers.get('If-None-Match')
                if inm and inm.find(etag) != -1:
                    self._write_buffer = []
                    self.status_code = 304
                else:
                    self.set_header('Etag', etag)
            if 'Content-Length' not in self._headers:
                content_length = sum(len(part) for part in self._write_buffer)
                self.set_header('Content-Length', content_length)

        self.flush()
        if no_keep_alive:
            self.connection.no_keep_alive = True
        self.connection.finish()
        self._finished = True

    def _generate_headers(self):
        lines = [self.request.version + " " + str(self._status_code) + " " +
                 httplib.responses[self._status_code]]
        lines.extend(['%s: %s' % (n, v) for n, v in self._headers.iteritems()])
        return '\r\n'.join(lines) + '\r\n\r\n'