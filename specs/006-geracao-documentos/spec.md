# Feature Specification: Geração de documentos no padrão da empresa

**Feature Branch**: `006-geracao-documentos`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "Geração dos documentos no padrão visual da empresa a partir dos dados do sistema. Leia docs/contexto/03-padroes-formatacao.md e veja os arquivos de docs/modelos/. Objetivo: economizar o tempo de montagem e eliminar erros de cópia; o documento sai pronto, com capa, numeração e rodapé corretos. Histórias: 1. Como analista, gero o documento de qualquer subdocumento em DOCX (editável, para conferência) e em PDF (oficial). 2. A capa reproduz o padrão da planilha Capas Projeto: logotipo, título do subdocumento, nome do produto, versão, lista 'ESTE RELATÓRIO DEVE CONTER', bloco de assinaturas e rodapé 'Formulário Versão: NN. Referência: <referência>' com os valores do modelo usado. 3. No corpo, os tópicos aparecem como títulos numerados, as tabelas são numeradas em sequência ('Tabela 01 – ...') e repetem o cabeçalho quando quebram de página; as páginas são numeradas 'Página N de M'. 4. No PDF oficial, as assinaturas eletrônicas aparecem no bloco de assinaturas com nome, função, data e hora e significado; o arquivo é selado digitalmente e o rodapé mostra um código de verificação. 5. Como Garantia da Qualidade, mantenho os modelos de layout (capa, cabeçalho, rodapé, estilos) sem programador, e cada modelo é versionado. 6. Todo documento gerado fica arquivado com versão, data, autor da geração e hash; gerar de novo uma versão aprovada produz o mesmo conteúdo. Regras: documento de versão não aprovada sai com marca d'água 'RASCUNHO – NÃO VÁLIDO'; o PDF oficial é PDF/A; todo dado vem do sistema, nada é digitado no gerador. Fora do escopo: documento completo do projeto (009) e dossiê (011), que reutilizam este gerador."

## Clarifications

