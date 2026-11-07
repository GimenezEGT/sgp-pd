# Research: Fundação — acesso, perfis e trilha de auditoria

Decisões técnicas da Fase 0. Nenhum item do Technical Context ficou como NEEDS CLARIFICATION. As
versões foram conferidas no PyPI, no npm e no Docker Hub em 2026-11-07.

## R1. Linguagem, framework e versões

- **Decision**: Python 3.12 e Django 5.2 LTS (5.2.19), com dependências fixadas em `uv.lock`.
- **Rationale**: o plano pede a "versão LTS vigente"; a 5.2 é a LTS suportada até abril de 2028 (a
  6.1 não é LTS e a 6.2 LTS só sai em 2027). Python 3.12 é a versão mínima pedida e tem rodas para
  todas as dependências, inclusive python-ldap compilado na imagem.
- **Alternatives considered**: Django 6.1 (sem LTS, ciclo de suporte curto para um sistema
  validado); .NET (plano B da TI, não necessário).

## R2. Banco de dados e papéis

- **Decision**: PostgreSQL 17 com dois papéis: `sgp_owner` (dono do esquema, roda migrações e
  testes) e `sgp_app` (aplicação em execução). O comando `apply_db_privileges`, executado depois de
  cada `migrate`, concede ao `sgp_app` SELECT, INSERT e UPDATE em todas as tabelas e sequências,
  DELETE só em `django_session`, e revoga UPDATE das tabelas append-only. Nenhum TRUNCATE é
  concedido.
- **Rationale**: o plano exige trilha "sem UPDATE e DELETE por permissão do usuário de banco"; tirar
  o DELETE de todas as tabelas de negócio aplica o "nada é apagado" também no banco. A tabela de
  sessões precisa de DELETE porque o logout remove a sessão.
- **Alternatives considered**: um papel único (não impede adulteração pela aplicação); privilégios
  por `ALTER DEFAULT PRIVILEGES` (valem por banco e não alcançam o banco de testes).

## R3. Autenticação no Active Directory

- **Decision**: django-auth-ldap 5.4 + python-ldap 3.4. Busca do usuário por filtro configurável
  (`(sAMAccountName=%(user)s)` no AD; `(uid=%(user)s)` no OpenLDAP de desenvolvimento), bind com a
  senha digitada, mapa de atributos `givenName`, `sn`, `displayName`, `mail` e `title` (função).
  LDAPS ou StartTLS configuráveis, com arquivo de CA da empresa. Tipo de grupo configurável:
  `NestedActiveDirectoryGroupType` no AD e `GroupOfNamesType` no desenvolvimento.
- **Rationale**: biblioteca madura e mantida pela comunidade Django; não guarda senha (FR-001); o
  usuário desativado no AD falha no bind e perde o acesso no próximo login (FR-004).
- **Indisponibilidade**: o django-auth-ldap trata `ldap.LDAPError` e devolve `None`; o sinal
  `ldap_error` é usado para distinguir "serviço indisponível" (`SERVER_DOWN`, `TIMEOUT`) de senha
  inválida, para não contar a tentativa e mostrar a mensagem certa.
- **Grupos → perfis (FR-013)**: mapeamento opcional `LDAP_PROFILE_GROUPS` (perfil → DN do grupo).
  A sincronização roda a cada login: concede perfis de origem "grupo da rede" e revoga só esses;
  concessões manuais nunca são tocadas. Sem mapeamento, os perfis são só os concedidos no sistema
  (premissa do plano: "perfis e permissões no próprio sistema").
- **Desenvolvimento e testes**: contêiner `osixia/openldap:1.5.0` com usuários e grupos fictícios
  (`deploy/ldap-dev/seed.ldif`), só no `docker-compose.override.yml`. Testes de regra usam um backend
  falso; testes marcados `ldap` fazem bind real no contêiner.
- **Alternatives considered**: contas locais (rejeitado no clarify); SAML/OIDC (a TI não oferece
  provedor; o plano define LDAP).

## R4. Fluxo de login, bloqueio e sessão

