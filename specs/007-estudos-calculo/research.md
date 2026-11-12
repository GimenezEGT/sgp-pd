# Research: Estudos de desempenho e estabilidade com cálculo automático

## R1. Módulo de cálculo puro

- **Decision**: `sgp/studies/stats.py` sem Django: média e desvio-padrão com o módulo `statistics`
  (aritmética exata, reproduz o NumAcc1 do NIST — V2), regressão e correlação com
  `statistics.linear_regression`/`correlation`, IC de Clopper-Pearson com `scipy.stats.beta`
  (SciPy traz o NumPy), Wilson pela fórmula fechada. Valores entram como `Decimal` (dados guardados
  em texto) e o valor completo fica no resultado; arredondar é só exibir.
- **Rationale**: o módulo `statistics` dá exatidão melhor que somas em ponto flutuante para os
  vetores; o SciPy é a referência para a função beta inversa.
- **Alternatives considered**: NumPy em tudo (desvio com ponto flutuante simples); implementar a
  beta inversa à mão (risco numérico sem ganho).

## R2. Arredondamento

- **Decision**: `Decimal.quantize` com `ROUND_HALF_EVEN` (padrão), `ROUND_HALF_UP` ou `ROUND_DOWN`
  sobre a representação decimal exata do valor completo (`Decimal(repr(float))` ou o `Decimal` do
  cálculo), com casas por tipo de resultado (2; 4 para R², correlação, inclinação e intercepto);
  a regra aplicada vai junto de cada resultado ("meio para o par, 2 casas"). Reproduz V7 e V8.

## R3. Perfis de cálculo por tipo de estudo

- **Decision**: o código do tipo (lista controlada `tipo-estudo`, semeada por migração com os 14
  tipos) aponta um perfil de cálculo em `sgp/studies/profiles.py` (contrato `perfis-calculo.md`):
  colunas da medida usadas, métricas calculadas, métricas aceitas no critério. Tipo novo cadastrado
  pela Qualidade sem perfil não aceita estudo (mensagem clara).

## R4. Medidas e resultados no estudo

- **Decision**: as linhas ficam em JSON no estudo (`rows`), como as tabelas dos subdocumentos da
  004: a tela edita a tabela inteira, o sistema numera as linhas e cada gravação registra na trilha
  o que mudou; os resultados calculados (`results`) são recalculados a cada gravação em elaboração e
  congelados no bloqueio. Referências a amostra, lote e kit guardam o id da versão do cadastro.
- **Rationale**: nada é apagado fisicamente (linhas retiradas ficam na trilha) e a versão do estudo
  copia o conjunto inteiro.

## R5. Versões e bloqueio

- **Decision**: cada versão é uma linha de `Study` com a mesma linhagem (`lineage`), como os
  cadastros da 003. A aprovação do subdocumento vinculado (005) bloqueia a versão em uso; nova
  versão com motivo copia configuração, critérios e linhas. O subdocumento mostra, de cada linhagem
  vinculada, a versão mais recente.

## R6. Integração com assinatura e geração

- **Decision**: o conteúdo canônico do subdocumento (005) ganha a chave `estudos` (só quando há
  estudo vinculado, para não mudar o resumo dos já aprovados) com tipo, versão, critérios, linhas e
  resultados; o conteúdo de renderização (006) acrescenta, no tópico vinculado, a tabela de medidas,
  a tabela de resultados e a conclusão, numeradas na sequência do documento.

## R7. Importação

- **Decision**: CSV (`;` ou `,`, UTF-8 com ou sem BOM) e XLSX (openpyxl, já dependência); o
  mapeamento coluna → campo fica em `ImportMapping` por equipamento; a pré-visualização vai assinada
  (`django.core.signing`) para a confirmação, sem tabela temporária.

## R8. Testes

- **Decision**: vetores V1 a V8 de docs/contexto/06-casos-de-teste.md e propriedades com
  `hypothesis` (média entre mínimo e máximo, desvio não negativo e invariante a deslocamento,
  arredondamento idempotente, IC contém a proporção observada).
