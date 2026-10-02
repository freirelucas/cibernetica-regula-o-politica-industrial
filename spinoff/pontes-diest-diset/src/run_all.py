"""Orquestrador: roster → colheita → atribuição → análise → relatório.

  python src/run_all.py              # tudo (usa cache; só busca o que falta)
  python src/run_all.py --from attribute   # só o offline (a partir dos dados versionados)
  NET_OFFLINE=1 python src/run_all.py --from attribute   # garante zero rede
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["roster", "harvest_repo", "attribute", "analysis", "report"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default="roster", choices=STEPS)
    ap.add_argument("--with-openalex", action="store_true")
    a = ap.parse_args()
    steps = STEPS[STEPS.index(a.start):]
    if a.with_openalex:
        steps.insert(steps.index("analysis") if "analysis" in steps else len(steps), "openalex_enrich")
    for s in steps:
        print(f"── {s}", file=sys.stderr, flush=True)
        subprocess.run([sys.executable, os.path.join(HERE, s + ".py")], check=True)


if __name__ == "__main__":
    main()
