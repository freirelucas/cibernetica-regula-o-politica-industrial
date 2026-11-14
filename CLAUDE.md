# Instruções para agentes neste repositório

Estudo cienciométrico do Ipea/Diest sobre cibernética organizacional, regulação econômica e
política industrial. O entregável é um sítio estático em `docs/` (GitHub Pages), gerado por
Python de biblioteca padrão a partir de dados versionados em `data/`.

## Tarefa em curso

**Construir o redesenho por ordens de serviço.** O quadro está em `design/PLANO.md`
(`python scripts/aceite.py --lista` mostra o que está feito e o que está liberado); cada ordem
é um arquivo em `design/ordens/`. Você executa **uma** ordem: faz exatamente o que ela manda,
só nos arquivos que ela lista, e termina quando `python scripts/aceite.py ORDEM` disser
APROVADA. Não redesenhe. Se a ordem não bater com o que está no arquivo, pare e relate em vez
de improvisar.

## Comandos

```bash
python scripts/preparar.py                            # ambiente: tem de terminar em AMBIENTE PRONTO
python scripts/aceite.py --lista                      # o quadro das ordens
python scripts/aceite.py ORDEM --iniciar              # começa uma ordem
python scripts/aceite.py ORDEM                        # veredito da ordem: APROVADA ou REPROVADA
python src/build_site.py                              # gera docs/ (segundos)
python -m pytest -q                                    # suíte inteira
python .claude/skills/run-scisci-ipea/driver.py       # abre as telas num navegador; STATUS: OK
python scripts/conferir_telas.py                      # mede as telas em três tamanhos
python design/ferramentas/gera_prototipos.py          # regera os protótipos de desenho
```

Dependências para tudo acima: `python -m pip install pytest numpy scipy networkx playwright
python-igraph leidenalg`. Use sempre `python -m pip` (o `pip` solto pode apontar para outro
Python). O Playwright precisa de um Chromium; se o ambiente já traz um, instale a versão do
pacote que combina com ele em vez de baixar outro navegador.

## Regras que não se negociam

1. **`docs/` nunca é editado à mão.** Mude o modelo em `src/` e reconstrua.
2. **Nenhum número é digitado** em modelo, página ou texto de interface. Todo número vem de um
   derivado em `data/`, por marcador (`PROV_*`, `ENT_*`, `{{caminho}}`, `data-n="..."`).
3. **Zero carga externa.** Sem CDN, sem fonte remota, sem biblioteca nova. Fontes e bibliotecas
   estão em `docs/vendor/`.
4. **Zero dado inventado.** Identificador, título, autor, contagem: só o que está nos dados.
5. **Português sem anglicismo** na prosa e na interface (`tests/test_anglicismos.py`), com
   vírgula decimal e ponto de milhar.
6. **Nada só por cor.** Tradição = sólido + cor + nome. Rótulo observado cheio, inferido vazado.
7. **Alvo de toque de 44 px** e nenhuma rolagem lateral, de 320 px para cima.
8. **Só os pesos de fonte vendorizados**: Spectral 300, 400, 400 itálico, 600; DM Sans 300,
   400, 500; JetBrains Mono 400, 500.
9. **Não apague nem afrouxe teste para passar.** Teste vermelho é informação. O mesmo vale
   para `scripts/aceite.py`, `scripts/preparar.py` e `design/ordens/quadro.json`.
10. **Não reescreva prosa nem troque número do relatório.** "Q ≈ 0,59" e "z ≈ 80" são da rede
    interna do funil (ver `METODOLOGIA.md`) e ficam como estão.

## Antes de commitar

- `pytest -q` verde, driver em `STATUS: OK`, `scripts/conferir_telas.py` sem problema novo.
- **`docs/` canônico.** A rede de coautoria usa Leiden com semente. Com `python-igraph` e
  `leidenalg` instalados, `git status` depois de `python src/build_site.py` **não** mostra
  mudança em `docs/dados/` nem nos números da seção 10·6 do relatório. Se mostrar, o arquivo
  `data/author_network.json` (fora do git) foi gerado sem essas bibliotecas: instale-as, rode
  `OA_OFFLINE=1 python src/author_network.py` e reconstrua. Não commite `docs/` divergente.
- `pytest` reconstrói `docs/` como efeito colateral: rode `python src/build_site.py` por
  último, antes do `git add`.
- Um commit por ordem, só com os arquivos que o aceite listar. `docs/` só entra em commit
  das ordens de integração (I1 e F1): nas outras, nunca use `git add -A`.
- Não crie pull request nem faça push para outra branch sem que peçam.

## Onde as coisas estão

| caminho | o que é |
|---|---|
| `src/build_site.py` | gera as telas; `global_nav()` monta a barra |
| `src/*_template.html` | modelos das telas (relatório, explorador, espaço 3D, triagem) |
| `src/espaco.py`, `src/espaco3d.js` | dados e motor da cena 3D |
| `src/token_injection.py` | injetores de números (`PROV_*`, `SOLIDEZ_*`, `XGI_*`...) |
| `data/` | derivados versionados; `data/oa_cache/` é o cache do OpenAlex |
| `design/` | sistema de desenho, protótipos e o plano de construção |
| `design/ordens/` | uma ordem de serviço por arquivo, e o quadro (`quadro.json`) |
| `scripts/preparar.py`, `scripts/aceite.py` | ambiente pronto e veredito de cada ordem |
| `tests/test_redesenho.py` | critérios do redesenho; cada ordem acorda os seus testes |
| `scripts/conferir_telas.py` | conferência em navegador: transbordo, alvos, abas, erros |
| `METODOLOGIA.md` | como ler os achados e onde não confiar |
| `.claude/skills/` | rotinas do projeto (pontes, orçamento da API, cache, changelog, driver) |

## Custo e rede

Nada neste trabalho precisa da API do OpenAlex. Rode offline (`OA_OFFLINE=1`). Não dispare
coletas nem o funil.
