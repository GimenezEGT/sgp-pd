# Contrato: perfis de cálculo por tipo de estudo (feature 007)

Colunas da medida: `amostra`, `lote`, `kit` (ids das versões dos cadastros), `dia`, `corrida`,
`replicata`, `grupo` (nível, concentração, tempo ou substância), `x` (valor de referência,
concentração, tempo ou esperado), `y` (valor medido), `esperado` e `obtido` (`pos`/`neg`).

| Código do tipo | Perfil | Colunas | Métricas (critério aceito) |
| --- | --- | --- | --- |
| `repetibilidade` | descritivo | `y` | `media`, `dp`, `cv` |
| `reprodutibilidade` | descritivo por dia | `dia`, `y` | por dia e global: `media`, `dp`, `cv` |
| `entre-lotes` | descritivo por lote | `lote`, `y` | por lote e global: `media`, `dp`, `cv` |
| `comparacao-metodos` | comparação | `x` (referência), `y` (em teste) | `diferenca_media`, `dp_diferencas`, `inclinacao`, `intercepto`, `r2`, `correlacao` |
| `linearidade` | regressão | `x`, `y` | `inclinacao`, `intercepto`, `r2` |
| `estabilidade-longa` | regressão | `x` (tempo), `y` | `inclinacao`, `intercepto`, `r2` |
| `sensibilidade-especificidade` | proporções | `esperado`, `obtido` | `sensibilidade`, `especificidade`, `concordancia` (com IC 95%) |
| `cut-off` | proporções com corte | `y`, `esperado`; corte do estudo | `sensibilidade`, `especificidade`, `concordancia` |
| `sensibilidade-analitica` | detecção | `grupo`/`x` (nível), `obtido` | taxa por nível; `menor_nivel_detectado` |
| `reatividade-cruzada` | detecção | `grupo`, `obtido` | `deteccoes` (contagem de positivos) |
| `efeito-prozona` | detecção | `grupo`/`x`, `obtido` | `deteccao` (% de positivos) |
| `interferentes` | esperado × encontrado | `grupo` (substância), `x`, `y` | `desvio_max` (% absoluto) |
| `estabilidade-aberto` | variação no tempo | `x` (tempo), `y` | `variacao_max` (% em relação ao tempo zero) |
| `estabilidade-transporte` | variação no tempo | `x` (tempo), `y` | `variacao_max` |

Critério: métrica do perfil, comparação (`<`, `≤`, `>`, `≥`) e limite decimal; com grupos, vale o
resultado global. Valor "não calculável" nunca atende critério.
