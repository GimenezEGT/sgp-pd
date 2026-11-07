# Feature Specification: Revisão, versões e assinatura eletrônica

**Feature Branch**: `005-revisao-assinatura`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Ciclo de revisão, versões e assinatura eletrônica dos subdocumentos, do TAP e do Plano de Negócios. Leia docs/contexto/04-requisitos-regulatorios.md. Objetivo: eliminar a impressão para assinatura. Todo documento tem versão, Analista Responsável (nome/função), Gestor de P&D e data; as assinaturas desses dois papéis passam a ser eletrônicas. Histórias: 1. Como analista, envio um documento em rascunho para revisão; ele fica bloqueado para edição enquanto estiver em revisão. 2. Como Gestor de P&D, aprovo ou devolvo com comentário obrigatório; os comentários ficam no histórico do documento. 3. Para assinar, informo de novo minha senha de rede e escolho o significado (elaborado, revisado, aprovado); a assinatura guarda nome, função, data e hora do servidor e a identificação exata do conteúdo assinado. 4. Documento assinado pelos dois papéis fica "Aprovado" e imutável. Para corrigir, crio nova versão (02, 03...) com motivo; a anterior fica "Substituída" e continua consultável. 5. Como qualquer pessoa autorizada, verifico se um documento foi alterado depois de assinado. 6. Como Gestor de P&D, delego a aprovação a outra pessoa por um período, com motivo registrado. Regras: quem elaborou não aprova o mesmo documento; uma assinatura nunca vale para outra versão; três falhas de senha seguidas bloqueiam a assinatura e geram alerta; a Validação do Produto usa o rótulo "Gestor de P&D responsável pela Aprovação", como no formulário atual. Fora do escopo: certificado ICP-Brasil individual (avaliar depois) e geração do PDF (006), que exibirá as assinaturas."

## Clarifications

### Session 2026-11-07

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: Quais significados de assinatura são aceitos e quais são obrigatórios? → A: Elaborado (obrigatório; Analista Responsável, quem envia para revisão), Aprovado (obrigatório; Gestor de P&D ou delegado) e Revisado (opcional; qualquer pessoa com acesso ao projeto que não seja a elaboradora nem a aprovadora) (ratificar com a Garantia da Qualidade).
- Q: A delegação de aprovação é permitida? Para quem? → A: Sim, provisoriamente: o Gestor de P&D delega, com motivo, por até 30 dias, a pessoa com perfil Gestor de P&D, Líder de projeto ou Qualidade/AR; a assinatura do delegado registra "em delegação de" (ratificar com a Garantia da Qualidade e o PSG 20).
- Q: A Qualidade assina algum documento obrigatoriamente (ex.: Saída)? → A: Não nesta versão; a Qualidade pode assinar "Revisado" em qualquer documento em revisão; Elaborado e Aprovado continuam os únicos obrigatórios (ratificar com a Garantia da Qualidade).
- Q: Qual o prazo máximo de revisão antes do alerta? → A: 5 dias corridos, configurável; o documento aparece como atrasado na fila de revisão e o e-mail vem na feature 010 (ratificar com o Gestor de P&D).
- Q: Por quanto tempo a assinatura fica bloqueada depois de três falhas? → A: 15 minutos, configurável, como o bloqueio de login da feature 001 (ratificar com a TI).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enviar para revisão com a assinatura de quem elaborou (Priority: P1)

O analista responsável envia o documento em rascunho para revisão assinando como "elaborado". Enquanto está em revisão, ninguém edita o documento.

**Why this priority**: É o começo do ciclo que substitui a impressão e a assinatura manual.

**Independent Test**: Enviar um subdocumento completo para revisão com a senha de rede; conferir a assinatura registrada e a recusa de edição.

**Acceptance Scenarios**:

1. **Given** um documento em rascunho completo, **When** o analista o envia informando a senha de rede, **Then** o documento fica "Em revisão" com a assinatura "elaborado" (nome, função, data e hora do servidor, resumo do conteúdo).
2. **Given** um documento incompleto, **When** o analista tenta enviar, **Then** o envio é recusado com o que falta.
3. **Given** um documento em revisão, **When** alguém tenta editá-lo, **Then** a edição é recusada.
4. **Given** a senha errada, **When** o analista tenta assinar, **Then** a assinatura é recusada e a tentativa fica registrada.

---

### User Story 2 - Aprovar com assinatura ou devolver com comentário (Priority: P1)

O Gestor de P&D (ou quem recebeu a delegação) aprova assinando como "aprovado", ou devolve com comentário obrigatório; o documento devolvido volta a ser editável e os comentários ficam no histórico.

**Why this priority**: Fecha o ciclo com valor de registro (RDC 665/2022, arts. 27, 42, 47, 57 e 59).

**Independent Test**: Devolver com comentário, corrigir, reenviar e aprovar; conferir que a assinatura do elaborador da primeira rodada não vale para o conteúdo novo.

**Acceptance Scenarios**:

1. **Given** um documento em revisão, **When** o Gestor o devolve sem comentário, **Then** a devolução é recusada; com comentário, o documento fica "Devolvido" e editável.
2. **Given** um documento devolvido e corrigido, **When** é reenviado, **Then** o elaborador assina de novo, porque a assinatura anterior não vale para outro conteúdo.
3. **Given** um documento em revisão, **When** o Gestor aprova com a senha de rede, **Then** o documento fica "Aprovado" e imutável, com as duas assinaturas.
4. **Given** quem elaborou, **When** tenta aprovar o próprio documento, **Then** o sistema recusa.

---

### User Story 3 - Assinatura com reautenticação e significado (Priority: P1)

Toda assinatura exige a senha de rede e o significado (elaborado, revisado ou aprovado); guarda nome, função, data e hora do servidor e o resumo exato do conteúdo; três falhas seguidas bloqueiam a assinatura por um tempo e geram alerta.

**Why this priority**: Assinatura eletrônica avançada (Lei 14.063/2020, art. 4º): ligada ao signatário, sob seu controle e capaz de revelar alterações.

**Independent Test**: Errar a senha três vezes, conferir o bloqueio e o alerta; depois do tempo, assinar.

**Acceptance Scenarios**:

1. **Given** uma assinatura, **When** é registrada, **Then** guarda pessoa, função, significado, data e hora do servidor e o resumo do conteúdo da versão.
2. **Given** três falhas de senha seguidas, **When** a pessoa tenta assinar de novo, **Then** a assinatura fica bloqueada pelo tempo configurado e o bloqueio vai para a trilha como alerta.
3. **Given** uma pessoa autorizada que não é elaboradora nem aprovadora, **When** assina como "revisado" um documento em revisão, **Then** a assinatura fica registrada sem mudar a situação do documento.

---

### User Story 4 - Versões: aprovado imutável, nova versão com motivo (Priority: P1)

Documento aprovado não muda. Para corrigir, cria-se a versão seguinte (02, 03...) com motivo; a versão anterior fica "Substituída" quando a nova for aprovada e continua consultável com suas assinaturas.

**Why this priority**: Nada é apagado e a versão assinada é imutável (princípios I e III).

**Independent Test**: Aprovar a versão 01, criar a 02 com motivo, aprovar a 02 e consultar a 01.

**Acceptance Scenarios**:

1. **Given** um documento aprovado, **When** alguém tenta editá-lo, **Then** a edição é recusada.
2. **Given** um documento aprovado, **When** o analista cria nova versão sem motivo, **Then** é recusado; com motivo, nasce a versão 02 em rascunho com o conteúdo da 01.
3. **Given** a versão 02 aprovada, **When** a 01 é consultada, **Then** aparece como "Substituída", com o conteúdo e as assinaturas dela.

---

### User Story 5 - Verificar se o documento foi alterado depois de assinado (Priority: P2)

Qualquer pessoa que acessa o documento pede a verificação de integridade: o sistema recalcula o resumo de cada versão aprovada e confere com as assinaturas e com o conteúdo atual.

**Why this priority**: Prova de que o registro assinado não foi adulterado.

**Independent Test**: Alterar direto no banco o conteúdo guardado de uma versão aprovada e conferir que a verificação aponta a divergência.

**Acceptance Scenarios**:

1. **Given** um documento aprovado sem alteração, **When** a verificação roda, **Then** o resultado é íntegro.
2. **Given** o conteúdo de uma versão aprovada alterado fora do sistema, **When** a verificação roda, **Then** a divergência é apontada e registrada.

---

### User Story 6 - Delegação da aprovação (Priority: P3)

O Gestor de P&D delega a aprovação a outra pessoa por um período, com motivo; o delegado aprova como "em delegação de" e a delegação pode ser encerrada antes do fim.

**Why this priority**: Evita que documentos parem na ausência do Gestor.

**Independent Test**: Criar delegação de uma semana, aprovar como delegado e conferir o registro da delegação na assinatura.

**Acceptance Scenarios**:

1. **Given** uma delegação vigente, **When** o delegado aprova, **Then** a assinatura registra a delegação e o Gestor que delegou.
2. **Given** delegação vencida ou encerrada, **When** o delegado tenta aprovar, **Then** é recusado.
3. **Given** uma delegação, **When** é criada sem motivo ou para quem não tem perfil elegível, **Then** é recusada.

---

### Edge Cases

- TAP e Plano de Negócios: a submissão do projeto exige a assinatura "elaborado" do líder em cada um, e a aprovação do projeto exige a assinatura "aprovado" do Gestor em cada um; devolver o projeto devolve os dois.
- Documento em revisão parado além do prazo configurado: aparece como atrasado na fila de revisão do Gestor.
- Diretório da rede indisponível na assinatura: a assinatura é recusada sem contar como falha de senha.
- Assinatura em versão já aprovada ou substituída: recusada.
- Versão nova criada enquanto outra está em revisão: recusada.
- Delegado que é o elaborador do documento: não aprova esse documento.
- A aprovação bloqueia as versões dos cadastros referenciados, como já fazia a aprovação provisória da 004.

