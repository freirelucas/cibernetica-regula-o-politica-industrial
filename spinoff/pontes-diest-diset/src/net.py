"""GET com cache gzip em disco, retentativa e pausa educada — só stdlib.

Cache por URL em data/cache/ (versionável): re-execução e depuração não tocam a rede.
`NET_OFFLINE=1` → só cache (falha alta se faltar), para CI e reprodução.
"""
import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get("NET_CACHE", os.path.join(ROOT, "data", "cache"))
OFFLINE = os.environ.get("NET_OFFLINE") == "1"
UA = {"User-Agent": "pontes-diest-diset/0.1 (pesquisa cienciometrica; contato via IPEA)",
      "Accept-Encoding": "gzip"}
PAUSE = float(os.environ.get("NET_PAUSE", "0.4"))


def _cf(url):
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE, h[:2], h + ".gz")


def url_with(base, params):
    return base + ("&" if "?" in base else "?") + urllib.parse.urlencode(params)


def get_text(url, use_cache=True, tries=5):
    cf = _cf(url)
    if use_cache and os.path.exists(cf):
        with gzip.open(cf, "rt", encoding="utf-8") as f:
            return f.read()
    if OFFLINE:
        raise RuntimeError(f"NET_OFFLINE=1 e sem cache para {url}")
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                # o portal do Ipea responde em deflate (zlib) mesmo pedindo gzip
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                elif raw[:1] == b"x" and r.headers.get("Content-Encoding") in ("deflate", "gzip"):
                    raw = zlib.decompress(raw)
                txt = raw.decode("utf-8", errors="replace")
            os.makedirs(os.path.dirname(cf), exist_ok=True)
            with gzip.open(cf, "wt", encoding="utf-8") as f:
                f.write(txt)
            time.sleep(PAUSE)
            return txt
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            code = getattr(e, "code", None)
            if code == 404:
                raise
            time.sleep(2 ** k)
    raise RuntimeError(f"falhou após {tries} tentativas: {url} ({last})")


def get_json(url, use_cache=True):
    return json.loads(get_text(url, use_cache=use_cache))
