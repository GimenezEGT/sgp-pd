# Feature Specification: Revisão controlada dos modelos de documentos e subdocumentos

**Feature Branch**: `013-revisao-modelos`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Os modelos dos documentos e subdocumentos podem ser revisados e alterados. Isso deve ser feito também apenas por usuários autorizados e logados, e as revisões e mudanças devem ter rastreabilidade."

Origem: pedido do usuário em 2026-11-07, fora do roteiro original do plano. Numerada como 013 para manter a numeração 001–012 do plano; executada depois da 006, porque usa os modelos de formulário (004), a assinatura eletrônica (005) e os modelos de layout (006).

## Clarifications

### Session 2026-11-07

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: Quais perfis elaboram e quais aprovam revisões de modelos? → A: Qualidade/AR elabora (abre, altera, envia e descarta); o Gestor de P&D, dono do processo PSG 20, aprova ou devolve; Administrador do sistema não elabora nem aprova; os demais perfis só consultam (ratificar com a Garantia da Qualidade e o Gestor de P&D).
- Q: TAP e Plano de Negócios passam a ter modelo de formulário revisável? → A: Não nesta feature: os campos do TAP e do Plano de Negócios continuam os da feature 002; só os modelos de layout deles (capa, cabeçalho, rodapé, estilos) entram na revisão controlada (ratificar com o Gestor de P&D).
- Q: A aprovação exige assinatura de quem elaborou também? → A: Não; o envio da elaboradora fica registrado na trilha com a sessão autenticada, e só a aprovação exige assinatura eletrônica com reautenticação e significado "aprovado" (ratificar com a Garantia da Qualidade).
- Q: A vigência pode ser futura? → A: Sim; na aprovação, o aprovador escolhe vigência imediata (padrão) ou uma data futura; até a data, a versão aprovada aguarda vigência e novos documentos continuam na anterior (ratificar com a Garantia da Qualidade).
- Q: Como um modelo é retirado de uso? → A: Qualidade/AR pede a retirada com motivo e o Gestor de P&D a aprova com assinatura eletrônica, como numa revisão; o modelo retirado continua consultável e não é oferecido a novos documentos (ratificar com a Garantia da Qualidade).

## Contexto

Os formulários do PSG 20 mudam de versão ("Formulário Versão: 05"), e o rodapé de todos os documentos muda quando o formulário é revisado (docs/contexto/01-visao-geral.md). A Qualidade/Assuntos Regulatórios mantém os modelos de formulário e de layout. O sistema guarda dois tipos de modelo:

- **Modelo de subdocumento** (modelo de formulário, feature 004): tipo de subdocumento, versão do formulário, referência PSG, título da capa, tópicos numerados, campos e regras.
- **Modelo de documento** (modelo de layout, feature 006): capa, cabeçalho, rodapé e estilos usados na geração dos documentos (subdocumentos, TAP, Plano de Negócios, documento completo e dossiê).

Esta feature define como esses modelos são revisados e alterados: quem pode, em que etapas, com que registros, e como cada mudança fica rastreável. Os modelos são registros do sistema da qualidade: nada é apagado, versão publicada não muda e cada documento continua com a versão de modelo que usou.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Abrir e elaborar uma revisão de modelo (Priority: P1)

A pessoa autorizada a elaborar abre uma revisão de um modelo publicado. O sistema cria um rascunho da próxima versão, com o conteúdo da versão vigente, e a pessoa altera o que precisa (tópicos, campos, regras, rótulos, capa, rodapé, estilos), informando o motivo da revisão e o impacto esperado.

**Why this priority**: É a função pedida: modelos podem ser revisados e alterados sem programação.

**Independent Test**: Abrir revisão de um modelo publicado, alterar o rótulo de um tópico e salvar; conferir que a versão publicada continua igual e que o rascunho guarda o motivo e a mudança.

**Acceptance Scenarios**:

1. **Given** um modelo publicado na versão 05, **When** a pessoa autorizada abre uma revisão, **Then** nasce o rascunho da versão 06 com o conteúdo da 05, e a 05 continua vigente e intacta.
2. **Given** o rascunho, **When** a pessoa o altera, **Then** cada alteração vai para a trilha com valor anterior e novo.
3. **Given** um modelo que já tem revisão em andamento, **When** alguém tenta abrir outra, **Then** o sistema recusa e aponta a revisão aberta.
4. **Given** um rascunho sem motivo da revisão, **When** a pessoa o envia para aprovação, **Then** o envio é recusado.
5. **Given** uma pessoa sem autorização para elaborar, **When** tenta abrir ou alterar uma revisão (inclusive pela URL direta), **Then** o acesso é negado e registrado.

---

### User Story 2 - Aprovar ou devolver a revisão (Priority: P1)

O aprovador vê a revisão enviada com a comparação item a item contra a versão vigente, o motivo e o impacto, e aprova com assinatura eletrônica ou devolve com comentário obrigatório. Quem elaborou não aprova a própria revisão.

**Why this priority**: Garante que nenhuma mudança de modelo entra em uso sem revisão e aprovação de outra pessoa (RDC 665/2022, arts. 104 a 106: alteração sob controle).

**Independent Test**: Enviar uma revisão, abri-la como aprovador, conferir a comparação, devolver com comentário, corrigir, reenviar e aprovar.

**Acceptance Scenarios**:

1. **Given** uma revisão enviada, **When** o aprovador a abre, **Then** vê o que entrou, saiu e mudou em relação à versão vigente, com o motivo e o impacto.
2. **Given** a revisão, **When** o aprovador a devolve sem comentário, **Then** a devolução é recusada; com comentário, a revisão volta para rascunho e o comentário fica no histórico.
3. **Given** a revisão, **When** o aprovador a aprova, **Then** a aprovação exige assinatura eletrônica e registra pessoa, data e hora e o resumo do conteúdo aprovado.
4. **Given** quem elaborou a revisão, **When** tenta aprová-la, **Then** o sistema recusa.
5. **Given** uma revisão enviada, **When** alguém tenta alterá-la, **Then** a alteração é recusada até ela voltar para rascunho.

---

### User Story 3 - Publicação e vigência sem alterar documentos já iniciados (Priority: P1)

Na aprovação, a nova versão é publicada com a data de início de vigência (imediata ou futura). A partir dela, documentos novos usam a nova versão; documentos já iniciados continuam na versão em que começaram, salvo migração autorizada (feature 004). Versão publicada nunca é alterada.

**Why this priority**: Sem isso, revisar um modelo mudaria documentos em andamento ou já assinados.

**Independent Test**: Publicar a versão 06 com um documento em rascunho na 05; conferir que o documento continua na 05, que um documento novo nasce na 06 e que a 05 fica como substituída e consultável.

**Acceptance Scenarios**:

1. **Given** uma revisão aprovada com vigência imediata, **When** é publicada, **Then** a nova versão passa a ser a vigente e a anterior fica substituída e consultável.
2. **Given** vigência futura, **When** a data chega, **Then** a nova versão passa a valer para novos documentos; antes disso, novos documentos continuam na versão anterior.
3. **Given** documentos iniciados na versão anterior, **When** a nova versão é publicada, **Then** eles continuam na versão em que começaram, e a publicação informa quantos documentos ficaram na versão anterior.
4. **Given** uma versão publicada, **When** alguém tenta alterá-la, **Then** o sistema recusa; correção só por nova revisão.
5. **Given** uma versão publicada, **When** a Qualidade verifica a integridade, **Then** o sistema confirma que o conteúdo não mudou desde a aprovação ou aponta a divergência.

---

### User Story 4 - Histórico e rastreabilidade das revisões (Priority: P2)

Qualquer pessoa autorizada a consultar modelos vê o histórico de cada modelo: todas as versões com situação, datas de elaboração, envio, devolução, aprovação e vigência, quem fez cada etapa, motivo, impacto e comentários; e compara quaisquer duas versões.

**Why this priority**: É a rastreabilidade pedida e a evidência para auditoria e validação do sistema.

