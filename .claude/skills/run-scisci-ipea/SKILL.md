---
name: run-scisci-ipea
description: Build, run, serve, screenshot and verify the SciSci/IPEA cienciometria static site (docs/, GitHub Pages) about cibernética · regulação · política industrial. Use when asked to launch the site, rebuild docs/ from scisci_results.json, drive it headless, check the charts/sections render, or capture a screenshot/PDF of the report.
---

# Run: SciSci · Cibernética, Regulação e Política Industrial

Static academic site published via **GitHub Pages from `docs/`**. It is **built**
by stdlib-only Python (`src/build_site.py`) from a single data source
(`data/scisci_results.json`) and **driven** headless with Playwright/Chromium via
`.claude/skills/run-scisci-ipea/driver.py`. All paths below are relative to the
repository root. There is no server-side runtime — it is HTML + vendored
Chart.js/fonts in `docs/vendor/` (no CDN).

## Prerequisites

Build needs only Python 3 (no numpy/pandas — they are intentionally absent here).
The agent/driver path additionally needs a headless browser:

```bash
pip install playwright && python -m playwright install --with-deps chromium
```

## Build

Regenerate `docs/` (HTML + the 8 CSVs in `docs/dados/`) from the JSON:

```bash
python src/build_site.py
```

Prints each of the 17 sections as `ok` and regenerates `docs/dados/`.

## Run — agent path (use this)

The driver builds (optional), serves `docs/` on an ephemeral port, drives it with
headless Chromium, and writes a full-page screenshot:

```bash
python .claude/skills/run-scisci-ipea/driver.py --build --shot /tmp/scisci_site.png
```

Verified output ends with:

```
charts:     3 (esperado 3)
sections:   17/17
spans vazios: nenhum
page errors:  NENHUM
STATUS: OK
```

`STATUS: OK` (exit 0) requires 0 page errors, exactly 3 Chart.js charts, all 17
sections present, and the 5 data spans filled. Drop `--build` to verify the
already-built `docs/` without regenerating. Target a section with
`--path '/#discussao'`. The screenshot lands at `--shot` (default
`/tmp/scisci_site.png`) — open it to confirm it is not blank.

## Run — human path

Serve and open in a browser (useless headless; for a human at a screen):

```bash
python3 -m http.server -d docs 8000   # then open http://127.0.0.1:8000/  · Ctrl-C to stop
```

To publish: GitHub repo → **Settings → Pages → Source: branch + `/docs`**.

## Gotchas

- **Assets are vendored on purpose** (`docs/vendor/chart.umd.min.js`,
  `docs/vendor/fonts/`). Do **not** repoint them at a CDN — under a restricted/
  .gov network the CDN fails the TLS handshake and **all charts vanish**
  (`Chart is not defined`). This was the original bug.
- **Charts draw after `document.fonts.ready`** (function `drawCharts()` in the
  template). Add new charts *inside* that function — drawing before the web font
  loads makes Chart.js mis-measure and **clip the axis labels**.
- **Single data source:** `data/scisci_results.json`. `build_site.py` generates
  `docs/dados/*.csv` from it — never hand-edit the CSVs. `docs/.nojekyll` keeps
  GitHub Pages from running Jekyll.
- **The full pipeline does NOT run here.** `colab/scisci_*.ipynb` needs igraph,
  leidenalg, scipy, sklearn, pyarrow, networkx + the OpenAlex API + ~45 min. This
  container regenerates the site from the saved JSON instead.
- Serve over HTTP, not `file://` (the driver and the human path both do this).

## Troubleshooting

| Symptom | Fix |
|---|---|
| Driver prints `Playwright ausente` | run the Prerequisites install line |
| Driver prints `docs/index.html ausente` | run the driver with `--build` (or `python src/build_site.py`) |
| `Chart is not defined` / `ERR_CERT_AUTHORITY_INVALID` in console | a chart/script is pointing at a CDN; restore the `docs/vendor/` local reference |
| Chart axis labels clipped | the chart was created outside `drawCharts()` (before fonts loaded) — move it inside |
