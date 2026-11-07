# Feature Specification: Fundação — acesso, perfis e trilha de auditoria

**Feature Branch**: `001-fundacao-acesso-auditoria`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Fundação do SGP-P&D: acesso, perfis e trilha de auditoria. Leia docs/contexto/01-visao-geral.md e docs/contexto/04-requisitos-regulatorios.md. Contexto: o sistema roda na intranet e guarda registros de controle de projeto sujeitos às Boas Práticas de Fabricação (RDC 665/2022). Só pessoas autorizadas entram, e tudo o que acontece precisa ser rastreável. Perfis: Administrador do sistema; Gestor de P&D; Líder de projeto; Analista/Pesquisador; Qualidade/Assuntos Regulatórios (leitura ampla e revisão); Leitor (consulta). Uma pessoa pode ter mais de um perfil. O acesso a cada projeto depende de ser membro dele, exceto para Gestor de P&D, Qualidade e Administrador. Histórias: 1. Como colaborador, entro com meu usuário e senha de rede; sem perfil no sistema, vejo como pedir acesso. 2. Como administrador, concedo e revogo perfis; cada mudança de permissão registra quem fez, quando e por quê. 3. Como usuário, minha sessão expira após inatividade configurável e o login bloqueia após tentativas inválidas, conforme a política da TI. 4. Como auditor da Qualidade, consulto a trilha de auditoria por usuário, projeto, período e tipo de evento, e exporto o resultado. 5. Como Garantia da Qualidade, preciso provar que a trilha não foi adulterada: o sistema verifica a integridade da cadeia de eventos e aponta qualquer quebra. Regras: nenhum registro é apagado fisicamente; data e hora vêm do servidor sincronizado; eventos guardam valor anterior, valor novo e motivo quando houver; colaborador desativado na rede perde o acesso no próximo login. Fora do escopo: projetos e documentos (features seguintes)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entrar com o login de rede (Priority: P1)

O colaborador abre o sistema na intranet e entra com o mesmo usuário e senha que usa na rede da empresa. Quem já tem perfil cai na página inicial com as funções do seu perfil. Quem ainda não tem perfil não acessa nenhuma função: vê uma página explicando como pedir acesso e pode registrar uma solicitação com justificativa, que fica visível para o Administrador.

**Why this priority**: Sem entrada controlada nenhuma outra função pode existir; é o primeiro requisito de segurança (princípio VII) e o ponto de partida da rastreabilidade (toda ação passa a ter autor).

**Independent Test**: Com uma conta de rede de teste com perfil e outra sem perfil, entrar com cada uma: a primeira chega à página inicial; a segunda vê só a página de pedido de acesso e é recusada em qualquer outra página.

**Acceptance Scenarios**:

1. **Given** um colaborador ativo na rede e com perfil ativo no sistema, **When** informa usuário e senha de rede corretos, **Then** entra na página inicial e o login fica registrado na trilha.
2. **Given** um colaborador ativo na rede sem nenhum perfil ativo, **When** entra com credenciais corretas, **Then** vê a página "Solicitar acesso" com as instruções e é recusado ao tentar abrir qualquer outra página, com o acesso negado registrado na trilha.
3. **Given** um colaborador sem perfil na página "Solicitar acesso", **When** envia uma solicitação com justificativa, **Then** a solicitação fica registrada com data e hora do servidor e aparece na lista de solicitações pendentes do Administrador.
4. **Given** um colaborador desativado na rede, **When** tenta entrar, **Then** o login é recusado com mensagem genérica e a tentativa fica registrada.
5. **Given** o primeiro login de um colaborador, **When** a autenticação é aceita, **Then** o cadastro da pessoa é criado com login, nome, e-mail e função vindos da rede, e a criação fica na trilha.

---

### User Story 2 - Conceder e revogar perfis com motivo (Priority: P1)

O Administrador do sistema consulta as pessoas cadastradas, vê os perfis ativos e o histórico de cada uma, concede e revoga perfis informando o motivo e a referência da aprovação. Nada é apagado: uma revogação encerra a concessão, que continua no histórico.

**Why this priority**: Perfis definem o que cada pessoa pode fazer nas features seguintes; a RDC 665/2022 e o princípio II exigem que toda mudança de permissão seja rastreável.

