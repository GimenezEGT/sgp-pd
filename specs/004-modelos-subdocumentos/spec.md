# Feature Specification: Modelos de formulário versionados e subdocumentos

**Feature Branch**: `004-modelos-subdocumentos`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Modelos de formulário versionados e preenchimento dos subdocumentos do projeto. Leia docs/contexto/02-dicionario-documentos.md (todos os subdocumentos), 03-padroes-formatacao.md e 05-vocabularios.md. Problema: os formulários do PSG 20 mudam de versão ("Formulário Versão: 05") e cada aba da planilha Capas Projeto tem tópicos próprios. O sistema precisa refletir isso sem programação a cada mudança. Histórias: 1. Como Garantia da Qualidade, cadastro um modelo de formulário: tipo de subdocumento, versão do formulário, referência (ex.: "PSG 20 - Pesquisa e Desenvolvimento de Produtos"), vigência, título da capa, tópicos numerados da lista "ESTE RELATÓRIO DEVE CONTER" e, para cada tópico, os campos: texto formatado, lista, tabela com colunas definidas, seleção de vocabulário, referência a cadastro, anexo e "não aplicável" com justificativa. 2. Publico uma nova versão do modelo; documentos já iniciados continuam no modelo em que começaram, a menos que o gestor migre o documento. 3. Como analista, crio num projeto aberto os subdocumentos: Entrada de Projeto, Elaboração de Formulação, Elaboração de Lote Piloto, RAPD, Análise Crítica, Validação do Produto, Verificação Final de Validação, Saída de Projeto e, quando necessário, Alteração de Projeto. 4. Na Entrada de Projeto preencho os 13 tópicos e a parte estruturada do formulário opcional (amostras, funcionalidade, classificação, automação, usuário, armazenamento, filtros, classificação de uso) e marco "aplica / não se aplica" em cada requisito de desempenho. 5. A Verificação Final de Validação é montada pelo sistema: uma linha por tópico da Entrada, com "Previsto" vindo da Entrada aprovada, "Realizado" preenchido pelo analista e "Disposição" (aprovado, reprovado ou outros, com justificativa). 6. Na Saída de Projeto escolho os setores que recebem a transferência (Produção, Supply Chain, Controle de Qualidade, SAC, Comercial, Marketing, S&OP); os itens marcados "MAPA" só aparecem em projetos com esse órgão. 7. A Alteração de Projeto registra versão alterada e nova versão, justificativa, requisitos de entrada afetados e outros dados; quando aprovada, a versão do projeto sobe e os subdocumentos afetados ficam marcados para revisão. Regras: "não aplicável" exige justificativa e bloqueia a lista daquele tópico; a numeração de tópicos e tabelas é automática; requisitos marcados "aplica" na Entrada geram pendências na Validação; o sistema avisa quando a ordem do fluxo não foi seguida (ex.: Lote Piloto antes da Formulação aprovada) e só segue com autorização do gestor. Fora do escopo: assinatura (005), geração de DOCX/PDF (006) e cálculos estatísticos (007)."

## Clarifications

### Session 2026-11-07

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: A ordem dos subdocumentos é obrigatória ou só recomendada? → A: Recomendada: criar um subdocumento com o antecessor ainda não aprovado mostra aviso e só segue com autorização registrada do Gestor de P&D, com motivo (ratificar com o Gestor de P&D).
- Q: O tópico 9 da Entrada, que repete o rótulo do tópico 6 ("Classificação de Uso"), é a classe de risco da RDC 830/2023? → A: Sim; no modelo versão 05 do sistema o tópico 9 passa a se chamar "Classificação de Risco (RDC 830/2023)", com a classe (I a IV) e a regra de classificação; a linha 9 da Verificação Final acompanha (ratificar com Assuntos Regulatórios e a Garantia da Qualidade).
- Q: Na Análise Crítica, vale a lista da capa (3 tópicos) ou a do projeto (4)? → A: O modelo versão 05 segue a capa, com 3 tópicos; um quarto tópico só entra por nova versão do modelo publicada pela Qualidade (ratificar com a Garantia da Qualidade).
- Q: O "Realizado" da Verificação Final é pré-preenchido? → A: Não nesta versão: o analista preenche cada linha e a tela mostra, ao lado, o acesso à Validação e à Saída do projeto; a regra de correspondência para o pré-preenchimento fica pendente de definição pela Qualidade (pendência a esclarecer).
- Q: Como tratar a edição simultânea do mesmo documento por dois analistas? → A: Controle otimista: os dois podem abrir; a segunda gravação feita sobre a versão desatualizada é recusada com aviso para recarregar, sem bloqueio exclusivo (ratificar com o Gestor de P&D).

