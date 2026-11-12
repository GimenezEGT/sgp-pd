# Feature Specification: Estudos de desempenho e estabilidade com cálculo automático

**Feature Branch**: `007-estudos-calculo`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Estudos de desempenho e estabilidade estruturados, com cálculo automático, que alimentam o RAPD, a Validação do Produto e o dossiê. Leia docs/contexto/05-vocabularios.md e 06-casos-de-teste.md. Problema: hoje os resultados são tabelas digitadas no Word, com médias, desvios e CV% calculados à mão ou em planilhas soltas, sem um vocabulário comum para os tipos de estudo. Histórias: 1. Como analista, crio um estudo escolhendo o tipo numa lista controlada: comparação de métodos (exatidão), repetibilidade, reprodutibilidade, entre lotes, sensibilidade analítica, linearidade, interferentes, reatividade cruzada, efeito prozona, cut-off, sensibilidade e especificidade clínicas, estabilidade de longa duração, estabilidade após aberto e estabilidade de transporte. 2. Defino o critério de aceitação antes de lançar resultados (ex.: CV% < 15%, R² > 0,95, diferença média de Ct ≤ 2); o critério fica congelado no estudo. 3. Lanço ou importo resultados (planilha ou arquivo do equipamento), ligando cada linha a amostra, lote, kit de referência, dia, corrida e replicata cadastrados. 4. O sistema calcula média, desvio-padrão, CV%, diferença média, regressão linear com equação e R², concordância e sensibilidade/especificidade com IC 95%, e informa se o critério foi atendido. 5. Para estudo não aplicável (ex.: efeito prozona em método não imunológico), registro 'não aplicável' com justificativa, que segue para o dossiê. 6. Tabelas e conclusões entram no RAPD ou na Validação sem redigitação, com numeração automática. Regras: estudo usado em documento assinado não é editado; recalcular gera nova versão; casas decimais e separador seguem o padrão brasileiro e a configuração do estudo; todo cálculo tem teste com vetores de referência de resultado conhecido. Fora do escopo: protocolos estatísticos além dos listados (avaliar depois)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar o estudo com tipo controlado e critério congelado (Priority: P1)

O analista cria um estudo do projeto escolhendo o tipo numa lista controlada e define o critério de aceitação antes de lançar resultados; depois do primeiro resultado lançado, o critério não muda.

**Why this priority**: Sem tipo controlado e critério prévio não há conclusão objetiva nem rastreabilidade.

**Independent Test**: Criar um estudo de repetibilidade com critério "CV% < 15", lançar um resultado e tentar mudar o critério.

**Acceptance Scenarios**:

1. **Given** um projeto aberto, **When** o analista cria um estudo, **Then** o tipo é escolhido numa lista controlada (não há texto livre) e o estudo nasce na versão 01.
2. **Given** um estudo sem resultados, **When** o analista define o critério (métrica, comparação e limite), **Then** o critério fica gravado; **When** já há resultados, **Then** mudar o critério é recusado.
3. **Given** um estudo, **When** o analista o vincula a um tópico do RAPD ou da Validação do projeto, **Then** o estudo passa a alimentar esse tópico.

---

### User Story 2 - Lançar ou importar resultados ligados aos cadastros (Priority: P1)

O analista lança os resultados linha a linha ou importa uma planilha (CSV ou XLSX), ligando cada linha a amostra, lote, kit de referência, dia, corrida e replicata cadastrados; o mapeamento das colunas fica salvo por equipamento.

**Why this priority**: É o fim da redigitação de tabelas e a base dos cálculos.

**Independent Test**: Importar um CSV de 30 linhas com o mapeamento de um equipamento, conferir a pré-visualização e confirmar.

**Acceptance Scenarios**:

1. **Given** um estudo, **When** o analista lança linhas, **Then** cada linha guarda os valores e as referências aos cadastros (amostra, lote, kit), dia, corrida e replicata; a numeração das linhas é feita pelo sistema.
2. **Given** um arquivo CSV ou XLSX e um mapeamento de colunas, **When** o analista importa, **Then** vê a pré-visualização com as linhas recusadas e o motivo, e só confirma o que é válido; o mapeamento fica salvo para o equipamento.
3. **Given** um código de lote ou de amostra que não existe no cadastro, **When** a linha é lançada ou importada, **Then** a linha é recusada com o motivo.

---

### User Story 3 - Cálculo automático e conclusão contra o critério (Priority: P1)

O sistema calcula as estatísticas do tipo de estudo (média, desvio-padrão, CV%, diferença média, regressão com equação e R², concordância, sensibilidade e especificidade com IC 95%) com a regra de arredondamento do estudo, e informa se cada critério foi atendido.

