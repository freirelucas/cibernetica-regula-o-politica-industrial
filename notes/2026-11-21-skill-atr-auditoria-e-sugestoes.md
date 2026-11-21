# Skill de Análise Temática Reflexiva — auditoria de engenharia e sugestões de melhoria

Data: 21/11/2026. Objeto: `https://github.com/labiia-lab/analise-tematica-reflexiva`, commit
`3fb9a89` (versão 2.0.0, de 16/11/2026). É repositório de terceiros.

## 0. O que é esta nota e o que falta decidir

O link foi trazido para a sessão sem dizer o uso pretendido. Um uso plausível é a frente de
dados primários do plano de 18/09 (item M4: entrevistas e oficinas com servidores). **Confirmar
com o responsável** se a skill será usada no projeto, se as sugestões devem ser levadas ao
repositório dela, ou as duas coisas.

- Nada foi alterado nem publicado no repositório da skill. A sessão só tinha leitura.
- Esta nota é o registro. Levar as sugestões para lá (como issue ou como PR) depende de acesso
  de escrita naquele repositório, ou de o responsável publicar.
- A auditoria é de engenharia. Não avalia o mérito metodológico do conteúdo.

A skill é um pacote para agentes de IA: um contrato (`SKILL.md`), 11 referências, 9 templates,
28 cenários de comportamento e dois scripts Python (1.324 linhas) que conferem a parte
computável de uma análise. O script `scripts/auditar_analise.py` funciona como portão
automático de cada fase: a análise só é dada por completa se ele não devolver erros.

## 1. Resumo

- Como pacote, está bem montado: a suíte passa, as referências internas fecham e a bibliografia
  confere.
- O ponto fraco é o portão automático. Um falso positivo reprova quase qualquer análise escrita
  em português, e várias checagens aprovam o que deveriam barrar.
- A conferência de privacidade não lê os arquivos que mais carregam identificadores.
- A versão 2.0.0 é citável, mas não tem etiqueta nem integração contínua, e a própria nota de
  versão diz que não foi exercitada em entrevistas.

## 2. Como reproduzir

```bash
git clone --depth 1 https://github.com/labiia-lab/analise-tematica-reflexiva /caminho/do/clone
python3 -I -B notes/anexos/2026-11-21-atr-repro.py /caminho/do/clone       # 25 ensaios
python3 -I -B notes/anexos/2026-11-21-atr-estrutura.py /caminho/do/clone   # conferência estática
```

O primeiro script monta análises mínimas e fictícias numa pasta temporária, roda os scripts da
skill e diz, achado por achado, `REPRODUZ` ou `não reproduz`. No commit auditado, os 25
reproduzem e a linha de base passa. Numa versão futura, "não reproduz" indica correção; com
`--estrito` o script sai com 1 enquanto algo reproduzir. Os identificadores abaixo (A1, A2a…)
são os que o script imprime.

A suíte da própria skill roda com `python -m unittest discover -s testes -p "test_*.py"`: 41
testes, todos verdes.

## 3. Sugestões

Os caminhos são do repositório da skill.

### Gravidade alta

**A1 — A palavra "todo" reprova a análise.**
- Hoje: a regra de resto de rascunho usa `\bTODO\b` sem diferenciar maiúsculas
  (`scripts/auditar_analise.py:490`) e casa com a palavra portuguesa. A frase "A leitura cobriu
  todo o corpus declarado" e uma fala literal verificada com "o dia todo" geram erro E10, e o
  comando sai com 1. O portão da última fase exige zero erros (`SKILL.md:340`), e fala literal
  não pode ser reescrita. A palavra aparece em 14 linhas dos documentos da própria skill.
- Sugestão: casar `TODO` só em maiúsculas.
- Teste que falta: nenhum dado de teste contém a palavra
  (`testes/test_auditar_analise.py:232-243`).

**A2 — O "PASS" não garante que os excertos existem no corpus inventariado.**
- A2a: a verificação é ligada ao excerto só pelo identificador (`auditar_analise.py:401-414`).
  Um excerto trocado por frase inventada depois de verificado continua aprovado.