**Independent Test**: Conceder o perfil Analista/Pesquisador a uma pessoa e depois revogá-lo, conferindo que a pessoa ganha e perde o acesso e que a trilha mostra as duas mudanças com autor, data, hora, motivo e aprovação.

**Acceptance Scenarios**:

1. **Given** um Administrador e uma pessoa sem perfil, **When** concede o perfil Analista/Pesquisador informando motivo e referência da aprovação, **Then** a pessoa passa a ter o perfil e a trilha registra quem concedeu, quando, motivo, aprovação, valor anterior e valor novo.
2. **Given** uma pessoa com o perfil Leitor, **When** o Administrador o revoga informando o motivo, **Then** o perfil deixa de valer imediatamente, a concessão continua no histórico com a data de revogação e a trilha registra a mudança.
3. **Given** uma concessão ou revogação sem motivo, **When** o Administrador tenta salvar, **Then** o sistema recusa com mensagem clara.
4. **Given** uma pessoa com vários perfis, **When** abre o sistema, **Then** tem acesso à soma das funções de todos os seus perfis ativos.
5. **Given** que só existe um Administrador ativo, **When** ele tenta revogar o próprio perfil de Administrador, **Then** o sistema recusa, para que o sistema nunca fique sem administrador.
6. **Given** um usuário sem o perfil Administrador, **When** tenta abrir a gestão de perfis, **Then** o acesso é negado e registrado.

---

### User Story 3 - Provar que a trilha não foi adulterada (Priority: P1)

A Garantia da Qualidade precisa demonstrar, numa inspeção ou na validação do sistema, que nenhum evento da trilha foi alterado, inserido ou apagado fora do sistema. O sistema verifica a cadeia de eventos todos os dias e sob demanda, e aponta qualquer quebra.

**Why this priority**: A trilha só tem valor de evidência se a integridade puder ser provada; é critério de pronto da feature e base para todas as outras.

**Independent Test**: Gerar eventos, alterar um deles diretamente no armazenamento (fora do sistema) e rodar a verificação: o resultado aponta o evento adulterado.

**Acceptance Scenarios**:

1. **Given** uma trilha íntegra, **When** a verificação roda, **Then** o resultado é "Íntegra", com o número de eventos verificados e a identificação do último evento.
2. **Given** um evento cujo conteúdo foi alterado direto no armazenamento, **When** a verificação roda, **Then** o resultado aponta esse evento e o tipo de quebra "conteúdo alterado".
3. **Given** um evento apagado ou inserido direto no armazenamento, **When** a verificação roda, **Then** o resultado aponta a posição da quebra na sequência.
4. **Given** uma quebra detectada, **When** Qualidade/AR ou Administrador abrem o sistema, **Then** veem o alerta de quebra até que uma nova verificação volte a dar "Íntegra".
5. **Given** a rotina diária, **When** chega o horário configurado, **Then** a verificação roda sem ação humana e o resultado fica registrado.

---

### User Story 4 - Consultar e exportar a trilha de auditoria (Priority: P2)

O auditor da Qualidade filtra a trilha por usuário, projeto, período e tipo de evento, vê os eventos com data e hora, autor, objeto, valor anterior, valor novo e motivo, e exporta o resultado filtrado para planilha.

**Why this priority**: É a forma de usar a trilha em auditorias internas, inspeções e investigações; depende de existirem eventos (histórias 1 a 3).

**Independent Test**: Com eventos de vários usuários e tipos, aplicar filtros combinados e exportar: o arquivo traz exatamente os eventos filtrados, os filtros usados e a data e hora da exportação, e a exportação aparece na trilha.

**Acceptance Scenarios**:

1. **Given** eventos de vários usuários, **When** o auditor filtra por um usuário e um período, **Then** vê só os eventos daquele usuário naquele período, em ordem cronológica e paginados.
2. **Given** eventos de tipos diferentes, **When** filtra por tipo de evento, **Then** vê só os eventos daquele tipo.
3. **Given** eventos ligados a um projeto, **When** filtra pelo projeto, **Then** vê só os eventos daquele projeto.
4. **Given** um resultado filtrado, **When** exporta em CSV ou XLSX, **Then** o arquivo contém os mesmos eventos da tela, os filtros aplicados e a data e hora da exportação, e a exportação é registrada na trilha com os filtros.
5. **Given** um usuário sem perfil de consulta à trilha, **When** tenta abrir a trilha, **Then** o acesso é negado e registrado.

