# Quickstart: Fundação — acesso, perfis e trilha de auditoria

Roteiro para subir o ambiente de desenvolvimento e validar a feature de ponta a ponta. Detalhes de
rotas e eventos em [contracts/](contracts/); entidades em [data-model.md](data-model.md).

## Pré-requisitos

- Docker com Compose v2.
- Portas livres: 8443 (HTTPS do Nginx), 8080 (HTTP, só redireciona) e 3890 (LDAP de desenvolvimento).

## Subir o ambiente

```bash
cp .env.example .env          # preencha as senhas fictícias de desenvolvimento
docker compose up -d --build  # db, redis, web, worker, nginx e ldap (override de desenvolvimento)
docker compose ps             # todos "healthy"/"running"
```

Na primeira subida o Nginx gera um certificado autoassinado (`deploy/nginx/certs/`, fora do Git) e o
`web` roda as migrações com o papel dono e aplica os privilégios do papel da aplicação.

Usuários fictícios do LDAP de desenvolvimento (`deploy/ldap-dev/seed.ldif`, senha `Senha#Dev01`):
`admin.ti`, `gestor.pd`, `lider.projeto`, `ana.analista`, `qualidade.ar`, `leitor.consulta`,
`sem.perfil` e `ex.colaborador` (conta desativada: sem senha válida).

## Designar o primeiro Administrador

```bash
docker compose exec web python manage.py grant_initial_admin admin.ti --motivo "Implantação do ambiente de desenvolvimento" --aprovacao "Gestão da TI (ambiente de desenvolvimento)"
```

## Cenários de validação

1. **Login e pessoa sem perfil (US1)**: abrir `https://localhost:8443/`, entrar como `admin.ti`
   (chega ao início) e depois como `sem.perfil` (vê só "Solicitar acesso"; qualquer outra URL volta
   para lá). Registrar uma solicitação e conferir em Administração › Solicitações.
2. **Perfis (US2)**: como `admin.ti`, conceder "Analista/Pesquisador" a `sem.perfil` com motivo e
   aprovação; entrar como `sem.perfil` e ver o início; revogar e conferir o histórico.
3. **Bloqueio (US5)**: errar a senha de `leitor.consulta` 5 vezes; a 6ª tentativa, mesmo correta, é
   recusada com a mensagem de bloqueio; desbloquear em Administração › Bloqueios.
4. **Trilha e exportação (US4)**: como `qualidade.ar` (com perfil Qualidade/AR concedido), filtrar a
   trilha por usuário e período e exportar CSV e XLSX; conferir o evento `audit.exported`.
5. **Adulteração detectada (US3)**: alterar um evento direto no banco e verificar:

   ```bash
   docker compose exec db psql -U sgp_owner -d sgp -c "ALTER TABLE audit_auditevent DISABLE TRIGGER audit_event_immutable; UPDATE audit_auditevent SET reason = 'adulterado' WHERE seq = 3; ALTER TABLE audit_auditevent ENABLE TRIGGER audit_event_immutable;"
   docker compose exec web python manage.py verify_audit_chain
   ```

   Esperado: código de saída 1, quebra `content_altered` no evento 3 e a faixa de alerta para
   Qualidade/AR e Administrador.
6. **Papel da aplicação sem UPDATE/DELETE**:

   ```bash
   docker compose exec db psql -U sgp_app -d sgp -c "DELETE FROM audit_auditevent WHERE seq = 1;"
   ```

   Esperado: `permission denied for table audit_auditevent`.

## Testes automatizados

```bash
docker compose run --rm web pytest                       # suíte completa com cobertura
docker compose run --rm web pytest -m ldap               # integração com o LDAP de desenvolvimento
docker compose run --rm web python scripts/rastreabilidade.py   # gera docs/validacao/matriz-rastreabilidade.md
```

Critérios: todos os testes passam, cobertura ≥ 90% em `sgp.core` e `sgp.audit` e nenhum requisito da
feature 001 sem teste na matriz.

## Homologação com o AD da empresa

Trocar no `.env` as variáveis `LDAP_*` pelas do AD (ver [contracts/configuracao.md](contracts/configuracao.md)),
com `LDAP_GROUP_TYPE=active_directory_nested` e o filtro `(sAMAccountName=%(user)s)`, e subir sem o
override de desenvolvimento: `docker compose -f docker-compose.yml up -d`.
