"""Acesso ao OpenAlex: pool polido (mailto) + suporte a chave Premium via ambiente.

Lê do ambiente (ex.: secret do GitHub):
  OPENALEX_MAILTO   e-mail do pool polido (grátis; padrão lucasfreire@gmail.com)
  OPENALEX_API_KEY  chave do OpenAlex Premium (opcional) — sobe os limites de taxa

Sem a chave, usa o pool polido grátis (10 req/s, 100k/dia). Com a chave no secret,
os crawls pesados rodam com folga. `get()` tem backoff exponencial que honra o 429.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

MAILTO = os.environ.get("OPENALEX_MAILTO", "lucasfreire@gmail.com")
API_KEY = os.environ.get("OPENALEX_API_KEY", "")
UA = {"User-Agent": f"scisci-ipea/1.0 (mailto:{MAILTO})"}


def _augment(url):
    sep = "&" if "?" in url else "?"
    extra = "mailto=" + urllib.parse.quote(MAILTO)
    if API_KEY:
        extra += "&api_key=" + urllib.parse.quote(API_KEY)
    return url + sep + extra


def get(url):
    """GET JSON com pool polido/chave e backoff exponencial honrando o 429 do OpenAlex."""
    u = _augment(url)
    for i in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            time.sleep(min(60, 5 * (2 ** i)) if e.code == 429 else 3)
        except Exception:
            time.sleep(3)
    return {}