Decisão de estrutura: a capa atual da Saída numera dois itens como "11"; com a numeração automática, a Saída versão 05 do sistema tem os itens 1 a 12.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar o modelo de formulário (Priority: P1)

A Garantia da Qualidade cadastra um modelo de formulário: tipo de subdocumento, versão do formulário, referência, início de vigência, título da capa, tópicos da lista "ESTE RELATÓRIO DEVE CONTER" (rótulo da capa e, quando diferente, rótulo do corpo) e, para cada tópico, os campos com seus tipos e se o tópico aceita "não aplicável". O sistema valida a definição antes de publicar.

**Why this priority**: Sem modelos não há subdocumento; mudar o formulário passa a ser cadastro, não programação (princípio IV).

**Independent Test**: Cadastrar um modelo com tópicos de vários tipos de campo, publicá-lo e conferir a numeração automática, a recusa de rótulos repetidos e a capa resultante.

**Acceptance Scenarios**:

1. **Given** a Qualidade, **When** cadastra um modelo com tipo, versão, referência, vigência, título e tópicos, **Then** o modelo fica em rascunho e pode ser conferido antes da publicação.
2. **Given** dois tópicos com o mesmo rótulo ou um campo de tipo desconhecido, **When** a Qualidade publica, **Then** a publicação é recusada com a explicação.
3. **Given** um modelo publicado, **When** é exibido, **Then** os tópicos aparecem numerados pela ordem (1, 2, 3...), sem número digitado.
4. **Given** uma pessoa sem o perfil Qualidade/AR, **When** tenta cadastrar ou publicar modelo, **Then** o acesso é negado e registrado.

---

### User Story 2 - Nova versão do modelo sem alterar documentos iniciados (Priority: P1)

A Qualidade publica a versão seguinte de um modelo. Documentos já iniciados continuam na versão em que começaram; documentos novos usam a versão vigente. O Gestor de P&D pode migrar um documento em rascunho para a versão vigente, com motivo, sem perder dados.

**Why this priority**: Sem isso, mudar o formulário alteraria documentos em andamento (princípios I e IV).

**Independent Test**: Com um documento em rascunho na versão 05, publicar a 06; conferir que o documento continua na 05, que um documento novo nasce na 06 e que a migração pelo gestor mantém os dados.

**Acceptance Scenarios**:

1. **Given** um documento iniciado na versão 05, **When** a versão 06 é publicada, **Then** o documento continua na 05 e mostra os tópicos dela.
2. **Given** a versão 06 vigente, **When** alguém cria um documento do mesmo tipo, **Then** ele nasce na 06.
3. **Given** um modelo publicado, **When** alguém tenta alterá-lo, **Then** a alteração é recusada; mudança só por nova versão.
4. **Given** um documento em rascunho na 05, **When** o Gestor de P&D o migra para a 06 com motivo, **Then** os dados dos tópicos que existem nas duas versões são mantidos, o que não couber fica guardado e visível no documento, e a migração vai para a trilha.

---

### User Story 3 - Criar e preencher os subdocumentos do projeto (Priority: P1)

Num projeto aberto, a equipe cria os subdocumentos (Entrada de Projeto, Elaboração de Formulação, Elaboração de Lote Piloto, RAPD, Análise Crítica, Validação do Produto, Verificação Final de Validação, Saída de Projeto e, quando necessário, Alteração de Projeto) e os preenche num formulário montado a partir do modelo usado, com referências aos cadastros e anexos.

**Why this priority**: É o trabalho diário do analista; substitui o Word.

**Independent Test**: Criar a Elaboração de Formulação num projeto aberto, preencher tabela com insumos do cadastro, anexar arquivo, salvar e conferir a trilha e a numeração das tabelas.

**Acceptance Scenarios**:

1. **Given** um projeto aberto, **When** um membro da equipe cria um subdocumento, **Then** ele nasce em rascunho, na versão 01, com a versão vigente do modelo do tipo.
2. **Given** o formulário do subdocumento, **When** a pessoa preenche e salva, **Then** os dados são conferidos contra o modelo, o rascunho pode ficar incompleto e cada mudança vai para a trilha com valor anterior e novo.
3. **Given** um tópico marcado "não aplicável", **When** a pessoa salva sem justificativa ou com campos do tópico preenchidos, **Then** a gravação é recusada.
4. **Given** um subdocumento com tabelas em vários tópicos, **When** é exibido, **Then** as tabelas aparecem numeradas em sequência ("Tabela 01", "Tabela 02"...).
5. **Given** dois analistas editando o mesmo subdocumento, **When** o segundo grava depois do primeiro, **Then** a gravação do segundo é recusada com aviso para recarregar.
6. **Given** uma pessoa sem acesso ao projeto, **When** tenta ver ou editar subdocumentos dele, **Then** o acesso é negado e registrado.

