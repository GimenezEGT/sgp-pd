# Feature Specification: Correções do ciclo de revisão e assinatura

**Feature Branch**: `015-correcoes-revisao-assinatura`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "Correções do ciclo de revisão e assinatura encontradas no teste do usuário em 13/11/2026: (1) a mesma pessoa consegue assinar "Revisado" várias vezes na mesma versão do documento; (2) quando o próprio Gestor de P&D envia o documento para revisão (assina como Elaborado), a regra de segregação esconde a aprovação, mas a tela não explica o motivo nem oferece a devolução, a Fila de revisão não mostra o documento e, sem delegação, ele fica travado; (3) as telas de envio e aprovação mostram a situação pelo código interno ("in_review") em vez do nome."

## Contexto

Correção da feature 005 (revisão, versões e assinatura eletrônica), vista no teste do usuário na pilha
local: a Entrada de um projeto foi enviada para revisão pelo próprio Gestor de P&D; a analista assinou
"Revisado" duas vezes na mesma versão; o Gestor não encontrou como aprovar. As regras da 005 continuam:
quem elaborou não aprova a mesma versão; quem assinou como revisor não aprova a mesma versão; a
devolução exige comentário; assinaturas gravadas nunca são alteradas nem apagadas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gestor que elaborou entende e destrava o documento (Priority: P1)

O Gestor de P&D que enviou um documento para revisão (assinatura "Elaborado") vê, na tela do documento,
que a aprovação precisa de outra pessoa com poder de aprovação e o que pode fazer: devolver o documento
com comentário ou delegar a aprovação. A Fila de revisão mostra esses documentos à parte, para que não
fiquem esquecidos.

**Why this priority**: Sem isso o documento fica travado em revisão e o Gestor não sabe por quê; foi o
problema encontrado no teste.

**Independent Test**: Enviar um documento como Gestor, abrir a tela do documento e a Fila de revisão com
o mesmo Gestor e conferir o aviso, a devolução e a seção própria da fila.

**Acceptance Scenarios**:

1. **Given** um documento em revisão cuja assinatura "Elaborado" é do próprio Gestor, **When** ele abre o documento, **Then** vê o aviso de que a aprovação precisa de outro Gestor de P&D ou de quem tem delegação vigente, o caminho para as delegações e a devolução com comentário obrigatório.
2. **Given** o mesmo documento, **When** o Gestor abre a Fila de revisão, **Then** o documento aparece numa seção "Elaborados por você — aguardam outro aprovador", com os dias de espera e sem ação de aprovação.
3. **Given** um Gestor que vai enviar um documento para revisão, **When** abre a tela de envio, **Then** é avisado de que, ao assinar como Elaborado, não poderá aprovar a mesma versão.
4. **Given** o Gestor que elaborou, **When** tenta aprovar pelo endereço da aprovação, **Then** não há botão de aprovação na tela e a tentativa é recusada com o motivo, como hoje.

---

### User Story 2 - Assinatura "Revisado" uma vez por versão (Priority: P1)

Quem revisa assina "Revisado" uma única vez em cada versão do documento.

**Why this priority**: Assinaturas repetidas da mesma pessoa poluem o registro assinado e a trilha de
um documento regulado.

**Independent Test**: Assinar como revisor, conferir que a opção some e que nova tentativa é recusada;
criar nova versão e conferir que a pessoa pode revisar de novo.

**Acceptance Scenarios**:

1. **Given** uma pessoa que já assinou "Revisado" na versão em revisão, **When** abre o documento, **Then** a opção de assinar como revisor não aparece para ela.
2. **Given** a mesma pessoa, **When** tenta assinar de novo (por exemplo, por um envio repetido do formulário), **Then** a tentativa é recusada com a mensagem "Você já assinou como revisor esta versão." e nenhuma assinatura nova é gravada.
3. **Given** uma nova versão do documento em revisão, **When** a mesma pessoa abre o documento, **Then** pode assinar como revisor dessa nova versão.

---

### User Story 3 - Situação pelo nome (Priority: P2)

As telas de envio para revisão e de aprovação mostram a situação do documento pelo nome em português.

**Why this priority**: O código interno confunde quem usa o sistema.

**Independent Test**: Abrir as telas de envio e de aprovação e conferir "Rascunho", "Em revisão",
"Devolvido" ou "Aprovado" no lugar dos códigos.

**Acceptance Scenarios**:

1. **Given** um documento em revisão, **When** a tela de aprovação é aberta, **Then** mostra "situação Em revisão" e nenhum código interno de situação.

---

### Edge Cases

- Gestor que elaborou e que também tem delegação de outro Gestor: continua sem poder aprovar a mesma versão (a delegação não anula a segregação); vê o mesmo aviso.
- Pessoa sem poder de aprovação que elaborou (ex.: analista): não vê a devolução; vê que o documento aguarda aprovação.
- Assinaturas "Revisado" repetidas gravadas antes desta correção continuam no registro, sem alteração.
- Delegação: o Gestor só cria delegação se tiver o perfil Gestor de P&D (regra da 005); o aviso mostra o caminho só para quem pode delegar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Na tela de um documento em revisão cuja assinatura "Elaborado" é da própria pessoa, que tem poder de aprovação (Gestor de P&D ou delegação vigente), o sistema DEVE mostrar o aviso de que a aprovação precisa de outro aprovador e, para quem tem o perfil Gestor de P&D, o caminho para criar delegação.
- **FR-002**: A pessoa do FR-001 DEVE poder devolver o documento, com comentário obrigatório, a partir da tela do documento [NEEDS CLARIFICATION: quem elaborou e tem poder de aprovação pode devolver a própria versão, ou só outro aprovador devolve?].
- **FR-003**: A Fila de revisão DEVE mostrar, numa seção própria, os documentos em revisão elaborados pela própria pessoa (com poder de aprovação), com projeto, data do envio e dias de espera, sem ação de aprovação.
- **FR-004**: A tela de envio para revisão DEVE avisar quem tem poder de aprovação que, ao assinar como Elaborado, não poderá aprovar a mesma versão [NEEDS CLARIFICATION: o envio pelo Gestor fica só com aviso ou é bloqueado quando não há outro aprovador?].
- **FR-005**: A assinatura "Revisado" DEVE ser única por pessoa em cada versão do documento: a opção não aparece para quem já assinou e o sistema recusa nova tentativa com mensagem, sem gravar assinatura.
- **FR-006**: As telas de envio para revisão e de aprovação DEVEM mostrar a situação pelo nome (Rascunho, Em revisão, Devolvido, Aprovado), nunca pelo código interno.
- **FR-007**: As regras da feature 005 DEVEM continuar valendo: quem elaborou não aprova a mesma versão; quem assinou como revisor não aprova a mesma versão; devolução com comentário obrigatório e registrada na trilha; assinaturas gravadas nunca são alteradas nem apagadas.

### Key Entities *(include if feature involves data)*

- Sem entidade nova: assinaturas, comentários de devolução e delegações da feature 005.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, uma segunda assinatura "Revisado" da mesma pessoa na mesma versão é recusada e não grava registro.
- **SC-002**: Em 100% dos testes, o Gestor que elaborou vê o aviso e a devolução na tela do documento e encontra o documento na seção própria da Fila de revisão.
- **SC-003**: Nenhuma das telas de envio e aprovação exibe código interno de situação.

## Assumptions

- Correção de telas e de regra de assinatura; sem mudança de modelo de dados.
- O teste do usuário na pilha local (13/11/2026) é a origem; os registros já gravados ficam como estão.
