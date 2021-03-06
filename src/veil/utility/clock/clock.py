from __future__ import unicode_literals, print_function, division
import contextlib
from datetime import datetime
from datetime import timedelta
import calendar
import pytz

LOCAL_TIMEZONE = pytz.timezone('Asia/Shanghai')
DEFAULT_CLIENT_TIMEZONE = pytz.timezone('Asia/Shanghai')
assert LOCAL_TIMEZONE is DEFAULT_CLIENT_TIMEZONE

current_time = None

@contextlib.contextmanager
def require_current_time_being(time):
    assert time.tzinfo, 'must be explicit with time zone'
    global current_time
    current_time = time
    try:
        yield
    finally:
        current_time = None


def get_current_time():
    return current_time or datetime.now(pytz.utc)


def get_current_time_in_client_timezone():
    return convert_datetime_to_client_timezone(get_current_time())


def get_current_date_in_client_timezone():
    return get_current_time_in_client_timezone().date()


def get_current_timestamp():
    """
    Caveat: the guaranteed precision of timestamp is 1 second
    """
    return calendar.timegm(get_current_time().utctimetuple())


def convert_datetime_to_timestamp(dt):
    return calendar.timegm(dt.utctimetuple())


def convert_timestamp_to_utc_datetime(timestamp):
    return datetime.fromtimestamp(timestamp, pytz.utc)


def convert_datetime_to_naive_local(dt):
    return datetime.fromtimestamp(convert_datetime_to_timestamp(dt))


def convert_datetime_to_client_timezone(dt):
    if is_naive_datetime(dt):
        return convert_naive_datetime_to_aware(dt, DEFAULT_CLIENT_TIMEZONE)
    else:
        return convert_aware_datetime_to_timezone(dt, DEFAULT_CLIENT_TIMEZONE)


def convert_datetime_to_utc_timezone(dt):
    if is_naive_datetime(dt):
        aware_dt = convert_naive_datetime_to_aware(dt, DEFAULT_CLIENT_TIMEZONE)
        return convert_aware_datetime_to_timezone(aware_dt, pytz.utc)
    else:
        return dt if is_utc_datetime(dt) else convert_aware_datetime_to_timezone(dt, pytz.utc)


def convert_naive_datetime_to_aware(dt, tzinfo):
    assert is_naive_datetime(dt)
    if hasattr(tzinfo, 'localize'): # pytz
        converted = tzinfo.localize(dt)
    else:
        converted = dt.replace(tzinfo=tzinfo)
    return converted


def convert_aware_datetime_to_timezone(dt, tzinfo):
    assert not is_naive_datetime(dt)
    if dt.tzinfo is tzinfo:
        return dt
    converted = dt.astimezone(tzinfo)
    if hasattr(tzinfo, 'normalize'): # pytz
        converted = tzinfo.normalize(converted)
    return converted


def is_naive_datetime(dt):
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def is_utc_datetime(dt):
    return dt.tzinfo is pytz.utc or dt.tzinfo.utcoffset(dt) in (0, timedelta(0))
