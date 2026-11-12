# Feature Specification: Cópia de segurança, restauração e qualificação do sistema

**Feature Branch**: `014-copia-seguranca-qualificacao`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Cópia de segurança, restauração e qualificação do sistema (entregáveis de validação e implantação do plano): cópia de segurança diária do banco e dos arquivos com teste de restauração (RDC 665/2022, art. 35; constituição, restrições), qualificação de instalação (roteiro de implantação executado no servidor, com evidências), qualificação de operação (testes automatizados mais roteiros manuais dos fluxos críticos: assinatura, auditoria, geração), matriz de rastreabilidade gerada por script e, na operação, backup diário com teste de restauração mensal, revisão trimestral de acessos e revalidação periódica (art. 105)."

## Clarifications

### Session 2026-11-12

Respostas provisórias: a recomendação de cada pergunta foi adotada para não bloquear o desenvolvimento e precisa ser ratificada pelo responsável indicado antes do uso oficial.

- Q: Onde as cópias são gravadas, separadas dos dados do sistema? → A: Num diretório definido pela TI e montado de outro servidor ou compartilhamento da rede da empresa, nunca no disco dos dados; a segunda cópia fora do prédio é procedimento da TI sobre esse destino (ratificar com a TI).
- Q: Por quanto tempo ficam as cópias diárias e as mensais? → A: As diárias por 35 dias; a primeira cópia bem-sucedida de cada mês fica sem remoção automática (ratificar com a TI e a Garantia da Qualidade).
- Q: O sistema cifra as cópias ou o controle de acesso do destino protege o conteúdo? → A: O sistema não cifra; o destino tem acesso restrito à TI e cifragem do armazenamento feita pela infraestrutura (ratificar com a TI e a Garantia da Qualidade).
- Q: Quem executa as qualificações de instalação e de operação, e por onde? → A: A de instalação só a TI, pela linha de comando no servidor ou pela tela de operação; a de operação a TI (linha de comando ou tela) e a Garantia da Qualidade (tela) (ratificar com a TI e a Garantia da Qualidade).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cópia de segurança diária (Priority: P1)

Todo dia, sem intervenção, o sistema copia o banco de dados e todos os arquivos guardados (anexos, documentos gerados, certificados) para o destino de cópias definido pela TI, com um manifesto que permite conferir a integridade da cópia.

**Why this priority**: A RDC 665/2022 (art. 35) exige cópia de segurança de todos os documentos e registros digitais; sem ela o sistema não pode ser usado oficialmente.

**Independent Test**: Executar a cópia e conferir no destino o banco copiado, os arquivos e o manifesto com resumos e contagens; conferir o registro na trilha e na tela da TI.

**Acceptance Scenarios**:

1. **Given** o horário agendado, **When** a cópia roda, **Then** o banco e os arquivos são copiados num ponto consistente no tempo, o manifesto registra resumos, contagens e o último evento da trilha, e o resultado aparece para a TI e na trilha.
2. **Given** um arquivo já copiado antes, **When** a cópia seguinte roda, **Then** o arquivo não é copiado de novo, mas continua listado e conferido no manifesto.
3. **Given** o destino indisponível ou igual ao diretório dos dados, **When** a cópia roda, **Then** ela falha com o motivo registrado e os administradores são avisados.

---

### User Story 2 - Teste de restauração (Priority: P1)

Todo mês, e quando a TI pedir, o sistema restaura a cópia mais recente num banco isolado e confere se ela recupera tudo: banco, trilha íntegra e arquivos.

**Why this priority**: Cópia que não restaura não protege os registros; o teste é a evidência pedida pela constituição e pelo plano (teste de restauração mensal).

**Independent Test**: Fazer uma cópia, executar o teste e conferir as conferências aprovadas; danificar a cópia e conferir que o teste reprova e avisa.

**Acceptance Scenarios**:

1. **Given** uma cópia bem-sucedida, **When** o teste de restauração roda, **Then** a cópia é restaurada num banco isolado, sem tocar no banco em uso, e são conferidos os resumos, as contagens por tabela, a cadeia da trilha até o último evento do manifesto e todos os arquivos referenciados; o banco isolado é descartado ao fim.
2. **Given** uma cópia com arquivo alterado ou ausente, **When** o teste roda, **Then** ele reprova apontando o item e avisa os administradores.

---

### User Story 3 - Qualificação de instalação (Priority: P2)

Na implantação (homologação e produção), a TI executa no servidor uma verificação automatizada da instalação e guarda o relatório como evidência.

**Why this priority**: A qualificação de instalação (IQ) é entregável da validação exigida antes do uso oficial (RDC 665/2022, arts. 104 a 106).

**Independent Test**: Executar a verificação numa instalação correta (todos os itens aprovados) e numa com configuração inválida (itens reprovados com motivo).

