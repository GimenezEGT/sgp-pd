# Feature Specification: Dossiê técnico para a ANVISA

**Feature Branch**: `011-dossie-tecnico`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Geração do dossiê técnico para notificação ou registro na ANVISA, quando todos os dados necessários estiverem presentes. Leia docs/contexto/03-padroes-formatacao.md (seção Dossiê) e 04-requisitos-regulatorios.md. Objetivo: montar o dossiê a partir dos dados aprovados do projeto, no formato atual da empresa (itens I a XII), sem copiar e colar, mostrando antes o que falta. Histórias: 1. Como Assuntos Regulatórios, abro o dossiê de um projeto e vejo a checagem de completude: cada item exigido pelo art. 58 e pelo Anexo II da RDC 830/2023 para a classe de risco do produto, com a origem do dado e o status (completo, faltando, não aplicável com justificativa). 2. Gero o dossiê em DOCX e PDF com cabeçalho "Dossiê Técnico <produto>", rodapé com a razão social e numeração de páginas, itens em algarismos romanos, subitens em letras e números e tabelas numeradas. 3. Textos que não vêm de dados (ex.: processo de fabricação, unidade fabril) saem de uma biblioteca de textos padrão aprovados e versionados. 4. O dossiê termina com a declaração de responsabilidade do responsável técnico e legal (nome, registro no conselho, cidade e data) para assinatura. 5. Gero aditamentos: o sistema compara com a última versão enviada e destaca o que mudou. 6. Registro o envio (número do processo ou expediente, data) e o resultado da petição. Regras: só entram dados de versões aprovadas; produto de classe I gera o dossiê para arquivo, sem envio; itens "não aplicável" saem com a justificativa registrada na Entrada ou no estudo; uma família de produtos gera um dossiê com todos os kits da família."

## Clarifications

### Session 2026-11-11

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: A estrutura final foi conferida contra o Manual para Regularização de Dispositivos para Diagnóstico in Vitro (ANVISA, 25/08/2026)? → A: Ainda não; adota-se a estrutura I a XII do contexto (alinhada ao art. 58 e ao Anexo II), guardada numa definição declarativa que a Qualidade/AR ajusta sem programação; a conferência contra o Manual fica pendente com Assuntos Regulatórios antes do primeiro envio (ratificar com Assuntos Regulatórios).
- Q: Os anexos (rótulos, instrução de uso, gerenciamento de risco, imagens) são incorporados ao documento ou enviados como PDFs separados? → A: Seguem como arquivos separados num pacote junto com o dossiê; o dossiê traz a lista de anexos (número, nome, origem e resumo criptográfico) e cada item cita o anexo correspondente (ratificar com Assuntos Regulatórios).
- Q: Como o responsável técnico e legal assina? → A: O sistema gera a declaração com os dados do responsável e o bloco de assinatura; a assinatura é feita fora do sistema (certificado ICP-Brasil no PDF ou na plataforma de peticionamento) e, no registro do envio, Assuntos Regulatórios anexa o PDF assinado, arquivado com resumo criptográfico (ratificar com Assuntos Regulatórios e o Jurídico).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Checagem de completude por item (Priority: P1)

Assuntos Regulatórios abre o dossiê de um projeto e vê, item a item, o que o art. 58 e o Anexo II da RDC 830/2023 exigem para a classe de risco do produto, com a origem do dado e o status (completo, faltando, não aplicável com justificativa).

**Why this priority**: Mostra antes o que falta, evitando indeferimento por documentação ausente.

**Independent Test**: Abrir a checagem de um projeto de classe II sem estudo de estabilidade e conferir o item VII como faltando.

**Acceptance Scenarios**:

1. **Given** um projeto com a classe de risco aprovada na Entrada, **When** a pessoa abre a checagem, **Then** vê cada item exigido para a classe, com a origem e o status.
2. **Given** um item marcado como não aplicável na Entrada ou no estudo, **When** a checagem é feita, **Then** o item aparece como não aplicável com a justificativa registrada.
3. **Given** um item obrigatório faltando, **When** a pessoa tenta gerar o dossiê final, **Then** só o rascunho é gerado, com o item indicado.

---

### User Story 2 - Gerar o dossiê em DOCX e PDF (Priority: P1)

O dossiê é gerado em DOCX e PDF no formato da empresa: cabeçalho "Dossiê Técnico <produto>", rodapé com a razão social e o número da página, itens em algarismos romanos, subitens em letras e números e tabelas numeradas.

**Why this priority**: Substitui a montagem manual do dossiê.

**Independent Test**: Gerar o dossiê de um projeto completo e conferir a árvore de títulos I a XII, o cabeçalho e o rodapé.

**Acceptance Scenarios**:

1. **Given** um projeto completo, **When** o dossiê é gerado, **Then** os itens I a XII aparecem na estrutura definida, com o nome do produto em itálico, cabeçalho, rodapé e tabelas numeradas.
2. **Given** um dossiê gerado, **When** é consultado depois, **Then** está arquivado com versão e resumo criptográfico.

---

### User Story 3 - Biblioteca de textos padrão (Priority: P2)

Textos que não vêm de dados (processo de fabricação, unidade fabril) saem de uma biblioteca de textos padrão aprovados e versionados.

**Why this priority**: Padroniza os trechos repetidos entre dossiês.

**Independent Test**: Aprovar o texto "Unidade fabril", gerar o dossiê e conferir o texto no item X; alterar o texto e conferir que o dossiê antigo não muda.

**Acceptance Scenarios**:

1. **Given** um texto padrão aprovado, **When** o dossiê é gerado, **Then** o item usa a versão aprovada vigente e registra a versão usada.

---

