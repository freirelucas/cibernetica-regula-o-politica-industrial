---
name: run-scisci-ipea
description: Build, run, serve, screenshot and verify the SciSci/IPEA cienciometria static site (docs/, GitHub Pages) about cibernética · regulação · política industrial — the report (index), the d3 co-citation explorer, and the inclusion/exclusion triage. Use when asked to launch/build the site, rebuild docs/ from scisci_results.json, drive it headless, check the charts/network/triage render, regenerate the Rayyan export, or capture a screenshot.
---

# Run: SciSci · Cibernética, Regulação e Política Industrial

Static academic site published via **GitHub Pages from `docs/`**. It is **built**
by stdlib-only Python (`src/build_site.py`) from a single data source
(`data/scisci_results.json` + `data/network.json`) and **driven** headless with
Playwright/Chromium via `.claude/skills/run-scisci-ipea/driver.py`. There is no
server runtime — HTML + vendored Chart.js/d3/fonts in `docs/vendor/` (no CDN).

The build emits **three pages** and the data exports:
- `docs/index.html` — the 22-section report (3 Chart.js charts + a canvas co-citation network).
- `docs/explorador.html` — interactive **d3 SVG** co-citation network (filters, search, communities).
- `docs/triagem.html` — **triage** tool: include/exclude/maybe over the synthesis, exports RIS.
- `docs/dados/` — 10 CSVs, the network JSON, and the **Rayyan** synthesis (`rayyan_sintese.{ris,csv,enw,bib,zip}`).

All paths below are relative to the repository root.

## Prerequisites

Build needs only Python 3 (no numpy/pandas — intentionally absent). The
agent/driver path additionally needs a headless browser:

```bash
pip install playwright && python -m playwright install --with-deps chromium
```

## Build

Regenerate everything in `docs/` from the JSON (no network needed):

```bash
python src/build_site.py
```

Prints the three pages (`site:`, `expl:`, `triag:`), `dados:` (CSVs), `rayyan:`
(N works), and each of the **22 sections** as `ok`. It calls `build_rayyan.build()`
internally, so the Rayyan files are refreshed too.

## Run — agent path (use this)

The driver builds (optional), serves `docs/` on an ephemeral port, drives **all
three pages** with headless Chromium, and writes a screenshot of each:

```bash
python .claude/skills/run-scisci-ipea/driver.py --build
```

Verified output ends with:

```
[index]       charts: 3 (esperado 3) · sections: 22/22 · spans vazios: nenhum · page errors: NENHUM -> OK
[explorador]  nós (círculos d3): 219 · page errors: NENHUM -> OK
[triagem]     cartões: 203 · page errors: NENHUM -> OK
screenshots: /tmp/scisci_site.png, /tmp/scisci_explorador.png, /tmp/scisci_triagem.png
STATUS: OK
```

`STATUS: OK` (exit 0) requires, on every page present: 0 page errors; index = 3
charts + 22 sections + 5 data spans filled; explorer = d3 nodes drawn; triage =
cards rendered. Drop `--build` to check the already-built `docs/`. Target an index
section with `--path '/#sintese'`. Open the screenshots to confirm they are not blank.

## Test

```bash
python -m pytest -q
```

26 tests: build/sections/placeholder, CSV headers (PT) + row counts, network
metrics, Rayyan export (RIS well-formed, dedup by OpenAlex id, abstract coverage,
single-file zip), and an anglicism scan of the site/explorer/triage/README/notebook.

## One-off data steps (network — cached, so re-runs are cheap/resumable)

These hit the OpenAlex API and rewrite committed data. **Every response is cached
in `data/oa_cache/`** (gzip, versioned) via `src/oa.py`, so re-runs and debugging
don't re-query and survive a mid-run 429/break (see the `/oa-cache` skill). Run to
refresh, then rebuild + commit:

```bash
python src/minirun.py                # real co-citation rede -> data/network.json
python src/enrich_rayyan.py          # authors/type/abstracts -> data/openalex_enrich.json
python src/split_eecs2.py --merge    # EECS-II volume -> 21 capítulos em data/cplx_works.json
python src/author_snowball.py        # obra dos autores-semente -> data/author_works.json
python src/coauthorship.py           # autores-ponte entre eixos -> data/coauthor_bridges.json
python src/cocitation_hypergraph.py  # ordem superior (hipergrafo) -> data/cocitation_hyperedges.json  (needs: pip install xgi)
```

## Run — human path

Serve and open in a browser (useless headless; for a human at a screen):

```bash
python3 -m http.server -d docs 8000   # http://127.0.0.1:8000/ · /explorador.html · /triagem.html · Ctrl-C
```

To publish: GitHub repo → **Settings → Pages → Source: branch + `/docs`**.

## Gotchas

- **`const X = …` is NOT `window.X`.** The injected data blocks declare
  `const NETWORK/NETMETA/RAYYAN_WORKS`. In a classic script these are lexical
  globals, **not** properties of `window`. The explorer and triage IIFEs must
  reference them bare (`typeof NETWORK !== 'undefined'`), never `window.NETWORK`
  — that bug renders an **empty graph / zero cards** with no error.
- **Assets are vendored on purpose** (`docs/vendor/`). Do **not** repoint them at
  a CDN — under a restricted/.gov network the TLS handshake fails and **all charts
  vanish** (`Chart is not defined`). This was the original bug.
- **Charts draw after `document.fonts.ready`** (`drawCharts()` in the template).
  Add new charts *inside* it, or Chart.js mis-measures and **clips axis labels**.
- **The Rayyan `.zip` holds ONE format (RIS).** Rayyan imports every file in the
  archive, so bundling ris+csv+enw+bib would create duplicate records. Synthesis
  is **deduplicated by OpenAlex id** (`build_rayyan.dedup_oaid`) — variants of the
  same work (truncated titles, "The X"/"X") collapse.
- **Single data source.** `build_site.py` regenerates `docs/dados/*.csv` from the
  JSON — never hand-edit the CSVs. `docs/.nojekyll` disables Jekyll on Pages.
- **The full pipeline does NOT run here.** `colab/scisci_*.ipynb` needs igraph,
  leidenalg, scipy, sklearn, networkx + the OpenAlex API + ~45 min. This container
  rebuilds the site from the saved JSON; `minirun.py` is the lightweight local rede.
- Serve over HTTP, not `file://` (the driver and the human path both do).
- **OpenAlex queries are cached + versioned** (`data/oa_cache/`, gzip, content-addressed
  by URL — immutable, no history churn). Re-running any crawl script above reads the
  cache (no re-query; survives a 429/break). Force a refresh by deleting the cache file
  or passing `use_cache=False`. The pre-commit hook keeps the cache staged. See `/oa-cache`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Driver prints `Playwright ausente` | run the Prerequisites install line |
| Driver prints `docs/index.html ausente` | run the driver with `--build` (or `python src/build_site.py`) |
| Explorer empty / triage 0 cards, no error | a script used `window.NETWORK`/`window.RAYYAN_WORKS`; reference the bare const |
| `Chart is not defined` / `ERR_CERT_AUTHORITY_INVALID` in console | a chart/script points at a CDN; restore the `docs/vendor/` local reference |
| Chart axis labels clipped | the chart was created outside `drawCharts()`; move it inside |
| `enrich_rayyan.py`/`minirun.py` hang or return little | needs outbound network (OpenAlex/Crossref); without it, the committed caches are used |
