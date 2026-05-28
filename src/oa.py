"""Acesso ao OpenAlex: pool polido (mailto) + chave Premium via ambiente + cache em disco.

Lê do ambiente (ex.: secret do GitHub):
  OPENALEX_MAILTO   e-mail do pool polido (grátis; padrão lucasfreire@gmail.com)
  OPENALEX_API_KEY  chave do OpenAlex Premium (opcional) — sobe os limites de taxa
  OA_CACHE          diretório do cache de consultas (padrão data/oa_cache)

Sem a chave, usa o pool polido grátis (10 req/s, 100k/dia). `get()` tem backoff
exponencial que honra o 429 E **guarda cada resposta em disco** (por URL): re-execução
e depuração não re-consultam o OpenAlex e sobrevivem a quebras no meio do funil.
"""
import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

MAILTO = os.environ.get("OPENALEX_MAILTO", "lucasfreire@gmail.com")
API_KEY = os.environ.get("OPENALEX_API_KEY", "")
UA = {"User-Agent": f"scisci-ipea/1.0 (mailto:{MAILTO})"}
CACHE = os.environ.get("OA_CACHE", os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "oa_cache"))


def _augment(url):
    sep = "&" if "?" in url else "?"
    extra = "mailto=" + urllib.parse.quote(MAILTO)
    if API_KEY:
        extra += "&api_key=" + urllib.parse.quote(API_KEY)
    return url + sep + extra


def _cache_file(url):
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE, h[:2], h + ".json.gz")


def _read_cache(cf):
    """Lê o cache gzip; aceita o formato legado .json (sem .gz) por segurança."""
    if os.path.exists(cf):
        try:
            with gzip.open(cf, "rt", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    legacy = cf[:-3]  # .json sem o .gz
    if os.path.exists(legacy):
        try:
            return json.load(open(legacy, encoding="utf-8"))
        except Exception:
            pass
    return None


def get(url, use_cache=True):
    """GET JSON com pool polido/chave, **cache gzip em disco** e backoff honrando o 429.

    O cache é por URL (independe da credencial) e comprimido (~5–10× menor, imutável:
    cada consulta é gravada uma vez). Só respostas bem-sucedidas entram — um 429
    esgotado devolve {} e NÃO envenena o cache."""
    cf = _cache_file(url)
    if use_cache:
        cached = _read_cache(cf)
        if cached is not None:
            return cached
    u = _augment(url)
    for i in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45) as r:
                data = json.load(r)
            if use_cache:
                os.makedirs(os.path.dirname(cf), exist_ok=True)
                with gzip.open(cf, "wt", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            return data
        except urllib.error.HTTPError as e:
            time.sleep(min(60, 5 * (2 ** i)) if e.code == 429 else 3)
        except Exception:
            time.sleep(3)
    return {}

