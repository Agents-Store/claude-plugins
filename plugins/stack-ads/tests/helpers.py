"""Shared test helpers: import path of the toolkit, a temporary workspace and a scripted HTTP fake."""
import json
import os
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
TOOLKIT = PLUGIN / "skills" / "init-project" / "scripts"
sys.path.insert(0, str(TOOLKIT))

from adskit.core import Context, HttpError  # noqa: E402
from adskit.workspace import init  # noqa: E402

FAKE_ENV = {
    "GOOGLE_ADS_CLIENT_ID": "client-id-example", "GOOGLE_ADS_CLIENT_SECRET": "client-secret-example",
    "GOOGLE_ADS_REFRESH_TOKEN": "refresh-token-example", "GOOGLE_ADS_CUSTOMER_ID": "123-456-7890",
    "META_ACCESS_TOKEN": "meta-token-example", "META_AD_ACCOUNT_ID": "111222333", "META_PAGE_ID": "444555666",
    "TIKTOK_ACCESS_TOKEN": "tiktok-token-example", "TIKTOK_ADVERTISER_ID": "777888999",
}


class Reply:
    """What adskit.core.request returns."""

    def __init__(self, payload, status=200, headers=None):
        self.payload, self.status, self.headers = payload, status, headers or {}
        self.raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.url = ""

    @property
    def text(self):
        return self.raw.decode("utf-8")

    def json(self):
        return json.loads(self.raw)


class FakeHttp:
    """Records every call and answers through a handler(method, url, kwargs) -> payload or Reply."""

    def __init__(self, handler):
        self.handler, self.calls = handler, []

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        answer = self.handler(method, url, kwargs)
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, Reply) else Reply(answer)

    def sent(self, fragment):
        return [c for c in self.calls if fragment in c[1]]


def http_error(status, payload):
    return HttpError(status, json.dumps(payload), "https://example.com/api")


class Workspace:
    """A throwaway project with an ads workspace and fake keys."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.saved = {k: os.environ.pop(k) for k in list(os.environ) if k in self._tracked()}
        init(self.project / "ads")
        env = "\n".join("%s=%s" % kv for kv in FAKE_ENV.items()) + "\n"
        (self.project / "ads" / ".env").write_text(env, encoding="utf-8")
        self.ctx = Context(self.project / "ads")
        return self

    def __exit__(self, *exc):
        os.environ.update(self.saved)
        self.tmp.cleanup()

    @staticmethod
    def _tracked():
        from adskit.keys import all_keys
        return set(all_keys()) | {"ADS_DIR", "GOOGLE_ACCESS_TOKEN"}

    def write_plan(self, plan):
        path = self.project / "ads" / "launch" / ("%s.plan.json" % plan["name"])
        path.write_text(json.dumps(plan), encoding="utf-8")
        return str(path)
