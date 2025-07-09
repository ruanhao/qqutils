import httpx
import requests
from typing import Awaitable
from qqutils.asyncutils import wait_for_complete
from qqutils.osutils import from_module
from qqutils.netutils import (
    upload_multipart,
    httpx_get,
    httpx_post,
    httpx_put,
    httpx_delete,
    httpx_patch,
    http_get,
    http_post,
    http_put,
    http_delete,
    http_patch,
)


def test_upload_multipart():
    r = upload_multipart("https://httpbin.org/post", from_module("test_osutils.py", as_path=True))
    assert r.ok, r.text
    assert r.json()["headers"]["Content-Type"].startswith('multipart/form-data; boundary=')
    assert "file" in r.json()["files"]


def test_upload_multipart_case_with_name():
    r = upload_multipart("https://httpbin.org/post", from_module("test_osutils.py", as_path=True), name="myfile")
    assert r.ok, r.text
    assert r.json()["headers"]["Content-Type"].startswith('multipart/form-data; boundary=')
    assert "myfile" in r.json()["files"]


def test_upload_multipart_case_with_progress():
    r = upload_multipart("https://httpbin.org/post", from_module("test_osutils.py", as_path=True), progress=True)
    assert r.ok, r.text
    assert r.json()["headers"]["Content-Type"].startswith('multipart/form-data; boundary=')
    assert "file" in r.json()["files"]


# def _wait_for_complete(coro: Awaitable[httpx.Response]) -> httpx.Response:
#     return asyncio.run(coro)


def _wait_for_all_complete(*coros: Awaitable[httpx.Response], progress=False) -> list[httpx.Response]:
    return wait_for_complete(*coros, progress=progress)


def test_httpx_method_case_success():
    responses: list[httpx.Response] = _wait_for_all_complete(
        httpx_get("https://httpbin.org/get"),
        httpx_post("https://httpbin.org/post"),
        httpx_put("https://httpbin.org/put"),
        httpx_delete("https://httpbin.org/delete"),
        httpx_patch("https://httpbin.org/patch"),
        progress=True,
    )
    for response in responses:
        assert response.is_success, response.text


def test_httpx_method_case_fail_without_check():
    responses: list[httpx.Response] = _wait_for_all_complete(
        httpx_get("https://httpbin.org/status/404", check=False),
        httpx_post("https://httpbin.org/status/404", check=False),
        httpx_put("https://httpbin.org/status/404", check=False),
        httpx_delete("https://httpbin.org/status/404", check=False),
        httpx_patch("https://httpbin.org/status/404", check=False),
    )
    for response in responses:
        if isinstance(response, httpx.Response):
            assert not response.is_success, response.text
        elif isinstance(response, Exception):
            raise response
        else:
            raise TypeError(f"Unexpected response type: {type(response)}")



def test_httpx_method_case_fail_with_check():
    responses = _wait_for_all_complete(
        httpx_get("https://httpbin.org/status/404"),
        httpx_post("https://httpbin.org/status/404"),
        httpx_put("https://httpbin.org/status/404"),
        httpx_delete("https://httpbin.org/status/404"),
        httpx_patch("https://httpbin.org/status/404"),
    )
    for response in responses:
        assert isinstance(response, httpx.HTTPStatusError)


def test_http_method_case_success():
    response = [
        http_get("https://httpbin.org/get"),
        http_post("https://httpbin.org/post"),
        http_put("https://httpbin.org/put"),
        http_delete("https://httpbin.org/delete"),
        http_patch("https://httpbin.org/patch"),
    ]
    for r in response:
        assert r.ok, r.text


def test_http_method_case_fail_without_check():
    responses = [
        http_get("https://httpbin.org/status/404", check=False),
        http_post("https://httpbin.org/status/404", check=False),
        http_put("https://httpbin.org/status/404", check=False),
        http_delete("https://httpbin.org/status/404", check=False),
        http_patch("https://httpbin.org/status/404", check=False),
    ]
    for response in responses:
        assert not response.ok, response.text


def test_http_method_case_fail_with_check():
    try:
        http_get("https://httpbin.org/status/404")
        assert False, "Expected HTTPStatusError but none was raised"
    except requests.HTTPError as e:
        assert e.response.status_code == 404, e.response.text

    try:
        http_post("https://httpbin.org/status/404")
        assert False, "Expected HTTPStatusError but none was raised"
    except requests.HTTPError as e:
        assert e.response.status_code == 404, e.response.text

    try:
        http_put("https://httpbin.org/status/404")
        assert False, "Expected HTTPStatusError but none was raised"
    except requests.HTTPError as e:
        assert e.response.status_code == 404, e.response.text

    try:
        http_delete("https://httpbin.org/status/404")
        assert False, "Expected HTTPStatusError but none was raised"
    except requests.HTTPError as e:
        assert e.response.status_code == 404, e.response.text

    try:
        http_patch("https://httpbin.org/status/404")
        assert False, "Expected HTTPStatusError but none was raised"
    except requests.HTTPError as e:
        assert e.response.status_code == 404, e.response.text
