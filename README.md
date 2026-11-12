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
| 007 | Estudos de desempenho e estabilidade com tipo controlado (14 tipos), critério congelado, medidas lançadas ou importadas (CSV/XLSX com mapeamento por equipamento) e cálculo automático (média, DP, CV%, diferenças, regressão e R², correlação, sensibilidade e especificidade com IC 95% de Clopper-Pearson ou Wilson, detecção e desvios), com arredondamento registrado; não aplicável com justificativa; tabelas e conclusão no RAPD e na Validação, no resumo assinado e no documento gerado; bloqueio na aprovação e nova versão com motivo |
| 008 | Caderno de laboratório eletrônico por projeto: entradas numeradas com data e hora do servidor, texto formatado com lista branca no servidor e imagens coladas, materiais ligados à versão dos cadastros, anexos com SHA-256, modelos de entrada versionados, assinatura do autor e da testemunha com a senha de rede (bloqueio e correção só por adendo assinado), vínculos nos dois sentidos com subdocumentos, lotes e estudos, promoção de CSV/XLSX para estudo, linha do tempo e busca em português com filtros e entradas atrasadas |
| 009 | Documento completo do projeto (registro histórico, RDC 665/2022 art. 61) com um clique: capa geral, sumário com as páginas reais, TAP, Plano de Negócios (dados financeiros só com permissão ou omitidos por opção), subdocumentos aprovados na versão vigente com as capas, alterações, Verificação Final, Saída, quadro de versões, resumo da trilha, histórico do caderno (completo ou resumido) e lista de anexos; pendências antes de gerar; rascunho com marca d'água ou oficial com selo e código de verificação; geração assíncrona com progresso e reaproveitamento quando nada mudou |
| 010 | Painel do gestor e notificações: quatro totais e carteira dos projetos acessíveis (etapa atual, percentual aprovado, marcos, atraso, líder; custo e retorno só com permissão), cache de 5 minutos, linha do tempo do projeto pela trilha, minhas pendências, exportação XLSX e e-mails imediatos de devolução e aprovação mais resumo diário às 7h das pendências vencidas, com preferências por tipo (assinatura pendente sempre ligada) |
| 011 | Dossiê técnico para a ANVISA na estrutura I a XII: definição declarativa em YAML (itens, classes e fontes) versionada, checagem item a item para a classe de risco (completo, faltando, não aplicável com justificativa, com a origem), PDF/A e DOCX no formato do contexto com declaração do responsável técnico e legal, pacote ZIP com os anexos, biblioteca de textos padrão com aprovação por senha, complementos por projeto, família de kits, registro do envio e do resultado e aditamento com os itens alterados |
| 013 | Revisão controlada dos modelos de subdocumento e de layout (pedido do usuário): a Qualidade/AR abre, altera, envia com motivo e impacto e descarta; o Gestor de P&D devolve com comentário ou aprova com assinatura e vigência imediata ou futura; histórico com etapas, comparação entre versões, uso por versão, verificação de integridade e retirada de uso de modelo de subdocumento |
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

## Kit de contexto

O kit original (contexto da empresa, padrões e prompts) está em `docs/contexto/`, `docs/modelos/`
e `prompts/`. Os arquivos de `docs/modelos/` servem só como referência de estrutura e layout.
