"""Heuristics of scripts/hooks/webfetch_camoufox_fallback.py, without network or a browser."""
import io, json, urllib.error
import pytest
from conftest import load

hook = load("webfetch_fallback", "scripts/hooks/webfetch_camoufox_fallback.py")

LONG_ARTICLE = ("HTTP 403 Forbidden is a client error status code indicating that the server understood the request but "
                "refuses to authorize it. The article covers RFC 9110, file permissions, IP blocks and web application "
                "firewalls like Cloudflare, how it differs from 404, related codes 429 and 503, and captcha challenges. ") * 3


class FakeResp(io.BytesIO):
    def __init__(self, body, status=200, ctype="text/html; charset=utf-8"):
        super().__init__(body.encode())
        self.status, self.headers = status, {"Content-Type": ctype}
    def __enter__(self): return self
    def __exit__(self, *a): return False


def fake_urlopen(body, status=200, ctype="text/html"):
    return lambda req, timeout=None: FakeResp(body, status, ctype)


def test_strong_summary_phrase_triggers():
    assert hook.summary_reasons("No quotes are present on this page. The content shown consists only of navigation elements.")


def test_weak_words_ignored_in_long_article_summary():
    assert len(LONG_ARTICLE) > hook.WEAK_MAX_SUMMARY_CHARS
    assert hook.summary_reasons(LONG_ARTICLE) == []


def test_weak_words_count_in_short_summary():
    assert hook.summary_reasons("403 Forbidden")


def test_raw_js_shell_detected(monkeypatch):
    html = "<html><head><script src='app.js'></script></head><body><div id='app'></div><noscript>You need to enable JavaScript</noscript></body></html>"
    monkeypatch.setattr(hook.urllib.request, "urlopen", fake_urlopen(html))
    reasons = hook.raw_reasons("https://example.test/")
    assert any("JS shell" in r for r in reasons)


def test_raw_normal_article_with_captcha_script_is_clean(monkeypatch):
    body = "<p>" + ("Real article text about many things. " * 200) + "</p>"
    html = f"<html><body>{body}<script>window.recaptchaSiteKey='x'; loadCaptcha();</script></body></html>"
    monkeypatch.setattr(hook.urllib.request, "urlopen", fake_urlopen(html))
    assert hook.raw_reasons("https://example.test/") == []


def test_raw_challenge_interstitial_detected(monkeypatch):
    html = "<html><head><title>Just a moment...</title></head><body><script src='/cdn-cgi/challenge-platform/h/b/orchestrate'></script></body></html>"
    monkeypatch.setattr(hook.urllib.request, "urlopen", fake_urlopen(html))
    assert any("challenge" in r for r in hook.raw_reasons("https://example.test/"))


def test_raw_http_403_detected(monkeypatch):
    def boom(req, timeout=None):
        raise urllib.error.HTTPError("https://example.test/", 403, "Forbidden", {}, None)
    monkeypatch.setattr(hook.urllib.request, "urlopen", boom)
    assert hook.raw_reasons("https://example.test/") == ["raw fetch returned HTTP 403"]


def test_non_html_is_not_rendered(monkeypatch):
    monkeypatch.setattr(hook.urllib.request, "urlopen", fake_urlopen('{"a": 1}', ctype="application/json"))
    assert hook.raw_reasons("https://example.test/data.json") == []


def test_blocked_domain_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(hook, "BLOCKED", str(tmp_path / "blocked.json"))
    assert hook.blocked_until("https://www.g2.com/x") is None
    hook.remember_blocked("https://www.g2.com/x", 403)
    assert hook.blocked_until("https://www.g2.com/other")["status"] == 403
    data = json.load(open(tmp_path / "blocked.json"))
    data["www.g2.com"]["until"] = "2000-01-01T00:00:00"
    json.dump(data, open(tmp_path / "blocked.json", "w"))
    assert hook.blocked_until("https://www.g2.com/x") is None


def test_non_webfetch_tool_is_ignored(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})))
    assert hook.main() == 0
    assert capsys.readouterr().out == ""
