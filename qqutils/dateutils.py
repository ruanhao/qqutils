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


def datetimestr(utc_ts: int, fmt: str = "%m/%d/%Y %H:%M:%S", to_local: bool = True) -> str:
    if utc_ts > 253_402_210_800:
        date_time = datetime.utcfromtimestamp(utc_ts // 1000).replace(microsecond=utc_ts % 1000 * 1000)
    else:
        date_time = datetime.utcfromtimestamp(utc_ts)
    if to_local:
        date_time = date_time.replace(tzinfo=tz.tzutc()).astimezone(tz=None)
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
        ('M', 60),
        ('S', 1)
    )
    if seconds == 0:
        return '0S'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{}{}'.format(amount, unit))
    return ', '.join(parts)
