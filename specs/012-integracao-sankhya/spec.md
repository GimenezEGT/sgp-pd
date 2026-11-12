# Feature Specification: Integração com o Sankhya

**Feature Branch**: `012-integracao-sankhya`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Integração com o ERP Sankhya para que os dados dos subdocumentos aprovados fiquem armazenados e utilizáveis no ERP, e para que códigos de produtos e insumos venham do cadastro oficial. Leia docs/contexto/07-integracao-sankhya.md. Histórias: 1. Como analista, ao cadastrar insumos e lotes, busco o código no cadastro de produtos do Sankhya e o sistema traz descrição e unidade, evitando código digitado errado. 2. Quando um subdocumento é aprovado, seus dados estruturados vão para o Sankhya, nas tabelas adicionais definidas com a TI: projeto, subdocumento, versão, data, signatários, campos principais e identificação do PDF oficial. 3. Na Saída de Projeto aprovada, novas matérias-primas e materiais de embalagem viram solicitações de cadastro no Sankhya, com dados e certificados. 4. Como TI, acompanho a fila de integração (enviado, erro, reenviado) e reprocesso falhas sem duplicar registros. 5. Enquanto a API não estiver liberada, exporto os mesmos dados em CSV, XLSX ou JSON no layout combinado. Regras: integração só pelo API Gateway oficial; credenciais fora do código; cada envio é idempotente e registrado na trilha de auditoria; falha de integração nunca bloqueia o trabalho no sistema."

## Clarifications

### Session 2026-11-12

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: Quais tabelas adicionais e campos a consultoria vai criar no Sankhya? → A: Ainda não definidos; o sistema monta os registros do modelo lógico do contexto (Projeto P&D, Documento P&D, Lote P&D, Insumo novo, Resultado de estudo) e um mapeamento configurável, mantido pela TI, liga cada registro à entidade e aos campos do Sankhya; sem mapeamento, as mensagens ficam "aguardando configuração" e a exportação em arquivo funciona (ratificar com a TI e a consultoria Sankhya).
- Q: Envio imediato na aprovação ou lote noturno? → A: Imediato, logo depois da aprovação, com novas tentativas automáticas em espera crescente e reprocessamento manual pela TI (ratificar com a TI).
- Q: A nova matéria-prima é cadastrada direto ou entra como solicitação para o cadastro? → A: Entra como solicitação de cadastro (registro "Insumo novo" com situação "solicitado"); o cadastro no Sankhya continua com a equipe responsável (ratificar com o Gestor de P&D, a Produção e a TI).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar o código no cadastro do Sankhya (Priority: P1)

Ao cadastrar insumos e lotes, o analista busca o código no cadastro de produtos do Sankhya e o sistema traz descrição e unidade.

**Why this priority**: Evita código digitado errado, a origem mais comum de divergência com o ERP.

**Independent Test**: Buscar um código existente no Sankhya (simulado) e conferir descrição e unidade preenchidas; buscar um inexistente e conferir a mensagem.

**Acceptance Scenarios**:

1. **Given** a integração configurada, **When** o analista busca um código, **Then** o sistema traz descrição, unidade e situação do cadastro do Sankhya.
2. **Given** o Sankhya indisponível, **When** a busca é feita, **Then** o cadastro continua possível com o aviso de que o código não foi conferido.

---

### User Story 2 - Enviar os dados do subdocumento aprovado (Priority: P1)

Quando um subdocumento é aprovado, os dados estruturados vão para o Sankhya nas tabelas adicionais: projeto, subdocumento, versão, data, signatários, campos principais e identificação do PDF oficial.

**Why this priority**: Deixa os dados de P&D utilizáveis no ERP.

**Independent Test**: Aprovar um subdocumento e conferir uma mensagem na fila e um único registro no Sankhya simulado, mesmo com reenvio.

**Acceptance Scenarios**:

1. **Given** um subdocumento aprovado, **When** a aprovação é registrada, **Then** nasce uma mensagem de integração na mesma transação, enviada depois em segundo plano.
2. **Given** um envio repetido da mesma mensagem, **When** o Sankhya recebe, **Then** existe um único registro.

---

### User Story 3 - Solicitações de cadastro de insumos novos (Priority: P2)

Na Saída de Projeto aprovada, novas matérias-primas e materiais de embalagem viram solicitações de cadastro no Sankhya, com dados e certificados.

**Why this priority**: Transfere à Produção o que o projeto introduziu.

**Independent Test**: Aprovar uma Saída com uma matéria-prima nova e conferir a solicitação na fila.

**Acceptance Scenarios**:

1. **Given** uma Saída aprovada com insumos novos, **When** a aprovação é registrada, **Then** cada insumo vira uma solicitação de cadastro com descrição, tipo, fabricante e certificado.

---

### User Story 4 - Fila de integração (Priority: P1)

A TI acompanha a fila (enviado, erro, reenviado) e reprocessa falhas sem duplicar registros.

**Why this priority**: Falha de integração não pode passar despercebida nem duplicar dados.

**Independent Test**: Simular erro do gateway, conferir a mensagem com erro e reprocessar com sucesso.

**Acceptance Scenarios**:

1. **Given** uma mensagem com erro, **When** a TI reprocessa, **Then** ela é reenviada com a mesma chave de idempotência e fica enviada.
2. **Given** falhas seguidas, **When** a fila é consultada, **Then** mostra tentativas, último erro e próxima tentativa.

---

### User Story 5 - Exportação de contingência (Priority: P2)

Enquanto a API não estiver liberada, os mesmos dados são exportados em CSV, XLSX ou JSON no layout combinado.

**Why this priority**: Permite a importação assistida no ERP antes da API.

**Independent Test**: Exportar os documentos aprovados em CSV e conferir separador, vírgula decimal e colunas.

**Acceptance Scenarios**:

1. **Given** mensagens de integração, **When** a TI exporta, **Then** recebe um arquivo por registro no formato escolhido, no layout do contexto.

---

### Edge Cases

- Credenciais ausentes ou inválidas: nada é enviado, a fila mostra o erro e o trabalho no sistema continua.
- Token expirado: renovado automaticamente antes de nova tentativa.
- Mudança no layout das tabelas adicionais: mensagens antigas continuam reprocessáveis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A integração DEVE usar só o API Gateway oficial da Sankhya (OAuth 2.0 client credentials e serviços `CRUDServiceProvider`), sem acesso direto ao banco do ERP.
- **FR-002**: Credenciais (client_id, client_secret, X-Token) DEVEM ficar só em variáveis de ambiente.
- **FR-003**: A busca de produto ou insumo pelo código DEVE trazer descrição, unidade e situação do cadastro do Sankhya, sem bloquear o cadastro quando o ERP estiver indisponível.
- **FR-004**: A aprovação de subdocumento DEVE gerar, na mesma transação, a mensagem de integração com projeto, subdocumento, versão, data, signatários, resumo do conteúdo aprovado e identificação do PDF oficial (quando houver), no modelo lógico do contexto; a entidade e os campos do Sankhya vêm de um mapeamento configurável mantido pela TI.
- **FR-005**: As mensagens DEVEM ser enviadas em segundo plano logo depois da aprovação, com novas tentativas em espera crescente e chave de idempotência; reenvio não duplica registros; sem mapeamento configurado, ficam aguardando configuração.
- **FR-006**: Insumos novos da Saída aprovada DEVEM gerar solicitações de cadastro (registro "Insumo novo" com situação "solicitado"), com descrição, tipo, fabricante e certificado; o sistema não cadastra o produto direto no ERP.
- **FR-007**: A TI DEVE acompanhar a fila (situação, tentativas, último erro) e reprocessar falhas.
- **FR-008**: A exportação de contingência DEVE gerar CSV (UTF-8, ";", vírgula decimal), XLSX e JSON no envelope do contexto, um arquivo por registro.
- **FR-009**: Envio, falha, reprocessamento e exportação DEVEM ser registrados na trilha; falha de integração nunca bloqueia o trabalho no sistema.

### Key Entities *(include if feature involves data)*

- **Mensagem de integração**: tipo de registro, chave de idempotência, conteúdo, situação, tentativas, último erro, próxima tentativa, registro de origem.
- **Configuração da integração**: ambiente (testes ou produção), usuário do Sankhya, entidades e campos mapeados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, uma aprovação gera um único registro no Sankhya, mesmo com reenvio.
- **SC-002**: A busca de insumo pelo código traz os dados do Sankhya em homologação (verificação no ambiente de testes da Sankhya).
- **SC-003**: Em 100% dos testes, a exportação em arquivo reproduz os registros da fila no layout combinado.
- **SC-004**: Em 100% dos testes de falha do gateway, o trabalho no sistema continua e a mensagem fica reprocessável.

## Assumptions

- O usuário do Sankhya que representa o sistema e as permissões dele são definidos pela TI e pela consultoria.
- Homologação no ambiente de testes da Sankhya antes da produção.
- Mapeamento, momento do envio e solicitação de insumo novo definidos nas respostas provisórias do esclarecimento (sessão 2026-11-12).
