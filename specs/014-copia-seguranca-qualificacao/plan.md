# Implementation Plan: Cópia de segurança, restauração e qualificação do sistema

**Branch**: `014-copia-seguranca-qualificacao` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/014-copia-seguranca-qualificacao/spec.md`

## Summary

Entregáveis de operação e validação que o próprio sistema produz: cópia de segurança diária
(banco num instantâneo consistente + arquivos guardados copiados uma vez para um acervo endereçado
pelo conteúdo + manifesto com resumos e contagens), retenção de 35 dias com a cópia mensal mantida,
teste de restauração mensal num banco isolado e descartável (resumos, restauração, contagens por
tabela, cadeia da trilha e arquivos), avisos por e-mail à TI, qualificação de instalação (IQ) e de
operação (OQ) com relatório em PDF guardado no sistema, exportação para a revisão trimestral de
acessos e os roteiros de IQ, OQ e recuperação versionados no repositório.

Abordagem técnica: app `sgp/operations`; `pg_dump`/`pg_restore` da versão 17 (repositório oficial
do PostgreSQL na imagem) chamados pelo worker; instantâneo exportado (`pg_export_snapshot`) numa
transação REPEATABLE READ em que também se contam as linhas, se lê o último evento da trilha e a
lista de arquivos, e o `pg_dump --snapshot` grava exatamente esse estado; tarefas Celery agendadas
no beat; verificação da cadeia da trilha reaproveitada da feature 001 sobre um apelido de banco
criado em tempo de execução para o banco restaurado; relatórios renderizados pelo WeasyPrint e
guardados pelo armazenamento da feature 003.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as anteriores (Django 5.2, psycopg 3, Celery, WeasyPrint, pyHanko,
openpyxl); `postgresql-client-17` na imagem (repositório PGDG); `tomllib` da biblioteca padrão
para conferir versões contra o `uv.lock`; nenhuma dependência Python nova

**Storage**: PostgreSQL 17 (registros de cópias, testes e qualificações); destino de cópias em
diretório montado (`BACKUP_DIR`); relatórios de qualificação no armazenamento de arquivos

**Testing**: pytest; testes de cópia e restauração com `django_db(transaction=True)` (dados
gravados de fato, vistos pelo `pg_dump`) e destino em diretório temporário; marcador
`req("014:…")`

**Target Platform / Project Type**: os mesmos; aplicação web com worker e beat em contêineres

**Performance Goals**: cópia diária sem bloquear gravações (instantâneo MVCC); teste de restauração
mensal em minutos para o volume previsto (dezenas de GB de arquivos, banco de poucos GB)

**Constraints**: nada é apagado do banco em uso; o teste nunca toca no banco em uso; nenhuma tela
baixa cópias nem restaura sobre o banco em uso; credenciais só em variáveis de ambiente; relatórios
e avisos em português

**Scale/Scope**: uma cópia por dia, um teste por mês, algumas qualificações por ano

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Manifesto com resumos e contagens; cada cópia, teste e qualificação registrado com versão do sistema e quem pediu | Atende |
| II. Trilha imutável | Eventos `operations.*`; o teste confere a cadeia da trilha restaurada até o último evento do manifesto; qualificações somente de inclusão | Atende |
| III. Assinatura | Não altera a assinatura; a OQ confere o selo num PDF de teste | Atende |
| IV. Modelos versionados | Não se aplica | Atende |
| V. Fonte única | Cópia e restauração do próprio banco e acervo de arquivos; nenhuma cópia paralela de dados no sistema | Atende |
| VI. Cálculo automático | Não se aplica | Atende |
| VII. Segurança | Ações só para a TI (OQ também para a Qualidade), sem download de cópias pela tela, credenciais do papel dono só em variáveis de ambiente, destino com acesso restrito | Atende |
| VIII. Qualidade verificável | Testes de cópia, restauração (inclusive com dano), retenção, IQ, OQ e exportação; SC-004 manual em homologação | Atende |
| IX. Simplicidade | Ferramentas nativas do PostgreSQL, acervo de arquivos endereçado pelo conteúdo, sem serviço novo | Atende |
| Restrição: cópia diária com teste de restauração (RDC 665/2022, art. 35) | É o objeto da feature | Atende |
| Restrição: validação antes do uso oficial (arts. 104 a 106) | Relatórios de IQ e OQ, roteiros manuais e pacote de validação | Atende |

Reavaliação depois do desenho (Fase 1): sem violações; a remoção de cópias diárias antigas apaga
arquivos de cópia no destino, nunca registros do sistema, e cada remoção vai para a trilha.

## Project Structure

### Documentation (this feature)

```text
specs/014-copia-seguranca-qualificacao/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/rotas-ui.md        # telas, rotas, permissões e eventos
├── contracts/copia-e-manifesto.md  # destino, manifesto, conferências do teste e comandos
└── tasks.md
docs/validacao/README.md          # pacote de validação: entregável → onde está
docs/validacao/iq-roteiro.md      # roteiro de qualificação de instalação
docs/validacao/oq-roteiro.md      # roteiro de qualificação de operação (automatizado e manual)
docs/operacao/recuperacao.md      # procedimento de recuperação (só a TI, no servidor)
```

### Source Code (repository root)

```text
sgp/operations/
├── models.py          # BackupRun, RestoreTest, QualificationRun
├── version.py         # versão do sistema (pyproject + commit)
├── backup.py          # instantâneo, pg_dump, acervo de arquivos, manifesto, retenção
├── restore.py         # teste de restauração num banco isolado
├── alerts.py          # e-mail para os administradores
├── installation.py    # itens da qualificação de instalação
├── operation.py       # itens da qualificação de operação (tentativas desfeitas)
├── qualification.py   # execução, relatório em PDF, registro
├── access_review.py   # exportação da revisão de acessos
├── tasks.py / views.py / urls.py / templates/operations/
└── management/commands/  copia_seguranca, teste_restauracao,
                          qualificacao_instalacao, qualificacao_operacao
sgp/audit/services.py  # verificação da cadeia separada em função reutilizável (walk_chain)
deploy/docker/Dockerfile   # postgresql-client-17 e SGP_COMMIT
docker-compose.yml         # volume do destino de cópias
tests/operations/
```

**Structure Decision**: uma app nova no monólito, como nas features anteriores; a verificação da
cadeia da trilha é extraída para uma função que recebe o conjunto de eventos, usada pela
verificação diária (feature 001) e pelo teste de restauração.

## Complexity Tracking

Sem violações da constituição a justificar.