---

### User Story 4 - Entrada de Projeto com o formulário opcional (Priority: P1)

Na Entrada de Projeto, o analista preenche os 13 tópicos, a parte estruturada do formulário opcional (analito, amostras, funcionalidade, classificação do teste, automação, usuário, armazenamento, filtros, classificação de uso) e marca "aplica / não se aplica" em cada um dos 16 requisitos de desempenho, justificando os que não se aplicam.

**Why this priority**: A Entrada é o dado de entrada aprovado (RDC 665/2022, art. 46) que alimenta Validação, Verificação Final e dossiê.

**Independent Test**: Preencher a Entrada com seleções das listas controladas, marcar requisitos e conferir que "não se aplica" sem justificativa é recusado.

**Acceptance Scenarios**:

1. **Given** a Entrada, **When** o analista a abre, **Then** vê os 13 tópicos numerados com as seleções das listas controladas e a tabela dos 16 requisitos.
2. **Given** um requisito marcado "não se aplica", **When** o analista salva sem justificativa, **Then** a gravação é recusada.
3. **Given** a Entrada aprovada com requisitos "aplica", **When** a Validação do Produto é criada, **Then** cada requisito "aplica" aparece como pendência na Validação, e os "não se aplica" seguem com a justificativa.

---

### User Story 5 - Verificação Final montada pelo sistema (Priority: P2)

A Verificação Final de Validação nasce da Entrada aprovada: uma linha por requisito de entrada do modelo, com "Previsto" vindo da Entrada, "Realizado" preenchido pelo analista e "Disposição" (Aprovado, Reprovado ou Outros); disposição diferente de Aprovado exige justificativa.

**Why this priority**: Fecha a verificação de saídas contra entradas (RDC 665/2022, art. 49) sem redigitação.

**Independent Test**: Aprovar a Entrada, criar a Verificação Final e conferir as linhas e o "Previsto"; tentar criar sem Entrada aprovada.

**Acceptance Scenarios**:

1. **Given** a Entrada aprovada, **When** a Verificação Final é criada, **Then** cada linha traz o requisito e o "Previsto" da Entrada.
2. **Given** a Entrada ainda não aprovada, **When** alguém cria a Verificação Final, **Then** o sistema recusa.
3. **Given** uma linha com disposição "Reprovado" ou "Outros", **When** o analista salva sem justificativa, **Then** a gravação é recusada.

---

### User Story 6 - Saída de Projeto com setores e itens MAPA (Priority: P2)

Na Saída de Projeto, o analista escolhe os setores que recebem a transferência; os itens marcados MAPA só aparecem em projetos com esse órgão; matérias-primas e materiais de embalagem novos vêm do cadastro de insumos marcados como novos para a empresa.

**Why this priority**: A Saída libera o projeto para produção (RDC 665/2022, arts. 52 e 59).

**Independent Test**: Criar a Saída num projeto ANVISA e num MAPA e conferir os itens 6 e 7; escolher setores e insumos novos.

**Acceptance Scenarios**:

1. **Given** um projeto ANVISA, **When** a Saída é aberta, **Then** os itens MAPA não aparecem.
2. **Given** um projeto MAPA, **When** a Saída é aberta, **Then** os itens MAPA aparecem.
3. **Given** a Saída, **When** o analista escolhe os setores de transferência, **Then** a escolha vem da lista controlada e fica gravada.

---

### User Story 7 - Alteração de Projeto que sobe a versão (Priority: P2)

A Alteração de Projeto registra a versão alterada e a nova versão do projeto, a justificativa, os requisitos de entrada afetados, a análise de risco e os subdocumentos afetados. Quando aprovada, a versão do projeto sobe e os subdocumentos afetados ficam marcados para revisão.

**Why this priority**: Alterações de projeto precisam ser documentadas, com avaliação de risco e aprovação antes de implementar (RDC 665/2022, art. 60).

**Independent Test**: Criar uma Alteração afetando a Formulação, aprová-la e conferir a versão do projeto e a marca de revisão na Formulação.

**Acceptance Scenarios**:

1. **Given** um projeto na versão 01, **When** a Alteração é criada, **Then** ela mostra "Versão alterada: 01" e "Nova Versão: 02".
2. **Given** uma Alteração sem análise de risco, **When** é enviada para aprovação, **Then** é recusada.
3. **Given** a Alteração aprovada, **When** a aprovação é registrada, **Then** a versão do projeto passa a 02 e os subdocumentos afetados aparecem marcados para revisão, com a Alteração de origem.

---

### Edge Cases

- Subdocumento criado fora da ordem do fluxo (ex.: Lote Piloto antes da Formulação aprovada): o sistema avisa e só cria com autorização registrada do Gestor de P&D, com motivo.
- Segundo documento do mesmo tipo no projeto: recusado, exceto Alteração de Projeto, que é numerada (1, 2, 3...).
- Referência a cadastro desativado ou substituído depois de usado: o documento continua mostrando a versão referenciada; o formulário só oferece cadastros ativos e vigentes, além dos já referenciados.
- Lote de outro projeto: não é oferecido nem aceito.
- Modelo com vigência futura: só vale para documentos criados a partir da data.
- Item da Saída restrito a MAPA em projeto ANVISA: não aparece e não é exigido.
- Migração para a versão vigente de documento já aprovado: recusada.
- Aprovação pelo mesmo usuário que criou o subdocumento: recusada.
- Subdocumento aprovado: não é editado nesta feature; nova versão é assunto da feature 005.

## Requirements *(mandatory)*

### Functional Requirements

**Modelos de formulário**

- **FR-001**: O modelo de formulário DEVE ter tipo de subdocumento, versão do formulário (dois dígitos), referência, início de vigência, título da capa, disposição dos tópicos na capa (uma ou duas colunas) e tópicos ordenados, cada um com rótulo da capa, rótulo do corpo quando diferente, campos, se aceita "não aplicável" e, quando houver, o órgão regulador a que se restringe.
- **FR-002**: Os campos DEVEM ser de um destes tipos: texto formatado, texto curto, lista, tabela com colunas definidas, seleção de lista controlada (única ou múltipla), referência a cadastro (lote, insumo, kit de referência, amostra, painel, norma ou referência bibliográfica), anexo, data e número; cada campo pode ser obrigatório.
- **FR-003**: A publicação DEVE ser recusada quando a definição tiver rótulos de tópico repetidos, chaves repetidas ou tipo de campo desconhecido; a numeração dos tópicos é sempre calculada pela ordem.
- **FR-004**: Modelo publicado NÃO DEVE ser alterado; mudança só por nova versão, que nasce como rascunho com o conteúdo da vigente.
- **FR-005**: Só a Qualidade/AR DEVE cadastrar, editar rascunhos e publicar modelos; todos os perfis podem consultá-los.
- **FR-006**: O sistema DEVE trazer carregados os modelos versão 05 dos nove tipos de subdocumento, conforme docs/contexto/02-dicionario-documentos.md.
- **FR-007**: Cada subdocumento DEVE guardar a versão de modelo usada; documentos novos usam a versão vigente na data de criação e os iniciados continuam na sua; o Gestor de P&D DEVE poder migrar documento em rascunho para a versão vigente, com motivo, mantendo os dados compatíveis e guardando, visíveis, os que não couberem.

**Subdocumentos**

- **FR-008**: Em projeto aberto, membros da equipe com perfil Analista/Pesquisador ou Líder de projeto e o Gestor de P&D DEVEM poder criar e editar subdocumentos; há um documento por tipo por projeto, exceto a Alteração de Projeto, numerada em sequência.
- **FR-009**: O formulário DEVE ser montado a partir do modelo usado e os dados conferidos contra ele a cada gravação; o rascunho pode ficar incompleto; a aprovação exige os campos obrigatórios preenchidos ou o tópico marcado "não aplicável" com justificativa.
- **FR-010**: "Não aplicável" DEVE exigir justificativa e só ser aceito com os campos do tópico vazios.
- **FR-011**: Tópicos e tabelas DEVEM ser numerados automaticamente na ordem do documento ("1. Amostras"; "Tabela 01").
- **FR-012**: Toda criação, edição, migração, autorização e aprovação DEVE ir para a trilha, com valor anterior e novo; gravação sobre versão desatualizada do documento DEVE ser recusada.
- **FR-013**: Referências a cadastros DEVEM apontar para a versão do cadastro; lotes só do próprio projeto; o formulário oferece só cadastros ativos e vigentes, mantendo os já referenciados.
- **FR-014**: Anexos DEVEM ser guardados com conferência de integridade (feature 003) e entregues só a quem acessa o projeto.
- **FR-015**: Nesta feature, a aprovação de subdocumento DEVE ser uma confirmação registrada do Gestor de P&D que não criou o documento; aprovado, o documento fica bloqueado para edição e bloqueia as versões de cadastros que referencia.

