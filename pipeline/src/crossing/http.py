"""One cached, rate-limited JSON client for the public APIs the pipeline reads (Wikidata, Commons).

Every answer is saved on disk, so a rerun makes no requests. Network errors (timeouts, DNS, resets) are
retried a few times; an HTTP error is not, since a 403 or 429 means the service wants no more requests,
and it is raised as Refused for the caller to stop on.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

USER_AGENT = "crossing-map-pipeline/0.1 (+https://github.com/JBurkinshaw/crossing-map)"
TIMEOUT_S = 60
RETRIES = 3


class Refused(Exception):
    """The service refused or rate-limited a request, or never answered."""


class CachedClient:
    """GET JSON through a cache folder, at most one request every `interval_s` seconds.

    `cache_name(url, params)` gives the cache file's name, so each caller keeps the names its existing cache
    already uses. With `envelope`, the file holds {"request": url, "response": data} and the whole envelope
    is returned; otherwise it holds and returns the answer alone.
    """

    def __init__(self, cache: Path, interval_s: float, cache_name: Callable[[str, dict], str], envelope: bool = False):
        self.cache, self.interval_s, self.cache_name, self.envelope = cache, interval_s, cache_name, envelope
        self.offline = False  # answer from the cache only; a miss returns {}
        self.requests = 0
        self.missing = 0
        self._last = 0.0

    def get(self, url: str, params: dict) -> dict:
        path = self.cache / self.cache_name(url, params)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        if self.offline:
            self.missing += 1
            return {}
        full = url + "?" + urllib.parse.urlencode(sorted(params.items()))
        data = self._fetch(full, url)
        out = {"request": full, "response": data} if self.envelope else data
        self.cache.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out), encoding="utf-8")
        return out

    def _fetch(self, full: str, url: str) -> dict:
        req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        for attempt in range(1, RETRIES + 1):
            wait = self.interval_s - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                    data = json.load(r)
                break
            except urllib.error.HTTPError as e:
                raise Refused(f"HTTP {e.code} from {url} (Retry-After: {e.headers.get('Retry-After')})") from e
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if attempt == RETRIES:
                    raise Refused(f"{url}: no answer after {RETRIES} tries ({e})") from e
            finally:
                self._last = time.monotonic()
                self.requests += 1
        if "error" in data:  # MediaWiki errors, maxlag among them, come back as HTTP 200
            raise Refused(f"{url}: {data['error'].get('code')}: {data['error'].get('info')}")
        return data
