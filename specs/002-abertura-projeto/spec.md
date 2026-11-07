# Feature Specification: Abertura de projeto — TAP e Plano de Negócios

**Feature Branch**: `002-abertura-projeto`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Abertura de projeto com Termo de Abertura de Projeto (TAP) e Plano de Negócios. Leia docs/contexto/02-dicionario-documentos.md, seções TAP e Plano de Negócios. Objetivo: o líder abre um projeto de produto para diagnóstico in vitro pelo sistema, em vez de documentos avulsos; o Gestor de P&D aprova; a partir daí o projeto aceita subdocumentos. Histórias: 1. Como líder de projeto, crio um projeto em rascunho informando o produto: nome, família (quando houver), tecnologia (ex.: bioquímica, imunologia, biologia molecular), órgão regulador (ANVISA ou MAPA), classe de risco prevista e regra de classificação. 2. Preencho o TAP: justificativa, objetivo, escopo incluído e excluído, entregas, premissas, restrições, riscos iniciais, partes interessadas, equipe com papéis e marcos planejados por subdocumento. 3. Preencho o Plano de Negócios: nome do projeto, data, líder, objetivo, descrição geral, custo total do projeto, prazo de execução, mercado-alvo e retorno esperado ano a ano por 5 anos. Incluo a viabilidade financeira (concorrentes, preço por teste dos concorrentes, apresentações dos concorrentes, custo máximo de produção, preço de venda previsto, venda anual prevista) e a viabilidade produtiva (estrutura fabril, equipe de produção, controle de qualidade). 4. Submeto para aprovação; o Gestor de P&D aprova ou devolve com comentário obrigatório. Na aprovação, o projeto recebe código único, fica "Aberto" na versão 01 e a equipe ganha acesso. 5. Como Gestor de P&D, vejo a lista de projetos com filtros por status, líder e produto. Regras: dados financeiros só aparecem para Gestor de P&D, líder do projeto e perfis autorizados; o retorno total em 5 anos é a soma das previsões anuais; cada marco tem data planejada e, depois, data realizada; toda edição vai para a trilha de auditoria. Fora do escopo: subdocumentos técnicos (004) e assinatura eletrônica (005). Nesta feature a aprovação é uma confirmação registrada na auditoria; a 005 a substitui por assinatura."

## Clarifications

### Session 2026-11-07

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo Gestor de P&D antes do uso oficial.

- Q: Quais campos o TAP deve ter, já que o pedido original não os lista? → A: Os da proposta de `docs/contexto/02-dicionario-documentos.md`: produto (nome, família, tecnologia, órgão regulador, classe de risco e regra), justificativa, objetivo, escopo incluído e excluído, entregas, premissas, restrições, riscos iniciais (risco, impacto, resposta), partes interessadas (nome/área, interesse), equipe (pessoa, papel) e marcos (subdocumento, data prevista, data realizada); código gerado na aprovação (ratificar com o Gestor de P&D).
- Q: Qual é o formato do código do projeto? → A: PD-AAAA-NNN, com o ano da aprovação e sequência de 3 dígitos que recomeça a cada ano (ex.: PD-2026-001), configurável no prefixo (ratificar com o Gestor de P&D).
- Q: O "retorno esperado" é receita, margem ou lucro, e precisa de indicador como payback? → A: Receita líquida prevista de cada ano, em R$, com o total calculado; nenhum indicador adicional (payback) nesta versão (ratificar com o Gestor de P&D).
- Q: Projetos acima de certo custo exigem aprovação da diretoria? → A: Não nesta versão; o Gestor de P&D aprova todos os projetos, e uma alçada por custo vira nova feature se for exigida (ratificar com o Gestor de P&D).
- Q: Quem além do Gestor de P&D e do líder do projeto vê os dados financeiros? → A: Ninguém por padrão; a lista de perfis autorizados é uma configuração da implantação (ratificar com o Gestor de P&D).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar o projeto em rascunho com os dados do produto (Priority: P1)

