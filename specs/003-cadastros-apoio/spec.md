# Feature Specification: Cadastros de apoio

**Feature Branch**: `003-cadastros-apoio`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Cadastros de apoio usados por todos os subdocumentos: lotes, insumos (matérias-primas e materiais de embalagem), kits de referência, amostras e painéis, normas e referências bibliográficas. Leia docs/contexto/02-dicionario-documentos.md e 05-vocabularios.md. Problema: hoje o mesmo lote, código ou concentração é redigitado em vários documentos, o que abre espaço para divergências. Cada dado deve existir uma vez e ser referenciado. Histórias: 1. Como analista, cadastro os lotes do projeto (piloto ou validação) com código, data de fabricação, validade, local de fabricação e responsável pela produção. 2. Cadastro insumos com código, descrição, fabricante, lote do fabricante e certificado de análise anexado; marco se é novo para a empresa, para entrar na Saída de Projeto. 3. Cadastro kits de referência e comparativos com nome, fabricante, lote, validade e número de registro quando houver. 4. Cadastro amostras e painéis com identificador, tipo de amostra (vocabulário controlado), origem, caracterização e condição de armazenamento; uma amostra pode estar em vários estudos. 5. Mantenho bibliotecas de normas (ex.: NBR ISO 13485:2016, NBR ISO 14971:2020, CLSI EP25) e de referências bibliográficas reutilizáveis entre projetos. 6. Importo uma lista de insumos de uma planilha exportada do ERP enquanto a integração com o Sankhya não existe. Regras: código de insumo é único; o código de um lote não muda depois de usado em documento assinado; cadastro usado em documento assinado só é corrigido por nova versão com motivo, e o documento antigo continua mostrando o valor assinado; buscas rápidas por código e descrição; amostras não guardam dados pessoais de pacientes. Fora do escopo: integração automática com o Sankhya (feature 012)."

## Clarifications

### Session 2026-11-07

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: Qual é o padrão de código dos lotes piloto e de validação? → A: Não há padrão imposto nesta versão: código alfanumérico que pode ter hífen, barra ou ponto, sem espaços, único entre os lotes vigentes do projeto; quando a Qualidade definir o padrão, ele entra como expressão configurável (ratificar com a Garantia da Qualidade).
- Q: Quem pode cadastrar e corrigir insumos? → A: Analista/Pesquisador, Líder de projeto, Gestor de P&D e Qualidade/AR; Leitor e Administrador só consultam; correção de insumo bloqueado exige motivo e gera nova versão (ratificar com o Gestor de P&D e a Garantia da Qualidade).
- Q: Que atributos clínicos das amostras precisam ser guardados, considerando a LGPD? → A: Só identificador interno, tipo de amostra, origem (instituição ou banco, sem identificador do paciente), caracterização analítica (resultado de referência, concentração, status), condição de armazenamento e data de coleta; nenhum dado demográfico ou de identificação do paciente (ratificar com a Garantia da Qualidade e o encarregado de dados).
- Q: Certificados de análise vencidos bloqueiam o uso do insumo? → A: Não; o sistema registra a validade do certificado e mostra alerta de certificado vencido onde o insumo aparece, sem bloquear (ratificar com a Garantia da Qualidade).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lotes do projeto (Priority: P1)

O analista cadastra os lotes do projeto (piloto, validação ou produção) com código, data de fabricação, validade, local de fabricação e responsável pela produção. O lote aparece sempre no formato "Lote <código> – Fabricação: MM/AAAA – Validade: MM/AAAA".

**Why this priority**: Lotes são citados em Lote Piloto, Validação, Saída e dossiê; a divergência de lote entre documentos é o problema central.

**Independent Test**: Cadastrar um lote num projeto aberto e conferir o formato de exibição, a recusa de validade anterior à fabricação e o evento na trilha.

**Acceptance Scenarios**:

1. **Given** um projeto a que o analista tem acesso, **When** cadastra um lote com os dados completos, **Then** o lote fica disponível no projeto e a criação vai para a trilha.
2. **Given** um lote, **When** é exibido, **Then** aparece como "Lote <código> – Fabricação: MM/AAAA – Validade: MM/AAAA".
3. **Given** validade anterior à fabricação ou código repetido no mesmo projeto, **When** o analista salva, **Then** o sistema recusa com mensagem clara.
4. **Given** um projeto a que a pessoa não tem acesso, **When** tenta ver ou cadastrar lotes dele, **Then** o acesso é negado e registrado.