**Independent Test**: Num modelo com três versões, abrir o histórico, comparar a versão 01 com a 03 e conferir os eventos na trilha de auditoria.

**Acceptance Scenarios**:

1. **Given** um modelo com várias versões, **When** a pessoa abre o histórico, **Then** vê cada versão com situação, etapas, pessoas, datas e motivos.
2. **Given** duas versões quaisquer, **When** a pessoa pede a comparação, **Then** vê os itens incluídos, retirados e alterados.
3. **Given** a trilha de auditoria, **When** filtrada pelo modelo, **Then** mostra abertura, alterações, envio, devolução, aprovação, publicação e descarte de revisões.
4. **Given** uma versão de modelo, **When** a pessoa consulta onde ela é usada, **Then** vê quantos e quais documentos foram iniciados nela.

---

### User Story 5 - Descartar uma revisão e retirar um modelo de uso (Priority: P3)

A pessoa autorizada descarta uma revisão em rascunho que não vai adiante, com motivo, sem apagar nada. Um modelo que deixa de ser usado é retirado de uso com motivo e aprovação, e não serve mais para novos documentos.

**Why this priority**: Fecha o ciclo sem exclusão física e evita uso de modelos obsoletos.

**Independent Test**: Descartar um rascunho com motivo e conferir que ele continua no histórico como descartado; retirar um modelo de uso e conferir que não aparece para novos documentos.

**Acceptance Scenarios**:

1. **Given** uma revisão em rascunho, **When** é descartada com motivo, **Then** fica no histórico como descartada e o modelo volta a aceitar nova revisão.
2. **Given** um modelo retirado de uso, **When** alguém cria um documento, **Then** o modelo não é oferecido; documentos existentes continuam com ele.

---

### Edge Cases

- Duas pessoas alterando o mesmo rascunho ao mesmo tempo: a segunda gravação é recusada com aviso para recarregar.
- Revisão que não muda nada em relação à vigente: o envio para aprovação é recusado.
- Revisão com dois tópicos de mesmo rótulo ou numeração repetida: o envio é recusado (docs/contexto/06-casos-de-teste.md, caso 12).
- Aprovador que perde o perfil entre o envio e a aprovação: a aprovação é recusada.
- Vigência futura com outra revisão aprovada antes da data: a mais recente só vale depois da anterior; não há duas versões vigentes ao mesmo tempo.
- Reverter para uma versão antiga: é feito por nova revisão com o conteúdo da versão antiga, nunca reativando a versão antiga.
- Modelo usado em documento assinado: continua consultável para sempre; não pode ser retirado de forma que o documento perca a referência.
- Assinatura da aprovação com senha errada: segue as regras de tentativas e bloqueio da feature 005.

## Requirements *(mandatory)*

### Functional Requirements

**Abrangência**

- **FR-001**: A revisão controlada DEVE valer para os modelos de subdocumento (modelos de formulário) e para os modelos de documento (modelos de layout) do sistema, incluídos os layouts do TAP e do Plano de Negócios; os campos do TAP e do Plano de Negócios continuam os definidos na feature 002.

**Permissões**

- **FR-002**: Só pessoas autenticadas com o perfil Qualidade/AR DEVEM poder abrir, alterar, enviar e descartar revisões de modelos e pedir a retirada de uso; só pessoas com o perfil Gestor de P&D DEVEM poder aprovar ou devolver; as demais pessoas autenticadas com perfil só consultam modelos e histórico.
- **FR-003**: Quem elaborou uma revisão NÃO DEVE aprová-la.
- **FR-004**: Toda tentativa sem permissão DEVE ser negada e registrada na trilha, inclusive por URL direta.

**Ciclo da revisão**