**Why this priority**: Cálculo à mão é a principal fonte de erro apontada no problema.

**Independent Test**: Lançar os vetores de referência de docs/contexto/06-casos-de-teste.md e conferir os resultados.

**Acceptance Scenarios**:

1. **Given** as medidas 2, 4, 4, 4, 5, 5, 7 e 9, **When** o sistema calcula, **Then** média 5, desvio-padrão amostral 2,13809 e CV 42,76%.
2. **Given** pares x e y, **When** o sistema calcula a regressão, **Then** mostra a equação e o R² (ex.: y = 2x + 1; R² = 1).
3. **Given** 45 acertos em 50 amostras positivas, **When** o sistema calcula a sensibilidade, **Then** mostra 90% com o IC 95% pelo método do estudo.
4. **Given** média zero, **When** o sistema calcula o CV%, **Then** o resultado aparece como "não calculável", sem erro.
5. **Given** o critério "CV% < 15", **When** o CV calculado é 42,76%, **Then** o estudo mostra "critério não atendido".
6. **Given** qualquer resultado calculado, **When** exibido, **Then** usa vírgula decimal e as casas e a regra de arredondamento do estudo, registradas junto do resultado; não existe campo para digitar média, desvio ou CV%.

---

### User Story 4 - Estudo não aplicável com justificativa (Priority: P2)

Quando um estudo não se aplica ao produto (ex.: efeito prozona em método não imunológico), o analista registra "não aplicável" com justificativa obrigatória, que segue para os documentos e para o dossiê.

**Why this priority**: O dossiê precisa justificar cada item ausente (docs/contexto/03-padroes-formatacao.md).

**Independent Test**: Marcar um estudo de efeito prozona como não aplicável sem justificativa (recusado) e com justificativa.

**Acceptance Scenarios**:

1. **Given** um estudo, **When** o analista o marca como não aplicável sem justificativa, **Then** é recusado; com justificativa, o estudo fica não aplicável e sem resultados.
2. **Given** um estudo não aplicável com resultados lançados, **When** o analista tenta salvar, **Then** é recusado (não aplicável e resultados são exclusivos).

---

### User Story 5 - Tabelas e conclusões no RAPD e na Validação, com versões (Priority: P2)

Os estudos vinculados entram nos documentos do RAPD e da Validação como tabelas numeradas com as medidas, os resultados calculados e a conclusão, sem redigitação. Quando o documento é aprovado, os estudos vinculados ficam bloqueados; corrigir ou recalcular gera nova versão do estudo.

**Why this priority**: Fecha o ciclo com os documentos assinados (features 005 e 006).

**Independent Test**: Vincular dois estudos à Validação, gerar o documento, aprovar a Validação e tentar editar um estudo.

**Acceptance Scenarios**:

1. **Given** estudos vinculados a um tópico, **When** o documento do subdocumento é gerado, **Then** cada estudo aparece no tópico com a tabela de medidas e a tabela de resultados numeradas em sequência e a conclusão.
2. **Given** um subdocumento aprovado com estudos vinculados, **When** alguém tenta editar ou recalcular um desses estudos, **Then** é recusado; criar nova versão do estudo com motivo é permitido e a versão anterior continua no documento aprovado.
3. **Given** a aprovação, **When** o conteúdo é assinado, **Then** o resumo assinado cobre os dados e os resultados dos estudos vinculados.

---

### Edge Cases

- Uma única medida: desvio-padrão e CV% "não calculáveis".
- Regressão com todos os x iguais: "não calculável".
- Proporção com zero casos no denominador: "não calculável".
- Linha com valor não numérico em campo numérico: recusada na importação com o motivo.
- Estudo de projeto ao qual a pessoa não tem acesso: negado e registrado.
- Arredondamento sempre sobre o valor calculado completo, nunca sobre valor já arredondado.

## Requirements *(mandatory)*

### Functional Requirements

**Estudo e critério**

- **FR-001**: O tipo de estudo DEVE ser escolhido numa lista controlada mantida pela Qualidade, com os 14 tipos da história 1; não há texto livre para o tipo.
- **FR-002**: O estudo DEVE pertencer a um projeto, ter versão (01, 02...) e poder ser vinculado a um tópico do RAPD ou da Validação do Produto do mesmo projeto.
- **FR-003**: O critério de aceitação (métrica do tipo de estudo, comparação e limite) DEVE ser definido antes dos resultados e NÃO DEVE mudar depois do primeiro resultado lançado.
- **FR-004**: Cada estudo DEVE registrar a regra de arredondamento [NEEDS CLARIFICATION: truncar ou arredondar, e com quantas casas, por tipo de resultado?] e o método do IC 95% de proporções [NEEDS CLARIFICATION: Clopper-Pearson, Wilson ou outro?].

