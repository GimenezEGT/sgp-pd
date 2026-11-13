# Feature Specification: Versionamento do documento final do projeto

**Feature Branch**: `016-versao-documento-final`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "Versionamento do documento final do projeto com rastreabilidade (pedido do usuário em 13/11/2026): "cada subdocumento deve ter sua própria versão, e o documento final deve ter também sua própria versão que muda sempre que um subdocumento muda de versão. Tudo isso com rastreabilidade." Hoje cada subdocumento já tem versão própria, mas o documento completo do projeto (feature 009) usa a versão do projeto, que só muda com Alteração de Projeto aprovada, e não há registro de quais versões de subdocumentos compõem cada versão do documento final."

## Contexto

O documento final do projeto é o documento completo da feature 009 (registro histórico, RDC
665/2022, art. 61), composto pelo TAP, pelo Plano de Negócios e por cada subdocumento na versão
aprovada vigente (as "partes"). Cada parte já tem numeração de versão própria (features 002, 004 e
005: nova versão com motivo; versão aprovada congelada). O documento final, porém, mostra a versão do
projeto, que só muda com Alteração de Projeto aprovada, e nada registra quais versões das partes
formavam o documento final em cada momento.

## Clarifications

### Session 2026-11-13

Respostas do usuário (não provisórias).

- Q: Quando a versão do documento final sobe: na aprovação de uma nova versão de parte ou já na abertura da nova versão em rascunho? → A: Na aprovação, quando a nova versão da parte passa a valer; abrir uma versão em rascunho não muda o documento final.
- Q: Como fica o histórico dos projetos que já têm aprovações? → A: É reconstruído a partir das aprovações já registradas, em ordem de data, com as versões marcadas como reconstruídas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Versão própria do documento final, que acompanha as partes (Priority: P1)

Quando uma nova versão de qualquer parte passa a valer, o documento final do projeto ganha
automaticamente a versão seguinte, registrada com o que mudou e com a composição completa.

**Why this priority**: É o pedido do usuário; sem isso o documento final não diz de quais versões das
partes é feito.

**Independent Test**: Aprovar a versão 02 de um subdocumento e conferir que o documento final passou à
versão seguinte, com a mudança e a composição registradas.

**Acceptance Scenarios**:

1. **Given** um projeto com o documento final na versão N, **When** a versão 02 da Formulação é aprovada, **Then** o documento final passa à versão N+1, que registra "Formulação: 01 → 02", quem aprovou, quando, e a composição com todas as partes.
2. **Given** a aprovação do projeto (TAP e Plano de Negócios aprovados juntos), **When** ela é registrada, **Then** nasce uma única versão do documento final com as duas partes.
3. **Given** uma devolução, um envio para revisão ou a abertura de nova versão em rascunho, **When** registrados, **Then** a versão do documento final não muda.

---

### User Story 2 - Rastreabilidade das versões do documento final (Priority: P1)

Na tela do projeto, o histórico das versões do documento final mostra, para cada versão, o que mudou,
quem aprovou e quando, e a composição completa; cada nova versão vai para a trilha de auditoria.

**Why this priority**: Rastreabilidade pedida pelo usuário e exigida pela constituição (princípios I e
II).

**Independent Test**: Aprovar duas partes em momentos diferentes e conferir o histórico com duas
versões, a mudança de cada uma, a composição e os eventos na trilha.

**Acceptance Scenarios**:

1. **Given** um projeto com três versões do documento final, **When** a tela do projeto é aberta, **Then** mostra as três, com número, data e hora, quem aprovou e o que mudou, e a composição de qualquer uma (parte, versão, data de aprovação, resumo criptográfico).
2. **Given** uma nova versão do documento final, **When** ela nasce, **Then** a trilha registra o evento com a mudança e o resumo da composição.

---

### User Story 3 - Documento completo gerado traz a versão do documento final (Priority: P1)

O PDF do documento completo indica a versão do documento final que representa e traz o quadro das
versões do documento final; a versão do projeto continua indicada à parte.

**Why this priority**: Quem lê o documento precisa saber qual versão tem em mãos.

**Independent Test**: Gerar o documento depois de uma nova versão e conferir capa, nome do arquivo,
registro arquivado e quadro.

**Acceptance Scenarios**:

1. **Given** o documento final na versão 03, **When** o documento completo é gerado, **Then** a capa e o nome do arquivo indicam a versão 03 do documento final, o registro arquivado aponta para ela e o quadro lista as versões 01 a 03 com o que mudou em cada uma.

---

### User Story 4 - Histórico de versões de cada parte (Priority: P2)

