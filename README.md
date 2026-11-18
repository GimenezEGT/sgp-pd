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

## Instalar em outra máquina

Tudo roda no Docker: na máquina nova não é preciso instalar Python, PostgreSQL nem bibliotecas.

1. **Pré-requisitos.** Windows 10/11 ou macOS (Intel ou Apple Silicon): Docker Desktop (no Windows,
   com WSL 2). Linux: Docker Engine com o plugin Compose v2 e o usuário no grupo `docker`. Git.
   Uns 6 GB livres em disco. Internet na primeira construção (imagens base e pacotes); sem internet,
   veja "Máquina sem internet".
2. **Levar o código.** O repositório é privado no GitHub
   ([GimenezEGT/sgp-pd](https://github.com/GimenezEGT/sgp-pd)), por decisão do usuário em
   18/11/2026; o plano previa mantê-lo só na rede da empresa (ratificar com a TI e a Garantia da
   Qualidade).
   - GitHub (recomendado): na máquina nova, entre numa conta com acesso ao repositório
     (`gh auth login` ou a janela de login que o Git abre) e rode
     `git clone https://github.com/GimenezEGT/sgp-pd.git`. Mudanças: `git push` aqui e `git pull` lá.
   - Pasta compartilhada da rede: nesta máquina, uma vez,
     `git clone --bare . //servidor/pasta/sgp-pd.git` e `git remote add rede //servidor/pasta/sgp-pd.git`;
     depois de cada mudança, `git push rede main`. Na máquina nova:
     `git clone //servidor/pasta/sgp-pd.git sgp-pd`.
   - Sem rede: `git bundle create sgp-pd.bundle --all` aqui, leve o arquivo e, na máquina nova,
     `git clone sgp-pd.bundle sgp-pd`.
3. **Configurar.** Na pasta `sgp-pd`: `cp .env.example .env` (PowerShell:
   `Copy-Item .env.example .env`). Para testes, os valores fictícios servem; troque senhas e chave se
   outras pessoas forem usar. Porta ocupada no computador: troque `HTTPS_PORT`, `HTTP_PORT` ou
   `LDAP_DEV_PORT` no `.env`.
4. **Subir.**

   ```bash
   docker compose up -d --build
   docker compose exec web python manage.py selo_teste
   docker compose exec web python manage.py grant_initial_admin admin.ti --motivo "Implantação" --aprovacao "Gestão da TI"
   ```

   A primeira construção leva alguns minutos; o `web` cria o banco (migrações) ao subir. O
   `selo_teste` cria o certificado de teste do selo dos PDFs oficiais (só em desenvolvimento). Acesse
   `https://localhost:8443/` e aceite o certificado autoassinado; usuários do diretório fictício em
   `deploy/ldap-dev/seed.ldif` (senha `Senha#Dev01`). O banco começa vazio: `gestor.pd`,
   `ana.analista` e `qualidade.ar` entram com o perfil do grupo do diretório; os demais pedem acesso
   em "Solicitar acesso" e o `admin.ti` aprova.
5. **Levar os dados (opcional).** Os projetos ficam no banco e nos arquivos desta máquina, não no
   Git. Aqui, `docker compose exec web python manage.py copia_seguranca`; copie a pasta da cópia
   (`BACKUP_HOST_DIR`, padrão `var/backups`) para a máquina nova e siga
   [docs/operacao/recuperacao.md](docs/operacao/recuperacao.md) (em desenvolvimento, use
   `docker compose` sem `-f docker-compose.yml`).

Outras máquinas da rede acessando esta: inclua o nome ou o IP dela em `DJANGO_ALLOWED_HOSTS`, o
endereço completo (`https://nome:8443`) em `DJANGO_CSRF_TRUSTED_ORIGINS` e o nome em `SGP_CERT_CN`
(apague `deploy/nginx/certs/sgp.*` para gerar o certificado de novo), libere a porta no firewall e
rode `docker compose up -d`. Para uso real, siga "Homologação e produção" (AD e certificados da
empresa).

- **Linux:** os contêineres de desenvolvimento gravam na pasta do projeto como o usuário uid 1000.
  Se `id -u` não for 1000, dê acesso: `sudo setfacl -R -m u:1000:rwX -m d:u:1000:rwX .`
- **Máquina sem internet:** numa máquina com internet e a mesma arquitetura (x86 ou ARM), rode
  `docker compose build` e `docker compose pull`, depois
  `docker save -o sgp-imagens.tar sgp-pd:dev sgp-pd-nginx:latest postgres:17-bookworm redis:7.4-alpine osixia/openldap:1.5.0`;
  na máquina nova, `docker load -i sgp-imagens.tar` e `docker compose up -d` (sem `--build`).
- **Windows, Docker Desktop não inicia** ("Inference manager … dockerInference"): feche o Docker
  Desktop, renomeie as pastas `%LOCALAPPDATA%\Docker\run` e `%LOCALAPPDATA%\docker-secrets-engine`
  e abra o Docker Desktop de novo.

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
`DJANGO_DEBUG=false`. O PKCS#12 do selo e a CA do AD ficam numa pasta do servidor fora do
repositório, indicada em `SGP_SECRETS_DIR` e montada em `/run/sgp-segredos` (somente leitura,
legível pelo uid 1000): `DOCUMENT_SEAL_PKCS12=/run/sgp-segredos/selo.p12` e
`LDAP_CA_CERT_FILE=/run/sgp-segredos/ca-ad.pem`. As variáveis estão em
[specs/001-fundacao-acesso-auditoria/contracts/configuracao.md](specs/001-fundacao-acesso-auditoria/contracts/configuracao.md).

Cópias de segurança (feature 014): `BACKUP_HOST_DIR` aponta para o diretório do host montado pela TI
de outro servidor ou compartilhamento; a cópia roda todo dia (01:00) e o teste de restauração todo
mês (dia 1, 03:00), com o painel **Operação e validação**. Construa a imagem com
`SGP_COMMIT=$(git rev-parse HEAD)` para que relatórios e cópias registrem a versão. Validação:
[docs/validacao/README.md](docs/validacao/README.md) (IQ, OQ e pacote de validação) e
[docs/operacao/recuperacao.md](docs/operacao/recuperacao.md) (recuperação).

## Funções já entregues

| Feature | O que entrega |
| --- | --- |
| 001 | Login pela rede (AD/LDAP), perfis com motivo e aprovação, sessão com expiração, trilha de auditoria encadeada por SHA-256 e verificação de integridade |
| 002 | Abertura de projeto: TAP, Plano de Negócios (dados financeiros restritos), submissão, devolução e aprovação com código `PD-AAAA-NNN` |
| 007 | Estudos de desempenho e estabilidade com tipo controlado (14 tipos), critério congelado, medidas lançadas ou importadas (CSV/XLSX com mapeamento por equipamento) e cálculo automático (média, DP, CV%, diferenças, regressão e R², correlação, sensibilidade e especificidade com IC 95% de Clopper-Pearson ou Wilson, detecção e desvios), com arredondamento registrado; não aplicável com justificativa; tabelas e conclusão no RAPD e na Validação, no resumo assinado e no documento gerado; bloqueio na aprovação e nova versão com motivo |
| 008 | Caderno de laboratório eletrônico por projeto: entradas numeradas com data e hora do servidor, texto formatado com lista branca no servidor e imagens coladas, materiais ligados à versão dos cadastros, anexos com SHA-256, modelos de entrada versionados, assinatura do autor e da testemunha com a senha de rede (bloqueio e correção só por adendo assinado), vínculos nos dois sentidos com subdocumentos, lotes e estudos, promoção de CSV/XLSX para estudo, linha do tempo e busca em português com filtros e entradas atrasadas |
| 009 | Documento completo do projeto (registro histórico, RDC 665/2022 art. 61) com um clique: capa geral, sumário com as páginas reais, TAP, Plano de Negócios (dados financeiros só com permissão ou omitidos por opção), subdocumentos aprovados na versão vigente com as capas, alterações, Verificação Final, Saída, quadro de versões, resumo da trilha, histórico do caderno (completo ou resumido) e lista de anexos; pendências antes de gerar; rascunho com marca d'água ou oficial com selo e código de verificação; geração assíncrona com progresso e reaproveitamento quando nada mudou |
| 010 | Painel do gestor e notificações: quatro totais e carteira dos projetos acessíveis (etapa atual, percentual aprovado, marcos, atraso, líder; custo e retorno só com permissão), cache de 5 minutos, linha do tempo do projeto pela trilha, minhas pendências, exportação XLSX e e-mails imediatos de devolução e aprovação mais resumo diário às 7h das pendências vencidas, com preferências por tipo (assinatura pendente sempre ligada) |
| 011 | Dossiê técnico para a ANVISA na estrutura I a XII: definição declarativa em YAML (itens, classes e fontes) versionada, checagem item a item para a classe de risco (completo, faltando, não aplicável com justificativa, com a origem), PDF/A e DOCX no formato do contexto com declaração do responsável técnico e legal, pacote ZIP com os anexos, biblioteca de textos padrão com aprovação por senha, complementos por projeto, família de kits, registro do envio e do resultado e aditamento com os itens alterados |
| 012 | Integração com o Sankhya só pelo API Gateway oficial: cliente com OAuth 2.0 client credentials e renovação do token, mensagens de integração criadas na transação das aprovações (projeto, documento, lotes, insumos novos como solicitação de cadastro, resultados de estudo) e enviadas por saveRecord com chave de idempotência e novas tentativas em espera crescente, mapeamento configurável pela TI, consulta de produto no cadastro de insumos e lotes, fila com reprocessamento e exportação de contingência em CSV, XLSX e JSON |
| 013 | Revisão controlada dos modelos de subdocumento e de layout (pedido do usuário): a Qualidade/AR abre, altera, envia com motivo e impacto e descarta; o Gestor de P&D devolve com comentário ou aprova com assinatura e vigência imediata ou futura; histórico com etapas, comparação entre versões, uso por versão, verificação de integridade e retirada de uso de modelo de subdocumento |
| 014 | Operação e validação: cópia de segurança diária do banco (instantâneo consistente) e dos arquivos (acervo endereçado pelo SHA-256) com manifesto, retenção de 35 dias com a cópia mensal mantida, teste de restauração mensal num banco isolado (resumos, restauração, contagens, cadeia da trilha e arquivos), avisos por e-mail à TI, qualificações de instalação (IQ) e de operação (OQ) com relatório PDF guardado, revisão de acessos em CSV/XLSX e roteiros de IQ, OQ e recuperação |
| 015 | Correções do ciclo de revisão e assinatura (teste do usuário): assinatura "Revisado" única por pessoa e versão; Gestor que elaborou vê o aviso da segregação, o caminho para a delegação e a devolução com comentário, e encontra o documento na seção "Elaborados por você" da Fila de revisão; aviso no envio por quem pode aprovar; situação pelo nome nas telas de envio e aprovação |
| 016 | Versão do documento final do projeto: cada parte (TAP, Plano de Negócios e subdocumentos) mantém a versão própria e cada aprovação de nova versão de uma parte registra a versão seguinte do documento final, imutável, com o que mudou (parte, versão anterior e nova), a composição completa (versão, data de aprovação e resumo de cada parte), quem aprovou e o evento na trilha; seção "Versões do documento final" na tela do documento completo, histórico de versões de cada parte, capa, quadro e nome do arquivo do PDF com a versão do documento final e histórico reconstruído a partir das aprovações já registradas |
| 006 | Geração dos documentos no padrão da planilha Capas Projeto: PDF/A-2b (oficial quando aprovado, selado com o certificado da empresa e com código de verificação) e DOCX de conferência para subdocumentos, TAP e Plano de Negócios; marca d'água nos rascunhos, conteúdo congelado na aprovação (regeneração idêntica), arquivo das gerações com SHA-256 e modelos de layout versionados mantidos pela Qualidade |
| 005 | Ciclo de revisão (rascunho, em revisão, devolvido, aprovado; anterior substituída) com assinatura eletrônica: senha de rede, significado, data e hora do servidor e SHA-256 do conteúdo canônico; versões aprovadas congeladas, verificação de integridade, nova versão com motivo, delegação, bloqueio após três falhas e fila de revisão; TAP e Plano assinados na submissão e na aprovação do projeto |
| 004 | Modelos de formulário versionados (versão 05 dos nove subdocumentos carregada) e subdocumentos preenchidos a partir do modelo: Entrada com "aplica / não se aplica", Validação com pendências, Verificação Final derivada, Saída e Alteração de Projeto; ordem do fluxo com autorização do Gestor e aprovação provisória até a 005 |
| 003 | Cadastros de apoio versionados (lotes, insumos, kits, amostras, painéis, normas, referências), anexos com SHA-256 conferido, importação de insumos e listas controladas mantidas pela Qualidade |

Cadastros (feature 003): em **Cadastros**, cada registro é corrigido no próprio lugar até ser
usado em documento assinado; depois disso a correção cria nova versão com motivo e a anterior
continua intacta. A importação de insumos aceita CSV (`;` ou `,`) ou XLSX no layout de
`/cadastros/insumos/modelo.csv`, mostra a pré-visualização e só grava depois da confirmação.
Amostras guardam só o código interno e dados analíticos (LGPD). As listas controladas ficam em
**Listas controladas**, só para a Qualidade/AR.

Documentos (feature 006): em cada subdocumento e no projeto, **Documentos gerados** pede o PDF
ou o DOCX; a geração roda no worker e a tela acompanha a situação. O PDF de versão aprovada é o
documento oficial: o selo usa o PKCS#12 indicado em `DOCUMENT_SEAL_PKCS12` e a senha em
`DOCUMENT_SEAL_PASSWORD` (fora do repositório; em desenvolvimento, `python manage.py selo_teste`
gera um certificado de teste em `var/certs/`). **Verificar documento** confere o código impresso
no rodapé. A Qualidade/AR mantém capa, cabeçalho, rodapé e estilos em **Modelos de layout**.

## Estrutura

```text
config/        settings, urls, celery
sgp/           apps (core, accounts, audit, vocab, projects, files, catalog, formtemplates, subdocuments, signatures)
tests/         pytest, espelhando as apps
deploy/        Dockerfile, Nginx, PostgreSQL, LDAP de desenvolvimento
docs/          contexto do kit, plano, validação
specs/         artefatos do spec-kit por feature
prompts/       textos das etapas do plano
```

## Relatório final da execução do plano

[docs/relatorio-final.md](docs/relatorio-final.md): situação das features 001 a 016, decisões
provisórias a ratificar, dependências de terceiros, verificações manuais e checklists pendentes e
próximos passos da implantação.

## Kit de contexto

O kit original (contexto da empresa, padrões e prompts) está em `docs/contexto/`, `docs/modelos/`
e `prompts/`. Os arquivos de `docs/modelos/` servem só como referência de estrutura e layout.