## Requirements *(mandatory)*

### Functional Requirements

**Ciclo do documento**

- **FR-001**: Subdocumentos, TAP e Plano de Negócios DEVEM seguir as situações Rascunho, Em revisão, Devolvido e Aprovado; a versão aprovada anterior fica Substituída quando a seguinte é aprovada.
- **FR-002**: O envio para revisão DEVE exigir o documento completo e a assinatura "elaborado" de quem envia; documento em revisão ou aprovado NÃO DEVE ser editado.
- **FR-003**: Só o Gestor de P&D ou quem tem delegação vigente DEVE aprovar ou devolver; a devolução DEVE exigir comentário, que fica no histórico, e torna o documento editável.
- **FR-004**: A aprovação DEVE exigir a assinatura "aprovado" sobre o mesmo conteúdo da assinatura "elaborado"; quem elaborou NÃO DEVE aprovar o mesmo documento.
- **FR-005**: Documento aprovado DEVE ser imutável; correção só por nova versão (02, 03...) com motivo obrigatório, criada a partir do conteúdo aprovado; a anterior continua consultável com suas assinaturas.

**Assinatura**

- **FR-006**: Toda assinatura DEVE exigir reautenticação com a senha de rede (sem guardar a senha) e o significado (Elaborado, Revisado ou Aprovado), e DEVE guardar pessoa, função, significado, data e hora do servidor, versão do documento e resumo criptográfico do conteúdo assinado.
- **FR-007**: Uma assinatura NÃO DEVE valer para outra versão nem para outro conteúdo: alteração depois da assinatura exige assinar de novo.
- **FR-008**: Três falhas de senha seguidas DEVEM bloquear a assinatura da pessoa pelo tempo configurado (padrão 15 minutos) e gerar alerta na trilha; indisponibilidade do diretório não conta como falha.
- **FR-009**: Pessoa com acesso ao projeto que não é elaboradora nem aprovadora DEVE poder assinar "revisado" um documento em revisão, sem mudar a situação.

**Integridade**

- **FR-010**: O conteúdo de cada versão aprovada DEVE ser guardado de forma imutável (sem alteração pelo papel da aplicação no banco), com o resumo calculado sobre uma representação canônica do conteúdo e dos resumos dos anexos.
- **FR-011**: A verificação de integridade DEVE recalcular o resumo de cada versão aprovada, conferir com as assinaturas e com o conteúdo atual do documento aprovado, apontar divergências e registrar o resultado na trilha.

**TAP e Plano de Negócios**

- **FR-012**: A submissão do projeto DEVE exigir a assinatura "elaborado" do líder no TAP e no Plano de Negócios; a aprovação do projeto DEVE exigir a assinatura "aprovado" do Gestor de P&D (ou delegado) nos dois, substituindo a confirmação registrada da feature 002.

**Delegação e prazos**

- **FR-013**: O Gestor de P&D DEVE poder delegar a aprovação, com motivo e por até 30 dias, a pessoa com perfil Gestor de P&D, Líder de projeto ou Qualidade/AR, e encerrá-la antes do fim; a assinatura do delegado registra a delegação.
- **FR-014**: Documento em revisão há mais que o prazo configurado (padrão 5 dias corridos) DEVE aparecer como atrasado na fila de revisão do Gestor de P&D.
- **FR-015**: Na Validação do Produto, o bloco de assinatura DEVE usar o rótulo "Gestor de P&D responsável pela Aprovação:".
- **FR-016**: Envio, assinatura, falha e bloqueio de assinatura, devolução, aprovação, nova versão, delegação e verificação de integridade DEVEM gerar eventos na trilha.

### Key Entities *(include if feature involves data)*

- **Versão aprovada**: documento, número da versão, conteúdo canônico congelado, resumo, data de aprovação, situação (aprovada ou substituída).
- **Assinatura**: documento, versão, resumo do conteúdo assinado, pessoa, função, significado, data e hora, delegação (quando houver).
- **Tentativa de assinatura**: pessoa, resultado, data e hora (para o bloqueio).
- **Delegação de aprovação**: quem delega, delegado, período, motivo, encerramento.
- **Comentário de revisão**: documento, versão, autor, texto, data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, alterar no banco o conteúdo de uma versão aprovada é apontado pela verificação de integridade.
- **SC-002**: Em 100% dos testes, o elaborador não consegue aprovar o próprio documento.
- **SC-003**: Em 100% dos testes, a versão substituída continua consultável com conteúdo e assinaturas.
- **SC-004**: Em 100% dos testes, a terceira falha de senha seguida bloqueia a assinatura e gera alerta.
- **SC-005**: A verificação de integridade de um documento com 10 versões termina em menos de 2 segundos.

## Assumptions

- A reautenticação usa o mesmo diretório da rede do login (feature 001).
- A geração do PDF com as assinaturas e o selo é da feature 006.
- Significados, delegação, assinatura da Qualidade, prazo de revisão e tempo de bloqueio definidos nas respostas provisórias do esclarecimento (sessão 2026-11-07).
