# Feature 007 — Estudos de desempenho e estabilidade com cálculo automático

Os resultados do RAPD e da Validação passam a ser lançados como dados, e o sistema calcula estatísticas e conclusões; cada cálculo é testado contra vetores de referência de resultado conhecido.

```text
/speckit-specify Estudos de desempenho e estabilidade estruturados, com cálculo automático, que alimentam o RAPD, a Validação do Produto e o dossiê. Leia docs/contexto/05-vocabularios.md e 06-casos-de-teste.md.

Problema: hoje os resultados são tabelas digitadas no Word, com médias, desvios e CV% calculados à mão ou em planilhas soltas, sem um vocabulário comum para os tipos de estudo.

Histórias:
1. Como analista, crio um estudo escolhendo o tipo numa lista controlada: comparação de métodos (exatidão), repetibilidade, reprodutibilidade, entre lotes, sensibilidade analítica, linearidade, interferentes, reatividade cruzada, efeito prozona, cut-off, sensibilidade e especificidade clínicas, estabilidade de longa duração, estabilidade após aberto e estabilidade de transporte.
2. Defino o critério de aceitação antes de lançar resultados (ex.: CV% < 15%, R² > 0,95, diferença média de Ct ≤ 2); o critério fica congelado no estudo.
3. Lanço ou importo resultados (planilha ou arquivo do equipamento), ligando cada linha a amostra, lote, kit de referência, dia, corrida e replicata cadastrados.
4. O sistema calcula média, desvio-padrão, CV%, diferença média, regressão linear com equação e R², concordância e sensibilidade/especificidade com IC 95%, e informa se o critério foi atendido.
5. Para estudo não aplicável (ex.: efeito prozona em método não imunológico), registro "não aplicável" com justificativa, que segue para o dossiê.
6. Tabelas e conclusões entram no RAPD ou na Validação sem redigitação, com numeração automática.

Regras: estudo usado em documento assinado não é editado; recalcular gera nova versão; casas decimais e separador seguem o padrão brasileiro e a configuração do estudo; todo cálculo tem teste com vetores de referência de resultado conhecido.

Fora do escopo: protocolos estatísticos além dos listados (avaliar depois).
```

Pontos que o `/speckit-clarify` deve fechar:

- **Arredondamento.** Truncar ou arredondar, e com quantas casas, por tipo de resultado.
- **Intervalo de confiança.** Método do IC 95% para proporções (exato de Clopper-Pearson, Wilson ou outro).
- Os formatos de arquivo dos equipamentos que precisam de importação.
- Quais estudos são obrigatórios por tecnologia (bioquímica, imunologia, biologia molecular).
- Quem fornece e aprova os vetores de referência usados nos testes de cálculo.

```text
/speckit-plan App "estudos" com Estudo, CriterioAceitacao, Medida e ResultadoCalculado. Cálculos num módulo Python puro, sem dependência da camada web, com numpy e scipy; desvio-padrão amostral (n−1); IC 95% de proporções pelo método definido no clarify; regra de arredondamento configurável e registrada junto do resultado. Importação CSV/XLSX com mapeamento de colunas salvo por equipamento. Testes com os vetores de referência de docs/contexto/06-casos-de-teste.md e testes de propriedade (hypothesis). Tabelas renderizadas pelo gerador da feature 006.
```

Checklists sugeridos: estatística (fórmulas, arredondamento) e regulatório (RDC 830/2023, art. 58, itens VI a VIII).

Pronto quando:

- [ ] Os cálculos reproduzem os vetores de referência do kit (CV%, regressão, IC 95%).
- [ ] Estudo "não aplicável" exige justificativa e aparece no dossiê.
- [ ] Recalcular um estudo assinado gera nova versão.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
