from urllib.parse import urlparse
from urllib.parse import parse_qs


def get_param(url, param):
    parsed_url = urlparse(url)
    captured_value = parse_qs(parsed_url.query)[param][0]
    return captured_value