---

### User Story 5 - Sessão com expiração e bloqueio por tentativas (Priority: P2)

A sessão de quem deixa o sistema aberto e sem uso expira após o tempo de inatividade definido pela TI. Depois de um número de tentativas de senha inválidas seguidas, o login daquele usuário fica bloqueado por um período, conforme a política da TI.

**Why this priority**: Protege contra uso indevido de sessão aberta e contra tentativa de adivinhação de senha; os parâmetros vêm da política da TI.

**Independent Test**: Com tempo de inatividade e limite de tentativas configurados com valores baixos, deixar a sessão parada além do limite e errar a senha até o limite, conferindo o encerramento, o bloqueio, as mensagens e os eventos.

**Acceptance Scenarios**:

1. **Given** uma sessão parada além do tempo configurado, **When** o usuário volta a usar o sistema, **Then** é levado ao login com a mensagem de sessão expirada e o encerramento fica na trilha.
2. **Given** um usuário que errou a senha o número configurado de vezes seguidas, **When** tenta de novo dentro do período de bloqueio, mesmo com a senha certa, **Then** o login é recusado com a mensagem de bloqueio e a tentativa não é enviada à rede.
3. **Given** um login bloqueado, **When** o período de bloqueio termina, **Then** o usuário volta a poder entrar.
4. **Given** um login bloqueado, **When** o Administrador desbloqueia informando o motivo, **Then** o usuário volta a poder entrar e o desbloqueio fica na trilha.
5. **Given** um login com senha certa antes de atingir o limite, **When** entra, **Then** a contagem de tentativas inválidas recomeça.

---

### Edge Cases

- Serviço de autenticação da rede indisponível: o login é recusado com a mensagem "Serviço de autenticação indisponível. Tente novamente ou acione a TI.", o evento é registrado e não existe forma alternativa de entrada.
- Tentativas com usuário inexistente na rede: são contadas e bloqueadas como as demais, e a mensagem é a mesma de senha inválida, para não revelar quais usuários existem.
- Nome, e-mail ou função alterados na rede: o cadastro é atualizado no próximo login e a mudança vai para a trilha com valor anterior e novo.
- Pessoa retirada de um grupo da rede mapeado para perfil: o perfil sincronizado é revogado no próximo login; perfis concedidos manualmente não são afetados.
- Concessão de um perfil que a pessoa já tem ativo: recusada com mensagem, sem criar concessão duplicada.
- Dois eventos gravados ao mesmo tempo: a cadeia continua única e sequencial, sem bifurcação nem lacuna.
- Exclusão do último trecho da trilha (eventos mais recentes) fora do sistema: detectada pela verificação seguinte ao confrontar o último ponto de controle registrado.
- Exportação sem eventos no filtro: o arquivo é gerado só com cabeçalho e a indicação de zero eventos, e a exportação é registrada.
- Relógio do computador do usuário errado: irrelevante, pois data e hora sempre vêm do servidor.
- Pessoa com sessão aberta que perde o último perfil: as próximas páginas passam a ser recusadas e ela vê a página de pedido de acesso.

## Requirements *(mandatory)*

### Functional Requirements

**Autenticação e sessão**