O líder de projeto cria um projeto em rascunho informando o nome do projeto e o produto: nome, família (quando houver), tecnologia, órgão regulador (ANVISA ou MAPA), classe de risco prevista e regra de classificação. O regime (notificação ou registro) é deduzido da classe de risco. O rascunho só é visto pelo líder e pelos perfis com acesso a todos os projetos.

**Why this priority**: Sem o projeto não existem TAP, Plano de Negócios nem, nas features seguintes, subdocumentos.

**Independent Test**: Criar um projeto como líder, conferir os dados, o regime deduzido e o evento na trilha; outra pessoa sem acesso global não consegue abrir o rascunho.

**Acceptance Scenarios**:

1. **Given** uma pessoa com perfil Líder de projeto, **When** cria um projeto com os dados do produto, **Then** o projeto fica em "Rascunho", sem código, com ela como líder, e a criação vai para a trilha.
2. **Given** um projeto ANVISA de classe II, **When** é salvo, **Then** o regime exibido é "Notificação"; para classes III e IV, "Registro".
3. **Given** um projeto MAPA, **When** é salvo, **Then** a classe de risco da RDC 830/2023 não é exigida.
4. **Given** um rascunho, **When** um Analista que não tem acesso global tenta abri-lo, **Then** o acesso é negado e registrado.
5. **Given** uma pessoa sem os perfis Líder de projeto ou Gestor de P&D, **When** tenta criar projeto, **Then** o acesso é negado.

---

### User Story 2 - Preencher o TAP (Priority: P1)

O líder preenche o Termo de Abertura de Projeto: justificativa, objetivo, escopo incluído e excluído, entregas, premissas, restrições, riscos iniciais (risco, impacto, resposta), partes interessadas (nome/área, interesse), equipe com papéis e marcos planejados por subdocumento.

**Why this priority**: O TAP é o planejamento exigido pela RDC 665/2022 (art. 44) e a base da aprovação.

**Independent Test**: Preencher o TAP de um rascunho, incluir dois membros e três marcos, e conferir que cada edição gera evento com valor anterior e novo.

**Acceptance Scenarios**:

1. **Given** um rascunho, **When** o líder salva o TAP, **Then** os campos ficam gravados e a trilha registra os campos alterados com valor anterior e novo.
2. **Given** a equipe do TAP, **When** o líder inclui uma pessoa com papel no projeto, **Then** a pessoa aparece na equipe com início de vigência; ela só ganha acesso ao projeto depois da aprovação.
3. **Given** um marco planejado, **When** o líder o registra, **Then** o marco tem subdocumento e data planejada; a data realizada fica em branco até ser informada.
4. **Given** um projeto submetido, **When** alguém tenta editar o TAP, **Then** a edição é recusada até o projeto ser devolvido.

---

### User Story 3 - Preencher o Plano de Negócios com dados financeiros protegidos (Priority: P1)

O líder preenche o Plano de Negócios: data, objetivo, descrição geral, custo total do projeto, prazo de execução, mercado-alvo, retorno esperado de cada um dos 5 anos (o total é calculado), viabilidade financeira (principais concorrentes, preço por teste dos concorrentes, apresentações dos concorrentes, custo máximo de produção, preço de venda previsto, venda anual prevista) e viabilidade produtiva (estrutura fabril, equipe de produção, controle de qualidade). O nome do projeto e o líder vêm do próprio projeto. Os dados financeiros só aparecem para o Gestor de P&D, o líder do projeto e os perfis autorizados.

**Why this priority**: O Plano de Negócios é a justificativa econômica que o Gestor aprova; o vazamento de custos e projeções causa dano comercial.

**Independent Test**: Preencher o plano como líder; abrir o projeto como membro sem permissão e como Qualidade: custos e retornos não aparecem na tela, na página de edição nem na trilha de auditoria.

**Acceptance Scenarios**:

1. **Given** cinco previsões anuais, **When** o plano é salvo, **Then** o retorno total exibido é a soma das cinco, e não existe campo para digitar o total.
2. **Given** valores digitados no padrão brasileiro (1.234.567,89), **When** o plano é salvo, **Then** os valores ficam com 2 casas decimais e são exibidos como R$ 1.234.567,89.
3. **Given** uma pessoa sem permissão financeira com acesso ao projeto, **When** abre o projeto, **Then** vê os dados não financeiros e, no lugar dos financeiros, a indicação de conteúdo restrito.
4. **Given** essa mesma pessoa, **When** abre a página de edição do plano pela URL direta, **Then** o acesso é negado e registrado.
5. **Given** um auditor da Qualidade sem permissão financeira, **When** consulta ou exporta a trilha, **Then** os valores financeiros dos eventos do plano aparecem como restritos.

---

### User Story 4 - Submeter, aprovar ou devolver (Priority: P1)

O líder submete o projeto completo para aprovação. O Gestor de P&D aprova ou devolve com comentário obrigatório. Na aprovação, o projeto recebe código único, fica "Aberto" na versão 01 e a equipe ganha acesso. Os comentários e decisões ficam no histórico do projeto.

**Why this priority**: É o momento em que o projeto passa a existir oficialmente e a aceitar subdocumentos.

**Independent Test**: Submeter um projeto completo, devolvê-lo com comentário, corrigir, submeter de novo e aprovar, conferindo código, versão, acesso da equipe, histórico e eventos.

**Acceptance Scenarios**:

1. **Given** um rascunho incompleto, **When** o líder tenta submeter, **Then** o sistema recusa e lista as pendências.
2. **Given** um rascunho completo, **When** o líder submete, **Then** o projeto fica "Submetido" e bloqueado para edição.
3. **Given** um projeto submetido, **When** o Gestor de P&D devolve sem comentário, **Then** a devolução é recusada; com comentário, o projeto fica "Devolvido" e editável pelo líder.
4. **Given** um projeto submetido, **When** o Gestor de P&D aprova, **Then** o projeto recebe código no formato definido, fica "Aberto" na versão 01, os membros com vigência ativa passam a acessá-lo e a aprovação vai para a trilha.
5. **Given** que o líder também tem o perfil Gestor de P&D, **When** tenta aprovar o próprio projeto, **Then** a aprovação é recusada.
6. **Given** duas aprovações de projetos diferentes ao mesmo tempo, **When** concluem, **Then** recebem códigos diferentes, sem lacuna nem repetição.

---

### User Story 5 - Lista de projetos com filtros (Priority: P2)

O Gestor de P&D vê a lista de projetos com filtros por status, líder e produto. Cada pessoa vê na lista só os projetos a que tem acesso.

**Why this priority**: Dá visibilidade à carteira; depende de projetos existirem.

**Independent Test**: Com projetos em vários status e líderes, filtrar por cada critério; uma pessoa sem acesso global vê só os seus projetos.

**Acceptance Scenarios**:

1. **Given** projetos em vários status, **When** o Gestor filtra por status, **Then** vê só os projetos daquele status.
2. **Given** projetos de líderes diferentes, **When** filtra por líder, **Then** vê só os daquele líder.
3. **Given** um texto de produto, **When** filtra por produto, **Then** vê os projetos cujo nome de produto ou família contém o texto.
4. **Given** um Analista membro de um projeto aberto, **When** abre a lista, **Then** vê só os projetos de que é membro.
5. **Given** uma pessoa sem permissão financeira, **When** abre a lista, **Then** a coluna de custo não aparece.

---

### Edge Cases

- Retorno anual em branco: o total considera só os anos preenchidos e a submissão exige os cinco anos.
- Valor monetário negativo ou com mais de 2 casas decimais: recusado com mensagem clara.
- Faixa de preço com mínimo maior que o máximo: recusada.
- Membro removido da equipe: a vigência é encerrada com motivo; o registro continua no histórico e a pessoa perde o acesso.
- Marco removido no planejamento: o marco é cancelado com motivo, sem exclusão, e deixa de aparecer como pendente.
- Data realizada anterior à criação do projeto ou no futuro: recusada.
- Projeto devolvido várias vezes: cada devolução e cada submissão ficam no histórico, em ordem.
- Líder deixa de ter o perfil Líder de projeto: o projeto continua com ele como líder; a troca de líder fica para feature futura e não é oferecida aqui.
- Duas pessoas editando o mesmo plano: a segunda gravação sobre dados desatualizados é recusada com aviso para recarregar.