**Fluxo**

- **FR-016**: A criação fora da ordem recomendada (Entrada → Formulação → Lote Piloto → RAPD → Análise Crítica → Validação → Verificação Final → Saída, com o antecessor aprovado) DEVE mostrar aviso e só seguir com autorização registrada do Gestor de P&D, com motivo; a Alteração de Projeto pode ser criada a qualquer momento com a Entrada aprovada.

**Entrada, Validação e Verificação Final**

- **FR-017**: A Entrada DEVE ter os 13 tópicos do dicionário, a parte estruturada do formulário opcional (nome do projeto, versão, data e analito; seleções de amostra, funcionalidade, classificação do teste, automação, usuário, armazenamento, filtros e classificação de uso) e a tabela "aplica / não se aplica" dos 16 requisitos de desempenho, com justificativa obrigatória para "não se aplica".
- **FR-018**: Cada requisito "aplica" da Entrada aprovada DEVE gerar uma pendência na Validação do Produto, cumprida com o registro da evidência; os "não se aplica" seguem para a Validação com a justificativa.
- **FR-019**: A Verificação Final DEVE ser criada só com a Entrada aprovada, com uma linha por requisito de entrada do modelo, "Previsto" vindo da Entrada aprovada, "Realizado" preenchido pelo analista (sem pré-preenchimento nesta versão) e "Disposição" da lista controlada; disposição diferente de Aprovado exige justificativa.

**Saída e Alteração**

- **FR-020**: A Saída DEVE ter os setores de transferência por seleção múltipla da lista controlada; itens restritos a MAPA só aparecem e só são exigidos em projetos MAPA; os itens de novas matérias-primas e novos materiais de embalagem referenciam insumos marcados como novos para a empresa.
- **FR-021**: A Alteração de Projeto DEVE registrar versão alterada e nova versão do projeto, justificativa, requisitos de entrada afetados, análise de risco (obrigatória), outros dados e os subdocumentos afetados; aprovada, a versão do projeto sobe e os subdocumentos afetados ficam marcados para revisão, com a Alteração de origem.

### Key Entities *(include if feature involves data)*

- **Modelo de formulário**: tipo de subdocumento, versão do formulário, referência, vigência, situação (rascunho, publicado, substituído), definição (capa, tópicos, campos, regras), quem publicou e quando.
- **Subdocumento**: projeto, tipo, número (Alterações), versão do documento, situação (rascunho, aprovado), versão de modelo usada, dados, marca de revisão (com a Alteração de origem), autor, aprovador e datas.
- **Autorização de fluxo**: subdocumento, motivo, Gestor de P&D que autorizou, data.
- **Pendência da Validação**: requisito da Entrada, situação (pendente, cumprida), evidência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Os nove tipos de subdocumento da versão 05 estão carregados e podem ser criados e preenchidos em um projeto aberto.
- **SC-002**: Em 100% dos testes, publicar a versão 06 de um modelo não altera documentos já iniciados.
- **SC-003**: Em 100% dos testes, a Verificação Final nasce da Entrada aprovada, com uma linha por requisito de entrada e o "Previsto" igual ao da Entrada.
- **SC-004**: Em 100% dos testes, marcar "não aplicável" num tópico com itens preenchidos é rejeitado.
- **SC-005**: Gravar um subdocumento com 100 linhas de tabela leva menos de 2 segundos.

## Assumptions

- A aprovação nesta feature é uma confirmação registrada do Gestor de P&D; a feature 005 a substitui pela assinatura eletrônica e acrescenta revisão, devolução e novas versões de documento.
- A revisão controlada dos modelos (elaboração, aprovação e vigência) é a feature 013; aqui a Qualidade publica diretamente.
- A geração de DOCX/PDF (006) e os estudos com cálculo (007) usam os dados gravados aqui; nesta feature a pendência da Validação é cumprida com o registro da evidência em texto.
- Os rótulos e tópicos dos modelos versão 05 vêm de docs/contexto/02-dicionario-documentos.md; os dados dos arquivos de docs/modelos/ não são usados.
- Tópico 9 da Entrada, tópicos da Análise Crítica e numeração da Saída definidos nas respostas provisórias do esclarecimento (sessão 2026-11-07).
- Pendente de definição pela Qualidade: a regra de pré-preenchimento do "Realizado" da Verificação Final a partir da Validação e da Saída.
