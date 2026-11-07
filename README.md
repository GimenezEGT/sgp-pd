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

## Funções já entregues

| Feature | O que entrega |
| --- | --- |
| 001 | Login pela rede (AD/LDAP), perfis com motivo e aprovação, sessão com expiração, trilha de auditoria encadeada por SHA-256 e verificação de integridade |
| 002 | Abertura de projeto: TAP, Plano de Negócios (dados financeiros restritos), submissão, devolução e aprovação com código `PD-AAAA-NNN` |
| 003 | Cadastros de apoio versionados (lotes, insumos, kits, amostras, painéis, normas, referências), anexos com SHA-256 conferido, importação de insumos e listas controladas mantidas pela Qualidade |

Cadastros (feature 003): em **Cadastros**, cada registro é corrigido no próprio lugar até ser
usado em documento assinado; depois disso a correção cria nova versão com motivo e a anterior
continua intacta. A importação de insumos aceita CSV (`;` ou `,`) ou XLSX no layout de
`/cadastros/insumos/modelo.csv`, mostra a pré-visualização e só grava depois da confirmação.
Amostras guardam só o código interno e dados analíticos (LGPD). As listas controladas ficam em
**Listas controladas**, só para a Qualidade/AR.

## Estrutura

```text
config/        settings, urls, celery
sgp/           apps (core, accounts, audit, vocab, projects, files, catalog)
tests/         pytest, espelhando as apps
deploy/        Dockerfile, Nginx, PostgreSQL, LDAP de desenvolvimento
docs/          contexto do kit, plano, validação
specs/         artefatos do spec-kit por feature
prompts/       textos das etapas do plano
```

## Kit de contexto

O kit original (contexto da empresa, padrões e prompts) está em `docs/contexto/`, `docs/modelos/`
e `prompts/`. Os arquivos de `docs/modelos/` servem só como referência de estrutura e layout.