- A2b: o SHA-256 gravado pela verificação não é comparado com o do manifesto. Verificar contra
  outra pasta, com o arquivo alterado, passa.
- A2c: o verificador aceita fonte fora da pasta do corpus, por caminho absoluto ou `..`
  (`scripts/verificar_citacoes.py:190-192`).
- A2d e A2e: registro vazio sai com 0, e omitir `--verificacao` desliga a checagem sem marca no
  resultado (`auditar_analise.py:630-638`).
- A2f: o comando único do `SKILL.md:177` falha ao fim das fases 2 e 5 (`SKILL.md:174`), porque
  o relatório ainda não existe (`auditar_analise.py:431-436`). Isso empurra para a omissão de
  argumentos. O auditor não sabe em que fase está.
- Sugestão: gravar o hash do texto do excerto na exportação e na verificação e compará-lo na
  auditoria; exigir fonte dentro do corpus e com o mesmo hash do manifesto; gravar no resultado
  a lista das checagens que rodaram; tratar como erro haver excerto literal sem verificação;
  aceitar um argumento de fase.

**A3 — A conferência de privacidade só lê `.md`.**
- A3a: `auditar_analise.py:756` percorre só arquivos `.md`. E-mail, telefone, CPF e nome em
  `evidencias.jsonl`, e nome de pessoa no nome de arquivo do manifesto, não aparecem: zero
  candidatos, saída 0. O pacote que a skill manda entregar a terceiros inclui esses arquivos
  (`SKILL.md:338`), e o cenário 27 pede a conferência "em toda a pasta de saída"
  (`testes/cenario-27-identificadores-na-saida.md:23`).
- A3b: a lista de nomes diferencia acento: "José Antônio" não acha "jose antonio" (`:763`).
- Sugestão: varrer todos os arquivos de texto da pasta, incluindo os campos `falante`,
  `arquivo` e `source`; comparar nomes sem acento e sem caixa.

### Gravidade média

**M4 — Corpus em DOCX ou PDF nunca chega a cobertura "integral".**
- Hoje: o inventário inclui tudo o que estiver na pasta, também binário e oculto
  (`verificar_citacoes.py:147-150`). Com um `.docx` e um `.DS_Store` ao lado de dois `.txt`
  lidos por inteiro, a cobertura sai "parcial". O `SKILL.md:160-168` manda criar um derivado em
  texto, mas não diz qual manifesto alimenta a cobertura; o portão da fase 1 exige "integral"
  (`SKILL.md:265`).
- Sugestão: ignorar arquivos ocultos, aceitar filtro por extensão e documentar o fluxo com
  derivados com um exemplo completo.

**M5 — Códigos de saída e entrada inválida.**
- M5a: o `SKILL.md:182` diz que 2 indica entrada inválida. Em seis entradas inválidas testadas,
  nenhuma devolveu 2: pasta inexistente em `privacidade` e em `integridade` sai com 0; arquivo
  inexistente em `sobrealegacao`, `homogeneizacao` e `--nomes` termina em exceção com saída 1,
  o mesmo código de "há itens a ler".
- M5b: com registro inválido, o resultado da execução anterior continua no disco, com
  `erros: []` (`auditar_analise.py:610-618`).
- M5c: JSON válido com tipo errado (`"excertos": 3`) derruba o auditor com saída 1 e sem
  resultado.
- Sugestão: um ponto único que valide caminhos e tipos e saia com 2; em falha, gravar o erro no
  arquivo de saída.

**M6 — Conferência das citações do relatório** (`auditar_analise.py:49-54`, `:440`).
- M6a: bloco de citação sem aspas não é conferido.
- M6b: citação com menos de cinco palavras não é conferida.
- M6c: com aspas retas, um termo curto entre aspas antes da citação faz o script ler como
  citação o texto entre as duas. Ele acusa a prosa do analista e pula a fala real. Com aspas
  curvas funciona.
