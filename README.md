# SGP-P&D — Sistema de Gestão de Projetos de P&D (IVD)

Aplicação web da intranet que guarda cada projeto de P&D de diagnóstico in vitro, do Termo de
Abertura à Saída de Projeto, com trilha de auditoria encadeada e assinatura eletrônica. A construção
segue o Spec-Driven Development do spec-kit; o plano completo está em
[docs/plano-implementacao.md](docs/plano-implementacao.md) e os artefatos de cada feature em
[specs/](specs/).

## Ambiente de desenvolvimento

Pré-requisito: Docker com Compose v2.

```bash
cp .env.example .env            # troque os valores fictícios (senhas e chave)
docker compose up -d --build    # db, redis, web, worker, nginx e LDAP fictício
docker compose exec web python manage.py grant_initial_admin admin.ti --motivo "Implantação" --aprovacao "Gestão da TI"
```

Acesse `https://localhost:8443/` (certificado autoassinado de desenvolvimento). Usuários do
diretório fictício: veja `deploy/ldap-dev/seed.ldif` (senha `Senha#Dev01`).

## Testes e portão de qualidade

```bash
docker compose run --rm web sh scripts/verificar.sh        # ruff, pytest, cobertura mínima e matriz
docker compose run --rm web pytest -m slow -s               # medições de desempenho
```

A matriz requisito → teste fica em
[docs/validacao/matriz-rastreabilidade.md](docs/validacao/matriz-rastreabilidade.md).

## Homologação e produção

```bash
docker compose -f docker-compose.yml up -d --build
```

Sem o arquivo de override: sem LDAP fictício, imagem `runtime` com gunicorn. Configure no `.env` o
AD da empresa (`LDAPS`), o certificado do Nginx em `deploy/nginx/certs/` e
`DJANGO_DEBUG=false`. As variáveis estão em
[specs/001-fundacao-acesso-auditoria/contracts/configuracao.md](specs/001-fundacao-acesso-auditoria/contracts/configuracao.md).

## Estrutura

```text
config/        settings, urls, celery
sgp/           apps (core, accounts, audit, ...)
tests/         pytest, espelhando as apps
deploy/        Dockerfile, Nginx, PostgreSQL, LDAP de desenvolvimento
docs/          contexto do kit, plano, validação
specs/         artefatos do spec-kit por feature
prompts/       textos das etapas do plano
```

## Kit de contexto

O kit original (contexto da empresa, padrões e prompts) está em `docs/contexto/`, `docs/modelos/`
e `prompts/`. Os arquivos de `docs/modelos/` servem só como referência de estrutura e layout.
