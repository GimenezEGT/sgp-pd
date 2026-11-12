---

description: "Task list for feature 014 — Cópia de segurança, restauração e qualificação do sistema"
---

# Tasks: Cópia de segurança, restauração e qualificação do sistema

**Input**: Design documents from `/specs/014-copia-seguranca-qualificacao/`

**Tests**: obrigatórios (constituição VIII); marcador `req("014:…")`; cópia e restauração com
`django_db(transaction=True)` e destino em diretório temporário; dados fictícios.

## Phase 1: Setup

- [X] T001 Imagem com `postgresql-client-17` (repositório PGDG) e argumento de build `SGP_COMMIT` em `deploy/docker/Dockerfile`; destino `BACKUP_HOST_DIR` → `/app/var/backups` para web e worker em `docker-compose.yml`; variáveis `BACKUP_DIR`, `BACKUP_HOUR`, `BACKUP_MINUTE`, `BACKUP_KEEP_DAYS` (35), `RESTORE_TEST_DAY` (1), `RESTORE_TEST_HOUR` (3), `BACKUP_MAX_AGE_HOURS` (26), `DB_OWNER_USER`/`DB_OWNER_PASSWORD` em `config/settings.py` e `.env.example`; app `sgp.operations` registrada; beat com "copia-de-seguranca-diaria", "teste-de-restauracao-mensal" e "conferencia-de-copias-em-dia"

## Phase 2: Foundational

- [X] T002 Modelos `BackupRun` e `RestoreTest` (`ProtectedModel`) e `QualificationRun` (`AppendOnlyModel`) conforme `data-model.md`, com migrações `0001_initial` e `0002_trigger` (gatilho de imutabilidade em `operations_qualificationrun`), tipos de evento `operations.*`, `sgp/operations/version.py` (versão do `pyproject.toml` + `SGP_COMMIT` ou `.git`) e `sgp/operations/alerts.py` (e-mail aos administradores ativos depois do commit)
- [X] T003 Extrair `walk_chain(queryset)` da verificação da cadeia em `sgp/audit/services.py`, usada por `verify_chain` sem mudança de comportamento (testes da feature 001 continuam passando)

## Phase 3: User Story 1 - Cópia de segurança diária (P1) 🎯 MVP

**Goal**: cópia diária consistente do banco e dos arquivos, com manifesto, acervo e retenção.

**Independent Test**: executar a cópia e conferir banco copiado, manifesto, acervo, trilha e painel.

- [X] T004 [P] [US1] Testes em `tests/operations/test_backup.py`: manifesto com resumo e tamanho do banco, contagens por tabela e último evento iguais ao banco no instante da cópia; acervo `arquivos/aa/bb/<sha256>` com os arquivos conferidos; segunda cópia com 0 arquivos novos; gravação concorrente durante a cópia não é bloqueada e fica fora do manifesto e do banco copiado; destino inexistente, sem gravação, igual a `MEDIA_ROOT` ou dentro dele reprova com motivo e aviso por e-mail; arquivo guardado ausente reprova listando-o; uma cópia por vez; retenção de 35 dias com a primeira bem-sucedida do mês mantida e evento `operations.backup_removed`; eventos `backup_completed`/`backup_failed` (FR-001 a FR-005, FR-007, FR-008)
- [X] T005 [US1] Implementar `sgp/operations/backup.py` (instantâneo exportado em REPEATABLE READ, `pg_dump -Fc --snapshot`, acervo com cópia conferida, `manifesto.json` formato 1, bloqueio consultivo, retenção), tarefa `sgp.operations.backup` em `sgp/operations/tasks.py` e comando `copia_seguranca`
- [X] T006 [US1] Painel `/operacao/` (Administrador e Garantia da Qualidade; aviso de cópia atrasada) e `POST /operacao/copias/executar/` (Administrador, evento `operations.backup_requested`) em `sgp/operations/views.py`, `urls.py` e `templates/operations/`, item de menu "Operação e validação" em `sgp/core/navigation.py`, com testes em `tests/operations/test_views.py` (FR-007, FR-009)

## Phase 4: User Story 2 - Teste de restauração (P1)

**Goal**: restaurar a cópia mais recente num banco isolado e conferir C1 a C6.

**Independent Test**: cópia + teste aprovado; dano provocado reprova e avisa.

- [X] T007 [P] [US2] Testes em `tests/operations/test_restore.py`: C1 a C6 aprovadas, contagens do banco em uso iguais antes e depois e banco `<NAME>_restauracao` inexistente ao fim; manifesto alterado (C1), banco copiado alterado (C2) e arquivo do acervo alterado ou ausente (C6) reprovam com aviso; sem cópia bem-sucedida reprova; banco isolado que sobrou é descartado antes; conferência de cópia em dia avisa e registra `operations.backup_stale` depois de 26 horas (FR-006 a FR-008, SC-001, SC-002)
- [X] T008 [US2] Implementar `sgp/operations/restore.py` (banco isolado, `pg_restore --no-owner --no-privileges --exit-on-error`, apelido de banco em tempo de execução com o papel dono para contagens e `walk_chain`), tarefas `restore_test` e `check_freshness` e comando `teste_restauracao`
- [X] T009 [US2] Seção de testes de restauração no painel (conferências, aviso de teste atrasado ou reprovado) e `POST /operacao/restauracao/executar/` (Administrador, `operations.restore_requested`) com testes em `tests/operations/test_views.py`

