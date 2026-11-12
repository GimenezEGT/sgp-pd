# Feature Specification: Caderno de laboratório eletrônico

**Feature Branch**: `008-caderno-laboratorio`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Caderno de laboratório eletrônico por pesquisador e por projeto, para registrar experimentos e tentativas antes dos resultados oficiais do RAPD. Leia docs/contexto/01-visao-geral.md. Objetivo: guardar o histórico científico do desenvolvimento (o que foi tentado, o que falhou e por quê) com a mesma rastreabilidade dos documentos oficiais. Histórias: 1. Como pesquisador, crio uma entrada num projeto com título, data, objetivo, hipótese, materiais (ligando lotes, insumos e amostras cadastrados), procedimento, resultados (texto, tabelas, fotos, arquivos de equipamento) e conclusão. 2. Uso modelos de entrada por tipo de experimento (ex.: teste de formulação, estabilidade preliminar) para não começar do zero. 3. Ao terminar, assino a entrada e ela fica bloqueada. Correções viram adendos datados e assinados, sem apagar o original. 4. Peço a assinatura de uma testemunha quando o experimento for relevante para propriedade intelectual ou para uma decisão do projeto. 5. Ligo entradas a formulações, lotes piloto e estudos; a partir de uma entrada, promovo dados para um estudo oficial (feature 007), mantendo o vínculo. 6. Como gestor, vejo a linha do tempo do caderno de cada projeto, busco por palavra, amostra, lote ou pesquisador e vejo entradas abertas há mais de N dias. Regras: entradas não assinadas após o prazo configurado geram lembrete; data e hora vêm do servidor; anexos têm hash; o caderno do projeto é visível para a equipe do projeto, o Gestor de P&D e a Qualidade. Fora do escopo: integração direta com equipamentos; importar arquivos basta nesta fase."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar a entrada do experimento (Priority: P1)

O pesquisador cria, num projeto, uma entrada com título, objetivo, hipótese, materiais ligados aos cadastros (lotes, insumos e amostras), procedimento, resultados (texto, tabelas, fotos e arquivos de equipamento) e conclusão; a data e a hora vêm do servidor.

**Why this priority**: É o registro do histórico científico que hoje se perde.

**Independent Test**: Criar uma entrada com dois lotes, uma amostra e uma foto anexada e conferir os vínculos e o resumo do anexo.

**Acceptance Scenarios**:

1. **Given** um projeto em que a pessoa trabalha, **When** cria uma entrada, **Then** a entrada guarda autor, data e hora do servidor e os campos informados.
2. **Given** materiais informados pelo código, **When** a entrada é gravada, **Then** cada material fica ligado à versão do cadastro; código inexistente é recusado.
3. **Given** um anexo (foto ou arquivo de equipamento), **When** é enviado, **Then** fica guardado com resumo criptográfico conferido a cada leitura.

---

### User Story 2 - Começar de um modelo de entrada (Priority: P2)

O pesquisador escolhe um modelo de entrada por tipo de experimento, e a entrada nasce com os textos do modelo.

**Why this priority**: Reduz o tempo de registro e padroniza o conteúdo.

**Independent Test**: Criar um modelo "Teste de formulação" e uma entrada a partir dele.

**Acceptance Scenarios**:

1. **Given** um modelo de entrada ativo, **When** o pesquisador o escolhe, **Then** a entrada nasce com os textos do modelo e registra o modelo e a versão usados.
2. **Given** um modelo alterado depois, **When** a entrada antiga é consultada, **Then** ela continua com o texto em que nasceu.

---

### User Story 3 - Assinar, bloquear e corrigir por adendo (Priority: P1)

Ao terminar, o autor assina a entrada com a senha de rede e ela fica bloqueada; correções viram adendos datados e assinados, sem apagar o original.

**Why this priority**: Dá ao caderno a mesma rastreabilidade dos documentos oficiais.

**Independent Test**: Assinar uma entrada, tentar editá-la e acrescentar um adendo assinado.