- **FR-005**: A revisão DEVE nascer como rascunho da próxima versão, com o conteúdo da versão vigente, sem alterar a vigente.
- **FR-006**: Cada modelo DEVE ter no máximo uma revisão em andamento (rascunho, enviada ou aprovada aguardando vigência).
- **FR-007**: O envio para aprovação DEVE exigir motivo da revisão e descrição do impacto, e DEVE ser recusado se a revisão não muda nada ou viola as regras do modelo (rótulos únicos, numeração automática sem repetição).
- **FR-008**: Revisão enviada NÃO DEVE ser alterada; a devolução DEVE exigir comentário e voltar a revisão para rascunho.
- **FR-009**: A aprovação DEVE exigir assinatura eletrônica (reautenticação e significado "aprovado") e registrar o resumo do conteúdo aprovado; o envio pela elaboradora é registrado sem assinatura.
- **FR-010**: Na aprovação, DEVE ser definida a vigência: imediata (padrão) ou a partir de uma data futura; só uma versão do modelo é vigente em cada momento.
- **FR-011**: Revisão em rascunho DEVE poder ser descartada com motivo, sem exclusão física.

**Versões publicadas**

- **FR-012**: Versão publicada NÃO DEVE ser alterada; correção só por nova revisão.
- **FR-013**: Documentos já iniciados DEVEM continuar na versão de modelo em que começaram; documentos novos DEVEM usar a versão vigente na data de criação.
- **FR-014**: O conteúdo de cada versão publicada DEVE ter resumo criptográfico, e a verificação de integridade DEVE apontar qualquer alteração posterior.
- **FR-015**: Um modelo DEVE poder ser retirado de uso: a Qualidade/AR pede com motivo e o Gestor de P&D aprova com assinatura eletrônica; retirado, não é oferecido a novos documentos e continua consultável.

**Rastreabilidade**

- **FR-016**: Cada versão DEVE registrar quem elaborou, enviou, devolveu, aprovou e descartou, com data e hora do servidor, motivo, impacto e comentários.
- **FR-017**: Toda alteração de rascunho, envio, devolução, aprovação, publicação, entrada em vigência, descarte e retirada de uso DEVE gerar evento na trilha de auditoria, com valor anterior e novo quando houver.
- **FR-018**: O sistema DEVE comparar quaisquer duas versões de um modelo, mostrando itens incluídos, retirados e alterados.
- **FR-019**: O histórico de cada modelo DEVE listar todas as versões com situação e etapas, e informar quantos e quais documentos foram iniciados em cada versão.

### Key Entities *(include if feature involves data)*

- **Modelo**: identidade do modelo ao longo das versões (tipo: subdocumento ou documento; o que ele modela, ex.: Entrada de Projeto); situação (em uso ou retirado).
- **Versão de modelo**: número da versão, conteúdo, situação (rascunho, enviada, aprovada aguardando vigência, vigente, substituída, descartada), motivo, impacto, vigência, resumo do conteúdo aprovado.
- **Etapa da revisão**: quem, quando, qual etapa (abertura, envio, devolução, aprovação, descarte), comentário.
- **Assinatura de aprovação**: pessoa, significado, data e hora, resumo assinado (feature 005).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, nenhuma pessoa sem o perfil exigido abre, altera, envia, aprova ou descarta revisão, nem pela URL direta.
- **SC-002**: Em 100% dos testes, publicar uma nova versão não altera documentos já iniciados nem a versão anterior.
- **SC-003**: Em 100% dos testes, uma alteração feita direto no banco no conteúdo de versão publicada é apontada pela verificação de integridade.
- **SC-004**: Para cada versão publicada, o histórico mostra elaborador, aprovador, datas, motivo e impacto, e a comparação lista todas as diferenças em relação à versão anterior.
- **SC-005**: Um ciclo completo (abrir revisão, alterar um rótulo, enviar, aprovar e publicar) é concluído em menos de 5 minutos por quem conhece a tela.

## Assumptions

- Os modelos de formulário (004), a assinatura eletrônica (005) e os modelos de layout (006) existem antes desta feature; ela substitui a publicação direta dessas features pela revisão controlada.
- A migração de documentos em andamento para a nova versão continua sendo a da feature 004 (decisão do Gestor de P&D).
- Os modelos criados por features posteriores (modelos de entrada do caderno, 008; textos padrão do dossiê, 011) seguem o mesmo ciclo quando forem especificados.
- Perfis e abrangência definidos nas respostas provisórias do esclarecimento (sessão 2026-11-07).