## Requirements *(mandatory)*

### Functional Requirements

**Projeto e produto**

- **FR-001**: Pessoas com perfil Líder de projeto ou Gestor de P&D DEVEM poder criar projeto em rascunho com nome do projeto, nome do produto, família (opcional), tecnologia (lista controlada), órgão regulador (ANVISA ou MAPA), classe de risco prevista (I a IV) e regra de classificação; quem cria com perfil Líder de projeto fica como líder.
- **FR-002**: O regime DEVE ser deduzido da classe de risco: Notificação para as classes I e II e Registro para as classes III e IV; a classe e a regra só são exigidas em projetos ANVISA.
- **FR-003**: O rascunho, o submetido e o devolvido DEVEM ser visíveis só para o líder e para os perfis com acesso a todos os projetos (Gestor de P&D, Qualidade/AR e Administrador).

**TAP**

- **FR-004**: O líder DEVE poder preencher o TAP com justificativa, objetivo, escopo incluído, escopo excluído, entregas, premissas, restrições (listas), riscos iniciais (risco, impacto, resposta) e partes interessadas (nome/área, interesse).
- **FR-005**: O líder DEVE poder montar a equipe com pessoa, papel no projeto e vigência; remover alguém encerra a vigência com motivo, sem apagar o registro.
- **FR-006**: O líder DEVE poder registrar marcos com subdocumento (lista controlada dos subdocumentos do PSG 20) e data planejada, e depois informar a data realizada; marcos não são apagados, só cancelados com motivo.

**Plano de Negócios**

- **FR-007**: O líder DEVE poder preencher o Plano de Negócios com data, objetivo, descrição geral, custo total, prazo de execução (em meses e/ou data de término), mercado-alvo, retorno esperado (receita líquida prevista, em R$) de cada um dos 5 anos, viabilidade financeira (principais concorrentes, faixa de preço por teste dos concorrentes, principais apresentações dos concorrentes, custo máximo de produção considerando matéria-prima, faixa de preço de venda prevista, venda anual prevista em testes por ano) e viabilidade produtiva (estrutura fabril, equipe de produção, controle de qualidade); nome do projeto e líder DEVEM vir do projeto, sem redigitação.
- **FR-008**: O retorno total em 5 anos DEVE ser calculado como a soma das previsões anuais e NÃO DEVE ser digitável.
- **FR-009**: Valores monetários DEVEM ter 2 casas decimais, aceitar e exibir o formato brasileiro (R$ 1.234.567,89) e recusar valores negativos.
- **FR-010**: Custo total, previsões anuais e total, preço dos concorrentes, custo máximo de produção, preço de venda previsto e venda anual prevista são dados financeiros: DEVEM aparecer só para o Gestor de P&D, o líder do projeto e os perfis autorizados por configuração (nenhum por padrão), em telas, listas, exportações e na trilha de auditoria; para os demais aparecem como restritos. "Líder" é o líder atual do projeto; Administrador e Qualidade/AR acessam o projeto, mas não os dados financeiros, salvo configuração.

**Fluxo de aprovação**