### Session 2026-11-08

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: O DOCX também pode ser documento oficial ou só o PDF? → A: Só o PDF/A selado da versão aprovada é oficial; o DOCX é sempre cópia para conferência, sem selo nem código de verificação, com a indicação "Cópia para conferência – o documento oficial é o PDF" no rodapé quando a versão está aprovada (nas demais vale a marca d'água de rascunho) (ratificar com a Garantia da Qualidade).
- Q: O logotipo é único ou por marca (Bioclin, Quibasa)? → A: Único: a faixa "Bioclin · Quibasa" da planilha Capas Projeto, guardada no modelo de layout; trocar o logotipo é publicar nova versão do modelo de layout; logotipo por marca exigiria a marca no cadastro do produto, que não existe (ratificar com a Garantia da Qualidade).
- Q: A paginação é "Página N" ou "Página N de M"? → A: "Página N de M" em todas as páginas de todos os documentos gerados, também nos tipos em que a planilha usa "Página N" (Entrada, Formulação e Lote Piloto), porque o total revela página faltando (ratificar com a Garantia da Qualidade).
- Q: Subdocumentos isolados levam sumário? → A: Não; a capa já lista os tópicos em "ESTE RELATÓRIO DEVE CONTER:", e o sumário fica só no documento completo do projeto (feature 009) (ratificar com a Garantia da Qualidade).
- Q: O TAP e o Plano de Negócios, que já têm versões e assinaturas (feature 005), também geram documento? → A: Sim, em DOCX e PDF, com modelo de layout próprio de cada um no mesmo padrão visual (faixa do logotipo, título "Termo de Abertura de Projeto" ou "Plano de Negócios", nome do produto, versão, bloco de assinaturas com os significados Elaborado e Aprovado da feature 005) e rodapé com a paginação; sem "Formulário Versão" e "Referência" enquanto a Qualidade não definir formulário e referência para eles (o modelo de layout tem texto de rodapé configurável, vazio por padrão); o documento do Plano de Negócios só é gerado e baixado por quem vê dados financeiros (ratificar com o Gestor de P&D e a Garantia da Qualidade).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar o documento de um subdocumento em DOCX e PDF (Priority: P1)

Quem pode ver um subdocumento pede o documento dele em DOCX (editável, para conferência) ou em PDF. A geração corre em segundo plano, a tela mostra a situação do pedido e, ao fim, o arquivo fica disponível para baixar e arquivado no sistema.

**Why this priority**: É o ganho principal da feature: o documento sai pronto, sem montagem manual nem cópia de dados.

**Independent Test**: Gerar o DOCX e o PDF de uma Entrada de Projeto em rascunho; acompanhar a situação na tela, baixar os dois arquivos e conferir o registro de cada geração.

**Acceptance Scenarios**:

1. **Given** um subdocumento que a pessoa pode ver, **When** ela pede o PDF, **Then** a tela mostra o pedido em andamento e, ao concluir, oferece o arquivo, que fica arquivado com documento, versão, data e hora, autor da geração e resumo criptográfico.
2. **Given** um pedido em andamento para o mesmo documento, versão e formato, **When** alguém pede de novo, **Then** o sistema mostra o pedido em andamento em vez de abrir outro.
3. **Given** uma pessoa sem acesso ao projeto, **When** tenta gerar ou baixar um documento (inclusive pela URL direta), **Then** o acesso é negado e registrado.
4. **Given** uma falha na geração, **When** o pedido termina, **Then** a tela mostra a falha com uma mensagem compreensível, nada é arquivado como documento gerado e a falha fica na trilha de auditoria.

---

### User Story 2 - Capa no padrão da planilha Capas Projeto (Priority: P1)

A capa de cada subdocumento reproduz a planilha Capas Projeto: faixa do logotipo, título do subdocumento, nome do produto em caixa alta, versão, lista "ESTE RELATÓRIO DEVE CONTER:" com os tópicos numerados do modelo, bloco de assinaturas e rodapé "Formulário Versão: NN. Referência: <referência>" com os valores do modelo de formulário usado pelo documento.

**Why this priority**: A capa é o primeiro critério de aceite da Qualidade; sem ela o documento não substitui o formulário atual.

**Independent Test**: Gerar a capa de cada tipo de subdocumento a partir de dados de teste e comparar elementos, ordem, fontes e tamanhos com a planilha e com docs/contexto/03-padroes-formatacao.md.

**Acceptance Scenarios**:

1. **Given** uma Entrada de Projeto no modelo de formulário versão 05, **When** a capa é gerada, **Then** ela traz, em ordem, a faixa do logotipo, "Entrada de Projeto", o nome do produto em caixa alta, "VERSÃO" com o número em dois dígitos, "ESTE RELATÓRIO DEVE CONTER:", os tópicos "1 - Amostras" a "13 - Outros dados pertinentes" em duas colunas, o bloco de assinaturas e o rodapé "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos".
2. **Given** um modelo com tópicos só para MAPA e um projeto ANVISA, **When** a capa é gerada, **Then** esses tópicos não aparecem e a numeração segue sem lacunas.
3. **Given** uma Alteração de Projeto, **When** a capa é gerada, **Then** ela mostra "Versão alterada:" e "Nova Versão:" no lugar de "VERSÃO".
4. **Given** uma Verificação Final de Validação, **When** a capa é gerada, **Then** a tabela "CHECK LIST" com as colunas "REQUISITOS DE ENTRADA", "PREVISTO", "REALIZADO" e "DISPOSIÇÃO (APROVADO, REPROVADO OU OUTROS)" aparece abaixo da versão, com os dados do documento.
5. **Given** uma Saída de Projeto, **When** a capa é gerada, **Then** os setores de transferência aparecem depois dos tópicos, em duas colunas, com os setores escolhidos marcados.
6. **Given** uma Validação do Produto, **When** a capa é gerada, **Then** o rótulo do aprovador é "Gestor de P&D responsável pela Aprovação:".

---

### User Story 3 - Corpo com tópicos e tabelas numerados e páginas numeradas (Priority: P1)

Depois da capa, os tópicos aparecem como títulos numerados com a mesma numeração da capa; as tabelas são numeradas em sequência no documento e repetem o cabeçalho quando quebram de página; todas as páginas são numeradas.

**Why this priority**: Numeração e quebras corretas são o que hoje mais consome tempo de montagem e gera erros.

**Independent Test**: Gerar um subdocumento com três tabelas, uma delas com 120 linhas, e conferir a numeração dos tópicos, das tabelas e das páginas e a repetição do cabeçalho.

**Acceptance Scenarios**:

1. **Given** um documento com tópicos visíveis, **When** é gerado, **Then** cada tópico aparece como título numerado em negrito ("1. Amostras"), na mesma numeração da capa.
2. **Given** tabelas em tópicos diferentes, **When** o documento é gerado, **Then** elas são numeradas em sequência ("Tabela 01 – <título>", "Tabela 02 – <título>"), com o título acima e as notas abaixo.
3. **Given** uma tabela de 120 linhas, **When** o documento é gerado, **Then** a tabela quebra de página e o cabeçalho se repete em cada página em que ela continua.
4. **Given** um documento de várias páginas, **When** é gerado, **Then** todas as páginas trazem a numeração "Página N de M" no rodapé.
5. **Given** um tópico marcado como não aplicável, **When** o documento é gerado, **Then** o tópico aparece com o título e "Não aplicável." seguido da justificativa.
6. **Given** números, datas e lotes, **When** o documento é gerado, **Then** os números usam vírgula decimal, as datas o formato dd/mm/aaaa e os lotes o formato "Lote <código> – Fabricação: MM/AAAA – Validade: MM/AAAA", lidos do cadastro.

---

### User Story 4 - PDF oficial com assinaturas, selo e código de verificação (Priority: P1)

O PDF da versão aprovada é o documento oficial: mostra as assinaturas eletrônicas no bloco de assinaturas, é selado digitalmente com o certificado da empresa, segue o formato de arquivamento de longo prazo (PDF/A) e traz no rodapé um código de verificação consultável no sistema.

**Why this priority**: Substitui a impressão para assinatura e dá ao documento valor de registro (RDC 665/2022, arts. 27, 42, 47, 57 e 59).

**Independent Test**: Aprovar um subdocumento, gerar o PDF oficial, validar o selo num leitor de PDF, consultar o código de verificação no sistema e alterar um byte do arquivo para ver o selo acusar a alteração.

**Acceptance Scenarios**:

1. **Given** uma versão aprovada, **When** o PDF oficial é gerado, **Then** o bloco de assinaturas mostra, para quem elaborou e para quem aprovou, nome, função, data e hora (horário de Brasília) e significado, e "Data:" mostra a data da aprovação.
2. **Given** uma aprovação feita por delegação, **When** o PDF oficial é gerado, **Then** a assinatura indica a delegação e quem delegou.
3. **Given** o PDF oficial, **When** aberto num leitor de PDF, **Then** o selo digital é apresentado como íntegro; **When** qualquer byte do arquivo é alterado, **Then** o leitor acusa a alteração.
4. **Given** o código de verificação do rodapé, **When** uma pessoa autenticada o informa no sistema, **Then** vê o tipo de documento, a versão, a situação (vigente ou substituída), a data de aprovação, as assinaturas e o resumo do arquivo arquivado; quem tem acesso ao projeto também baixa o arquivo.
5. **Given** uma versão não aprovada (rascunho, em revisão ou devolvida), **When** o documento é gerado, **Then** todas as páginas trazem a marca d'água "RASCUNHO – NÃO VÁLIDO", sem selo e sem código de verificação.
6. **Given** o DOCX de uma versão aprovada, **When** é gerado, **Then** sai sem selo e sem código de verificação, com a indicação "Cópia para conferência – o documento oficial é o PDF" no rodapé.

---

### User Story 5 - Modelos de layout mantidos pela Qualidade, com versões (Priority: P2)

A Garantia da Qualidade mantém, na interface e sem programação, os modelos de layout (logotipo, página e margens, fontes e tamanhos da capa e do corpo, cabeçalho, rodapé, estilos de títulos e de tabelas e texto da marca d'água). Cada modelo tem versões: rascunho editável, pré-visualização e publicação com início de vigência; versão publicada não muda.

**Why this priority**: Trocar o logotipo, um tamanho de fonte ou o rodapé precisa ser cadastro, não programação (constituição, princípio IV).

**Independent Test**: Criar o rascunho de uma nova versão do modelo de layout, trocar o tamanho do título, pré-visualizar, publicar e conferir que documentos já iniciados continuam na versão anterior.

**Acceptance Scenarios**:

1. **Given** o modelo de layout publicado, **When** a Qualidade cria uma nova versão, **Then** nasce um rascunho com o conteúdo da versão vigente, que pode ser alterado e pré-visualizado com dados de exemplo sem afetar documento nenhum.
2. **Given** um rascunho válido, **When** a Qualidade o publica com data de início de vigência, **Then** ele fica imutável e passa a valer para as versões de documento iniciadas a partir dessa data.
3. **Given** um rascunho sem logotipo ou com valor fora dos limites, **When** a Qualidade tenta publicar, **Then** a publicação é recusada com o que falta.
4. **Given** uma pessoa sem o perfil Qualidade/AR, **When** tenta criar, alterar ou publicar um modelo de layout (inclusive pela URL direta), **Then** o acesso é negado e registrado.
5. **Given** um documento iniciado antes da nova versão do layout, **When** é gerado, **Then** usa a versão de layout vigente quando a versão do documento começou, e o registro da geração guarda essa versão.

---

### User Story 6 - Arquivo de gerações e regeneração idêntica (Priority: P2)

Todo documento gerado fica arquivado com versão, data, autor da geração, modelos usados e resumo criptográfico. Gerar de novo uma versão aprovada produz o mesmo conteúdo, mesmo que cadastros, rótulos de listas ou dados do projeto tenham mudado depois da aprovação.

**Why this priority**: O documento oficial precisa ser reproduzível e rastreável; é a prova de que o sistema não altera registros aprovados.

**Independent Test**: Gerar duas vezes o PDF oficial da mesma versão aprovada, com uma troca do nome do produto e de um rótulo de lista entre as duas gerações, e comparar os resumos do conteúdo.

**Acceptance Scenarios**:

1. **Given** uma versão aprovada já gerada, **When** é gerada de novo, **Then** o conteúdo é idêntico ao da geração anterior (mesmo resumo do conteúdo) e o sistema indica a igualdade.
2. **Given** um rótulo de lista ou o nome do produto alterado depois da aprovação, **When** a versão aprovada é gerada de novo, **Then** o documento mostra os valores como foram aprovados.
3. **Given** um documento com várias gerações, **When** a pessoa abre o histórico de gerações, **Then** vê quem gerou, quando, o formato, a versão do documento, as versões dos modelos e o resumo de cada arquivo, e baixa os arquivos arquivados se tem acesso ao projeto.
4. **Given** um arquivo arquivado alterado fora do sistema, **When** alguém tenta baixá-lo, **Then** o download é recusado e a falha de integridade fica na trilha.

---

### User Story 7 - Documentos do TAP e do Plano de Negócios (Priority: P3)

O TAP e o Plano de Negócios, que já têm versões e assinaturas (feature 005), também geram documento em DOCX e PDF, com modelo de layout próprio de cada um no mesmo padrão visual dos subdocumentos.

**Why this priority**: Completa o registro dos documentos assinados do projeto, mas não substitui nenhum formulário atual.

**Independent Test**: Gerar o PDF oficial do TAP de um projeto aprovado e conferir capa, assinaturas, selo e código de verificação; tentar gerar o Plano de Negócios sem permissão para dados financeiros.

**Acceptance Scenarios**:

1. **Given** um TAP aprovado, **When** a pessoa gera o PDF oficial, **Then** o documento sai com a faixa do logotipo, "Termo de Abertura de Projeto", o nome do produto, a versão, as assinaturas Elaborado e Aprovado, o selo e o código de verificação, e os campos do TAP como seções numeradas.
2. **Given** o modelo de layout do TAP com o texto de rodapé vazio, **When** o documento é gerado, **Then** o rodapé traz só a paginação (e o código de verificação no PDF oficial), sem "Formulário Versão" nem "Referência".
3. **Given** uma pessoa sem permissão para dados financeiros, **When** tenta gerar ou baixar o documento do Plano de Negócios (inclusive pela URL direta), **Then** o acesso é negado e registrado.

---

### Edge Cases

- Documento em rascunho incompleto: gera normalmente, com os campos vazios indicados como não preenchidos e a marca d'água.
- Edição do documento depois do pedido de geração: o documento gerado registra a versão dos dados que usou.
- Certificado da empresa ausente, vencido ou ilegível: o PDF oficial não é emitido; a geração falha com mensagem clara e alerta na trilha. Nunca sai PDF oficial sem selo.
- Versão aprovada já substituída por outra: o PDF oficial dela continua podendo ser gerado com o mesmo conteúdo; a consulta do código de verificação mostra que está substituída e qual a versão vigente.
- Projeto cancelado ou encerrado: a geração continua permitida a quem tem acesso, porque não altera o documento.
- Código de verificação inexistente: a consulta informa que o código não foi encontrado e fica registrada.
- Assinatura "revisado" (opcional, feature 005): aparece na relação de assinaturas do PDF oficial.
- Anexos do subdocumento: aparecem listados com nome e resumo criptográfico; os arquivos continuam no sistema.
- Formulário opcional de entrada preenchido: sai no documento da Entrada de Projeto, sem número de tópico, com o layout próprio do formulário.
- Logotipo do modelo de layout com arquivo corrompido: a geração falha com a falha de integridade registrada.

## Requirements *(mandatory)*

### Functional Requirements

**Geração**

- **FR-001**: O sistema DEVE gerar o documento de qualquer subdocumento em DOCX (editável) e em PDF a partir só dos dados do sistema (documento, modelo de formulário, cadastros, assinaturas e modelo de layout); o gerador NÃO DEVE aceitar texto digitado.
- **FR-002**: A geração DEVE correr em segundo plano, com a situação visível na tela (na fila, gerando, concluída, falhou), sem travar o uso do sistema; novo pedido para o mesmo documento, versão e formato enquanto outro está em andamento DEVE reaproveitar o pedido em andamento.
- **FR-003**: Só quem pode ver o documento DEVE gerar e baixar os arquivos gerados dele; tentativa sem permissão DEVE ser negada e registrada, inclusive pela URL direta.

**Capa**

- **FR-004**: A capa DEVE seguir a planilha Capas Projeto, na ordem: faixa do logotipo; título do subdocumento; nome do produto em caixa alta; "VERSÃO" e o número da versão do documento com dois dígitos; "ESTE RELATÓRIO DEVE CONTER:"; os tópicos numerados do modelo visíveis para o órgão regulador do projeto ("1 - Amostras"), em duas colunas quando o modelo pede; o bloco de assinaturas ("Analista Responsável (Nome/Função):", rótulo do aprovador do modelo e "Data:"); e o rodapé "Formulário Versão: NN. Referência: <referência>" com os valores do modelo de formulário usado pelo documento.
- **FR-005**: A capa DEVE respeitar as particularidades: Alteração de Projeto com "Versão alterada:" e "Nova Versão:"; Verificação Final de Validação com a tabela "CHECK LIST" e os dados do documento abaixo da versão; Saída de Projeto com os setores de transferência em duas colunas depois dos tópicos, marcando os escolhidos; Validação do Produto com o rótulo "Gestor de P&D responsável pela Aprovação:".

**Corpo e página**

- **FR-006**: O corpo DEVE trazer os tópicos visíveis como títulos numerados em negrito com a mesma numeração da capa ("1. Amostras"); tópico não aplicável DEVE aparecer com o título e "Não aplicável." seguido da justificativa.
- **FR-007**: As tabelas DEVEM ser numeradas em sequência no documento, com título acima ("Tabela 01 – <título>") e notas abaixo, e DEVEM repetir o cabeçalho em cada página quando quebram; totais calculados aparecem na última linha.
- **FR-008**: As páginas DEVEM ser A4 retrato, nas margens e fontes do modelo de layout (padrão atual: margens de 1,3 cm laterais e 2,0 cm em cima e embaixo, fonte Calibri), sem escala de impressão, e DEVEM ser numeradas "Página N de M" no rodapé.
- **FR-009**: Os valores DEVEM sair no padrão brasileiro (vírgula decimal, datas dd/mm/aaaa, data e hora no horário de Brasília); lotes no formato "Lote <código> – Fabricação: MM/AAAA – Validade: MM/AAAA"; valores de cadastro lidos do cadastro, na versão referenciada pelo documento.
- **FR-010**: Os anexos DEVEM aparecer listados com nome e resumo criptográfico; o formulário opcional de entrada, quando preenchido, DEVE sair no documento da Entrada de Projeto sem número de tópico, com o layout próprio do formulário (cabeçalho em faixa e caixas de seleção agrupadas).

**Rascunho e documento oficial**

- **FR-011**: O documento de versão não aprovada DEVE sair, em DOCX e em PDF, com a marca d'água "RASCUNHO – NÃO VÁLIDO" em todas as páginas, sem selo e sem código de verificação.
- **FR-012**: O PDF da versão aprovada DEVE ser o documento oficial: formato de arquivamento de longo prazo (PDF/A); bloco de assinaturas com nome, função, data e hora, significado e delegação quando houver; relação de todas as assinaturas da versão; selo digital com o certificado da empresa; código de verificação no rodapé.
- **FR-013**: Sem certificado da empresa válido, o PDF oficial NÃO DEVE ser emitido: a geração falha com mensagem clara e alerta na trilha.
- **FR-014**: O código de verificação DEVE identificar de forma única o documento, a versão e o conteúdo gerado; pessoa autenticada DEVE poder consultá-lo e ver tipo de documento, versão, situação (vigente ou substituída), data de aprovação, assinaturas e resumo do arquivo arquivado; só quem tem acesso ao projeto vê o projeto e baixa o arquivo; toda consulta DEVE ser registrada.
- **FR-015**: O DOCX NUNCA DEVE ser documento oficial: sai sem selo e sem código de verificação e, quando a versão está aprovada, com a indicação "Cópia para conferência – o documento oficial é o PDF" no rodapé.

**Arquivo e regeneração**

- **FR-016**: Todo documento gerado DEVE ser arquivado, sem exclusão, com documento, versão, situação do documento na geração, formato, indicação de oficial, versões dos modelos de formulário e de layout usadas, data e hora, autor da geração e resumos criptográficos do conteúdo e do arquivo; a integridade do arquivo DEVE ser conferida a cada download.
- **FR-017**: Gerar de novo uma versão aprovada com o mesmo modelo de layout DEVE produzir o mesmo conteúdo (mesmo resumo do conteúdo antes do selo), mesmo que cadastros, rótulos de listas ou dados do projeto tenham mudado depois da aprovação: o documento aprovado mostra os valores como foram aprovados.
- **FR-018**: O histórico de gerações de cada documento DEVE listar quem gerou, quando, formato, versão do documento, versões dos modelos e resumo de cada arquivo, e permitir baixar os arquivos a quem tem acesso ao projeto.

**Modelos de layout**

- **FR-019**: Os modelos de layout (logotipo, página e margens, fontes e tamanhos da capa e do corpo, cabeçalho, rodapé, estilos de títulos e de tabelas e texto da marca d'água) DEVEM ser dados mantidos na interface, sem programação, com versões: rascunho editável, pré-visualização com dados de exemplo e publicação com início de vigência; versão publicada NÃO DEVE ser alterada.
- **FR-020**: Só o perfil Qualidade/AR DEVE criar, alterar, pré-visualizar e publicar modelos de layout; os demais perfis consultam; tentativa sem permissão DEVE ser negada e registrada.
- **FR-021**: Cada versão de documento DEVE usar o modelo de layout vigente quando ela começou (criação do documento ou da nova versão) e guardá-lo; publicar nova versão de modelo de layout NÃO DEVE alterar documentos já iniciados nem versões aprovadas.
- **FR-022**: DEVE haver um modelo de layout para os subdocumentos, com a faixa do logotipo "Bioclin · Quibasa" da planilha Capas Projeto, e um modelo de layout próprio para o TAP e outro para o Plano de Negócios.

**TAP e Plano de Negócios**

- **FR-023**: O TAP e o Plano de Negócios DEVEM gerar documento em DOCX e PDF com as mesmas regras de rascunho, documento oficial, arquivo e regeneração dos subdocumentos: capa com a faixa do logotipo, título ("Termo de Abertura de Projeto" ou "Plano de Negócios"), nome do produto, versão e bloco de assinaturas com os significados Elaborado e Aprovado; corpo com os campos do documento como seções numeradas; rodapé com o texto configurável do modelo de layout (vazio por padrão) e a paginação.
- **FR-024**: O documento do Plano de Negócios DEVE ser gerado e baixado só por quem vê dados financeiros do projeto; tentativa sem permissão DEVE ser negada e registrada.

**Trilha**

- **FR-025**: Pedido, conclusão e falha de geração, download de documento gerado, consulta de código de verificação e criação, alteração e publicação de modelo de layout DEVEM gerar eventos na trilha de auditoria.

### Key Entities *(include if feature involves data)*

- **Modelo de layout**: a que documentos se aplica, versão, situação (rascunho ou publicada), início de vigência, logotipo, página e margens, fontes e tamanhos, cabeçalho, rodapé, estilos, texto da marca d'água; quem criou, alterou e publicou.
- **Conteúdo congelado da versão aprovada**: a versão aprovada como é exibida (rótulos, valores de cadastro, nome do produto, numeração), com resumo criptográfico; base de toda geração dessa versão.
- **Pedido de geração**: documento, versão, formato, quem pediu, quando, situação e mensagem de falha.
- **Documento gerado**: documento, versão, situação do documento na geração, formato, oficial ou não, modelos de formulário e de layout usados, arquivo, resumos do conteúdo e do arquivo, código de verificação, autor e data da geração.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Qualidade compara a capa gerada da Entrada de Projeto com a capa da planilha Capas Projeto e não distingue as duas em elementos, ordem, fontes e tamanhos.
- **SC-002**: Em 100% dos testes, uma tabela de 120 linhas quebra de página repetindo o cabeçalho em todas as páginas em que continua.
- **SC-003**: O selo do PDF oficial é validado como íntegro num leitor de PDF, e a alteração de um único byte do arquivo é acusada em 100% dos testes.
- **SC-004**: Em 100% dos testes, todas as páginas de documento de versão não aprovada trazem a marca d'água.
- **SC-005**: Em 100% dos testes, duas gerações da mesma versão aprovada têm o mesmo resumo de conteúdo, inclusive depois de mudar o nome do produto e um rótulo de lista.
- **SC-006**: O PDF oficial passa na validação de conformidade PDF/A de um validador de referência.
- **SC-007**: Um subdocumento de 30 páginas fica pronto em PDF em menos de 30 segundos no servidor de homologação, sem travar a tela de quem pediu.
- **SC-008**: Regerar os documentos de referência dos testes produz páginas visualmente iguais às referências aprovadas pela Qualidade (regressão visual automatizada).

## Assumptions

- A faixa do logotipo, os textos fixos, as fontes e os tamanhos da capa vêm da planilha Capas Projeto e de docs/contexto/03-padroes-formatacao.md; os .docx originais listados em docs/modelos/LEIA-ME.md não estão no repositório, então cabeçalho e estilos do corpo seguem o padrão descrito em 03-padroes-formatacao.md até a Qualidade conferi-los contra os originais.
- O certificado da empresa para o selo é fornecido pela TI e guardado fora do repositório; desenvolvimento e homologação usam certificado de teste.
- O documento completo do projeto (009) e o dossiê (011) reutilizam este gerador e ficam fora do escopo; subdocumentos isolados não levam sumário, que fica para o documento completo.
- Valor oficial do DOCX, logotipo único, paginação "Página N de M", ausência de sumário e geração do TAP e do Plano de Negócios definidos nas respostas provisórias do esclarecimento (sessão 2026-11-08).
- Os anexos não são incorporados ao documento gerado; ficam no sistema, identificados pelo resumo criptográfico.
- Os estudos (007) e o caderno de laboratório (008) ainda não existem; quando existirem, seus dados entram no documento pelos tópicos do modelo de formulário.
- A revisão controlada dos modelos de layout, com aprovação e assinatura, é da feature 013; aqui a Qualidade/AR publica direto, como nos modelos de formulário da feature 004.
