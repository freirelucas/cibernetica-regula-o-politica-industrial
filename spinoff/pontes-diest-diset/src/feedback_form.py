"""Gera o formulário de feedback por pessoa (página estática, sem rede, sem servidor).

A página é derivada de data/membership_validation.csv e exporta o MESMO formato CSV que
`membership.py --ingest` já lê. Assim há um único caminho de entrada: a resposta do colega
vira fila de revisão, e só depois de conferida entra em membership_overrides.json.

Decisões:
- Nada é gravado no servidor: o colega baixa o CSV preenchido e devolve.
- Mostra só o que o colega precisa para reconhecer a pessoa: nome, diretoria inferida,
  confiança, nº de obras rotuladas, última obra e o perfil público. Não mostra peso de
  evidência nem ordena por volume (evita leitura de ranking de produtividade).
- Ordem alfabética.
- O progresso parcial fica no navegador do próprio colega (localStorage), só como
  conveniência; a fonte de verdade é o CSV exportado.
- A página contém nomes de servidores: publique só atrás de login institucional.

Saída: docs/formulario_membros.html
Uso:   python src/feedback_form.py
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT  # noqa: E402

SRC = os.path.join(ROOT, "data", "membership_validation.csv")
OUT = os.path.join(ROOT, "docs", "formulario_membros.html")
DIRETORIAS = ["DIEST", "DISET", "DISOC", "DIRUR", "DIMAC", "DINTE"]


def load_rows():
    with open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    out = []
    for r in rows:
        out.append({
            "author_id": r["author_id"],
            "nome": r["nome"],
            "grupo": r["grupo"],
            "diretoria_inferida": r["diretoria_inferida"],
            "confianca": r["confianca_inferida"],
            "obras_rotuladas": int(r["obras_rotuladas"] or 0),
            "ultima_obra": r["ultima_obra"],
            "perfil_url": r["perfil_url"],
        })
    out.sort(key=lambda x: x["nome"].lower())
    return out


TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conferência de lotação · DIEST × DISET</title>
<style>
:root { --bg:#fbfaf7; --fg:#1d2330; --mute:#5c6470; --line:#dcd8cf; --card:#ffffff;
        --acc:#2e5d8c; --warn:#8a5a00; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
        --bg:#14171e; --fg:#e8eaf0; --mute:#9aa3b2; --line:#2c3340; --card:#1b2029;
        --acc:#7fb1e6; --warn:#e8b15a; } }
:root[data-theme="dark"] { --bg:#14171e; --fg:#e8eaf0; --mute:#9aa3b2; --line:#2c3340;
        --card:#1b2029; --acc:#7fb1e6; --warn:#e8b15a; }
body { background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, sans-serif;
       margin:0; padding:0 16px; }
main { max-width:860px; margin:0 auto; padding:24px 0 80px; }
h1 { font-size:1.4rem; margin:.2rem 0 .6rem; }
.intro { color:var(--mute); font-size:.95rem; }
.intro p { margin:.4rem 0; }
.bar { position:sticky; top:0; background:var(--bg); padding:10px 0; border-bottom:1px solid var(--line);
       display:flex; gap:10px; flex-wrap:wrap; align-items:center; z-index:2; }
.bar .prog { flex:1; font-size:.9rem; color:var(--mute); min-width:160px; }
button, .btn { font:inherit; background:var(--acc); color:#fff; border:0; border-radius:6px;
               padding:8px 14px; cursor:pointer; }
button.sec { background:transparent; color:var(--acc); border:1px solid var(--acc); }
.filtro { font:inherit; padding:6px 8px; border:1px solid var(--line); border-radius:6px;
          background:var(--card); color:var(--fg); }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:14px 16px; margin:12px 0; }
.card.feito { border-color:var(--acc); }
.card h2 { font-size:1.05rem; margin:0 0 4px; }
.meta { color:var(--mute); font-size:.88rem; margin-bottom:8px; }
.meta a { color:var(--acc); }
.opts { display:flex; gap:6px 16px; flex-wrap:wrap; margin:6px 0; }
.opts label { white-space:nowrap; }
select, textarea { font:inherit; background:var(--bg); color:var(--fg);
                   border:1px solid var(--line); border-radius:6px; padding:6px; }
textarea { width:100%; box-sizing:border-box; min-height:44px; margin-top:6px; }
.corr { display:none; margin-top:6px; }
.corr.on { display:inline-block; }
.sem { color:var(--warn); font-size:.85rem; }
.aviso { font-size:.88rem; color:var(--mute); border-left:3px solid var(--acc); padding:4px 10px; }
</style>
</head>
<body>
<main>
<h1>Conferência de lotação · DIEST e DISET</h1>
<div class="intro">
  <p>Cada cartão mostra uma pessoa com produção no Repositório do Ipea e a diretoria que o
  método inferiu a partir das obras. Sua resposta corrige a lista; <strong>não avalia ninguém</strong>.</p>
  <p>Marque uma das opções. Se a pessoa é de outra diretoria, escolha qual. Pode deixar em
  branco o que não souber. Ao final, baixe o CSV e devolva o arquivo. As respostas só entram
  na análise depois de revisadas.</p>
  <p class="aviso">Confirmado: a diretoria inferida está certa. ·
  Corrigido: é de outra diretoria (escolha abaixo). ·
  Fora: não é de nenhuma diretoria de pesquisa (ex.: consultor, coautor externo, já saiu).
  · Não sei: fica pendente.</p>
</div>
<div class="bar">
  <div class="prog" id="prog">0 de __N__ respondidos</div>
  <input class="filtro" id="filtro" placeholder="filtrar por nome">
  <select class="filtro" id="so"><option value="todos">todos</option>
    <option value="pend">só pendentes</option></select>
  <button class="sec" id="importar">Continuar de um CSV</button>
  <input type="file" id="arq" accept=".csv" hidden>
  <button id="exportar">Baixar respostas (CSV)</button>
</div>
<div id="lista"></div>
</main>
<script>
const DADOS = __DADOS__;
const DIRS = __DIRS__;
const CHAVE = "conferencia-lotacao-v1";
const COLS = ["author_id","nome","grupo","diretoria_inferida","confianca_inferida","fonte","ativo",
  "obras","obras_rotuladas","peso_dominante","ultima_obra","evidencia_pesos","assinaturas",
  "perfil_url","situacao","diretoria_correta","observacao"];

let R = {};   // author_id -> {situacao, diretoria_correta, observacao}
try { R = JSON.parse(localStorage.getItem(CHAVE) || "{}"); } catch (e) { R = {}; }
function salvar() { try { localStorage.setItem(CHAVE, JSON.stringify(R)); } catch (e) {} }

function esc(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }

function cartao(p) {
  const r = R[p.author_id] || {};
  const opt = (v, t) => `<label><input type="radio" name="s-${esc(p.author_id)}" value="${v}" ${r.situacao===v?"checked":""}> ${t}</label>`;
  const selDir = DIRS.map(d => `<option value="${d}" ${r.diretoria_correta===d?"selected":""}>${d}</option>`).join("");
  const semDir = !p.diretoria_inferida ? `<div class="sem">Sem diretoria inferida: qual é a diretoria, se houver?</div>` : "";
  const link = p.perfil_url ? ` · <a href="${esc(p.perfil_url)}" target="_blank" rel="noopener">perfil no portal</a>` : "";
  return `<div class="card ${r.situacao?"feito":""}" data-id="${esc(p.author_id)}" data-nome="${esc(p.nome.toLowerCase())}">
    <h2>${esc(p.nome)}</h2>
    <div class="meta">Diretoria inferida: <strong>${esc(p.diretoria_inferida || "nenhuma")}</strong>
      · confiança da inferência: ${esc(p.confianca)}
      · ${p.obras_rotuladas} obras rotuladas${p.ultima_obra ? " · última em " + esc(p.ultima_obra) : ""}${link}</div>
    ${semDir}
    <div class="opts">${opt("confirmado","Confirmado")}${opt("corrigido","Corrigido")}${opt("fora","Fora")}${opt("desconhecido","Não sei")}
      <span class="corr ${r.situacao==="corrigido"?"on":""}" id="c-${esc(p.author_id)}">
        <select data-k="dir" data-id="${esc(p.author_id)}"><option value="">diretoria correta…</option>${selDir}</select></span></div>
    <textarea data-k="obs" data-id="${esc(p.author_id)}" placeholder="observação (opcional, ex.: migrou para a Diset em 2023)">${esc(r.observacao||"")}</textarea>
  </div>`;
}

function desenhar() {
  const q = document.getElementById("filtro").value.trim().toLowerCase();
  const so = document.getElementById("so").value;
  const lista = DADOS.filter(p => (!q || p.nome.toLowerCase().includes(q)) &&
                                   (so === "todos" || !(R[p.author_id] || {}).situacao));
  document.getElementById("lista").innerHTML = lista.map(cartao).join("");
  const feitos = DADOS.filter(p => (R[p.author_id] || {}).situacao).length;
  document.getElementById("prog").textContent = `${feitos} de ${DADOS.length} respondidos`;
}

document.getElementById("lista").addEventListener("change", e => {
  const id = e.target.closest(".card")?.dataset.id;
  if (!id) return;
  R[id] = R[id] || {};
  if (e.target.type === "radio") {
    R[id].situacao = e.target.value;
    document.getElementById("c-" + id).classList.toggle("on", e.target.value === "corrigido");
    if (e.target.value !== "corrigido") R[id].diretoria_correta = "";
  } else if (e.target.dataset.k === "dir") R[id].diretoria_correta = e.target.value;
  salvar();
  const c = e.target.closest(".card"); c.classList.toggle("feito", !!R[id].situacao);
  document.getElementById("prog").textContent = `${DADOS.filter(p => (R[p.author_id]||{}).situacao).length} de ${DADOS.length} respondidos`;
});
document.getElementById("lista").addEventListener("input", e => {
  if (e.target.dataset.k !== "obs") return;
  const id = e.target.dataset.id; R[id] = R[id] || {}; R[id].observacao = e.target.value; salvar();
});
document.getElementById("filtro").addEventListener("input", desenhar);
document.getElementById("so").addEventListener("change", desenhar);

function linhaCSV(cols) {
  return cols.map(c => { const s = String(c ?? ""); return /[;"\\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }).join(";");
}
document.getElementById("exportar").addEventListener("click", () => {
  const linhas = [COLS.join(";")];
  for (const p of DADOS) {
    const r = R[p.author_id] || {};
    const corr = r.situacao === "corrigido" ? (r.diretoria_correta || "") : "";
    linhas.push(linhaCSV([p.author_id, p.nome, p.grupo, p.diretoria_inferida, p.confianca,
      "", "", "", p.obras_rotuladas, "", p.ultima_obra, "", "", p.perfil_url,
      r.situacao || "", corr, r.observacao || ""]));
  }
  const blob = new Blob(["\\ufeff" + linhas.join("\\n") + "\\n"], {type: "text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "membership_validation_respostas.csv";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
});
document.getElementById("importar").addEventListener("click", () => document.getElementById("arq").click());
document.getElementById("arq").addEventListener("change", async e => {
  const f = e.target.files[0]; if (!f) return;
  const txt = (await f.text()).replace(/^\\ufeff/, "");
  const linhas = txt.split(/\\r?\\n/).filter(Boolean);
  const cab = linhas[0].split(";");
  const iId = cab.indexOf("author_id"), iS = cab.indexOf("situacao"),
        iD = cab.indexOf("diretoria_correta"), iO = cab.indexOf("observacao");
  for (const l of linhas.slice(1)) {
    const campos = []; let m; const re = /(?:^|;)("(?:[^"]|"")*"|[^;]*)/g;
    while ((m = re.exec(l)) !== null) campos.push(m[1].replace(/^"|"$/g, "").replace(/""/g, '"'));
    const id = campos[iId]; if (!id) continue;
    R[id] = {situacao: campos[iS] || "", diretoria_correta: campos[iD] || "", observacao: campos[iO] || ""};
  }
  salvar(); desenhar();
  e.target.value = "";
});

desenhar();
</script>
</body>
</html>
"""


def main():
    rows = load_rows()
    html = (TEMPLATE
            .replace("__N__", str(len(rows)))
            .replace("__DADOS__", json.dumps(rows, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__DIRS__", json.dumps(DIRETORIAS)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{len(rows)} cartões → {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