**Acceptance Scenarios**:

1. **Given** uma instalação, **When** a TI executa a qualificação de instalação, **Then** o sistema confere cada item (versões, serviços, banco, segurança, fuso, variáveis, certificado do selo, destino de cópias, ferramentas de geração) e gera um relatório em PDF com data, executor, versão do sistema e resultado de cada item.
2. **Given** uma configuração inválida (ex.: modo de depuração ligado, migração pendente), **When** a verificação roda, **Then** o item aparece reprovado com o motivo e o resultado geral é reprovado.

---

### User Story 4 - Qualificação de operação (Priority: P2)

No ambiente instalado, a TI ou a Garantia da Qualidade executa conferências operacionais automatizadas que não alteram dados e segue os roteiros manuais dos fluxos críticos; tudo fica guardado como evidência.

**Why this priority**: A qualificação de operação (OQ) é entregável da validação; reaproveita a suíte automatizada e acrescenta conferências no ambiente real.

**Independent Test**: Executar a qualificação de operação e conferir o relatório com trilha íntegra, imutabilidade efetiva, PDF de teste gerado e selado, agendamentos e cópias em dia.

**Acceptance Scenarios**:

1. **Given** o sistema instalado, **When** a qualificação de operação roda, **Then** confere a trilha, a imutabilidade e os privilégios efetivos (com tentativas desfeitas), a geração e o selo de um PDF de teste em memória, os agendamentos, a cópia e o teste de restauração em dia e as integrações configuradas, sem alterar dados, e gera o relatório em PDF.
2. **Given** os roteiros manuais dos fluxos críticos, **When** a Garantia da Qualidade os executa, **Then** registra o resultado de cada passo no roteiro versionado com o sistema.

---

### User Story 5 - Revisão periódica de acessos (Priority: P3)

A cada trimestre, a TI e a Garantia da Qualidade revisam quem tem acesso ao sistema, a partir de uma exportação com pessoas, perfis, papéis nos projetos e último acesso.

**Why this priority**: O plano prevê revisão trimestral de acessos na operação; a exportação dá a base da revisão.

**Independent Test**: Exportar a lista e conferir perfis ativos, quem concedeu, papéis por projeto e último acesso.

**Acceptance Scenarios**:

1. **Given** pessoas com perfis e papéis em projetos, **When** a TI ou a Qualidade exporta a revisão de acessos, **Then** recebe CSV ou XLSX com situação da conta, perfis ativos (data e quem concedeu), papéis por projeto e último acesso, e a exportação vai para a trilha.

---

### Edge Cases

