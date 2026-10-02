"""Validação da lista de membros com as chefias (item 1 da fila) — só stdlib.

Três funções, todas sobre `data/`:

1. `load_overrides()` / `resolve_override()` — leem `data/membership_overrides.json`, a
   palavra das chefias. É a única fonte que vence a inferência de `attribute.py`.
2. `export_sheet()` — gera `data/membership_validation.csv`, a planilha que vai para as
   chefias da DIEST e da DISET (uma linha por membro atribuído, com a evidência que
   produziu a atribuição e três colunas em branco para preencher).
3. `audit()` — depois que a planilha volta, mede a **precisão** da inferência por estrato
   de confiança e grava `data/membership_audit.json` (lido por analysis.py → report.py).

Por que isso vem primeiro: METODO.md §5 — a atribuição de diretoria é parcialmente
circular (as obras definem a diretoria das pessoas; as pessoas definem quais obras são
mistas). A validação externa é barata e decide a confiabilidade de todo o resto.

Uso:
    python src/membership.py --export        # planilha para as chefias
    python src/membership.py --audit         # precisão, depois de preencher os overrides

ATENÇÃO (rule 6 do CLAUDE.md): a planilha serve para corrigir a *lotação* de cada pessoa.
Não é instrumento de avaliação individual e não contém medida de desempenho.
"""
import csv
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, FOCUS, load_json, name_key, save_json  # noqa: E402

OVERRIDES_FILE = "membership_overrides.json"
SHEET_FILE = "membership_validation.csv"
AUDIT_FILE = "membership_audit.json"

DIRECTORATES = ("DIEST", "DISET", "DISOC", "DIRUR", "DIMAC", "DINTE")
# situação preenchida pela chefia:
#   confirmado   — a diretoria inferida está certa
#   corrigido    — é outra diretoria (preencher diretoria_correta)
#   fora         — não é (nem era) membro de nenhuma diretoria de pesquisa (ex.: terceirizado,
#                  bolsista de outra unidade, pessoa que saiu do Ipea antes da janela)
#   desconhecido — a chefia não sabe dizer (não entra no cálculo de precisão)
STATUSES = ("confirmado", "corrigido", "fora", "desconhecido")
SHEET_COLS = ["author_id", "nome", "grupo", "diretoria_inferida", "confianca_inferida",
              "fonte", "ativo", "obras", "obras_rotuladas", "peso_dominante",
              "ultima_obra", "evidencia_pesos", "assinaturas", "perfil_url",
              "situacao", "diretoria_correta", "observacao"]


# ───────────────────────── 1. overrides ─────────────────────────

def load_overrides(path=None):
    """Lê os overrides das chefias. Devolve índices por author_id e por nome.

    Arquivo ausente ou sem registros → {} (o núcleo roda sem validação alguma).
    Registro malformado é erro duro: é melhor quebrar do que atribuir errado em silêncio.
    """
    path = path or os.path.join(DATA, OVERRIDES_FILE)
    out = {"by_id": {}, "by_name": {}, "records": [], "meta": {}}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out["meta"] = {k: v for k, v in raw.items() if k != "records"}
    for i, r in enumerate(raw.get("records", [])):
        st = (r.get("status") or "").strip().lower()
        if st not in STATUSES:
            raise ValueError(f"{OVERRIDES_FILE}[{i}]: status {st!r} não está em {STATUSES}")
        d = (r.get("diretoria") or "").strip().upper() or None
        if st == "corrigido" and d not in DIRECTORATES:
            raise ValueError(f"{OVERRIDES_FILE}[{i}]: status 'corrigido' exige diretoria "
                             f"em {DIRECTORATES} (veio {r.get('diretoria')!r})")
        if not (r.get("author_id") or r.get("name")):
            raise ValueError(f"{OVERRIDES_FILE}[{i}]: precisa de author_id ou name")
        rec = {"author_id": r.get("author_id"), "name": r.get("name"), "status": st,
               "diretoria": d, "validado_por": r.get("validado_por"),
               "data": r.get("data"), "nota": r.get("nota", "")}
        out["records"].append(rec)
        if rec["author_id"]:
            out["by_id"][rec["author_id"]] = rec
        if rec["name"]:
            out["by_name"][name_key(rec["name"])] = rec
    return out


def resolve_override(ovs, author_id, name, signatures=()):
    """author_id é a chave preferida; o nome é o reserva (a chefia pode ter só o nome)."""
    r = ovs["by_id"].get(author_id)
    if r:
        return r
    for n in (name,) + tuple(signatures):
        r = ovs["by_name"].get(name_key(n or ""))
        if r:
            return r
    return None


