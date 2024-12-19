from datetime import datetime, timezone
from dateutil.parser import parse
from dateutil import tz


def datestr2ts(dateString, ignoretz=False):
    parsed_t = parse(dateString, ignoretz=ignoretz)
    ts = parsed_t.timestamp()
    return ts


def _timestamp(millis: bool = False) -> int:
    if millis:
        return int(datetime.now(timezone.utc).timestamp() * 1000)
    return int(datetime.now().timestamp())


def timestamp_millis() -> int:
    return _timestamp(millis=True)


def timestamp_seconds() -> int:
    return _timestamp(millis=False)


def local_timestamp(tz: str = None, millis=False) -> int:
    """Return the current local timestamp based on the timezone provided. If no timezone is provided, the local timezone is used.
:param tz: The timezone to use in form like 'America/New_York'
    """
    import pytz
    timezone_info = pytz.timezone(tz) if tz else timezone.utc
    ts = datetime.now(timezone_info).timestamp()
    if millis:
        return int(ts * 1000)
    return int(ts)


def datetimestr(utc_ts: int = -1, fmt: str = "%m/%d/%Y %H:%M:%S", to_local: bool = True, tz_str: str = None) -> str:
    """Convert a UTC timestamp to a formatted date string.
    :param utc_ts: The UTC timestamp to convert, if -1, the current time is used
    :param fmt: The format to use for the date string
    :param to_local: Convert the UTC timestamp to local time
    :param tz_str: The timezone to use in form like 'America/New_York'
    """
    import pytz
    if utc_ts == -1:
        utc_ts = timestamp_seconds()
    if utc_ts > 253_402_210_800:
        date_time = datetime.utcfromtimestamp(utc_ts // 1000).replace(microsecond=utc_ts % 1000 * 1000)
    else:
        date_time = datetime.utcfromtimestamp(utc_ts)

    tz_info = pytz.timezone(tz_str) if tz_str else None
    if to_local or tz_info:
        date_time = date_time.replace(tzinfo=tz.tzutc()).astimezone(tz=tz_info)
    return date_time.strftime(fmt)


def YmdHMS(fmt: str = "%Y%m%d%H%M%S") -> str:
    return datetime.now().strftime(fmt)


def utc_to_local(utc_dt: datetime) -> datetime:
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def pretty_duration(seconds: int) -> str:
    TIME_DURATION_UNITS = (
        ('W', 60 * 60 * 24 * 7),
        ('D', 60 * 60 * 24),
        ('H', 60 * 60),
        ('m', 60),
        ('s', 1)
    )
    if seconds == 0:
        return '0S'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{}{}'.format(amount, unit))
    return ', '.join(parts)