**Acceptance Scenarios**:

1. **Given** uma entrada aberta, **When** o autor a assina com a senha de rede, **Then** ela fica assinada (pessoa, data e hora do servidor e resumo do conteúdo) e bloqueada.
2. **Given** uma entrada assinada, **When** alguém tenta editá-la, **Then** é recusado; **When** o autor acrescenta um adendo com texto e senha, **Then** o adendo fica datado, assinado e imutável, e o original continua igual.
3. **Given** uma entrada aberta há mais que o prazo configurado, **When** o caderno é consultado, **Then** ela aparece como atrasada (lembrete).

---

### User Story 4 - Testemunha (Priority: P2)

Quando o experimento é relevante para propriedade intelectual ou para uma decisão do projeto, o autor marca a entrada como relevante e ela precisa da assinatura de uma testemunha.

**Why this priority**: Protege a prova de autoria e as decisões do projeto.

**Independent Test**: Marcar a entrada como relevante, assinar como autor e assinar como testemunha.

**Acceptance Scenarios**:

1. **Given** uma entrada relevante assinada pelo autor, **When** uma testemunha com acesso ao projeto assina com a senha, **Then** a entrada fica testemunhada.
2. **Given** o próprio autor, **When** tenta assinar como testemunha, **Then** é recusado.
3. **Given** uma entrada relevante sem testemunha, **When** o caderno é consultado, **Then** ela aparece como aguardando testemunha.

---

### User Story 5 - Vínculos e promoção para estudo (Priority: P2)

O pesquisador liga a entrada a subdocumentos (Formulação, Lote Piloto), lotes e estudos, e promove dados de um arquivo da entrada para um estudo oficial (feature 007), com o vínculo visível nos dois sentidos.

**Why this priority**: Liga o histórico ao resultado oficial sem redigitação.

**Independent Test**: Promover o CSV anexado de uma entrada para um estudo de repetibilidade e conferir o vínculo na entrada e no estudo.

**Acceptance Scenarios**:

1. **Given** uma entrada, **When** o pesquisador a liga a uma Formulação e a um estudo do projeto, **Then** os vínculos aparecem na entrada e no outro registro.
2. **Given** um arquivo CSV ou XLSX anexado e um estudo em elaboração, **When** o pesquisador promove os dados, **Then** as linhas entram no estudo pela importação da feature 007 e o vínculo de promoção fica registrado nos dois sentidos.

---

### User Story 6 - Linha do tempo, busca e pendências (Priority: P2)

O Gestor de P&D vê a linha do tempo do caderno de cada projeto, busca por palavra, amostra, lote ou pesquisador e vê as entradas abertas há mais de N dias.

**Why this priority**: Dá visibilidade ao andamento e às pendências de assinatura.

**Independent Test**: Buscar por um código de lote e conferir que todas as entradas que o usam aparecem.

**Acceptance Scenarios**:

1. **Given** um caderno com várias entradas, **When** o gestor abre a linha do tempo, **Then** vê as entradas por data, paginadas.
2. **Given** um lote usado em três entradas, **When** busca pelo código do lote, **Then** as três aparecem.
3. **Given** uma palavra do procedimento, **When** busca por ela, **Then** as entradas que a contêm aparecem (busca em português).

---

### Edge Cases

- Pessoa sem acesso ao projeto: não vê nem busca entradas do projeto; tentativa registrada.
- Senha errada ao assinar entrada ou adendo: segue as regras de tentativas e bloqueio da feature 005.
- Anexo maior que o limite ou de tipo não aceito: recusado com o motivo.
- Entrada assinada não recebe novos anexos nem materiais; só adendos e vínculos.

## Requirements *(mandatory)*

### Functional Requirements

**Entrada**

