# Feature Specification: Documento completo do projeto

**Feature Branch**: `009-documento-completo`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Documento completo do projeto, que é o registro histórico do projeto exigido pela RDC 665/2022 (art. 61), montado automaticamente. Leia docs/contexto/03-padroes-formatacao.md e 04-requisitos-regulatorios.md. Objetivo: gerar com um clique o documento consolidado que hoje é montado à mão, incluindo o histórico de experimentos do caderno de laboratório. Histórias: 1. Como líder ou gestor, gero o documento completo de um projeto com capa geral, sumário automático, TAP e Plano de Negócios, cada subdocumento aprovado na versão vigente (com sua capa), alterações de projeto, verificação final, saída, histórico do caderno e lista de anexos. 2. Escolho se o histórico do caderno entra completo ou resumido (título, data, autor, conclusão e vínculos). 3. O documento traz um quadro de versões (subdocumento, versão, data de aprovação, signatários) e um resumo da trilha de auditoria do projeto. 4. Versões substituídas aparecem só no quadro de versões, não no corpo, a menos que eu peça o histórico completo. 5. Antes de gerar, o sistema mostra o que falta para o documento estar completo (subdocumentos não aprovados, pendências da Verificação Final). Regras: só versões aprovadas entram no corpo; o documento gerado é arquivado com hash e versão; sumário e numeração de páginas são automáticos; dados financeiros do Plano de Negócios só entram para quem tem permissão."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar o documento completo com um clique (Priority: P1)

O líder do projeto ou o Gestor de P&D gera o documento completo: capa geral, sumário, TAP, Plano de Negócios, cada subdocumento aprovado na versão vigente com a sua capa, alterações de projeto, Verificação Final, Saída, histórico do caderno e lista de anexos.

**Why this priority**: É o registro histórico do projeto (RDC 665/2022, art. 61), hoje montado à mão.

**Independent Test**: Gerar o documento de um projeto com todos os subdocumentos aprovados e conferir as partes, a ordem e o sumário.

**Acceptance Scenarios**:

1. **Given** um projeto com subdocumentos aprovados, **When** o líder gera o documento completo, **Then** recebe um PDF com capa geral, sumário com as páginas reais e as partes na ordem definida.
2. **Given** a geração em andamento, **When** a pessoa acompanha a tela, **Then** vê o progresso e é avisada ao terminar.
3. **Given** um documento gerado, **When** é consultado depois, **Then** está arquivado com resumo criptográfico, versão do projeto e código de verificação.

---

### User Story 2 - Histórico do caderno completo ou resumido (Priority: P2)

Ao gerar, a pessoa escolhe se o histórico do caderno entra completo ou resumido (título, data, autor, conclusão e vínculos).

**Why this priority**: O caderno completo pode ser longo; o resumo basta em muitos usos.

**Independent Test**: Gerar as duas opções e comparar o conteúdo do caderno.

**Acceptance Scenarios**:

1. **Given** a opção resumida, **When** o documento é gerado, **Then** cada entrada assinada aparece com título, data, autor, conclusão e vínculos.
2. **Given** a opção completa, **When** o documento é gerado, **Then** cada entrada assinada aparece com todos os campos, adendos e assinaturas.

---

### User Story 3 - Quadro de versões e resumo da trilha (Priority: P1)

O documento traz um quadro de versões (subdocumento, versão, data de aprovação, signatários) e um resumo da trilha de auditoria do projeto.

**Why this priority**: Mostra a história das aprovações exigida pelo registro histórico.

**Independent Test**: Aprovar duas versões de um subdocumento e conferir as duas linhas no quadro.

**Acceptance Scenarios**:

1. **Given** um subdocumento com duas versões aprovadas, **When** o documento é gerado, **Then** o quadro lista as duas versões com data de aprovação e signatários e o corpo traz só a vigente.
2. **Given** a trilha do projeto, **When** o documento é gerado, **Then** o resumo da trilha aparece no formato definido.

---

### User Story 4 - Histórico completo de versões (Priority: P2)

Versões substituídas aparecem só no quadro, a menos que a pessoa peça o histórico completo; nesse caso, entram no corpo depois da vigente, marcadas como substituídas.

**Why this priority**: Atende auditorias que pedem o conteúdo das versões anteriores.

**Independent Test**: Gerar com e sem o histórico completo e comparar.

**Acceptance Scenarios**:

1. **Given** a opção de histórico completo, **When** o documento é gerado, **Then** as versões substituídas aparecem no corpo identificadas como substituídas.

---

### User Story 5 - Pendências antes de gerar (Priority: P1)

Antes de gerar, o sistema mostra o que falta para o documento estar completo: subdocumentos não aprovados e pendências da Verificação Final.