Na tela de cada subdocumento, do TAP e do Plano de Negócios, o histórico mostra cada versão da parte e
em quais versões do documento final ela entrou.

**Why this priority**: Fecha a rastreabilidade nos dois sentidos (parte → documento final).

**Independent Test**: Abrir um subdocumento com duas versões aprovadas e uma em rascunho e conferir o
histórico.

**Acceptance Scenarios**:

1. **Given** um subdocumento com as versões 01 e 02 aprovadas e a 03 em rascunho, **When** a tela é aberta, **Then** o histórico mostra as três versões com situação (Substituída, Vigente, Rascunho), motivo da abertura, quem abriu e quando, quem aprovou e quando, e as versões do documento final em que a 01 e a 02 entraram.

---

### Edge Cases

- Aprovação de Alteração de Projeto: sobe a versão do projeto (como hoje) e também a do documento final (a Alteração é uma parte).
- Aprovações de partes diferentes ao mesmo tempo: numeração sem lacunas nem repetição.
- Documento completo pedido antes de qualquer aprovação: o rascunho indica que ainda não há versão do documento final.
- Composição vigente diferente da última versão registrada (aprovação registrada por fora do fluxo, como cargas iniciais): o sistema registra a versão que falta antes de gerar o documento, com o motivo "recomposição".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cada subdocumento, o TAP e o Plano de Negócios DEVEM manter numeração de versão própria, independente da versão do projeto e das demais partes, com as regras da feature 005 (nova versão com motivo; versão aprovada congelada).
- **FR-002**: O documento final de cada projeto DEVE ter numeração de versão própria (01, 02, …), independente da versão do projeto.
- **FR-003**: A versão do documento final DEVE subir automaticamente, na mesma operação da aprovação, quando uma nova versão de qualquer parte é aprovada e passa a valer; abrir uma versão em rascunho, enviar para revisão ou devolver não muda o documento final; uma aprovação que alcança mais de uma parte ao mesmo tempo gera uma única versão.
- **FR-004**: Cada versão do documento final DEVE registrar número, data e hora, quem aprovou, o que mudou (parte, versão anterior e nova) e a composição completa (cada parte com versão vigente, data de aprovação e resumo criptográfico do conteúdo aprovado), com o resumo criptográfico da composição; o registro é imutável.
- **FR-005**: Cada nova versão do documento final DEVE gerar evento na trilha de auditoria com a mudança e o resumo da composição.
- **FR-006**: A tela do projeto DEVE mostrar o histórico das versões do documento final e a composição de qualquer versão.
- **FR-007**: O documento completo gerado DEVE indicar a versão do documento final que representa (capa, nome do arquivo e registro arquivado) e trazer o quadro das versões do documento final; a versão do projeto continua indicada à parte.
- **FR-008**: A tela de cada parte DEVE mostrar o histórico de versões da parte: número, situação, motivo da abertura, quem abriu e quando, quem aprovou e quando, e as versões do documento final em que cada versão entrou.
- **FR-009**: Projetos com aprovações anteriores a esta funcionalidade DEVEM ter o histórico das versões do documento final reconstruído a partir das aprovações já registradas, em ordem de data (aprovações do mesmo instante numa só versão), com as versões marcadas como reconstruídas e um evento na trilha para cada uma, gravado no momento da reconstrução (a trilha não aceita data passada; a data e o aprovador originais vão no evento).
- **FR-010**: O documento completo DEVE sempre corresponder a uma versão registrada do documento final: se a composição vigente não estiver registrada, o sistema registra a versão antes de gerar, com o motivo "recomposição".

### Key Entities *(include if feature involves data)*

- **Versão do documento final**: projeto, número, data e hora, quem aprovou, o que mudou (partes, versão anterior e nova), composição (parte, versão, data de aprovação, resumo), resumo da composição, motivo (aprovação, recomposição ou reconstrução).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, cada aprovação de nova versão de parte gera exatamente uma nova versão do documento final, com a mudança e a composição corretas.
- **SC-002**: Em 100% dos testes, o documento completo gerado indica a versão vigente do documento final e traz o quadro das versões.
- **SC-003**: Para qualquer versão do documento final, quem consulta descobre pela tela, em menos de 1 minuto, as versões de cada parte que a compunham e o que mudou em relação à anterior.

## Assumptions

- "Documento final" é o documento completo do projeto da feature 009; as partes são as que ele inclui (TAP, Plano de Negócios e subdocumentos aprovados).
- A versão do projeto (feature 004, Alteração de Projeto) continua existindo e é mostrada à parte.
- Mudança de modelo de dados com migração e teste (constituição VIII).