- **FR-001**: A entrada DEVE pertencer a um projeto [NEEDS CLARIFICATION: existem entradas fora de projeto, para pesquisa exploratória?] e guardar autor, data e hora do servidor, título, objetivo, hipótese, procedimento, resultados, conclusão e situação.
- **FR-002**: Materiais DEVEM ser ligados aos cadastros de lotes, insumos e amostras pela versão do registro; código inexistente DEVE ser recusado.
- **FR-003**: Anexos (fotos e arquivos de equipamento) DEVEM ser guardados com resumo criptográfico conferido a cada leitura [NEEDS CLARIFICATION: tamanho máximo e tipos de arquivo aceitos?].
- **FR-004**: Só membros do projeto com perfil Analista/Pesquisador ou Líder e o Gestor de P&D DEVEM criar entradas; o caderno é visível para a equipe do projeto, o Gestor de P&D e a Qualidade; tentativa sem permissão DEVE ser negada e registrada.

**Modelos de entrada**

- **FR-005**: Modelos de entrada por tipo de experimento DEVEM poder ser mantidos sem programação, com versões; a entrada copia os textos do modelo ao nascer e registra o modelo e a versão usados.

**Assinatura e adendos**

- **FR-006**: O autor DEVE assinar a entrada com reautenticação (regras da feature 005); a assinatura guarda pessoa, data e hora do servidor e resumo do conteúdo, e a entrada fica bloqueada.
- **FR-007**: Entrada assinada NÃO DEVE ser editada; correção só por adendo datado, assinado e imutável, sem apagar o original.
- **FR-008**: Entrada aberta além do prazo configurado [NEEDS CLARIFICATION: prazo para assinar: fim do dia, 24 h ou 7 dias?] DEVE aparecer como atrasada.
- **FR-009**: Entrada marcada como relevante para propriedade intelectual ou decisão do projeto DEVE exigir a assinatura de uma testemunha com acesso ao projeto, diferente do autor.

**Vínculos e promoção**

- **FR-010**: A entrada DEVE poder ser ligada a subdocumentos, lotes e estudos do mesmo projeto, com o vínculo visível nos dois sentidos; vínculos são acrescentados e retirados logicamente, nunca apagados.
- **FR-011**: Dados de um anexo CSV ou XLSX da entrada DEVEM poder ser promovidos para um estudo em elaboração pela importação da feature 007, registrando o vínculo de promoção nos dois sentidos.

**Consulta**

- **FR-012**: A linha do tempo do caderno de cada projeto DEVE listar as entradas por data, paginadas, com situação (aberta, atrasada, assinada, aguardando testemunha, testemunhada).
- **FR-013**: A busca DEVE encontrar entradas por palavra (busca textual em português), amostra, lote, pesquisador e período, só em projetos a que a pessoa tem acesso.
- **FR-014**: Criação, alteração, anexo, assinatura, testemunho, adendo, vínculo e promoção DEVEM gerar eventos na trilha de auditoria.

### Key Entities *(include if feature involves data)*

- **Entrada**: projeto, autor, data e hora, título, objetivo, hipótese, materiais, procedimento, resultados, conclusão, anexos, relevante (testemunha), situação, modelo usado.
- **Adendo**: entrada, texto, autor, data e hora, assinatura.
- **Modelo de entrada**: tipo de experimento, textos padrão, versão, ativo.
- **Vínculo**: entrada, registro ligado (subdocumento, lote ou estudo), tipo (relacionado ou promoção), quem ligou e quando, retirada.
- **Assinatura do caderno**: entrada ou adendo, pessoa, papel (autor ou testemunha), data e hora, resumo do conteúdo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, entrada assinada não é editada e só recebe adendo.
- **SC-002**: Em 100% dos testes, a busca por um lote traz todas as entradas que o usam.
- **SC-003**: Em 100% dos testes, dados promovidos para um estudo mantêm o vínculo nos dois sentidos.
- **SC-004**: A busca num caderno de 1.000 entradas responde em menos de 2 segundos.

## Assumptions

- A assinatura reaproveita a reautenticação da feature 005 (tentativas e bloqueio).
- O lembrete por e-mail fica para a feature 010; aqui a entrada aparece como atrasada.
- Integração direta com equipamentos está fora do escopo; importar arquivos basta.
