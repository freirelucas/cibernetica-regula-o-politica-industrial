#!/usr/bin/env python3
"""Reproduz os achados da auditoria da skill analise-tematica-reflexiva (labiia-lab).

Acompanha a nota notes/2026-11-21-skill-atr-auditoria-e-sugestoes.md. Os identificadores
(A1, A2a, M4...) são os da nota.

Uso:
    git clone --depth 1 https://github.com/labiia-lab/analise-tematica-reflexiva /caminho/do/clone
    python3 -I -B notes/anexos/2026-11-21-atr-repro.py /caminho/do/clone [PASTA_DE_TRABALHO_VAZIA]
    python3 -I -B notes/anexos/2026-11-21-atr-repro.py /caminho/do/clone --estrito   # sai com 1 se algo reproduzir

O que o script faz e não faz:
- só lê o clone; roda os dois scripts da skill em modo isolado (-I) e sem gravar .pyc (-B);
- monta análises mínimas e FICTÍCIAS numa pasta temporária (nomes, e-mail, telefone e CPF
  abaixo são inventados para o ensaio de privacidade; não descrevem ninguém);
- para cada achado imprime REPRODUZ ou "não reproduz" e, no fim, uma tabela.

Resultado na versão auditada (commit 3fb9a89, 2.0.0, Python 3.11): todos reproduzem, menos a
hipótese do difflib, que foi descartada. Numa versão futura, "não reproduz" indica correção
(ou mudança de interface: conferir a linha de base, que tem de sair com 0 e sem erros).
"""
from __future__ import annotations

import hashlib
import json
import random
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ESTRITO = "--estrito" in sys.argv
if not ARGS:
    sys.exit(__doc__)
REPO = Path(ARGS[0]).resolve()
AUD = REPO / "scripts" / "auditar_analise.py"
VER = REPO / "scripts" / "verificar_citacoes.py"
TEMPLATES = REPO / "templates"
if len(ARGS) > 1:
    TRAB = Path(ARGS[1]).resolve()
    TRAB.mkdir(parents=True, exist_ok=True)
    if any(TRAB.iterdir()):
        sys.exit(f"a pasta de trabalho precisa estar vazia: {TRAB}")
else:
    TRAB = Path(tempfile.mkdtemp(prefix="atr-repro-"))

RESULTADOS: list[tuple[str, str, bool]] = []


def achado(ident, descricao, reproduz, detalhe=""):
    RESULTADOS.append((ident, descricao, bool(reproduz)))
    print(f"  [{'REPRODUZ' if reproduz else 'não reproduz'}] {ident}  {descricao}" + (f"  | {detalhe}" if detalhe else ""))