- Sugestão: tratar bloco de citação como citação; parear aspas retas por posição; alertar para
  citação curta fora do registro.

**M7 — Regra de marcador de template** (`auditar_analise.py:482-497`).
- M7a e M7b: alternativa de duas opções e linha de tabela totalmente vazia não são acusadas.
  Com os nove templates entregues sem preencher, 44 dos 129 campos passam.
- M7c: anotação entre colchetes com quatro palavras ou mais, como "[trecho inaudível por alguns
  segundos]", é acusada como erro.
- Sugestão: comparar com os campos dos templates em vez de adivinhar pela forma.

**M8 — Rótulo "efeito estrutural".** O cálculo usa o campo `origem`, que não é obrigatório
(`auditar_analise.py:43`, `:338-377`). Com os mesmos temas e sem o campo, o resultado muda de
"sem efeito estrutural" para "estrutural" e o alerta some. Sugestão: exigir `origem` em tema
final quando houver candidatos, ou comparar os conjuntos de códigos.

**M9 — Verificador de citações.**
- M9a: a busca por similaridade compara com linhas inteiras (`verificar_citacoes.py:40-59`).
  Uma citação com uma palavra a mais, dentro de um turno de 480 caracteres numa linha só, sai
  como `not_found`; com o mesmo texto em linhas curtas, é achada (0,96).
- M9b: texto idêntico em outra forma Unicode, ou com aspas curvas, sai como `substituir`, que
  a skill define como "outro texto" (`:29-37` só normaliza espaços e caixa).
- M9c: em arquivo com fim de linha do Windows, o `suggested_text` não é trecho exato do
  arquivo, contra o `SKILL.md:170`.
- M9d: localizador diferente de "linha N" reprova texto exato (`:223-229`), embora a
  referência admita página e tempo (`referencias/evidencias-e-relato.md:79`).
- Sugestão: buscar por janela de caracteres; criar um estado para "igual, salvo forma
  tipográfica"; preservar o fim de linha original na sugestão; separar o localizador calculado
  do localizador do original.

**M10 — Detector de semelhança entre casos** (`auditar_analise.py:846`). O rótulo de cada
relatório é "pasta/arquivo". Dois relatórios idênticos em `casoA/output/` e `casoB/output/`
colidem: zero pares, saída 0. No leiaute do exemplo (`referencias/casos-multiplos.md:47`)
funciona. Sugestão: usar o caminho inteiro e acusar rótulo repetido.

**M11 — Teste de aptidão.** O gabarito está no script que o agente executa
(`auditar_analise.py:877-880`) e em `testes/test_auditar_analise.py:329-337`. O exemplo de
formato já traz duas das seis respostas (`scripts/aptidao/tarefa.md:45`), e as respostas
alternam. Vale como teste de fumaça, não como medida.

**M12 — Versão e publicação.**
- Não há etiqueta para a 2.0.0, embora `CITATION.cff:11` cite a versão.
- A versão não aparece no `SKILL.md`, nos scripts nem nas saídas: o dossiê não consegue
  registrá-la.
- Não há configuração de integração contínua.
- A 2.0.0 entrou num commit de 39 arquivos (`84e8022`).
- Três ramos ficaram fora da `main`: `fix/relocalizacao-citacoes` (14 commits),
  `agent/update-atr-skill` (8) e `atualiza-braun-clarke-2024-mapa-tematico` (1 commit, 2.049
  linhas, com `scripts/gerar_mapa_tematico.py`). Não se sabe se por decisão.
- O `CHANGELOG.md:81` diz que a versão não foi executada no perfil isolado, em entrevistas nem
  em casos múltiplos; o `testes/TESTES.md:73-82` pede esse teste antes de publicar.

**M13 — Testes.** 41 testes, com cobertura de linhas e ramos de 84% (`auditar_analise.py`) e
87% (`verificar_citacoes.py`). Nove dos 28 códigos não têm asserção: E01, E02, A02, A03, A04,
A06, A11, A12 e A16. Nenhum caminho de entrada inválida é testado.

