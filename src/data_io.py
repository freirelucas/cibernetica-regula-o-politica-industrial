"""Camada de I/O tolerante para os derivados em data/ (PR-2).

Centraliza os caminhos de data/ e padroniza a leitura/escrita dos JSON derivados.
Antes, build_rayyan e build_site espalhavam `os.path.join(ROOT, "data", ...)` por
uma dúzia de pontos e quebravam de forma OPACA quando um derivado faltava após uma
regeneração parcial (um traceback de FileNotFoundError no meio do build, sem dizer
qual passo o produz). Agora há uma fronteira só:

  - load_data(name, required=False): derivado OPCIONAL ausente -> default ({} por
    padrão, ou o `default` informado) + aviso no stderr; derivado OBRIGATÓRIO
    ausente -> erro claro e cedo (SystemExit dizendo o caminho e como regenerar).
  - save_data(name, obj): grava JSON utf-8 de forma ATÔMICA (tmp + os.replace),
    para nunca deixar um derivado truncado se o processo morrer no meio.
  - data_path(name) / exists(name): resolvem o caminho sob data/ (passam adiante
    caminhos já absolutos, p/ conviver com as constantes de caminho existentes).

Regra de ouro do repo (ver .gitignore e a skill oa-cache): versiona-se o INSUMO
(cache real, fonte curada scisci_results.json) e NÃO os derivados volumosos — estes
o orquestrador (run_all.py) regenera. Esta camada é onde "derivado ausente" deixa
de ser um traceback e vira um aviso (opcional) ou um erro explicativo (obrigatório).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")


def data_path(name):
    """Resolve `name` sob data/. Caminho já absoluto passa adiante inalterado
    (compatível com as constantes de caminho de build_rayyan/build_site)."""
    return name if os.path.isabs(name) else os.path.join(DATA_DIR, name)


def exists(name):
    return os.path.exists(data_path(name))


def load_data(name, required=False, default=None):
    """Lê um JSON de data/ com tolerância explícita.

    required=False (padrão): ausente -> devolve `default` (ou {}) e AVISA no stderr.
    required=True: ausente -> SystemExit com mensagem clara (qual arquivo, como
    regenerar). Use para a fonte curada (scisci_results.json) e nada mais.
    """
    p = data_path(name)
    if not os.path.exists(p):
        if required:
            raise SystemExit(
                f"[data_io] derivado OBRIGATÓRIO ausente: {p}\n"
                f"  Regenere antes de prosseguir (src/run_all.py ou o produtor do JSON)."
            )
        print(f"[data_io] aviso: derivado opcional ausente: {os.path.basename(p)} "
              f"(seguindo com vazio — regenere com src/run_all.py)", file=sys.stderr)
        return {} if default is None else default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_data(name, obj, indent=1, ensure_ascii=False):
    """Grava `obj` como JSON em data/<name> de forma atômica (tmp + os.replace)."""
    p = data_path(name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=ensure_ascii, indent=indent)
    os.replace(tmp, p)
    return p
