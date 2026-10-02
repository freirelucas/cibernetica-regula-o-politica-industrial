# Pontes epistêmicas DIEST × DISET (Ipea)

Spinoff autônomo do projeto [Cibernética · Regulação · Política Industrial](../../README.md).
Mapeia **quem produz** na Diretoria de Estudos e Políticas do Estado, das Instituições e da
Democracia (**DIEST**) e na Diretoria de Estudos e Políticas Setoriais, de Inovação, Regulação
e Infraestrutura (**DISET**), **o que é característico** de cada uma, **onde convergem** e
**quem poderia trabalhar junto** — com hipergrafos de coautoria e de vocabulário.

- Resultado legível: **[RELATORIO.md](RELATORIO.md)** (gerado)
- Como cada número é feito e onde não confiar: **[METODO.md](METODO.md)**
- Como conduzir o projeto com Claude: **[docs/ORIENTACAO_CLAUDE_SCIENCE.md](docs/ORIENTACAO_CLAUDE_SCIENCE.md)**

```bash
python src/run_all.py --from attribute   # reproduz tudo offline a partir de data/ (só stdlib)
python src/run_all.py                    # re-colhe portal + repositório do Ipea
```

Fontes: diretório "Quem faz pesquisa no Ipea" e Repositório do Conhecimento do Ipea (API
DSpace pública). OpenAlex é camada opcional (`OPENALEX_API_KEY`).

## Virar repositório próprio
O diretório não importa nada do projeto-mãe. Para extrair com histórico:
```bash
git subtree split --prefix=spinoff/pontes-diest-diset -b pontes-diest-diset
# crie o repo vazio no GitHub e:
git push git@github.com:<conta>/pontes-diest-diset.git pontes-diest-diset:main
```