### Gravidade baixa

- Não há catálogo dos 28 códigos de erro e alerta; a numeração tem lacunas (E12, A05).
- Não há instrução para tratar o conteúdo do corpus como dado. Documentos e postagens podem
  trazer instruções, e o agente que roda a skill tem acesso a shell.
- A `description` do frontmatter (297 caracteres) está só em inglês.
- A licença CC BY 4.0 cobre também o código.
- O Python mínimo (3.8) não é declarado.
- Nomenclatura: "advogado do diabo" (`referencias/exemplo-integrado.md:155`,
  `referencias/fundamentacao-e-proveniencia.md:23`, `testes/cenario-9-devils-advocate.md`) e
  "auditor de evidências" (`referencias/contestabilidade-interpretativa.md:88`) convivem com
  "contestador"; Byrne aparece como 2021 no texto e 2022 na lista de referências.
- O campo `fonte` tem dois sentidos: identificador no registro e caminho em `leitura.jsonl`.
- `auditar_analise.py` não tem docstring em nenhuma das 36 funções; `verificar_citacoes.py:10`
  importa `sys` sem usar e descarta a mensagem de erro de JSON (`:309`).
- A busca por similaridade custa cerca de 1,7 s por citação não encontrada a cada 1.000 linhas
  de corpus.

## 4. O que a skill faz bem

- As 55 referências internas entre arquivos existem, e as contagens declaradas batem.
- O `SKILL.md` tem 386 linhas e carrega as referências sob demanda, todas com sumário.
- Os scripts usam só a biblioteca padrão, sem rede, `eval` ou `subprocess`.
- Os 14 DOIs da bibliografia estão registrados, e autor, periódico, volume e páginas conferem
  com o Crossref. A referência sem DOI tem a URL respondendo com um PDF; o conteúdo não foi
  conferido.
- A nota de versão declara os limites conhecidos, e os scripts dizem que não medem qualidade
  interpretativa.

## 5. Se a skill for usada antes das correções

1. Corpus em `.txt` UTF-8, com fim de linha `\n`, em pasta limpa e sem arquivos ocultos.
   Inventariar essa pasta.
2. Rodar a exportação e a verificação de citações imediatamente antes de cada auditoria, com a
   mesma pasta do manifesto.
3. Tratar como falso positivo o erro E10 "resto de template ou anotação de rascunho" em linha
   com a palavra "todo", e registrar isso no dossiê. Não reescrever fala literal.
4. Procurar identificadores à mão nos `.jsonl` e nos nomes de arquivo antes de compartilhar o
   pacote.
5. Usar aspas curvas no relatório e pôr toda citação entre aspas.
6. Guardar o relatório de cada caso em pasta com nome próprio (`CASO/06-relatorio-final.md`).
7. Preencher `origem` em todo tema final.

## 6. Ordem sugerida para levar ao repositório da skill

Cada passo é pequeno e vem com o teste que hoje falta. Os ensaios do script de reprodução dão
os dados de teste.

1. A1: uma linha e um teste.
2. A3: privacidade em todos os arquivos de texto e nomes sem acento.
3. A2: hash do texto, fonte dentro do corpus, checagens registradas, argumento de fase.
4. M5: entrada inválida e códigos de saída.
5. M6 e M7: citações do relatório e marcadores de template.
6. M9 e M4: verificador, inventário e o fluxo com derivados.
7. M12 e M13: etiqueta, versão exposta, suíte rodando em integração contínua, testes dos nove
   códigos.

## 7. Limites desta auditoria

- A skill não foi executada de ponta a ponta com um agente. Os 28 cenários de comportamento não
  foram testados.
- Issues, PRs e configurações do GitHub não foram vistos: a sessão só tinha leitura git.
- Os ensaios usam corpus fictício mínimo. O custo medido vale para linhas curtas.
- Uma hipótese levantada na leitura foi descartada ao medir: a heurística `autojunk` do
  `difflib` quase não muda a similaridade (0,973 contra 0,977).