- **Decision**: view de login própria que, em ordem: normaliza o usuário; consulta bloqueio ativo
  (`LoginLockout`) e, se houver, recusa sem chamar o AD; tira um instantâneo do cadastro; chama
  `authenticate()`; registra `LoginAttempt`; em falha, conta as falhas desde o último login aceito,
  desbloqueio ou fim de bloqueio e cria o bloqueio ao atingir o limite; em sucesso, compara o
  cadastro (criação/alteração com valor anterior e novo), sincroniza perfis de grupo e encaminha
  para a página inicial ou para "Solicitar acesso".
- **Sessão**: sessões no banco (`django.contrib.sessions`), middleware de inatividade que guarda o
  último acesso na sessão, encerra e registra `auth.session_expired` quando passa do limite. O
  cookie vale 12 h e é renovado a cada acesso (`SESSION_SAVE_EVERY_REQUEST`), sempre acima do
  limite de inatividade, para que a sessão ainda exista e o encerramento possa ser registrado;
  expira também ao fechar o navegador. Cookies `Secure`, `HttpOnly`, `SameSite=Lax`.
- **Acesso por padrão negado**: `LoginRequiredMiddleware` do Django 5.2 e middleware que restringe a
  pessoa sem perfil à página "Solicitar acesso" e ao logout.
- **Rationale**: o bloqueio da aplicação protege a conta de rede de bloqueio no AD e evita enviar
  tentativas ao AD durante o bloqueio (FR-006); mensagem única para usuário inexistente, senha
  errada e conta desativada evita enumeração.
- **Alternatives considered**: django-axes (mais uma dependência e modelo de dados próprio que não
  segue o "nada é apagado"); contar só por IP (não atende "bloqueia o login do usuário").

## R5. Encadeamento e verificação da trilha

- **Decision**: cada `AuditEvent` tem `seq` (inteiro sem lacunas, atribuído pela aplicação),
  `prev_hash` e `hash = SHA-256(JSON canônico do evento, incluindo prev_hash)`. JSON canônico:
  chaves ordenadas, separadores `,`/`:`, UTF-8 sem escape, datas ISO 8601 em UTC com microssegundos
  e valores reduzidos a texto, inteiros, booleanos e nulos (sem ponto flutuante, para o JSONB
  devolver exatamente o que foi gravado). O primeiro evento usa 64 zeros como `prev_hash`.
- **Concorrência**: gravação dentro da transação do negócio com `pg_advisory_xact_lock`; o próximo
  `seq` e o `prev_hash` são lidos depois de obter a trava, o que impede bifurcação e lacuna; se a
  transação do negócio falhar, o evento também é desfeito.
- **Verificação**: percorre a cadeia em ordem de `seq` em blocos; aponta "conteúdo alterado" (hash
  recalculado diferente), "encadeamento rompido" (`prev_hash` diferente do hash anterior), "lacuna na
  sequência" e confronta o último ponto de controle registrado (`seq` e hash da verificação
  anterior), o que revela exclusão do trecho final. O resultado vai para `ChainVerification` e para
  um evento `audit.chain_verified` gravado depois do ponto de controle.
- **Imutabilidade**: trigger `BEFORE UPDATE OR DELETE` que lança exceção em `audit_auditevent` e
  `audit_chainverification`, além da falta de privilégio do papel da aplicação; o modelo base
  `AppendOnlyModel` recusa `save()` de registro existente e `delete()`.
- **Rotina diária**: tarefa Celery `audit.verify_chain_daily` às 02:00 (America/Sao_Paulo,
  configurável) e comando `verify_audit_chain` para execução manual ou por cron da TI.
- **Rationale**: atende FR-019 a FR-022 e o critério "uma alteração feita direto no banco é revelada";
  SHA-256 é o algoritmo pedido no plano.
- **Alternatives considered**: hash só do conteúdo, sem encadeamento (não revela exclusão); árvore de
  Merkle ou âncora externa (complexidade sem requisito; o ponto de controle diário cobre o trecho
  final).

## R6. Nada é apagado (modelos)

- **Decision**: `ProtectedModel` (abstrato) cujo `delete()` e cujo `QuerySet.delete()` lançam erro;
  `AppendOnlyModel` estende e recusa também atualização. Revogação de perfil e decisão de solicitação
  são atualizações de campos de encerramento, nunca exclusões.
- **Rationale**: defesa em profundidade junto com os privilégios de banco (R2).

