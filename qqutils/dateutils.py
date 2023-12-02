from datetime import datetime, timezone
from dateutil.parser import parse


def datestr2ts(dateString, ignoretz=False):
    parsed_t = parse(dateString, ignoretz=ignoretz)
    ts = parsed_t.timestamp()
    return ts


def timestamp_millis(utc=True) -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def timestamp_seconds(utc=True) -> int:
    return int(datetime.now(timezone.utc).timestamp())


def datetimestr(ts0, fmt="%m/%d/%Y %H:%M:%S"):
    try:
        ts = int(ts0)
    except Exception:
        return ''
    if len(str(ts)) > 10:
        ts = int(ts / 1000)
    date_time = datetime.fromtimestamp(ts)
    return date_time.strftime(fmt)


def YmdHMS(fmt="%Y%m%d%H%M%S"):
    return datetime.now().strftime(fmt)


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def pretty_duration(seconds):
    TIME_DURATION_UNITS = (
        ('w', 60 * 60 * 24 * 7),
        ('d', 60 * 60 * 24),
        ('h', 60 * 60),
        ('m', 60),
        ('s', 1)
    )
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{}{}'.format(amount, unit))
    return ','.join(parts)