---

### User Story 2 - Versões e bloqueio do que já foi usado em documento assinado (Priority: P1)

Enquanto um cadastro não foi usado em documento assinado, ele pode ser corrigido no próprio registro, com histórico na trilha. Depois de usado em documento assinado, o registro fica bloqueado: a correção gera nova versão com motivo obrigatório, a versão anterior continua intacta e o documento assinado continua mostrando o valor assinado. O código de lote e de insumo não muda depois do bloqueio.

**Why this priority**: É a regra que garante que documentos assinados não mudam por baixo (princípios I e V da constituição).

**Independent Test**: Bloquear um lote como o faria a assinatura de um documento, corrigir a validade e conferir que existe a versão 2, que a versão 1 ficou igual e que a referência antiga continua mostrando o valor original.

**Acceptance Scenarios**:

1. **Given** um lote não bloqueado, **When** o analista corrige a validade, **Then** o próprio registro é alterado e a trilha guarda o valor anterior e o novo.
2. **Given** um lote bloqueado por documento assinado, **When** o analista corrige a validade sem motivo, **Then** a correção é recusada; com motivo, nasce a versão 2 e a versão 1 continua igual.
3. **Given** uma referência à versão 1, **When** é exibida depois da correção, **Then** mostra o valor original.
4. **Given** um lote bloqueado, **When** alguém tenta mudar o código, **Then** a mudança é recusada.
5. **Given** um cadastro com várias versões, **When** o analista abre o histórico, **Then** vê todas as versões, quem fez, quando e por quê.

---

### User Story 3 - Insumos com certificado e importação da planilha do ERP (Priority: P1)

O analista cadastra insumos (matéria-prima ou material de embalagem) com código único, descrição, fabricante, lote do fabricante, certificado de análise anexado e validade do certificado, e marca se é novo para a empresa. Enquanto não há integração com o Sankhya, importa uma planilha CSV ou XLSX: o sistema mostra a pré-visualização com as linhas válidas e as rejeitadas e o motivo de cada rejeição; só depois da confirmação os insumos válidos são criados, e o relatório de rejeições pode ser baixado.

**Why this priority**: Insumos alimentam Formulação, Lote Piloto e Saída de Projeto; a importação evita redigitar centenas de códigos.

**Independent Test**: Importar uma planilha com 500 linhas, das quais algumas inválidas (código repetido, descrição vazia, tipo inválido), conferir a pré-visualização, confirmar e baixar o relatório de rejeições.

**Acceptance Scenarios**:

1. **Given** um insumo novo, **When** o analista salva com código já usado por outro insumo, **Then** o sistema recusa.
2. **Given** um certificado de análise anexado, **When** alguém o baixa, **Then** o sistema confere o resumo do arquivo antes de entregar e recusa se o arquivo tiver sido alterado.
3. **Given** um certificado vencido, **When** o insumo é exibido ou buscado, **Then** aparece o alerta "Certificado vencido", sem impedir o uso.
4. **Given** uma planilha com 500 linhas, **When** o analista a envia, **Then** vê a pré-visualização com quantas linhas são válidas e quantas rejeitadas, com o motivo de cada rejeição, sem nada gravado ainda.
5. **Given** a pré-visualização, **When** confirma, **Then** os insumos válidos são criados (cada criação na trilha) e o relatório das rejeitadas fica disponível para baixar.
6. **Given** insumos marcados como novos para a empresa, **When** a Saída de Projeto for montada (feature 004), **Then** eles poderão ser listados a partir do cadastro.

---

### User Story 4 - Kits de referência, amostras e painéis sem dados de pacientes (Priority: P2)

O analista cadastra kits de referência e comparativos (nome, fabricante, lote, validade, número de registro quando houver), amostras (identificador interno, tipo de amostra da lista controlada, origem, caracterização, condição de armazenamento, data de coleta opcional) e painéis (conjuntos de amostras). Nenhum campo de amostra aceita dado pessoal de paciente.

**Why this priority**: Base dos estudos (feature 007) e do caderno (008).

**Independent Test**: Cadastrar kit, amostras e um painel; tentar gravar nome, CPF ou e-mail de paciente em qualquer campo de amostra e conferir a recusa.

**Acceptance Scenarios**:

1. **Given** um kit de referência, **When** é salvo com validade, **Then** aparece com nome, fabricante, lote, validade e registro.
2. **Given** uma amostra, **When** o identificador não segue o padrão de código interno (ex.: um nome de pessoa), **Then** é recusado.
3. **Given** os campos de texto da amostra, **When** contêm CPF, e-mail, telefone ou expressões como "paciente" ou "nome", **Then** a gravação é recusada com explicação sobre dados pessoais.
4. **Given** um painel, **When** o analista inclui amostras, **Then** o painel referencia a versão de cada amostra e uma amostra pode estar em vários painéis e estudos.

---

### User Story 5 - Bibliotecas de normas e referências e listas controladas (Priority: P2)

O analista mantém a biblioteca de normas (identificação, título, abrangência nacional ou internacional) e de referências bibliográficas (citação completa, ano, DOI ou endereço), reutilizáveis entre projetos. A Qualidade mantém as listas controladas (tipos de amostra, faixas de armazenamento, tecnologias, tipos de subdocumento): inclui termos, corrige rótulos e desativa termos, sem apagar, com versão da lista e trilha.

**Why this priority**: Alimentam o tópico 11 da Entrada, o dossiê (IV e XII) e todos os formulários com seleção.

**Independent Test**: Cadastrar normas e referências e localizá-las pela busca; como Qualidade, incluir um tipo de amostra e desativar outro, conferindo a versão da lista e a trilha.

**Acceptance Scenarios**:

1. **Given** a identificação de uma norma já cadastrada, **When** alguém tenta cadastrá-la de novo, **Then** o sistema recusa.
2. **Given** a busca de cadastros, **When** a pessoa digita parte do código ou da descrição, **Then** os resultados aparecem enquanto digita.
3. **Given** a Qualidade, **When** inclui ou desativa um termo, **Then** a versão da lista sobe, a mudança vai para a trilha e o termo desativado deixa de ser oferecido em novos cadastros, mas continua nos antigos.
4. **Given** uma pessoa sem o perfil Qualidade/AR, **When** tenta alterar uma lista controlada, **Then** o acesso é negado.

---

### Edge Cases

- Cadastro desativado: deixa de aparecer na busca para novas referências e continua visível nas referências existentes e no histórico.
- Correção sem mudança real: não gera versão nem evento.
- Planilha com colunas faltando ou fora do layout: recusada por inteiro, com a lista das colunas esperadas.
- Planilha com o mesmo código duas vezes: a segunda linha é rejeitada.
- Planilha com código que já existe no cadastro: linha rejeitada, sem alterar o insumo existente.
- Pré-visualização abandonada: nada é gravado e a importação fica registrada como não confirmada.
- Certificado em formato não aceito ou acima do tamanho máximo: recusado na anexação.
- Arquivo de certificado alterado no armazenamento: o download é recusado e o incidente vai para a trilha.
- Painel que referencia amostra desativada: continua mostrando a amostra, com a indicação de desativada.

## Requirements *(mandatory)*

### Functional Requirements

**Regras comuns dos cadastros**

- **FR-001**: Lotes, insumos, kits de referência, amostras, painéis, normas e referências bibliográficas DEVEM ser cadastrados uma única vez e referenciados por versão; textos e tabelas dos documentos NÃO DEVEM redigitar esses dados.
- **FR-002**: Cadastro ainda não usado em documento assinado DEVE poder ser corrigido no próprio registro, com valor anterior e novo na trilha.
- **FR-003**: Cadastro usado em documento assinado DEVE ficar bloqueado; a correção DEVE gerar nova versão com motivo obrigatório, mantendo a versão anterior intacta e consultável.
- **FR-004**: O código de lote e o de insumo NÃO DEVEM mudar depois do bloqueio.
- **FR-005**: Cada cadastro DEVE ter histórico com todas as versões (autor, data e hora, motivo) e os eventos da trilha.
- **FR-006**: Nenhum cadastro DEVE ser apagado; sai de uso por desativação, que o tira da busca para novas referências.
- **FR-007**: A busca DEVE achar cadastros por parte do código ou da descrição enquanto a pessoa digita.
- **FR-008**: Perfis Analista/Pesquisador, Líder de projeto, Gestor de P&D e Qualidade/AR DEVEM poder cadastrar e corrigir; os demais perfis só consultam.

**Lotes**

- **FR-009**: Lote DEVE pertencer a um projeto e ter código (único entre os lotes vigentes do projeto e no padrão configurável), tipo (Piloto, Validação, Produção), data de fabricação, validade (posterior à fabricação), local de fabricação e responsável pela produção; só quem acessa o projeto vê e cadastra os lotes dele.
- **FR-010**: Lote DEVE ser exibido como "Lote <código> – Fabricação: MM/AAAA – Validade: MM/AAAA".