**Resultados**

- **FR-005**: As linhas de resultado DEVEM guardar valores e referências a amostra, lote e kit de referência cadastrados, dia, corrida e replicata, com numeração feita pelo sistema; código inexistente no cadastro DEVE ser recusado.
- **FR-006**: A importação de CSV ou XLSX DEVE usar um mapeamento de colunas salvo por equipamento, mostrar pré-visualização com as linhas recusadas e o motivo e só gravar depois da confirmação [NEEDS CLARIFICATION: quais formatos de arquivo de equipamento precisam de importação?].

**Cálculo**

- **FR-007**: O sistema DEVE calcular, conforme o tipo de estudo: média, desvio-padrão amostral (n − 1), CV% (por grupo e global), diferença média e desvio-padrão das diferenças, regressão linear (equação e R²), correlação, concordância, sensibilidade e especificidade com IC 95%, taxa de detecção por nível e desvio percentual entre esperado e encontrado.
- **FR-008**: Todo resultado DEVE ser calculado a partir dos dados guardados; NÃO DEVE existir campo para digitar média, desvio, CV% ou outro valor calculado.
- **FR-009**: O sistema DEVE informar, para cada critério, se foi atendido, com o valor calculado e o limite.
- **FR-010**: Valor que não pode ser calculado (CV% com média zero, desvio com uma medida, regressão com x constante, proporção sem casos) DEVE aparecer como "não calculável", sem erro.
- **FR-011**: Os resultados DEVEM ser exibidos com vírgula decimal e com as casas e a regra de arredondamento do estudo, registradas junto do resultado; o arredondamento DEVE ser aplicado sobre o valor completo.
- **FR-012**: Todo cálculo DEVE ter teste com os vetores de referência de docs/contexto/06-casos-de-teste.md.

**Não aplicável**

- **FR-013**: Estudo não aplicável DEVE exigir justificativa e NÃO DEVE ter resultados; a justificativa DEVE seguir para os documentos e o dossiê.

**Documentos e versões**

- **FR-014**: Os estudos vinculados DEVEM aparecer no tópico do documento gerado com a tabela de medidas, a tabela de resultados (numeradas na sequência do documento) e a conclusão; estudo não aplicável aparece com a justificativa.
- **FR-015**: O resumo assinado do subdocumento DEVE cobrir os dados e os resultados dos estudos vinculados; na aprovação, os estudos vinculados ficam bloqueados.
- **FR-016**: Estudo bloqueado NÃO DEVE ser editado nem recalculado; nova versão com motivo DEVE copiar critério e dados para correção, e a versão anterior continua no documento aprovado.
- **FR-017**: Só quem edita o projeto (feature 004) DEVE criar e alterar estudos; quem tem acesso ao projeto consulta; tentativa sem permissão DEVE ser negada e registrada.
- **FR-018**: Criação, alteração, importação, cálculo, não aplicável, bloqueio e nova versão de estudo DEVEM gerar eventos na trilha de auditoria.

### Key Entities *(include if feature involves data)*

- **Estudo**: projeto, tipo (lista controlada), título, versão, situação (em elaboração, bloqueado), vínculo ao tópico do RAPD ou da Validação, regra de arredondamento, método do IC, não aplicável e justificativa.
- **Critério de aceitação**: métrica, comparação, limite; congelado depois do primeiro resultado.
- **Medida**: número da linha, amostra, lote, kit de referência, dia, corrida, replicata, nível ou grupo, valores (de referência e medido) ou resultado qualitativo esperado e obtido.
- **Resultado calculado**: métrica, grupo, valor completo, valor arredondado, regra aplicada, critério atendido ou não.
- **Mapeamento de importação**: equipamento, coluna do arquivo para cada campo da medida.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, os cálculos reproduzem os vetores de referência V1 a V8 de docs/contexto/06-casos-de-teste.md.
- **SC-002**: Em 100% dos testes, estudo não aplicável sem justificativa é recusado, e a justificativa aparece no documento gerado.
- **SC-003**: Em 100% dos testes, editar ou recalcular estudo de documento aprovado é recusado, e a nova versão preserva a anterior.
- **SC-004**: Um estudo de 500 medidas é calculado em menos de 2 segundos.
- **SC-005**: A importação de um arquivo de 1.000 linhas mostra a pré-visualização em menos de 10 segundos.

## Assumptions

- A lista de tipos de estudo é a proposta de docs/contexto/05-vocabularios.md, reduzida aos 14 tipos da história 1; a Qualidade aprova e mantém a lista (feature 003).
- Os estudos alimentam os documentos pelo vínculo com o tópico; os modelos de formulário (004) não mudam nesta feature.
- Protocolos estatísticos além dos listados ficam para avaliação futura.