def apply_override(rec, diretoria, confidence):
    """(diretoria, confiança) depois da palavra da chefia. `validada*` vence tudo."""
    if rec is None or rec["status"] == "desconhecido":
        return diretoria, confidence
    if rec["status"] == "confirmado":
        return diretoria, "validada"
    if rec["status"] == "corrigido":
        return rec["diretoria"], "validada"
    return None, "validada_fora"  # status == "fora"


def write_template(path=None, force=False):
    """Cria o arquivo de overrides vazio, com o esquema documentado no próprio JSON."""
    path = path or os.path.join(DATA, OVERRIDES_FILE)
    if os.path.exists(path) and not force:
        return path
    tpl = {
        "_doc": ("Palavra das chefias da DIEST e da DISET sobre a lotação de cada pessoa. "
                 "Vence a inferência por produção de src/attribute.py. Preencher a partir de "
                 "data/membership_validation.csv (ver docs/VALIDACAO_MEMBROS.md)."),
        "_esquema": {
            "author_id": "chave de data/authors.json (ipea:…, repo:…, ext:…). Preferir a esta.",
            "name": "alternativa ao author_id, casada por (sobrenome, prenomes)",
            "status": list(STATUSES),
            "diretoria": list(DIRECTORATES) + [None],
            "validado_por": "quem respondeu (ex.: 'chefia DIEST')",
            "data": "AAAA-MM-DD",
            "nota": "texto livre (ex.: 'migrou da Diset para a Diest em 2023')",
        },
        "_fonte": "preencher",
        "_atualizado": None,
        "records": [],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tpl, f, ensure_ascii=False, indent=1)
    return path


# ───────────────────────── 2. planilha ─────────────────────────

def export_sheet(only_active=False, path=None):
    """Planilha de validação a partir de data/authors.json.

    Inclui (a) todo membro atribuído a DIEST ou DISET e (b) quem tem produção rotulada
    DIEST/DISET mas ficou *sem* atribuição (grupo `sem_atribuicao`) — pode ser membro que
    o método perdeu. Ordem: ativos primeiro, depois por volume de obras rotuladas, para
    que as primeiras linhas sejam as que mais afetam o resultado.
    """
    authors = load_json("authors.json")
    path = path or os.path.join(DATA, SHEET_FILE)
    rows = []
    for aid, v in authors.items():
        inf = v.get("inferred_diretoria", v.get("diretoria"))
        w = v.get("dir_weights", {})
        plausivel_quadro = v.get("roster") or v.get("staff") or (
            v.get("active") and v.get("n_tagged", 0) >= 3)
        if inf in FOCUS:
            grupo = "atribuido"
        elif (not v.get("diretoria") and (w.get("DIEST") or w.get("DISET"))
              and plausivel_quadro):
            # candidatos que o método pode ter perdido. Sem o filtro de quadro entram ~550
            # coautores externos com um único boletim — ruído que inviabiliza a revisão.
            grupo = "sem_atribuicao"
        else:
            continue
        if only_active and not v.get("active"):
            continue
        rows.append({
            "author_id": aid,
            "nome": v["name"],
            "grupo": grupo,
            "diretoria_inferida": inf or "",
            "confianca_inferida": v.get("inferred_confidence", v.get("confidence", "")),
            "fonte": "diretório" if v.get("roster") else ("cargo" if v.get("staff") else "produção"),
            "ativo": "sim" if v.get("active") else "não",
            "obras": v.get("n_items", 0),
            "obras_rotuladas": v.get("n_tagged", 0),
            "peso_dominante": v.get("share", 0),
            "ultima_obra": v.get("last_year") or "",
            "evidencia_pesos": "; ".join(f"{k} {val}" for k, val in list(w.items())[:4]),
            "assinaturas": " / ".join(v.get("signatures", [])[:3]),
            "perfil_url": v.get("profile_url") or "",
            "situacao": "", "diretoria_correta": "", "observacao": "",
        })
    rows.sort(key=lambda r: (r["grupo"] != "atribuido", r["ativo"] != "sim",
                             -r["obras_rotuladas"], r["nome"]))
    with open(path, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=SHEET_COLS, delimiter=";")
        wr.writeheader()
        # quebra de linha dentro de célula é CSV válido, mas atrapalha planilha de terceiro
        wr.writerows([{k: (v.replace("\n", " ").replace("\r", " ") if isinstance(v, str) else v)
                       for k, v in r.items()} for r in rows])
    return path, rows


