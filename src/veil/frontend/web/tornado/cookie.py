from __future__ import unicode_literals, print_function, division
import Cookie
import base64
import calendar
import datetime
import email.utils
from logging import getLogger
import re
import time
from veil.frontend.encoding import to_str
from veil.utility.hash import get_hmac
from .context import get_current_http_request
from .context import get_current_http_response

LOGGER = getLogger(__name__)
secure_cookie_salt = None

def set_secure_cookie_salt(value):
    global  secure_cookie_salt
    secure_cookie_salt = value


def get_secure_cookie(name, default=None, value=None, request=None):
    if value is None: value = get_cookie(name, request=request)
    if not value: return default
    parts = value.split('|')
    if len(parts) != 3: return default
    if not secure_cookie_salt:
        raise Exception('secret salt not set')
    signature = get_hmac(name, parts[0], parts[1], strong=False, salt=secure_cookie_salt)
    if not _time_independent_equals(parts[2], signature):
        LOGGER.warning('Invalid cookie signature %r', value)
        return default
    timestamp = int(parts[1])
    if timestamp < time.time() - 31 * 86400:
        LOGGER.warning('Expired cookie %r', value)
        return default
    if parts[1].startswith('0'):
        LOGGER.warning('Tampered cookie %r', value)
    try:
        return base64.b64decode(parts[0])
    except:
        return default


def set_secure_cookie(response=None, cookie=None, **kwargs):
    set_cookie(response, cookie=cookie or create_secure_cookie(**kwargs))


def create_secure_cookie(name, value, expires_days=30, **kwargs):
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    if not secure_cookie_salt:
        raise Exception('secret salt not set')
    signature = get_hmac(name, value, timestamp, strong=False, salt=secure_cookie_salt)
    value = '|'.join([value, timestamp, signature])
    return create_cookie(name=name, value=value, expires_days=expires_days, **kwargs)


def get_cookies(request=None):
    request = request or get_current_http_request()
    if not hasattr(request, '_cookies'):
        request._cookies = Cookie.BaseCookie()
        if 'Cookie' in request.headers:
            try:
                request._cookies.load(request.headers['Cookie'])
            except:
                clear_cookies(request=request)
    return request._cookies


def get_cookie(name, default=None, request=None):
    cookies = get_cookies(request=request)
    if name in cookies:
        return cookies[name].value
    return default


def clear_cookies(request=None, response=None):
    for name in get_cookies(request=request).iterkeys():
        clear_cookie(name, response=response)


def clear_cookie(name, path='/', domain=None, response=None):
    expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    set_cookie(response=response, name=name, value='', path=path, expires=expires, domain=domain)


def set_cookie(response=None, cookie=None, **kwargs):
    response = response or get_current_http_response()
    cookie = cookie or create_cookie(**kwargs)
    response.set_header('Set-Cookie', cookie.OutputString(None))


def create_cookie(name, value, domain=None, expires=None, path='/', expires_days=None, **kwargs):
    base_cookie = Cookie.BaseCookie()
    name = to_str(name)
    value = to_str(value)
    if re.search(r'[\x00-\x20]', name + value):
        # Don't let us accidentally inject bad stuff
        raise ValueError('Invalid cookie %r: %r' % (name, value))
    base_cookie[name] = value
    cookie = base_cookie[name]
    if domain:
        cookie['domain'] = domain
    if expires_days is not None and not expires:
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)
    if expires:
        timestamp = calendar.timegm(expires.utctimetuple())
        cookie['expires'] = email.utils.formatdate(timestamp, localtime=False, usegmt=True)
    if path:
        cookie['path'] = path
    for k, v in kwargs.iteritems():
        cookie[k] = v
    return cookie


def _time_independent_equals(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0