"""The network options."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from rayohx_cli import params
from rayohx_cli.params.panels import NETWORK
from tests.helpers.params import Declared, check_declaration, option, parse

CASES = [
    Declared("header", params.Header, ("--header", "-H"), None),
    Declared("cookie", params.Cookie, ("--cookie",), None),
    Declared("user-agent", params.UserAgent, ("--user-agent",), "RAYOHX_USER_AGENT"),
    Declared("referer", params.Referer, ("--referer",), "RAYOHX_REFERER"),
    Declared("origin", params.Origin, ("--origin",), "RAYOHX_ORIGIN"),
    Declared("proxy", params.Proxy, ("--proxy",), "RAYOHX_PROXY"),
    Declared("insecure", params.Insecure, ("--insecure",), "RAYOHX_INSECURE"),
    Declared("ca-bundle", params.CaBundle, ("--ca-bundle",), "RAYOHX_CA_BUNDLE"),
    Declared(
        "connect-timeout", params.ConnectTimeout, ("--connect-timeout",), "RAYOHX_CONNECT_TIMEOUT"
    ),
    Declared("read-timeout", params.ReadTimeout, ("--read-timeout",), "RAYOHX_READ_TIMEOUT"),
    Declared("timeout", params.Timeout, ("--timeout",), "RAYOHX_TIMEOUT"),
    Declared("retries", params.Retries, ("--retries",), "RAYOHX_RETRIES"),
    Declared("backoff", params.Backoff, ("--backoff",), "RAYOHX_BACKOFF"),
    Declared("max-redirects", params.MaxRedirects, ("--max-redirects",), "RAYOHX_MAX_REDIRECTS"),
    Declared(
        "proxy-username", params.ProxyUsername, ("--proxy-username",), "RAYOHX_PROXY_USERNAME"
    ),
    Declared(
        "proxy-password", params.ProxyPassword, ("--proxy-password",), "RAYOHX_PROXY_PASSWORD"
    ),
    Declared("cookie-file", params.CookieFile, ("--cookie-file",), "RAYOHX_COOKIE_FILE"),
    Declared("rate-limit", params.RateLimit, ("--rate-limit",), "RAYOHX_RATE_LIMIT"),
    Declared("credential-host", params.CredentialHost, ("--credential-host",), None),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_the_options_are_declared(case: Declared) -> None:
    check_declaration(case, NETWORK)


@pytest.mark.parametrize("annotated", [params.Header, params.Cookie])
def test_headers_and_cookies_are_never_read_from_the_environment(annotated: object) -> None:
    # They carry secrets; they come from the command line (or an @file), not from a variable.
    assert option(annotated).envvar is None


# --- values that can be given more than once -----------------------------------------------------


@pytest.mark.parametrize(
    ("annotated", "flag"),
    [
        (params.Header, "--header"),
        (params.Cookie, "--cookie"),
        (params.CredentialHost, "--credential-host"),
    ],
    ids=["header", "cookie", "credential-host"],
)
def test_headers_cookies_and_hosts_can_be_repeated(
    runner: CliRunner, annotated: object, flag: str
) -> None:
    assert parse(runner, annotated, None, []).value is None
    assert parse(runner, annotated, None, [flag, "a", flag, "b"]).value == ["a", "b"]


def test_a_header_has_a_short_form(runner: CliRunner) -> None:
    assert parse(runner, params.Header, None, ["-H", "X-A: 1"]).value == ["X-A: 1"]


def test_a_header_can_name_a_file_and_is_left_for_the_command_to_read(runner: CliRunner) -> None:
    assert parse(runner, params.Header, None, ["-H", "@secrets.txt"]).value == ["@secrets.txt"]


# --- text values ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("annotated", "flag", "variable"),
    [
        (params.UserAgent, "--user-agent", "RAYOHX_USER_AGENT"),
        (params.Referer, "--referer", "RAYOHX_REFERER"),
        (params.Origin, "--origin", "RAYOHX_ORIGIN"),
        (params.Proxy, "--proxy", "RAYOHX_PROXY"),
        (params.RateLimit, "--rate-limit", "RAYOHX_RATE_LIMIT"),
    ],
    ids=["user-agent", "referer", "origin", "proxy", "rate-limit"],
)
def test_text_options_are_passed_on_as_typed(
    runner: CliRunner, annotated: object, flag: str, variable: str
) -> None:
    assert parse(runner, annotated, None, []).value is None
    assert parse(runner, annotated, None, [flag, "typed"]).value == "typed"
    assert parse(runner, annotated, None, [], {variable: "from-env"}).value == "from-env"
    assert parse(runner, annotated, None, [flag, "typed"], {variable: "from-env"}).value == "typed"


# --- certificates ---------------------------------------------------------------------------------


def test_insecure_is_a_flag_that_is_off_by_default(runner: CliRunner) -> None:
    assert parse(runner, params.Insecure, False, []).value is False
    assert parse(runner, params.Insecure, False, ["--insecure"]).value is True
    assert parse(runner, params.Insecure, False, [], {"RAYOHX_INSECURE": "true"}).value is True


def test_the_ca_bundle_is_a_file_path(runner: CliRunner) -> None:
    assert parse(runner, params.CaBundle, None, []).value is None
    assert parse(runner, params.CaBundle, None, ["--ca-bundle", "ca.pem"]).value == Path("ca.pem")


def test_the_proxy_login_is_passed_on_as_typed(runner: CliRunner) -> None:
    for annotated, flag, variable in (
        (params.ProxyUsername, "--proxy-username", "RAYOHX_PROXY_USERNAME"),
        (params.ProxyPassword, "--proxy-password", "RAYOHX_PROXY_PASSWORD"),
    ):
        assert parse(runner, annotated, None, []).value is None
        assert parse(runner, annotated, None, [flag, "x"]).value == "x"
        assert parse(runner, annotated, None, [], {variable: "y"}).value == "y"


def test_the_cookie_file_is_a_file_path(runner: CliRunner) -> None:
    assert parse(runner, params.CookieFile, None, []).value is None
    assert parse(runner, params.CookieFile, None, ["--cookie-file", "c.txt"]).value == Path("c.txt")


# --- timeouts and retries -------------------------------------------------------------------------


def test_the_backoff_and_redirect_limit_cannot_be_negative(runner: CliRunner) -> None:
    assert option(params.Backoff).min == 0
    assert parse(runner, params.Backoff, None, ["--backoff", "1.5"]).value == 1.5
    assert parse(runner, params.Backoff, None, ["--backoff", "-1"]).exit_code == 2
    assert parse(runner, params.Backoff, None, [], {"RAYOHX_BACKOFF": "2"}).value == 2.0
    assert option(params.MaxRedirects).min == 0
    assert parse(runner, params.MaxRedirects, None, ["--max-redirects", "0"]).value == 0
    assert parse(runner, params.MaxRedirects, None, ["--max-redirects", "-1"]).exit_code == 2
    assert parse(runner, params.MaxRedirects, None, [], {"RAYOHX_MAX_REDIRECTS": "3"}).value == 3


@pytest.mark.parametrize(
    ("annotated", "flag", "variable"),
    [
        (params.ConnectTimeout, "--connect-timeout", "RAYOHX_CONNECT_TIMEOUT"),
        (params.ReadTimeout, "--read-timeout", "RAYOHX_READ_TIMEOUT"),
        (params.Timeout, "--timeout", "RAYOHX_TIMEOUT"),
    ],
    ids=["connect-timeout", "read-timeout", "timeout"],
)
def test_timeouts_are_seconds_with_decimals(
    runner: CliRunner, annotated: object, flag: str, variable: str
) -> None:
    assert parse(runner, annotated, None, []).value is None
    assert parse(runner, annotated, None, [flag, "2.5"]).value == 2.5
    assert parse(runner, annotated, None, [], {variable: "30"}).value == 30.0
    assert parse(runner, annotated, None, [flag, "soon"]).exit_code == 2


def test_retries_cannot_be_negative(runner: CliRunner) -> None:
    assert option(params.Retries).min == 0
    assert parse(runner, params.Retries, None, ["--retries", "0"]).value == 0
    assert parse(runner, params.Retries, None, ["--retries", "-1"]).exit_code == 2
    assert parse(runner, params.Retries, None, [], {"RAYOHX_RETRIES": "3"}).value == 3