def ingest_sheet(csv_path, validado_por=None, out_path=None):
    """Converte a planilha preenchida pelas chefias em data/membership_overrides.json.

    Só usa linhas com `situacao` preenchida; o resto é ignorado (fica pendente).
    """
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    records = []
    for i, r in enumerate(rows):
        st = (r.get("situacao") or "").strip().lower()
        if not st:
            continue
        if st not in STATUSES:
            raise ValueError(f"{csv_path} linha {i + 2}: situação {st!r} não está em {STATUSES}")
        records.append({"author_id": (r.get("author_id") or "").strip() or None,
                        "name": (r.get("nome") or "").strip() or None,
                        "status": st,
                        "diretoria": (r.get("diretoria_correta") or "").strip().upper() or None,
                        "validado_por": (r.get("validado_por") or validado_por or "").strip() or None,
                        "data": datetime.date.today().isoformat(),
                        "nota": (r.get("observacao") or "").strip()})
    out_path = out_path or os.path.join(DATA, OVERRIDES_FILE)
    base = {}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            base = json.load(f)
    base["records"] = records
    base["_atualizado"] = datetime.date.today().isoformat()
    base.setdefault("_fonte", f"planilha {os.path.basename(csv_path)} preenchida pelas chefias")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
    load_overrides(out_path)  # valida o que acabou de ser escrito
    return out_path, len(records)


# ───────────────────────── 3. precisão ─────────────────────────

def audit(authors=None, save=True):
    """Precisão da inferência contra a palavra das chefias, por estrato de confiança.

    Denominador: pessoas com situação decidida (`confirmado`/`corrigido`/`fora`);
    `desconhecido` não entra. `fora` conta como erro da inferência (atribuiu quem não é).
    """
    authors = authors or load_json("authors.json")
    strata = {}
    decided = confirmed = 0
    corrigidos, fora = [], []
    for aid, v in authors.items():
        st = v.get("validation")
        if st in (None, "desconhecido"):
            continue
        inf = v.get("inferred_diretoria")
        if inf not in FOCUS and st != "corrigido":
            continue  # só auditamos o que a inferência afirmou sobre DIEST/DISET
        conf = v.get("inferred_confidence", "?")
        s = strata.setdefault(conf, {"n": 0, "confirmados": 0})
        s["n"] += 1
        decided += 1
        if st == "confirmado":
            s["confirmados"] += 1
            confirmed += 1
        elif st == "corrigido":
            corrigidos.append({"name": v["name"], "inferida": inf, "correta": v.get("diretoria")})
        else:
            fora.append({"name": v["name"], "inferida": inf})
    for s in strata.values():
        s["precisao"] = round(s["confirmados"] / s["n"], 3) if s["n"] else None
    out = {
        "status": "pendente" if decided == 0 else "parcial",
        "n_decididos": decided, "n_confirmados": confirmed,
        "precisao": round(confirmed / decided, 3) if decided else None,
        "por_confianca": strata,
        "corrigidos": sorted(corrigidos, key=lambda x: x["name"]),
        "fora": sorted(fora, key=lambda x: x["name"]),
        "n_membros_focus": sum(1 for v in authors.values() if v.get("diretoria") in FOCUS),
        "n_desconhecido": sum(1 for v in authors.values() if v.get("validation") == "desconhecido"),
    }
    if save:
        save_json(AUDIT_FILE, out)
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--export" in argv:
        write_template()
        p, rows = export_sheet(only_active="--ativos" in argv)
        n_at = sum(1 for r in rows if r["grupo"] == "atribuido")
        print(f"→ {p}: {len(rows)} linhas ({n_at} atribuídos, {len(rows) - n_at} sem atribuição; "
              f"{sum(1 for r in rows if r['ativo'] == 'sim')} ativos)", file=sys.stderr)
    elif "--ingest" in argv:
        csv_path = argv[argv.index("--ingest") + 1]
        p, n = ingest_sheet(csv_path)
        print(f"→ {p}: {n} registros", file=sys.stderr)
    elif "--audit" in argv:
        a = audit()
        print(json.dumps({k: v for k, v in a.items() if k not in ("corrigidos", "fora")},
                         ensure_ascii=False, indent=1), file=sys.stderr)
    else:
        print(__doc__, file=sys.stderr)


if __name__ == "__main__":
    main()
