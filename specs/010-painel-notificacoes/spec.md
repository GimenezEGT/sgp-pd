# Feature Specification: Painel do gestor e notificações

**Feature Branch**: `010-painel-notificacoes`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Painel do Gestor de P&D e notificações. Leia docs/contexto/01-visao-geral.md. Objetivo: o gestor vê o andamento de todos os projetos sem pedir relatórios, e ninguém perde prazo de revisão ou assinatura. Histórias: 1. Como Gestor de P&D, vejo a carteira de projetos com etapa atual, percentual de subdocumentos aprovados, marcos planejados × realizados, atraso em dias e líder. 2. Abro um projeto e vejo a linha do tempo: marcos, subdocumentos e versões, assinaturas, alterações e atividade do caderno. 3. Vejo minha fila de pendências: documentos aguardando minha revisão ou assinatura, com o tempo de espera. 4. Como analista ou líder, vejo minhas pendências e recebo e-mail quando um documento é devolvido, aprovado ou fica parado além do prazo configurado. 5. Exporto a carteira em planilha. Regras: o painel respeita as permissões (quem não vê dados financeiros não vê custo nem retorno); notificações podem ser desligadas por tipo, exceto as de assinatura pendente."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Carteira de projetos (Priority: P1)

O Gestor de P&D vê a carteira de projetos: etapa atual, percentual de subdocumentos aprovados, marcos planejados × realizados, atraso em dias e líder.

**Why this priority**: É o acompanhamento sem pedir relatórios.

**Independent Test**: Abrir o painel com projetos em etapas diferentes e conferir os indicadores de cada um.

**Acceptance Scenarios**:

1. **Given** projetos com subdocumentos aprovados e marcos, **When** o gestor abre o painel, **Then** cada projeto mostra etapa atual, percentual aprovado, marcos planejados e realizados, atraso em dias e líder.
2. **Given** uma pessoa sem permissão de dados financeiros, **When** abre o painel, **Then** não vê custo nem retorno.
3. **Given** 100 projetos, **When** o painel é aberto, **Then** responde em menos de 2 segundos.

---

### User Story 2 - Linha do tempo do projeto (Priority: P2)

Ao abrir um projeto, a pessoa vê a linha do tempo: marcos, subdocumentos e versões, assinaturas, alterações e atividade do caderno.

**Why this priority**: Mostra a história do projeto num só lugar.

**Independent Test**: Aprovar um subdocumento e criar uma entrada no caderno e conferir os dois na linha do tempo, em ordem de data.

**Acceptance Scenarios**:

1. **Given** um projeto com eventos, **When** a pessoa abre a linha do tempo, **Then** vê os eventos em ordem de data, com quem e o quê.

---

### User Story 3 - Fila do gestor (Priority: P1)

O Gestor de P&D vê os documentos aguardando a sua revisão ou assinatura, com o tempo de espera.

**Why this priority**: Evita que documentos parem na aprovação.

**Independent Test**: Enviar um documento para revisão e conferir que aparece na fila do gestor com os dias de espera.

**Acceptance Scenarios**:

1. **Given** documentos em revisão, **When** o gestor abre a fila, **Then** vê cada um com o projeto e os dias de espera, do mais antigo para o mais recente.

---

### User Story 4 - Minhas pendências e e-mails (Priority: P1)

Analistas e líderes veem as suas pendências e recebem e-mail quando um documento é devolvido, aprovado ou fica parado além do prazo configurado; as notificações podem ser desligadas por tipo, exceto as de assinatura pendente.

**Why this priority**: Ninguém perde prazo de revisão ou assinatura.

**Independent Test**: Devolver um documento e conferir o e-mail ao elaborador; deixar um documento parado além do prazo e conferir o lembrete.

**Acceptance Scenarios**:

1. **Given** um documento devolvido, **When** a devolução é registrada, **Then** o elaborador recebe e-mail com o motivo.
2. **Given** um documento parado além do prazo configurado, **When** a rotina de notificações roda, **Then** o responsável recebe o lembrete.
3. **Given** uma pessoa que desligou um tipo de notificação, **When** ocorre um evento desse tipo, **Then** ela não recebe e-mail; assinatura pendente não pode ser desligada.

---

### User Story 5 - Exportar a carteira (Priority: P2)

O gestor exporta a carteira em planilha.

**Why this priority**: Atende reuniões e relatórios externos.

**Independent Test**: Exportar e conferir que a planilha tem as mesmas linhas e colunas do painel, respeitando as permissões.

**Acceptance Scenarios**:

1. **Given** o painel, **When** o gestor exporta, **Then** recebe um XLSX com os indicadores de cada projeto, e a exportação fica na trilha.

---

### Edge Cases

- Pessoa sem e-mail cadastrado: a pendência aparece na tela e a falta de e-mail é registrada.
- Falha no envio de e-mail: nova tentativa e registro da falha, sem perder a pendência.
- Projeto sem marcos: atraso não calculável, exibido como "sem marcos".

## Requirements *(mandatory)*

### Functional Requirements

**Painel**

- **FR-001**: O painel DEVE mostrar, para cada projeto que a pessoa acessa, etapa atual, percentual de subdocumentos aprovados, marcos planejados e realizados, atraso em dias e líder [NEEDS CLARIFICATION: quais indicadores o gestor quer na primeira tela?].
- **FR-002**: Custo e retorno só DEVEM aparecer para quem tem permissão de dados financeiros [NEEDS CLARIFICATION: haverá custo realizado (vindo do Sankhya) para comparar com o planejado?].
- **FR-003**: A linha do tempo do projeto DEVE reunir marcos, subdocumentos e versões, assinaturas, alterações e atividade do caderno, em ordem de data.
- **FR-004**: A fila do Gestor de P&D DEVE listar os documentos aguardando a sua revisão ou assinatura, com os dias de espera.
- **FR-005**: Cada pessoa DEVE ver as suas pendências (documentos devolvidos, entradas do caderno a assinar ou testemunhar, documentos parados).
- **FR-006**: A carteira DEVE poder ser exportada em XLSX com as mesmas permissões do painel; a exportação DEVE gerar evento na trilha.

**Notificações**

- **FR-007**: O sistema DEVE enviar e-mail quando um documento é devolvido ou aprovado e quando um documento ou entrada do caderno fica parado além do prazo configurado [NEEDS CLARIFICATION: e-mail imediato ou resumo diário?].
- **FR-008**: Cada pessoa DEVE poder desligar as notificações por tipo, exceto as de assinatura pendente.
- **FR-009**: Envios, falhas e preferências DEVEM ser registrados na trilha de auditoria.

### Key Entities *(include if feature involves data)*

- **Preferência de notificação**: pessoa, tipo, ligada ou desligada.
- **Notificação**: pessoa, tipo, registro de origem, situação (pendente, enviada, falhou), tentativas, data e hora.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O painel abre em menos de 2 segundos com 100 projetos.
- **SC-002**: O e-mail de pendência chega no dia seguinte ao vencimento do prazo em 100% dos testes.
- **SC-003**: Em 100% dos testes, quem não vê dados financeiros não vê custo nem retorno no painel nem na planilha.

## Assumptions

- O e-mail sai pelo SMTP interno da empresa, configurado por variáveis de ambiente.
- Os prazos de revisão (feature 005) e de assinatura do caderno (feature 008) são os já configurados.