## R7. Interface

- **Decision**: templates do Django, CSS próprio enxuto e HTMX 2.0.11 servido localmente (sem CDN),
  usado nos filtros e na paginação da trilha. Sem JavaScript inline, para permitir a CSP
  `default-src 'self'` no Nginx. Sem o admin do Django: toda alteração passa por telas que auditam.
- **Rationale**: plano pede templates com HTMX e sem SPA; o admin do Django permitiria alterar e
  apagar registros sem trilha.

## R8. Exportação da trilha

- **Decision**: CSV UTF-8 com BOM, separador `;`, gerado em streaming; XLSX com openpyxl em modo
  `write_only`. As primeiras linhas trazem título, filtros, data e hora da exportação e quantidade de
  eventos; depois o cabeçalho e os eventos (layout em `contracts/exportacao-trilha.md`). A exportação
  grava `audit.exported` com filtros e quantidade.
- **Rationale**: CSV com BOM e `;` abre direto no Excel em pt-BR; XLSX é o formato de planilha usado
  pela Qualidade; openpyxl já está previsto no plano (features 003 e 010).

## R9. Datas e horas

- **Decision**: `USE_TZ = True`, `TIME_ZONE = "America/Sao_Paulo"`; o banco guarda `timestamptz` em
  UTC e os templates exibem no horário de Brasília. O relógio é o do servidor (sincronizado por NTP
  pela TI); nenhum horário vem do navegador.

## R10. Tarefas em segundo plano

- **Decision**: Celery 5.7 com Redis 7.4; nesta feature só a verificação diária. O worker roda com o
  agendador embutido (`--beat`) e o agendamento fica nas settings (sem tabela extra).
- **Rationale**: Celery + Redis é a pilha do plano para PDFs (006), e-mails (010) e Sankhya (012);
  começar com ela evita um segundo mecanismo de agendamento. Instância única, então o beat embutido
  não duplica tarefas.
- **Alternatives considered**: cron no host chamando o comando (fica disponível como contingência).

## R11. Implantação e TLS

- **Decision**: `docker-compose.yml` com `db` (postgres:17), `redis`, `web` (gunicorn), `worker` e
  `nginx` (imagem própria baseada em nginx:1.28-alpine). O Nginx publica só HTTPS (redireciona HTTP),
  com certificado montado de fora do repositório; no desenvolvimento, um script gera certificado
  autoassinado na primeira subida. O `entrypoint.sh` aguarda o banco, roda `migrate` com o papel dono,
  aplica os privilégios e inicia o processo com o papel da aplicação.
- **Rationale**: mesmo ambiente em homologação e produção (plano); segredos só por variável de
  ambiente (`.env` fora do Git, `.env.example` versionado).

## R12. Testes, cobertura e rastreabilidade

- **Decision**: pytest + pytest-django com `config.settings_test` (credenciais do papel dono e backend
  de autenticação falso para os testes de regra). Cada teste leva `@pytest.mark.req("001:FR-020")`; o
  plugin de `tests/conftest.py` grava o mapa teste → requisitos e `scripts/rastreabilidade.py` gera
  `docs/validacao/matriz-rastreabilidade.md`, apontando requisito sem teste. Cobertura mínima de 90%
  em `sgp.core` e `sgp.audit` (`--cov-fail-under=90`). Testes de adulteração desligam o trigger com o
  papel dono para simular alteração direta no banco.
- **Rationale**: princípio VIII e a mitigação do plano "rastreabilidade gerada desde a 001".

## R13. Nomes no código

- **Decision**: identificadores em inglês; os nomes do plano são mapeados: contas → `accounts`,
  auditoria → `audit`, Membro do projeto → `ProjectMember` (feature 002). Rótulos de tela,
  mensagens, URLs e documentos em português.
- **Rationale**: princípio IX da constituição, que prevalece sobre os nomes do texto do plano.

## R14. Gestão de pacotes

- **Decision**: `uv` com `pyproject.toml` e `uv.lock`; a imagem usa `uv sync --frozen` (sem
  dependências de desenvolvimento no alvo `runtime`). Imagens Docker com tag fixa.
- **Rationale**: instalação reprodutível, requisito da qualificação de instalação (IQ).