### User Story 4 - Declaração de responsabilidade (Priority: P1)

O dossiê termina com a declaração do responsável técnico e legal (nome, registro no conselho, UF, cidade e data) para assinatura.

**Why this priority**: É exigida pela RDC 830/2023 (art. 56).

**Independent Test**: Gerar o dossiê e conferir a declaração com os dados do responsável.

**Acceptance Scenarios**:

1. **Given** o responsável técnico e legal cadastrado, **When** o dossiê é gerado, **Then** termina com a declaração, a cidade, a data e o bloco de assinatura.

---

### User Story 5 - Aditamentos (Priority: P2)

O sistema compara o dossiê com a última versão enviada e destaca o que mudou.

**Why this priority**: Facilita o aditamento ao peticionamento.

**Independent Test**: Registrar o envio, aprovar nova versão de um subdocumento, gerar de novo e conferir o item destacado.

**Acceptance Scenarios**:

1. **Given** um dossiê enviado e uma mudança aprovada depois, **When** o aditamento é gerado, **Then** os itens que mudaram aparecem destacados, com o texto anterior e o novo.

---

### User Story 6 - Registro do envio e do resultado (Priority: P2)

Assuntos Regulatórios registra o envio (número do processo ou expediente e data) e o resultado da petição.

**Why this priority**: Mantém o histórico regulatório do produto.

**Independent Test**: Registrar o envio e o deferimento e conferir no histórico do dossiê.

**Acceptance Scenarios**:

1. **Given** um dossiê gerado, **When** o envio é registrado, **Then** guarda número, data e versão enviada; **When** o resultado é registrado, **Then** guarda resultado e data.
2. **Given** um produto de classe I, **When** o dossiê é gerado, **Then** fica arquivado sem envio.

---

### Edge Cases

- Classe de risco não definida na Entrada aprovada: a checagem não roda e indica o que falta.
- Item não aplicável sem justificativa: conta como faltando.
- Família com um kit incompleto: o dossiê da família fica incompleto e mostra o kit.

## Requirements *(mandatory)*

### Functional Requirements

**Checagem**

- **FR-001**: A checagem DEVE listar, para a classe de risco do produto, cada item exigido pelo art. 58 e pelo Anexo II da RDC 830/2023 na estrutura I a XII do contexto, com a origem do dado e o status (completo, faltando, não aplicável com justificativa).
- **FR-002**: A definição dos itens, da aplicabilidade por classe e da origem de cada dado DEVE poder ser ajustada pela Qualidade/AR sem programação, com versões.
- **FR-003**: Só dados de versões aprovadas DEVEM entrar; item não aplicável DEVE sair com a justificativa registrada; não aplicável sem justificativa conta como faltando.

**Geração**

- **FR-004**: O dossiê DEVE ser gerado em DOCX e PDF no formato do contexto (cabeçalho, rodapé, itens em romanos, subitens, tabelas numeradas, nome do produto em itálico, não aplicável com justificativa).
- **FR-005**: Com item obrigatório faltando, só o rascunho DEVE ser gerado.
- **FR-006**: Os anexos (rótulos, instrução de uso, gerenciamento de risco, imagens) DEVEM seguir como arquivos separados num pacote com o dossiê, listados no dossiê com número, nome, origem e resumo criptográfico e citados nos itens.
- **FR-007**: O dossiê DEVE terminar com a declaração de responsabilidade do responsável técnico e legal (nome, conselho, UF, número, cidade e data) e o bloco de assinatura; a assinatura é feita fora do sistema e o PDF assinado é anexado no registro do envio.
- **FR-008**: Textos padrão (processo de fabricação, unidade fabril e outros) DEVEM vir de uma biblioteca versionada com aprovação, registrando a versão usada.
- **FR-009**: Uma família de produtos DEVE gerar um dossiê com todos os kits da família.
- **FR-010**: Cada dossiê gerado DEVE ser arquivado com versão, resumo criptográfico e as versões de origem.

**Envio e aditamento**

- **FR-011**: Assuntos Regulatórios DEVE registrar o envio (número do processo ou expediente, data, versão) e o resultado da petição; produto de classe I fica arquivado sem envio.
- **FR-012**: O aditamento DEVE comparar com a última versão enviada e destacar, item a item, o que mudou (textos e tabelas).
- **FR-013**: Checagem, geração, envio, resultado e aditamento DEVEM gerar eventos na trilha; só Qualidade/AR gera e registra envio; quem acessa o projeto consulta.

### Key Entities *(include if feature involves data)*

- **Definição do dossiê**: itens, aplicabilidade por classe, origem de cada dado, versão.
- **Texto padrão**: título, texto, versão, aprovação.
- **Dossiê gerado**: projeto ou família, versão, definição e textos usados, arquivos, resumo, situação (rascunho ou final).
- **Envio**: dossiê, número, data, resultado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, a checagem impede o dossiê final com item obrigatório faltando.
- **SC-002**: Em 100% dos testes, o aditamento destaca os itens que mudaram e só eles.
- **SC-003**: A árvore de títulos do dossiê gerado bate com a estrutura I a XII do contexto em 100% dos testes.
- **SC-004**: Assuntos Regulatórios confere o dossiê de um produto real sem retrabalho de estrutura (verificação manual).

## Assumptions

- A classe de risco vem do tópico "Classificação de Risco" da Entrada aprovada.
- Família de produtos: projetos com o mesmo nome de família do produto, a mesma tecnologia e a mesma classe de risco.
- Responsável técnico e legal, razão social e cidade vêm de configuração mantida pela Qualidade/AR.
- Estrutura, anexos e assinatura do responsável definidos nas respostas provisórias do esclarecimento (sessão 2026-11-11).