- **FR-001**: O sistema DEVE autenticar os colaboradores somente com o usuário e a senha de rede da empresa, sem guardar a senha.
- **FR-002**: No primeiro login aceito, o sistema DEVE criar o cadastro da pessoa com login, nome, e-mail e função vindos da rede, e DEVE atualizá-los a cada login, registrando na trilha a criação e cada alteração com valor anterior e novo.
- **FR-003**: Pessoa autenticada sem perfil ativo NÃO DEVE acessar nenhuma função; DEVE ver a página "Solicitar acesso", com as instruções para pedir acesso, e poder registrar uma solicitação com justificativa obrigatória.
- **FR-004**: O login de colaborador desativado na rede, com senha inválida ou com usuário inexistente DEVE ser recusado com a mesma mensagem genérica; o sistema NÃO DEVE oferecer forma alternativa de entrada.
- **FR-005**: O sistema DEVE encerrar a sessão após um tempo de inatividade configurável, levar o usuário ao login com a mensagem de sessão expirada e registrar o encerramento.
- **FR-006**: O sistema DEVE bloquear o login de um usuário depois de um número configurável de tentativas inválidas seguidas, por um período configurável; durante o bloqueio a tentativa NÃO DEVE ser enviada à rede; um login aceito zera a contagem.
- **FR-007**: O Administrador DEVE poder desbloquear um login antes do fim do período, informando o motivo.
- **FR-008**: O usuário DEVE poder sair (logout) de qualquer página.

**Perfis e permissões**

- **FR-009**: O sistema DEVE oferecer os perfis Administrador do sistema, Gestor de P&D, Líder de projeto, Analista/Pesquisador, Qualidade/Assuntos Regulatórios e Leitor; uma pessoa DEVE poder ter vários perfis ativos, e suas permissões são a soma deles.
- **FR-010**: Só o Administrador DEVE conceder e revogar perfis; cada concessão e revogação DEVE exigir motivo e referência da aprovação e registrar autor, data e hora.
- **FR-011**: Revogar um perfil NÃO DEVE apagar a concessão; o histórico de concessões e revogações de cada pessoa DEVE ficar consultável.
- **FR-012**: O sistema NÃO DEVE permitir revogar o perfil do último Administrador ativo.
- **FR-013**: Quando houver mapeamento configurado entre grupos da rede e perfis, o sistema DEVE, a cada login, conceder os perfis dos grupos a que a pessoa pertence e revogar os perfis sincronizados de grupos a que ela não pertence mais, registrando cada mudança com o grupo como origem; concessões manuais NÃO DEVEM ser revogadas pela sincronização.
- **FR-014**: O acesso a cada projeto DEVE depender de a pessoa ser membro dele, exceto para os perfis Gestor de P&D, Qualidade/Assuntos Regulatórios e Administrador, que acessam todos os projetos; a regra DEVE ser única e reutilizada pelas features que criam projetos e documentos.
- **FR-015**: Toda tentativa de abrir uma função sem permissão DEVE ser recusada e registrada na trilha.
- **FR-016**: O Administrador DEVE ver as solicitações de acesso pendentes e marcá-las como atendidas ou recusadas, com motivo.

**Trilha de auditoria**

- **FR-017**: O sistema DEVE registrar, no mínimo, os eventos: login aceito, login recusado, logout, encerramento por inatividade, bloqueio e desbloqueio de login, solicitação de acesso e sua decisão, criação e alteração de cadastro de pessoa, concessão e revogação de perfil, acesso negado, exportação da trilha e verificação de integridade.
- **FR-018**: Cada evento DEVE guardar data e hora do servidor, autor (pessoa ou "sistema"), tipo, objeto afetado, projeto quando houver, valor anterior, valor novo, motivo quando houver e endereço de origem da requisição.
- **FR-019**: A trilha DEVE ser somente de inclusão: o sistema NÃO DEVE oferecer edição nem exclusão de eventos, e o armazenamento DEVE recusar alteração e exclusão feitas pela aplicação.
- **FR-020**: Cada evento DEVE ser encadeado ao anterior por um resumo criptográfico, numa sequência sem lacunas, de modo que alteração, inserção ou exclusão de evento fora do sistema seja detectável.
- **FR-021**: O sistema DEVE verificar a integridade de toda a cadeia uma vez por dia, sem ação humana, e sob demanda pelos perfis Qualidade/AR e Administrador; o resultado DEVE informar "Íntegra" ou a posição e o tipo de cada quebra (conteúdo alterado, encadeamento rompido, lacuna na sequência, último ponto de controle ausente ou divergente), e DEVE ficar registrado.
- **FR-022**: Enquanto a última verificação indicar quebra, o sistema DEVE exibir um alerta aos perfis Qualidade/AR e Administrador.
- **FR-023**: Os perfis Qualidade/AR, Gestor de P&D e Administrador DEVEM consultar a trilha com filtros combináveis por usuário, projeto, período e tipo de evento, em ordem cronológica e com paginação.
- **FR-024**: O resultado filtrado DEVE ser exportável em CSV e XLSX, com os filtros aplicados e a data e hora da exportação no arquivo; cada exportação DEVE gerar um evento com os filtros e a quantidade de eventos exportados.
- **FR-025**: Datas e horas DEVEM vir do servidor, ser gravadas sem ambiguidade de fuso e exibidas no horário de Brasília (America/Sao_Paulo).
- **FR-026**: Nenhum cadastro de pessoa, concessão de perfil, solicitação de acesso, tentativa de login, verificação ou evento DEVE ser apagado fisicamente; pessoas saem de uso por desativação.