## Phase 5: User Story 3 - Qualificação de instalação (P2)

**Goal**: conferência automatizada da instalação com relatório em PDF guardado.

**Independent Test**: instalação correta aprova; configuração inválida reprova o item com motivo.

- [X] T010 [P] [US3] Testes em `tests/operations/test_qualification.py` (IQ): resultado por item (`aprovado`, `reprovado`, `nao_aplicavel`) e geral; depuração ligada, segredo de desenvolvimento, migração pendente, destino de cópias dentro dos dados e diretório (LDAP) ou e-mail não configurados reprovam com motivo; nenhum valor de segredo no relatório; relatório PDF guardado com SHA-256; `QualificationRun` imutável; comando com `--usuario` exige Administrador; evento `operations.qualification_executed` (FR-011, FR-013, SC-003)
- [X] T011 [US3] Implementar `sgp/operations/installation.py`, `sgp/operations/qualification.py` (execução, relatório HTML → PDF pelo WeasyPrint, guarda pelo armazenamento da feature 003), template `operations/report.html`, comando `qualificacao_instalacao`, tarefa `qualification`, lista de qualificações no painel (data, tipo, canal, executor, versão, resultado), `POST /operacao/qualificacao/instalacao/` (Administrador) e `GET /operacao/qualificacao/<id>/relatorio/` (Administrador e Garantia da Qualidade, `operations.report_downloaded`)

## Phase 6: User Story 4 - Qualificação de operação (P2)

**Goal**: conferências operacionais sem alterar dados, com relatório guardado.

**Independent Test**: OQ no ambiente de teste com cópia e teste em dia aprova; sem eles reprova o item.

- [X] T012 [P] [US4] Testes em `tests/operations/test_qualification.py` (OQ): trilha íntegra; UPDATE e DELETE recusados e desfeitos; PDF de teste gerado e selado com o selo íntegro; agendamentos presentes; cópia nas últimas 26 horas e teste aprovado nos últimos 32 dias (e reprovação sem eles); Sankhya desligado "não aplicável"; contagens do banco iguais antes e depois; Garantia da Qualidade executa pela tela e analista recebe 403 (FR-012, FR-013)
- [X] T013 [US4] Implementar `sgp/operations/operation.py`, comando `qualificacao_operacao` e `POST /operacao/qualificacao/operacao/` (Administrador e Garantia da Qualidade)

## Phase 7: User Story 5 - Revisão periódica de acessos (P3)

- [X] T014 [US5] Testes e implementação da exportação em `tests/operations/test_access_review.py` e `sgp/operations/access_review.py`, `GET /operacao/revisao-de-acessos/?formato=csv|xlsx` (Administrador e Garantia da Qualidade): pessoa, nome, e-mail, conta ativa, perfis ativos (desde, concedido por), papéis por projeto, último acesso; evento `operations.access_review_exported` (FR-014)

## Phase 8: Polish

- [X] T015 Rotas no contrato de `tests/core/test_route_scan.py`; `README.md` (feature 014 e operação); `docs/validacao/README.md` (pacote de validação: entregável → onde está), `docs/validacao/iq-roteiro.md`, `docs/validacao/oq-roteiro.md` (suíte, comando e roteiros manuais de assinatura, auditoria e geração) e `docs/operacao/recuperacao.md`; SC-004 em `docs/validacao/verificacoes-manuais.json` (FR-015)
- [X] T016 Rodar `scripts/verificar.sh` (1.255 testes, matriz com 309 requisitos cobertos)
- [X] T017 Executar o quickstart na pilha real e registrar em `docs/validacao/014-resultados-execucao.md`

## Dependencies & Execution Order

Setup → Foundational → US1 → US2 (precisa de uma cópia) → US3 → US4 (usa o relatório da US3 e a
cópia e o teste das US1 e US2) → US5 (independente depois do Foundational) → Polish.

## Parallel Opportunities

- T004, T007, T010 e T012 (testes) podem ser escritos em paralelo, em arquivos diferentes.
- T014 (US5) pode correr em paralelo com US3 e US4.

## Implementation Strategy

MVP: US1 (cópia diária) e US2 (teste de restauração), que atendem o art. 35 e a constituição;
depois as qualificações (US3, US4), a revisão de acessos (US5) e os roteiros.

## Phase 9: Convergence

- [X] T018 Atualizar `plan.md` (Summary) e `research.md` (R5): a C5 percorre a cadeia restaurada com `walk_rows` (feature 001) num cursor de servidor numa conexão direta ao banco isolado, em vez de apelido de banco criado em tempo de execução (bloqueado pelo isolamento dos testes do Django) per plan: mecanismo da C5 (contradicts)