- Cópia pedida enquanto outra está em andamento: recusada; uma cópia por vez.
- Arquivo guardado ausente do armazenamento na hora da cópia: a cópia reprova listando os ausentes.
- Teste de restauração sem nenhuma cópia bem-sucedida: reprova e avisa.
- Banco isolado de um teste anterior interrompido: descartado antes do novo teste.
- Nenhuma cópia bem-sucedida nas últimas 26 horas (ex.: agendador parado): os administradores são avisados.
- Serviço externo não configurado no ambiente: integração com o Sankhya desligada é "não aplicável" (a exportação de contingência da feature 012 está prevista); diretório (LDAP) e envio de e-mail são obrigatórios e o item reprova.
- Qualificação reprovada: fica registrada com o relatório e os itens reprovados; depois da correção, executa-se de novo e as duas execuções ficam no histórico; o uso oficial depende da liberação pela Garantia da Qualidade.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE fazer, todo dia e sem intervenção, a cópia de segurança do banco de dados e de todos os arquivos guardados, num ponto consistente no tempo e sem interromper o uso.
- **FR-002**: Cada cópia DEVE ter um manifesto com data e hora, versão do sistema, tamanho e resumo SHA-256 do banco copiado, contagem de registros por tabela, último evento da trilha (sequência e resumo) e a lista de arquivos com resumos; o resumo do manifesto fica registrado no sistema.
- **FR-003**: As cópias DEVEM ser gravadas num destino definido pela TI, montado de outro servidor ou compartilhamento da rede da empresa e nunca no diretório dos dados do sistema; com o destino indisponível ou igual ao diretório dos dados, a cópia falha com o motivo registrado. A segunda cópia fora do prédio é procedimento da TI sobre esse destino.
- **FR-004**: Os arquivos guardados, que nunca mudam, DEVEM ser copiados uma única vez para o destino, identificados pelo resumo do conteúdo, e conferidos pelo resumo na cópia.
- **FR-005**: As cópias diárias DEVEM ser mantidas por 35 dias e a primeira cópia bem-sucedida de cada mês sem remoção automática; os arquivos copiados nunca são removidos; cada remoção de cópia vai para a trilha.
- **FR-006**: O sistema DEVE testar a restauração todo mês e quando a TI pedir, restaurando a cópia bem-sucedida mais recente num banco isolado, sem tocar no banco em uso, e conferindo: resumos do manifesto e do banco copiado, restauração sem erro, contagem de registros por tabela igual à do manifesto, cadeia da trilha íntegra até o último evento do manifesto e presença e resumo de todos os arquivos referenciados; o banco isolado é descartado ao fim.
- **FR-007**: O resultado de cada cópia, remoção e teste de restauração DEVE ir para a trilha e ficar visível para a TI e a Garantia da Qualidade, com as conferências item a item.
- **FR-008**: Falha de cópia ou de teste de restauração, ou falta de cópia bem-sucedida nas últimas 26 horas, DEVE avisar por e-mail os administradores do sistema.
- **FR-009**: Só a TI (Administrador do sistema) DEVE poder pedir cópia ou teste de restauração fora do agendamento; restaurar sobre o banco em uso NÃO DEVE existir na interface e fica no procedimento documentado de recuperação, executado pela TI no servidor.
- **FR-010**: O conteúdo das cópias (resultados, custos e projeções do P&D) DEVE ficar protegido pelo controle de acesso do destino, restrito à TI, e pela cifragem do armazenamento feita pela infraestrutura; o sistema não cifra as cópias e nenhuma tela permite baixá-las.
- **FR-011**: Só a TI DEVE poder executar a qualificação de instalação, pela linha de comando no servidor ou pela tela de operação; ela confere versões dos componentes contra o fixado no repositório, serviços acessíveis, migrações aplicadas, gatilhos de imutabilidade e privilégios do banco, configurações de segurança, fuso de exibição e datas em UTC, variáveis obrigatórias presentes (sem expor valores), certificado do selo válido, destino de cópias gravável e ferramentas e fontes da geração de documentos, e gera relatório em PDF com data, executor, versão do sistema e resultado de cada item.
- **FR-012**: A TI (linha de comando ou tela de operação) e a Garantia da Qualidade (tela de operação) DEVEM poder executar no ambiente instalado a qualificação de operação, que, sem alterar dados, confere a cadeia da trilha, a imutabilidade e os privilégios efetivos com tentativas desfeitas, a geração e o selo de um PDF de teste em memória, os agendamentos, a cópia e o teste de restauração em dia e as integrações configuradas, e gera relatório em PDF.
- **FR-013**: Os relatórios de qualificação DEVEM ficar guardados no sistema com resumo SHA-256 e listados com data, tipo, executor, versão e resultado para a TI e a Garantia da Qualidade; cada execução vai para a trilha.
- **FR-014**: A TI e a Garantia da Qualidade DEVEM poder exportar em CSV e XLSX a revisão de acessos: pessoas com situação da conta, perfis ativos (data e quem concedeu), papéis por projeto e último acesso; cada exportação vai para a trilha.
- **FR-015**: Os roteiros de qualificação de instalação e de operação (incluindo os roteiros manuais de assinatura, auditoria e geração) e o procedimento de recuperação DEVEM ficar no repositório, versionados com o sistema.

### Key Entities *(include if feature involves data)*

- **Cópia de segurança**: tipo (agendada ou pedida), início e fim, situação, local no destino, resumo e tamanho do banco copiado, contagens por tabela, último evento da trilha, arquivos (total e novos), resumo do manifesto, motivo da falha, quem pediu.
- **Teste de restauração**: cópia testada, início e fim, situação, conferências item a item, motivo da falha, quem pediu.
- **Execução de qualificação**: tipo (instalação ou operação), executor, versão do sistema, itens com resultado, resultado geral, relatório em PDF guardado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes, a cópia restaurada num banco isolado reproduz a contagem de registros por tabela, a cadeia da trilha e os arquivos com resumo conferido.
- **SC-002**: Em 100% dos testes de dano (banco copiado ou arquivo alterado ou ausente), o teste de restauração reprova apontando o item e avisa os administradores.
- **SC-003**: Em 100% dos testes com configuração inválida, a qualificação de instalação reprova o item com o motivo.
- **SC-004**: IQ e OQ executadas no servidor de homologação, com relatórios guardados no sistema e roteiros manuais executados e assinados pela Garantia da Qualidade (verificação manual).

## Assumptions

- A TI provê o servidor, o destino de cópias e o envio de e-mail; o banco é o PostgreSQL do próprio ambiente.
- A qualificação de desempenho (piloto com projeto real), o plano e o relatório de validação são da Garantia da Qualidade; o sistema fornece as evidências (especificações, matriz, relatórios de IQ e OQ, cópias e testes de restauração).
- O teste de restauração usa o mesmo servidor de banco, num banco isolado e descartável.
- Destino, retenção, proteção das cópias e quem executa as qualificações definidos nas respostas provisórias do esclarecimento (sessão 2026-11-12).
