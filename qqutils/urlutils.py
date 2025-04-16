from urllib.parse import urlparse
from urllib.parse import parse_qs


def get_param(url, param):
    parsed_url = urlparse(url)
    qs = parse_qs(parsed_url.query)
    if param not in qs:
        return None
    return qs[param][0]