**Insumos**

- **FR-011**: Insumo DEVE ter código único entre os vigentes, descrição, tipo (matéria-prima ou material de embalagem), fabricante, lote do fabricante, certificado de análise anexado, validade do certificado e a marcação "novo para a empresa".
- **FR-012**: Certificado vencido DEVE gerar alerta na exibição e na busca, sem bloquear o uso.
- **FR-013**: A importação DEVE aceitar CSV (`;` ou `,`) e XLSX no layout definido, mostrar pré-visualização linha a linha com motivo das rejeições sem gravar nada, criar só as linhas válidas na confirmação e oferecer o relatório de rejeições para baixar.

**Kits, amostras e painéis**

- **FR-014**: Kit de referência DEVE ter nome, fabricante, lote, validade e número de registro quando houver.
- **FR-015**: Amostra DEVE ter identificador interno (código sem espaços, com ao menos um dígito), tipo da lista controlada, origem, caracterização, condição de armazenamento (lista controlada e detalhe) e data de coleta opcional; NÃO DEVE existir campo para dado pessoal de paciente.
- **FR-016**: Os textos da amostra DEVEM recusar CPF, e-mail, telefone e expressões que indiquem identificação de paciente ("paciente", "nome").
- **FR-017**: Painel DEVE ter código, descrição e as amostras (por versão); uma amostra pode estar em vários painéis e estudos.

**Bibliotecas e listas**

- **FR-018**: Norma DEVE ter identificação única entre as vigentes (ex.: "NBR ISO 13485:2016"), título e abrangência (Nacional ou Internacional); referência bibliográfica DEVE ter citação completa, ano e DOI ou endereço opcionais.
- **FR-019**: Só a Qualidade/AR DEVE manter as listas controladas: incluir termo, corrigir rótulo, desativar e reativar; cada mudança sobe a versão da lista e vai para a trilha.

**Anexos**

- **FR-020**: Anexos DEVEM ser guardados com resumo SHA-256 conferido a cada leitura; arquivo alterado é recusado e o incidente vai para a trilha; tipos (PDF, PNG, JPEG) e tamanho máximo são configuráveis.

### Key Entities *(include if feature involves data)*

- **Versão de cadastro**: base comum de todos os cadastros: linhagem (o mesmo cadastro ao longo das versões), número da versão, vigente ou não, bloqueado ou não, motivo da versão, autor e datas, ativo ou desativado.
- **Lote**: projeto, código, tipo, fabricação, validade, local, responsável.
- **Insumo**: código, descrição, tipo, fabricante, lote do fabricante, certificado, validade do certificado, novo para a empresa.
- **Kit de referência**: nome, fabricante, lote, validade, registro.
- **Amostra**: identificador interno, tipo, origem, caracterização, armazenamento, coleta.
- **Painel**: código, descrição, amostras (versões).
- **Norma** e **Referência bibliográfica**.
- **Arquivo guardado**: nome original, tipo, tamanho, resumo SHA-256, quem enviou e quando.
- **Importação de insumos**: arquivo, linhas com resultado da validação, situação (pré-visualizada, confirmada), quantidades criadas e rejeitadas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, corrigir cadastro bloqueado gera nova versão e a referência à versão antiga continua mostrando o valor original.
- **SC-002**: A importação de 500 insumos com linhas inválidas termina com o relatório das rejeitadas e só as válidas criadas, em menos de 30 segundos.
- **SC-003**: Em 100% dos testes, nenhum campo de amostra aceita nome, CPF, e-mail ou telefone de paciente.
- **SC-004**: A busca devolve resultados em menos de 1 segundo com 10 mil insumos cadastrados.
- **SC-005**: Em 100% dos downloads de arquivo alterado no armazenamento, o sistema recusa a entrega e registra o incidente.

## Assumptions

- O bloqueio por documento assinado é acionado pela feature 005 (assinatura); nesta feature o mecanismo de bloqueio existe e é testado diretamente.
- O layout da planilha de importação é o do contrato `contracts/importacao-insumos.md`; se a exportação do ERP vier em outro formato, o contrato é ajustado com a TI.
- A unidade de medida do insumo virá do Sankhya na feature 012.
- Insumos, kits, amostras, painéis, normas e referências valem para a empresa toda; lotes pertencem a um projeto.
