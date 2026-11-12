# Research: Cópia de segurança, restauração e qualificação do sistema

## R1. Ferramentas de cópia do banco

- Decision: `pg_dump` em formato custom (`-Fc`, comprimido) e `pg_restore` da versão 17, do
  repositório oficial do PostgreSQL (PGDG) instalado na imagem com o script
  `apt.postgresql.org.sh` do pacote `postgresql-common`; executados pelo worker com o papel dono.
- Rationale: o `pg_dump` precisa ser de versão igual ou maior que a do servidor (17); o Debian
  bookworm traz só o cliente 15. Formato custom permite restauração seletiva e conferência.
- Alternatives considered: copiar binários da imagem `postgres:17` (dependências de bibliotecas
  frágeis); serviço de cópia separado com a imagem do PostgreSQL (o resultado não chegaria à trilha
  nem à tela sem outra integração); cópia física do diretório de dados (exige parar o banco).

## R2. Ponto consistente no tempo

- Decision: conexão do papel dono em REPEATABLE READ somente leitura; `pg_export_snapshot()`;
  nessa transação contam-se as linhas de cada tabela do esquema `public`, lê-se o último evento da
  trilha (sequência e resumo) e a lista de arquivos guardados; `pg_dump --snapshot=<id>` grava o
  mesmo estado enquanto a transação continua aberta.
- Rationale: manifesto e banco copiado descrevem exatamente o mesmo instante, então a contagem
  restaurada tem de bater; MVCC não bloqueia gravações (FR-001).
- Alternatives considered: contar antes ou depois do `pg_dump` (diverge com uso concorrente);
  bloquear tabelas (interrompe o uso).

## R3. Arquivos guardados

- Decision: acervo endereçado pelo conteúdo no destino (`<BACKUP_DIR>/arquivos/aa/bb/<sha256>`),
  como no armazenamento da feature 003; cada arquivo do instantâneo que ainda não está no acervo é
  copiado para um temporário, conferido pelo SHA-256 e renomeado; arquivo ausente do armazenamento
  reprova a cópia com a lista. O acervo nunca é podado.
- Rationale: os arquivos guardados nunca mudam nem são apagados (constituição), então uma cópia
  única por conteúdo basta e cada cópia diária custa só os arquivos novos (FR-004).
- Alternatives considered: tar diário completo (35 cópias inteiras); rsync externo (fora da trilha).

## R4. Destino, retenção e proteção

- Decision: `BACKUP_DIR` (montado pela TI de outro servidor ou compartilhamento; no Compose,
  `BACKUP_HOST_DIR`); a cópia recusa destino inexistente, sem gravação ou igual/dentro de
  `MEDIA_ROOT`. Cópias em `<BACKUP_DIR>/copias/<AAAAMMDD-HHMMSS>/` (`banco.dump` e
  `manifesto.json`). Depois de cada cópia bem-sucedida, as diárias com mais de 35 dias são
  removidas, exceto a primeira bem-sucedida de cada mês; o registro fica com a data de remoção e o
  evento `operations.backup_removed`. Sem cifragem pelo sistema (clarificação); a IQ confere que o
  destino é outro sistema de arquivos que o dos dados.
- Rationale: respostas provisórias do esclarecimento (sessão 2026-11-12).
- Alternatives considered: retenção GFS; cifragem com chave em variável de ambiente.

## R5. Teste de restauração

- Decision: banco isolado `<NAME>_restauracao` (descartado antes, se sobrou de teste interrompido,
  e ao fim); conferências: C1 resumo do manifesto igual ao registrado, C2 resumo do banco copiado
  igual ao do manifesto, C3 `pg_restore --no-owner --no-privileges --exit-on-error` sem erro, C4
  contagem por tabela igual à do manifesto, C5 cadeia da trilha íntegra e último evento igual ao do
  manifesto, C6 todos os arquivos referenciados presentes no acervo com o SHA-256 conferido. A C5
  usa a verificação da feature 001 (`walk_rows`, extraída de `walk_chain`) sobre as linhas do
  banco restaurado, lidas por cursor de servidor numa conexão direta do papel dono. Um apelido de
  banco criado em tempo de execução (`connections.databases`) foi descartado na implementação:
  o isolamento dos testes do Django bloqueia conexões a apelidos não declarados. Quando a C5
  reprova, o detalhe lista as quebras e avisa se a verificação da trilha do banco em uso já as
  apontava (incidente existente, reproduzido fielmente pela cópia).
- Rationale: prova que a cópia recupera banco, trilha e arquivos (FR-006, SC-001, SC-002) sem tocar
  no banco em uso.
- Alternatives considered: restaurar num servidor separado (exige infraestrutura extra); conferir só
  os resumos (não prova a restauração).

## R6. Execução e concorrência

- Decision: tarefas Celery `sgp.operations.backup`, `restore_test`, `check_freshness`,
  `qualification`; beat com cópia diária (`BACKUP_HOUR`:`BACKUP_MINUTE`, padrão 01:00), teste no
  dia `RESTORE_TEST_DAY` (padrão 1) às `RESTORE_TEST_HOUR` (padrão 03:00) e conferência de cópia em
  dia às 08:00; uma cópia e um teste por vez com `pg_try_advisory_lock`; comandos de gerenciamento
  para a TI no servidor.
- Rationale: mesmo padrão das features 010 e 012; o bloqueio consultivo vale entre processos.
- Alternatives considered: cron do sistema operacional (fora da trilha e da tela).

## R7. Avisos

- Decision: `send_mail` para os e-mails das pessoas ativas com perfil Administrador do sistema
  ativo, depois do commit; assunto "[SGP-P&D] ..." com o motivo; falha de envio vai para o log.
- Rationale: FR-008; a fila de notificações da feature 010 é de pendências de projeto, com
  preferências por pessoa, e não serve para alerta de infraestrutura.

## R8. Qualificações e relatório

- Decision: itens como funções que devolvem (código, descrição, resultado, detalhe), resultado
  "aprovado", "reprovado" ou "não aplicável"; IQ (versões contra o `uv.lock`, Python, Django,
  PostgreSQL 17 e fuso UTC, migrações aplicadas, `check --deploy`, depuração desligada, cookies
  seguros, `SITE_URL` em HTTPS, fuso de exibição, variáveis obrigatórias presentes, gatilhos de
  imutabilidade, privilégios do papel da aplicação, papel dono com criação de banco, certificado do
  selo, destino de cópias gravável e em outro sistema de arquivos, ferramentas `pg_dump` 17, fontes
  Carlito e DejaVu da imagem e WeasyPrint,
  Redis, worker e beat, LDAP e SMTP acessíveis); OQ sem alterar dados (cadeia da trilha, UPDATE e
  DELETE recusados com ponto de salvamento desfeito, PDF de teste gerado e selado em memória com o
  selo validado, agendamentos, cópia nas últimas 26 horas, teste de restauração aprovado nos últimos
  32 dias, Sankhya quando ligado). Relatório HTML → PDF (WeasyPrint) guardado com SHA-256;
  `QualificationRun` somente de inclusão. A suíte automatizada (`scripts/verificar.sh`) roda com a
  imagem de desenvolvimento da mesma versão, como passo do roteiro de OQ.
- Rationale: a imagem de produção não tem as dependências de teste; as conferências no ambiente
  instalado complementam a suíte.

## R9. Versão do sistema

- Decision: versão do `pyproject.toml` mais o commit (`SGP_COMMIT`, argumento de build; no
  desenvolvimento, lido de `.git`); entra no manifesto, nos registros e nos relatórios.
- Rationale: liga cada evidência à versão validada (controle de mudanças, art. 106).