**Why this priority**: Evita gerar um registro histórico incompleto sem perceber.

**Independent Test**: Abrir a tela de geração num projeto com a Validação em elaboração e conferir a pendência listada.

**Acceptance Scenarios**:

1. **Given** um subdocumento obrigatório não aprovado, **When** a pessoa abre a geração, **Then** a pendência aparece com o nome do subdocumento e a situação.
2. **Given** itens da Verificação Final com disposição diferente de Aprovado, **When** a pessoa abre a geração, **Then** os itens aparecem como pendências.
3. **Given** pendências, **When** a pessoa gera mesmo assim, **Then** o documento sai como rascunho, com marca d'água e a lista de pendências, e não como documento oficial.

---

### Edge Cases

- Pessoa sem acesso ao projeto: não gera nem baixa; tentativa registrada.
- Pessoa sem permissão de dados financeiros: o Plano de Negócios sai sem os campos financeiros.
- Projeto sem nenhum subdocumento aprovado: só rascunho, com as pendências.
- Nova geração sem nenhuma mudança desde a anterior: reaproveita o documento já arquivado.
- Falha na geração: registrada, com mensagem clara e possibilidade de tentar de novo.

## Requirements *(mandatory)*

### Functional Requirements

**Geração**

- **FR-001**: O líder do projeto e o Gestor de P&D DEVEM poder gerar o documento completo de um projeto a que têm acesso; quem acessa o projeto DEVE poder consultar e baixar os documentos gerados; tentativa sem permissão DEVE ser negada e registrada.
- **FR-002**: O documento DEVE ter capa geral, sumário automático com a numeração real das páginas e numeração de páginas automática.
- **FR-003**: As partes DEVEM seguir a ordem oficial [NEEDS CLARIFICATION: ordem oficial das partes; no projeto DBS a Alteração aparece logo após a capa da Entrada].
- **FR-004**: Só versões aprovadas DEVEM entrar no corpo: TAP, Plano de Negócios e cada subdocumento na versão vigente, com a sua capa, no padrão visual da feature 006.
- **FR-005**: Os dados financeiros do Plano de Negócios só DEVEM entrar quando quem gera tem permissão de vê-los [NEEDS CLARIFICATION: o Plano de Negócios entra no documento completo ou fica num anexo restrito?].
- **FR-006**: A geração DEVE ser assíncrona, com progresso visível e aviso ao terminar.

**Conteúdo**

- **FR-007**: O histórico do caderno DEVE entrar completo ou resumido (título, data, autor, conclusão e vínculos), conforme a escolha; só entradas assinadas entram.
- **FR-008**: O documento DEVE trazer o quadro de versões (subdocumento, versão, data de aprovação, signatários) de todas as versões aprovadas.
- **FR-009**: O documento DEVE trazer o resumo da trilha de auditoria do projeto [NEEDS CLARIFICATION: eventos por tipo ou lista completa?].
- **FR-010**: Versões substituídas só DEVEM entrar no corpo quando a pessoa pedir o histórico completo, marcadas como substituídas.
- **FR-011**: O documento DEVE trazer a lista de anexos (nome, origem e resumo criptográfico).

**Pendências e arquivo**

- **FR-012**: Antes de gerar, o sistema DEVE listar as pendências: subdocumentos não aprovados e itens da Verificação Final com disposição diferente de Aprovado.
- **FR-013**: Com pendências, o documento só DEVE sair como rascunho (marca d'água e lista de pendências); sem pendências, sai como documento oficial.
- **FR-014**: O documento gerado DEVE ser arquivado com resumo criptográfico, versão do projeto, opções usadas e código de verificação, como os documentos da feature 006.
- **FR-015**: Geração, falha, reaproveitamento e download DEVEM gerar eventos na trilha de auditoria.

### Key Entities *(include if feature involves data)*

- **Pedido de documento completo**: projeto, quem pediu, opções (caderno completo ou resumido, histórico completo de versões), situação, progresso, resultado.
- **Documento completo gerado**: projeto, versão do projeto, opções, oficial ou rascunho, pendências na geração, arquivo, resumo criptográfico, código de verificação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, o sumário bate com as páginas reais do documento.
- **SC-002**: Em 100% dos testes com projeto incompleto, as pendências aparecem antes de gerar e no rascunho.
- **SC-003**: Um projeto de 300 páginas é gerado em menos de 3 minutos no servidor de homologação.
- **SC-004**: O documento completo de um projeto piloto é aprovado pela Qualidade (verificação manual).

## Assumptions

- O gerador, o layout, o selo e o código de verificação da feature 006 são reaproveitados.
- O documento completo é gerado em PDF; DOCX do documento completo fica fora do escopo.
- O caderno de laboratório da feature 008 fornece as entradas assinadas e os adendos.