- **FR-011**: O projeto DEVE seguir a máquina de estados Rascunho → Submetido → (Aberto | Devolvido), com Devolvido → Submetido; transições fora dessa ordem DEVEM ser recusadas.
- **FR-012**: Só o líder DEVE submeter, e a submissão DEVE ser recusada enquanto houver pendências (campos obrigatórios do produto, do TAP e do Plano de Negócios, ao menos um marco e um item de escopo e de entrega), listadas ao líder.
- **FR-013**: Projeto submetido DEVE ficar bloqueado para edição até ser devolvido.
- **FR-014**: Só o Gestor de P&D DEVE aprovar ou devolver, qualquer que seja o custo do projeto; a devolução DEVE exigir comentário; o líder do projeto NÃO DEVE aprovar o próprio projeto.
- **FR-015**: Na aprovação, o projeto DEVE receber código único no formato PD-AAAA-NNN (ano da aprovação e sequência anual), ficar "Aberto" na versão 01, e os membros com vigência ativa DEVEM passar a acessá-lo; aprovações simultâneas NÃO DEVEM gerar códigos repetidos.
- **FR-016**: Cada submissão, devolução e aprovação DEVE ficar no histórico do projeto com autor, data e hora e comentário, e na trilha de auditoria.
- **FR-017**: Depois de aberto, o TAP e o Plano de Negócios DEVEM ficar bloqueados; a equipe e as datas realizadas dos marcos continuam editáveis pelo líder, com registro na trilha.

**Lista e rastreabilidade**

- **FR-018**: O sistema DEVE listar os projetos com filtros por status, líder e produto (nome ou família), mostrando a cada pessoa só os projetos a que tem acesso.
- **FR-019**: Toda criação e edição de projeto, TAP, Plano de Negócios, equipe e marcos DEVE gerar evento na trilha com o projeto, os campos alterados, valor anterior e novo.
- **FR-020**: A gravação de TAP ou Plano de Negócios a partir de dados desatualizados (outra pessoa gravou antes) DEVE ser recusada com aviso.

### Key Entities *(include if feature involves data)*

- **Projeto**: nome, produto (nome, família, tecnologia, órgão regulador, classe de risco, regra), regime deduzido, líder, situação, código (na aprovação), versão, datas de criação, submissão e aprovação.
- **Termo de Abertura (TAP)**: justificativa, objetivo, listas de escopo incluído e excluído, entregas, premissas e restrições, tabela de riscos iniciais e de partes interessadas.
- **Plano de Negócios**: data, objetivo, descrição, custo total, prazo, mercado-alvo, viabilidade financeira e produtiva.
- **Previsão anual**: ano (1 a 5) e valor do retorno esperado.
- **Membro do projeto**: pessoa, papel no projeto, vigência (início e fim) e motivo do encerramento.
- **Marco**: subdocumento, descrição, data planejada, data realizada, cancelamento com motivo.
- **Decisão do projeto**: submissão, devolução ou aprovação, com autor, data e hora e comentário.
- **Tecnologia e tipo de subdocumento**: listas controladas, mantidas como dados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um projeto é aberto de ponta a ponta (criação, TAP, Plano de Negócios, submissão e aprovação) sem documentos fora do sistema.
- **SC-002**: Em 100% dos testes, pessoa sem permissão financeira não vê custo, retornos nem preços em telas, listas, exportações, trilha ou URL direta.
- **SC-003**: Em 100% das execuções de aprovações simultâneas de teste, os códigos gerados são distintos e consecutivos no ano.
- **SC-004**: 100% das edições de projeto, TAP, Plano de Negócios, equipe e marcos têm evento na trilha com valor anterior e novo.
- **SC-005**: A lista com 200 projetos abre e filtra em menos de 2 segundos.

## Assumptions

- Projetos legados não são migrados nesta feature (premissa do plano: entram como anexos somente leitura em fase posterior).
- A lista de tecnologias e a de tipos de subdocumento nascem com os valores de `docs/contexto/05-vocabularios.md` e `02-dicionario-documentos.md` e ficam como dados configuráveis.
- Projetos MAPA (uso veterinário) não seguem a classificação de risco da RDC 830/2023.
- A aprovação desta feature é uma confirmação registrada na trilha; a feature 005 a substitui por assinatura eletrônica.
- Textos longos são texto simples com quebras de linha; o editor de texto rico chega na feature 008.
- Os documentos gerados nas features 006 e 009 seguirão a mesma regra de visibilidade dos dados financeiros (dependência registrada para essas features).