def run(script, *args):
    p = subprocess.run([sys.executable, "-I", "-B", str(script), *[str(a) for a in args]],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def jl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def rjl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def ultima(stderr):
    linhas = [l for l in stderr.strip().splitlines() if l.strip()]
    return linhas[-1].split(":")[0] if linhas else "sem mensagem"


def titulo(t):
    print("\n" + t)


P1 = ("E1: Como foi o começo da cooperativa?\n"
      "P1: No começo a gente dividia o forno e ninguém anotava nada.\n"
      "P1: Depois que entrou o caderno de horas, quem amassava o pão passou a mandar no horário.\n"
      "P2: Eu aceito a escala quando ela protege a minha folga, não quando serve para me vigiar.\n"
      "P2: A gente trabalha o dia todo e ainda escuta que faltou empenho.\n")
P2 = ("P3: Quem nunca ficou até o fim da limpeza não devia cobrar horário de ninguém.\n"
      "P3: Faltar sem avisar pesa mais do que errar a receita.\n"
      "P4: Ela pode falar, ela carregou isso aqui sozinha por muitos anos.\n")
T1 = "quem amassava o pão passou a mandar no horário"
T2 = "Eu aceito a escala quando ela protege a minha folga, não quando serve para me vigiar."
T3 = "Quem nunca ficou até o fim da limpeza não devia cobrar horário de ninguém."
T4 = "Ela pode falar, ela carregou isso aqui sozinha por muitos anos."
T5 = "A gente trabalha o dia todo e ainda escuta que faltou empenho."
FABRICADA = "quem amassava o pão virou dono da cooperativa inteira"

RELATORIO = (
    "# O trabalho feito autoriza a cobrança\n\n## 5. Temas\n\n"
    "A regra é medida por quem a invoca.\n\n"
    f"> “{T1}” (F01, linha 3)\n\n"
    "O excerto liga o mando ao registro do trabalho, e não ao cargo de quem manda.\n\n"
    f"> “{T3}” (F02, linha 1)\n\n"
    "A cobrança é recusada pela falta de lastro de quem cobra, e não pelo conteúdo da regra.\n\n"
    f"> “{T4}” (F02, linha 3)\n\n"
    "O trabalho que autoriza não precisa ser de hoje, o que complica a primeira afirmação.\n\n"
    f"> “{T2}” (F01, linha 4)\n\n"
    "A mesma escala muda de sentido conforme a função que cumpre para quem a recebe.\n"
)


def registro_base():
    return [
        {"tipo": "fonte", "id": "F01", "arquivo": "p1.txt", "estatuto": "fala_primaria"},
        {"tipo": "fonte", "id": "F02", "arquivo": "p2.txt", "estatuto": "fala_primaria"},
        {"tipo": "excerto", "id": "Q001", "fonte": "F01", "forma": "literal", "texto": T1,
         "localizador": "linha 3", "contexto": "linhas 2-4", "falante": "P1"},
        {"tipo": "excerto", "id": "Q002", "fonte": "F01", "forma": "literal", "texto": T2,
         "localizador": "linha 4", "contexto": "linhas 3-5", "falante": "P2"},
        {"tipo": "excerto", "id": "Q003", "fonte": "F02", "forma": "literal", "texto": T3,
         "localizador": "linha 1", "contexto": "linhas 1-2", "falante": "P3"},
        {"tipo": "excerto", "id": "Q004", "fonte": "F02", "forma": "literal", "texto": T4,
         "localizador": "linha 3", "contexto": "linhas 2-3", "falante": "P4"},
        {"tipo": "excerto", "id": "Q005", "fonte": "F01", "forma": "literal", "texto": T5,
         "localizador": "linha 5", "contexto": "linhas 4-5", "falante": "P2"},
        {"tipo": "codigo", "id": "C01", "rotulo": "anotar o trabalho vira direito de mando", "excertos": ["Q001"]},
        {"tipo": "codigo", "id": "C02", "rotulo": "escala aceita como proteção, recusada como vigilância", "excertos": ["Q002"]},
        {"tipo": "codigo", "id": "C03", "rotulo": "só cobra quem ficou até o fim", "excertos": ["Q003", "Q004"]},
        {"tipo": "codigo", "id": "C04", "rotulo": "empenho medido por quem não vê a jornada", "excertos": ["Q005"]},
        {"tipo": "tema", "id": "TC1", "fase": "candidato", "nome": "Quem trabalha manda",
         "conceito": "mando derivado do trabalho", "codigos": ["C01", "C03"]},
        {"tipo": "tema", "id": "TC2", "fase": "candidato", "nome": "A regra medida por quem a invoca",
         "conceito": "legitimidade da cobrança", "codigos": ["C02", "C04"]},
        {"tipo": "tema", "id": "TF1", "fase": "final", "nome": "O trabalho feito autoriza a cobrança",
         "conceito": "mando derivado do trabalho reconhecido", "codigos": ["C01", "C03"], "origem": ["TC1"],
         "ancoras": ["Q001", "Q003"], "evidencia_decisiva": ["Q003"], "tensoes": ["Q004"]},
        {"tipo": "tema", "id": "TF2", "fase": "final", "nome": "A escala protege ou vigia conforme quem a aplica",
         "conceito": "legitimidade da cobrança", "codigos": ["C02", "C04"], "origem": ["TC2"],
         "ancoras": ["Q002", "Q005"],
         "busca_contraevidencia": "reli p1.txt e p2.txt buscando aceitação da escala sem condição; nada achado"},
        {"tipo": "hipotese", "id": "H1", "texto": "a escala seria recusada em bloco", "destino": "revista",
         "evidencia": "Q002 condiciona a aceitação"},
    ]


class Caso:
    """Uma análise fictícia completa: corpus, registro, relatório e arquivos de trilha."""

    def __init__(self, nome, registros=None, relatorio=RELATORIO):
        self.raiz = TRAB / nome
        if self.raiz.exists():
            shutil.rmtree(self.raiz)
        self.corpus, self.saida = self.raiz / "corpus", self.raiz / "saida"
        self.corpus.mkdir(parents=True)
        self.saida.mkdir()
        (self.corpus / "p1.txt").write_text(P1, encoding="utf-8")
        (self.corpus / "p2.txt").write_text(P2, encoding="utf-8")
        self.reg = self.saida / "evidencias.jsonl"
        jl(self.reg, registros or registro_base())
        self.rel = self.saida / "06-relatorio-final.md"
        self.rel.write_text(relatorio, encoding="utf-8")
        self.man, self.cit = self.saida / "manifesto-corpus.jsonl", self.saida / "citacoes.jsonl"
        self.ver, self.lei = self.saida / "verificacao-citacoes.jsonl", self.saida / "leitura.jsonl"
        self.aud = self.saida / "auditoria-integridade.json"

    def verificar(self, base=None):
        run(AUD, "citacoes", "--registro", self.reg, "--output", self.cit)
        return run(VER, "--input", self.cit, "--base", base or self.corpus, "--output", self.ver)

    def preparar(self):
        run(VER, "--inventario", self.corpus, "--output", self.man)
        self.verificar()
        jl(self.lei, [{"fonte": r["source"], "inicio": 1, "fim": r["lines"], "memo": "M-" + r["source"]}
                      for r in rjl(self.man)])
        return self

    def integridade(self, completo=True):
        """Roda o comando do SKILL.md; com completo=False, só --registro e --output."""
        args = ["integridade", "--registro", self.reg, "--output", self.aud]
        if completo:
            args += ["--verificacao", self.ver, "--manifesto", self.man, "--leitura", self.lei,
                     "--saida", self.saida, "--relatorio", self.rel, "--templates", TEMPLATES]
        cod, _, err = run(AUD, *args)
        res = json.loads(self.aud.read_text(encoding="utf-8")) if self.aud.exists() else {}
        return cod, res, err


def erros(res, codigo=None):
    return [e for e in res.get("erros", []) if codigo is None or e["codigo"] == codigo]


def alertas(res):
    return {a["codigo"] for a in res.get("alertas", [])}


def verifica(base, registros, nome="v"):
    ent, sai = base.parent / f"{nome}-citacoes.jsonl", base.parent / f"{nome}-resultado.jsonl"
    jl(ent, registros)
    cod, _, err = run(VER, "--input", ent, "--base", base, "--output", sai)
    return cod, (rjl(sai) if sai.exists() else []), err


def cit(ident, texto, fonte, loc=""):
    return {"citation_id": ident, "text": texto, "source": fonte, "declared_locator": loc}


def corpus_em(nome, arquivos):
    base = TRAB / nome / "corpus"
    base.mkdir(parents=True)
    for arquivo, conteudo in arquivos.items():
        if isinstance(conteudo, bytes):
            (base / arquivo).write_bytes(conteudo)
        else:
            (base / arquivo).write_text(conteudo, encoding="utf-8")
    return base


print(f"clone: {REPO}\npasta de trabalho: {TRAB}")

# ---------------------------------------------------------------- linha de base
titulo("Linha de base: análise fictícia íntegra, comando completo do SKILL.md")
c = Caso("base").preparar()
cod, res, _ = c.integridade()
BASE_OK = cod == 0 and not erros(res)
print(f"  saída {cod} | erros {len(erros(res))} | alertas {sorted(alertas(res))} | verificação {res.get('verificacao')} "
      f"| cobertura {res.get('cobertura', {}).get('estado')}")
if not BASE_OK:
    print("  ATENÇÃO: a linha de base não passou. A interface dos scripts mudou; os ensaios abaixo não são confiáveis.")

# ---------------------------------------------------------------- A1
titulo("A1  A palavra 'todo' vira erro de resto de rascunho (E10)")
c = Caso("a1").preparar()
(c.saida / "01-familiarizacao.md").write_text("# F1\n\nA leitura cobriu todo o corpus declarado, em dois lotes.\n", encoding="utf-8")
c.rel.write_text(RELATORIO + f"\n> “{T5}” (F01, linha 5)\n\nO empenho é medido por quem não acompanha a jornada inteira.\n", encoding="utf-8")
cod, res, _ = c.integridade()
rasc = [e for e in erros(res, "E10") if "rascunho" in e["mensagem"]]
achado("A1", "prosa e fala literal com 'todo' reprovam a auditoria", cod == 1 and len(rasc) >= 1,
       f"saída {cod}; E10 em {[e['ref'] for e in rasc]}")

# ---------------------------------------------------------------- A2
titulo("A2  O PASS não garante que os excertos existem no corpus inventariado")
c = Caso("a2a").preparar()
regs = registro_base()
regs[2]["texto"] = FABRICADA
jl(c.reg, regs)
c.rel.write_text(RELATORIO.replace(T1, FABRICADA), encoding="utf-8")
cod, res, _ = c.integridade()
achado("A2a", "excerto trocado por frase inventada depois de verificado continua aprovado",
       cod == 0 and not erros(res, "E04") and not erros(res, "E08"), f"saída {cod}; verificação {res.get('verificacao')}")

c = Caso("a2b").preparar()
falso = c.raiz / "corpus-alterado"
shutil.copytree(c.corpus, falso)
(falso / "p1.txt").write_text(P1.replace(T1, FABRICADA), encoding="utf-8")
jl(c.reg, regs)
c.rel.write_text(RELATORIO.replace(T1, FABRICADA), encoding="utf-8")
c.verificar(base=falso)
cod, res, _ = c.integridade()
sha_man = {r["source"]: r["sha256"] for r in rjl(c.man)}
sha_ver = {r["source"]: r.get("source_sha256") for r in rjl(c.ver)}
achado("A2b", "verificação feita contra outra pasta passa; SHA-256 da verificação não é cruzado com o manifesto",
       cod == 0 and sha_man["p1.txt"] != sha_ver["p1.txt"], f"saída {cod}; hashes de p1.txt diferentes")

base = corpus_em("a2c", {"p1.txt": P1})
fora = TRAB / "a2c" / "rascunho-do-agente.txt"
fora.write_text("frase que só existe fora do corpus declarado\n", encoding="utf-8")
cod, linhas_v, _ = verifica(base, [cit("X1", "frase que só existe fora do corpus declarado", "../rascunho-do-agente.txt", "linha 1"),
                                   cit("X2", "frase que só existe fora do corpus declarado", str(fora), "linha 1")])
achado("A2c", "verificador aceita fonte fora da pasta do corpus ('..' ou caminho absoluto)",
       all(r["status"] == "verified_exact" for r in linhas_v), str([r["status"] for r in linhas_v]))

c = Caso("a2d").preparar()
c.reg.write_text("", encoding="utf-8")
cod, res, _ = c.integridade(completo=False)
achado("A2d", "registro de evidências vazio sai com 0", cod == 0 and not erros(res), f"saída {cod}")

c = Caso("a2e").preparar()
cod, res, _ = c.integridade(completo=False)
achado("A2e", "omitir --verificacao desliga a checagem sem marca no resultado",
       cod == 0 and "verificacao" not in res, f"saída {cod}; 5 excertos literais; chaves {sorted(k for k in res if k not in ('erros', 'alertas'))}")

c = Caso("a2f").preparar()
c.rel.unlink()
cod, res, _ = c.integridade()
achado("A2f", "comando único do SKILL.md falha antes de existir o relatório (fim de F2 e F5)",
       cod == 1 and any("No such file" in e["mensagem"] or "Errno 2" in e["mensagem"] for e in erros(res, "E01")), f"saída {cod}")

# ---------------------------------------------------------------- A3
titulo("A3  Privacidade")
pasta = TRAB / "a3" / "saida"
pasta.mkdir(parents=True)
frase = "Pode me escrever em maria.souza@exemplo.org ou ligar no (61) 99876-5432, meu CPF é 123.456.789-09"
jl(pasta / "evidencias.jsonl", [{"tipo": "excerto", "id": "Q900", "fonte": "F01", "forma": "literal", "texto": frase,
                                 "localizador": "linha 9", "contexto": "linhas 8-10", "falante": "Maria de Souza"}])
jl(pasta / "manifesto-corpus.jsonl", [{"source": "entrevista_maria_de_souza.txt", "bytes": 10, "lines": 1, "sha256": "0" * 64}])
(pasta / "00-constituicao-analitica.md").write_text("# F0\n\nA análise usa identificadores neutros.\n", encoding="utf-8")
cod, _, _ = run(AUD, "privacidade", "--saida", pasta, "--output", pasta.parent / "p1.json")
n = len(json.loads((pasta.parent / "p1.json").read_text(encoding="utf-8"))["candidatos"])
achado("A3a", "identificadores em .jsonl do pacote de saída não são vistos (só .md é lido)", cod == 0 and n == 0,
       f"saída {cod}; {n} candidatos")
nomes = pasta.parent / "nomes.txt"
nomes.write_text("José Antônio\n", encoding="utf-8")
(pasta / "03-temas-candidatos.md").write_text("# F3\n\no relato de jose antonio sobre a escala\n", encoding="utf-8")
run(AUD, "privacidade", "--saida", pasta, "--nomes", nomes, "--output", pasta.parent / "p2.json")
achou = [x for x in json.loads((pasta.parent / "p2.json").read_text(encoding="utf-8"))["candidatos"]
         if x["classe"].startswith("nome informado")]
achado("A3b", "lista de nomes é sensível a acento ('José Antônio' não acha 'jose antonio')", not achou)

# ---------------------------------------------------------------- M4
titulo("M4  Cobertura com arquivo binário ou oculto na pasta do corpus")
c = Caso("m4")
(c.corpus / ".DS_Store").write_bytes(b"\x00\x01Bud1\n\x00\x02\n\x00")
(c.corpus / "entrevista-03.docx").write_bytes(b"PK\x03\x04\n" + b"\x00\xff\n" * 40)
run(VER, "--inventario", c.corpus, "--output", c.man)
c.verificar()
jl(c.lei, [{"fonte": "p1.txt", "inicio": 1, "fim": 5, "memo": "M1"}, {"fonte": "p2.txt", "inicio": 1, "fim": 3, "memo": "M2"}])
cod, res, _ = c.integridade()
incompletas = [x["fonte"] for x in res.get("cobertura", {}).get("fontes_incompletas", [])]
achado("M4", "dois .txt lidos por inteiro ao lado de .docx e .DS_Store dão cobertura 'parcial'",
       res.get("cobertura", {}).get("estado") == "parcial" and set(incompletas) == {".DS_Store", "entrevista-03.docx"},
       f"manifesto {[(r['source'], r['lines']) for r in rjl(c.man)]}")

# ---------------------------------------------------------------- M5
titulo("M5  Códigos de saída e tratamento de entrada inválida")
c = Caso("m5").preparar()
nada = TRAB / "m5" / "nao-existe"
lista = TRAB / "m5" / "respostas-lista.json"
lista.write_text("[1, 2, 3]", encoding="utf-8")
sondas = [
    ("privacidade --saida inexistente", [AUD, "privacidade", "--saida", nada, "--output", TRAB / "m5" / "o1.json"]),
    ("integridade --saida inexistente", [AUD, "integridade", "--registro", c.reg, "--saida", nada, "--output", TRAB / "m5" / "o2.json"]),
    ("sobrealegacao --relatorio inexistente", [AUD, "sobrealegacao", "--relatorio", nada / "r.md", "--output", TRAB / "m5" / "o3.json"]),
    ("homogeneizacao --relatorios inexistentes", [AUD, "homogeneizacao", "--relatorios", nada / "a.md", nada / "b.md", "--output", TRAB / "m5" / "o4.json"]),
    ("privacidade --nomes inexistente", [AUD, "privacidade", "--saida", c.saida, "--nomes", nada / "n.txt", "--output", TRAB / "m5" / "o5.json"]),
    ("aptidao com JSON em lista", [AUD, "aptidao", "--respostas", lista, "--output", TRAB / "m5" / "o6.json"]),
]
codigos = []
for rotulo, comando in sondas:
    cod, _, err = run(*comando)
    codigos.append(cod)
    print(f"    {rotulo:42} saída {cod}  ({ultima(err)})")
achado("M5a", "entrada inválida não devolve 2, contra o contrato do SKILL.md", any(k != 2 for k in codigos),
       f"{sum(1 for k in codigos if k != 2)} de {len(codigos)} sondas; códigos {codigos}")

c = Caso("m5b").preparar()
c.integridade()
antes = hashlib.sha256(c.aud.read_bytes()).hexdigest()
c.reg.write_text("{{{ isto não é JSON\n", encoding="utf-8")
cod2, _, _ = c.integridade()
achado("M5b", "com registro inválido, o resultado da execução anterior permanece no disco",
       cod2 == 2 and hashlib.sha256(c.aud.read_bytes()).hexdigest() == antes, f"saída {cod2}")

quedas = []
for rotulo, mutacao in (("codigo.excertos = 3", lambda r: r[7].update(excertos=3)),
                        ("tema.ancoras = [['Q001']]", lambda r: r[13].update(ancoras=[["Q001"]]))):
    regs_m = registro_base()
    mutacao(regs_m)
    c = Caso("m5c").preparar()
    jl(c.reg, regs_m)
    c.aud.unlink(missing_ok=True)
    cod, res, err = c.integridade(completo=False)
    quedas.append(cod == 1 and not res)
    print(f"    {rotulo:28} saída {cod}  gravou resultado: {bool(res)}  ({ultima(err)})")
achado("M5c", "JSON válido com tipo errado derruba o auditor com saída 1 e sem resultado", any(quedas))

# ---------------------------------------------------------------- M6
titulo("M6  Conferência das citações do relatório (E08)")
casos_rel = {
    "M6a": ("bloco de citação inventado, sem aspas, não é conferido",
            "# R\n\nA regra pesa.\n\n> A escala nunca foi discutida e sempre foi imposta pela diretoria da cooperativa\n\nComentário sobre o excerto.\n"),
    "M6b": ("citação inventada com menos de cinco palavras não é conferida",
            "# R\n\nP3 resume a recusa em “nunca mais volto lá” e encerra o assunto.\n"),
}
for ident, (descricao, texto) in casos_rel.items():
    c = Caso(ident.lower(), relatorio=texto).preparar()
    cod, res, _ = c.integridade()
    achado(ident, descricao, not erros(res, "E08"), f"saída {cod}")
retas = f'# R\n\nO termo "fiscal" aparece quando P3 explica por que parou de frequentar a cooperativa "{T3}" e isso desloca a regra.\n'
c = Caso("m6c", relatorio=retas).preparar()
cod, res, _ = c.integridade()
pub = res.get("relatorio", {}).get("excertos_publicados", [])
achado("M6c", "aspas retas: termo curto antes da citação faz acusar a prosa e pular a fala real",
       bool(erros(res, "E08")) and "Q003" not in pub, f"E08: {len(erros(res, 'E08'))}; publicados {pub}")
c = Caso("m6c-controle", relatorio=retas.replace('"fiscal"', "“fiscal”").replace(f'"{T3}"', f"“{T3}”")).preparar()
cod, res, _ = c.integridade()
print(f"    controle com aspas curvas: E08 {len(erros(res, 'E08'))}; publicados {res.get('relatorio', {}).get('excertos_publicados')}")

# ---------------------------------------------------------------- M7
titulo("M7  Regra de marcador de template (E10)")
c = Caso("m7").preparar()
linhas = ["# F4", "", "- perfil: isolado | sequencial", "- nível: Essencial | Aprofundada", "",
          "| Tema | Rival | Decisão |", "|---|---|---|", "|  |  |  |", "",
          "P3 hesita [trecho inaudível por alguns segundos] antes de responder.", ""]
(c.saida / "04-contestacao-e-revisao.md").write_text("\n".join(linhas), encoding="utf-8")
cod, res, _ = c.integridade()
acusadas = {e["ref"].split(":")[1] for e in erros(res, "E10") if e["ref"].startswith("04-")}
achado("M7a", "alternativa de duas opções deixada no texto não é acusada", "3" not in acusadas and "4" not in acusadas)
achado("M7b", "linha de tabela totalmente vazia não é acusada", "8" not in acusadas)
achado("M7c", "anotação entre colchetes com 4+ palavras é acusada como erro", "10" in acusadas)
moldes = TRAB / "m7-moldes" / "saida"
moldes.mkdir(parents=True)
for i, p in enumerate(sorted(TEMPLATES.rglob("*.md")), 1):
    shutil.copy(p, moldes / f"{i:02d}-{p.name}")
run(AUD, "integridade", "--registro", TRAB / "base" / "saida" / "evidencias.jsonl", "--saida", moldes, "--output", moldes.parent / "r.json")
res_m = json.loads((moldes.parent / "r.json").read_text(encoding="utf-8"))
print(f"    templates entregues sem preencher: {len(erros(res_m, 'E10'))} erros E10 "
      "(na versão auditada: 86, para 129 campos a preencher; 44 campos não são acusados)")

# ---------------------------------------------------------------- M8
titulo("M8  Rótulo 'efeito estrutural'")
regs_s = registro_base()
for r in regs_s:
    r.pop("origem", None)
c = Caso("m8", registros=regs_s).preparar()
cod, res, _ = c.integridade()
d = res.get("diff_temas", {})
achado("M8", "mesmos temas sem o campo opcional 'origem' viram 'efeito estrutural' e o alerta A09 some",
       d.get("efeito") == "estrutural" and "A09" not in alertas(res), f"novos {d.get('novos')}; abandonos {d.get('abandonos')}")

# ---------------------------------------------------------------- M9
titulo("M9  Verificador de citações: quase-acertos e formas equivalentes")
PARAGRAFO = ("P5: Quando a cooperativa começou a pagar por hora, eu achei que ia ser mais justo, porque antes quem chegava cedo "
             "e quem chegava tarde recebia igual, mas depois eu vi que a hora anotada virou motivo de briga, cada um conferindo "
             "o caderno do outro, e a padaria que era um lugar de conversa ficou parecendo repartição, com gente olhando o "
             "relógio em vez de olhar a massa, e eu mesma passei a anotar minuto por minuto com medo de alguém dizer que eu "
             "estava roubando tempo dos colegas.")
POLIDA = "a padaria que era um lugar de conversa ficou parecendo repartição, com gente olhando para o relógio em vez de olhar a massa"
longa = corpus_em("m9a-longa", {"p5.txt": PARAGRAFO + "\n"})
curta = corpus_em("m9a-curta", {"p5.txt": PARAGRAFO.replace(", ", ",\n") + "\n"})
_, rl, _ = verifica(longa, [cit("Y1", POLIDA, "p5.txt", "linha 1")])
_, rc, _ = verifica(curta, [cit("Y1", POLIDA, "p5.txt", "linha 1")])
achado("M9a", "citação com uma palavra a mais dentro de turno em linha longa sai como not_found",
       rl[0]["status"] == "not_found", f"linha longa: {rl[0]['status']}; mesmo texto em linhas curtas: {rc[0]['status']} {rc[0].get('similaridade', '')}")

base = corpus_em("m9b", {"nfd.txt": unicodedata.normalize("NFD", P2),
                         "aspas.txt": 'P7: Ela disse "aqui ninguém manda em ninguém" e foi embora.\n'})
_, rv, _ = verifica(base, [cit("N1", T3, "nfd.txt", "linha 1"),
                           cit("N2", "Ela disse “aqui ninguém manda em ninguém” e foi embora.", "aspas.txt", "linha 1")])
achado("M9b", "texto idêntico em outra forma Unicode (NFD) ou com aspas curvas sai como 'substituir'",
       any(r["status"] == "substituir" for r in rv), str([(r["citation_id"], r["status"]) for r in rv]))

bruto = ("P6: A gente combinou a escala no papel,\r\ne no outro dia ninguém lembrava do combinado.\r\n"
         "P6: Aí virou cada um por si.\r\n")
base = corpus_em("m9c", {"crlf.txt": bruto.encode("utf-8")})
_, rv, _ = verifica(base, [cit("W2", "P6: A gente combinou a escala no papel,\ne no outro dia ninguém se lembrava do combinado.", "crlf.txt", "linhas 1-2")])
achado("M9c", "em arquivo com fim de linha do Windows, o suggested_text não é trecho exato do arquivo",
       rv[0]["status"] == "substituir" and rv[0]["suggested_text"] not in bruto, f"{rv[0]['status']}; localizador sugerido {rv[0].get('suggested_locator')!r}")

base = corpus_em("m9d", {"p2.txt": P2})
_, rv, _ = verifica(base, [cit("L2", T3, "p2.txt", "p. 3"), cit("L3", T3, "p2.txt", "00:12:31")])
achado("M9d", "localizador diferente de 'linha N' reprova texto exato", all(r["status"] == "exact_locator_mismatch" for r in rv),
       str([(r["declared_locator"], r["status"]) for r in rv]))

variante = PARAGRAFO.replace("justo", "correto").replace("briga", "disputa").replace("medo", "receio")
com, sem = SequenceMatcher(None, variante, PARAGRAFO).ratio(), SequenceMatcher(None, variante, PARAGRAFO, autojunk=False).ratio()
print(f"    hipótese descartada: a heurística 'autojunk' do difflib quase não muda a razão ({com:.3f} contra {sem:.3f})")

# ---------------------------------------------------------------- M10
titulo("M10 Detector de semelhança entre casos")
texto = ("# Relatório\n\n## A regra vale para quem trabalha junto\n\n" +
         "A cobrança só convence quando parte de quem também ficou até o fim da limpeza do forno. " * 4 + "\n")
pares_por_leiaute = {}
for leiaute, caminhos in (("documentado", ("casoA/06-relatorio-final.md", "casoB/06-relatorio-final.md")),
                          ("subpasta", ("casoA/output/06-relatorio-final.md", "casoB/output/06-relatorio-final.md"))):
    raiz = TRAB / "m10" / leiaute
    alvos = []
    for rel in caminhos:
        alvo = raiz / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(texto, encoding="utf-8")
        alvos.append(alvo)
    cod, _, _ = run(AUD, "homogeneizacao", "--relatorios", *alvos, "--output", raiz / "h.json")
    pares_por_leiaute[leiaute] = (cod, len(json.loads((raiz / "h.json").read_text(encoding="utf-8"))["pares"]))
achado("M10", "dois relatórios idênticos em casoA/output/ e casoB/output/ não são comparados",
       pares_por_leiaute["subpasta"] == (0, 0), f"(saída, pares): {pares_por_leiaute}")

# ---------------------------------------------------------------- custo
titulo("Custo do passo 'substituir' (informativo)")
rng = random.Random(7)
vocab = ("casa forno escala horário regra limpeza caderno folga trabalho massa padaria turno colega cobrança "
         "manhã tarde receita farinha entrega conta dinheiro reunião decisão voto ajuda vizinho bairro feira").split()
base = TRAB / "custo" / "corpus"
base.mkdir(parents=True)
for i in range(5):
    (base / f"e{i}.txt").write_text("".join("P: " + " ".join(rng.choice(vocab) for _ in range(28)) + ".\n" for _ in range(200)), encoding="utf-8")
agulha = " ".join(rng.choice(["xilofone", "quasar", "zênite", "jabuti", "óbvio", "fugaz", "íngreme"]) for _ in range(25))
t0 = time.perf_counter()
verifica(base, [cit("Z1", agulha, "e0.txt", "linha 1")])
print(f"    corpus de 1.000 linhas: {time.perf_counter() - t0:.1f} s por citação não encontrada (cresce em linha reta com o corpus)")

# ---------------------------------------------------------------- resumo
print("\n" + "=" * 96)
print(f"linha de base: {'ok' if BASE_OK else 'FALHOU'}")
for ident, descricao, reproduz in RESULTADOS:
    print(f"  {ident:5} {'REPRODUZ    ' if reproduz else 'não reproduz'}  {descricao}")
n_rep = sum(1 for _, _, r in RESULTADOS if r)
print(f"{n_rep} de {len(RESULTADOS)} achados reproduzem. Pasta de trabalho: {TRAB}")
sys.exit(1 if (ESTRITO and n_rep) or not BASE_OK else 0)