### Key Entities *(include if feature involves data)*

- **Pessoa (usuário)**: colaborador que entrou ao menos uma vez; login de rede (único), nome, e-mail, função, situação (ativa/inativa), data do primeiro e do último login.
- **Perfil**: um dos seis papéis fixos do sistema (Administrador, Gestor de P&D, Líder de projeto, Analista/Pesquisador, Qualidade/AR, Leitor).
- **Concessão de perfil**: ligação pessoa × perfil com início, concedido por, motivo, referência da aprovação e origem (manual ou grupo da rede); quando revogada, data, revogado por e motivo da revogação. Nunca é apagada.
- **Solicitação de acesso**: pedido de uma pessoa sem perfil, com justificativa, data e hora, situação (pendente, atendida, recusada), quem decidiu e motivo.
- **Tentativa de login**: usuário informado, data e hora, resultado (aceita, recusada, bloqueada) e endereço de origem; base do bloqueio por tentativas.
- **Evento de auditoria**: posição na sequência, data e hora do servidor, autor, tipo, objeto, projeto, valor anterior, valor novo, motivo, endereço de origem, resumo do evento anterior e resumo próprio.
- **Verificação de integridade**: data e hora, origem (rotina diária ou sob demanda, e por quem), quantidade de eventos verificados, resultado, quebras encontradas e ponto de controle (último evento e seu resumo).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um colaborador com perfil entra no sistema com as credenciais de rede em até 5 segundos em 95% das tentativas, com o serviço de rede disponível.
- **SC-002**: 100% das páginas funcionais recusam pessoa sem perfil e pessoa sem a permissão exigida, conferido por uma varredura de todas as páginas.
- **SC-003**: Em 100% dos testes de adulteração (alterar, inserir e apagar evento direto no armazenamento), a verificação aponta a posição e o tipo da quebra.
- **SC-004**: 100% das concessões e revogações de perfil têm autor, data e hora, motivo e referência da aprovação registrados.
- **SC-005**: Um auditor obtém a trilha de um mês filtrada por usuário e tipo de evento e a exporta em menos de 1 minuto, com 500 mil eventos na base.
- **SC-006**: Em 100% dos casos de teste, a sessão parada além do limite é encerrada e a tentativa que atinge o limite bloqueia o login pelo período configurado.
- **SC-007**: A verificação completa de uma trilha com 1 milhão de eventos termina em menos de 15 minutos.

## Assumptions

- A autenticação usa o Active Directory da empresa, acessível a partir do servidor da intranet; a TI fornece uma conta de serviço de consulta e um ambiente de homologação.
- O horário do servidor é sincronizado pela TI (NTP); o sistema não confia no horário do computador do usuário.
- Os parâmetros de segurança (tempo de inatividade, número de tentativas e período de bloqueio) são definidos pela TI e alterados por configuração controlada da implantação; os valores iniciais estão em Clarifications até a confirmação da TI.
- Os seis perfis são fixos nesta feature; as permissões finas de cada perfil sobre projetos e documentos são detalhadas nas features 002 a 012.
- O primeiro Administrador é designado na implantação por um procedimento da TI, registrado na trilha.
- Projetos ainda não existem nesta feature: o filtro por projeto e a regra de acesso por projeto são entregues prontos para uso pelas features seguintes.
- A estrutura e os rótulos de tela seguem o português do Brasil; os perfis usam os nomes do plano.
