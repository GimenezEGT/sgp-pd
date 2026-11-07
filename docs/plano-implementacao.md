# Sistema de Gestão de Projetos de P&D (IVD) — Plano de Implementação com Spec-Driven Development

## Resumo

O sistema substitui os formulários avulsos do PSG 20 por uma aplicação web na intranet que guarda cada projeto de P&D de diagnóstico in vitro, do Termo de Abertura à Saída de Projeto, com trilha de auditoria e assinatura eletrônica. Ele gera os documentos no padrão visual atual da empresa, o documento completo do projeto com o caderno de laboratório, o dossiê técnico para registro na ANVISA e a exportação dos dados para o Sankhya.

Quem usa o sistema:

- **Analista/pesquisador** — registra experimentos no caderno de laboratório e preenche os subdocumentos.
- **Líder do projeto** — abre o projeto (TAP + Plano de Negócios) conduz as etapas e monta o dossiê.
- **Gestor de P&D** — acompanha o portfólio e assina as aprovações.
- **Qualidade e Assuntos Regulatórios** — consultam e revisam o dossiê.

Como usar este plano: a construção segue o Spec-Driven Development do spec-kit (repo: https://github.com/github/spec-kit.git) no Claude Code. Primeiro se prepara o repositório (Fase 0) e se grava a constituição; depois cada feature passa pelo mesmo ciclo — especificar, esclarecer, planejar, quebrar em tarefas, analisar , gerar checklist e implementar — com os prompts prontos de cada seção. Os artefatos do spec-kit (especificação, plano, tarefas, testes) também servem de evidência para a validação do sistema computadorizado exigida pelas Boas Práticas de Fabricação.

## Premissas e decisões a confirmar

O plano parte de dez premissas; stack, hospedagem e autenticação precisam do aval da TI antes da Feature 001, e a assinatura precisa do aval da Garantia da Qualidade.

| Tema | Premissa adotada | Alternativa | Quem confirma |
| --- | --- | --- | --- |
| Equipe | 1 desenvolvedor operando o Claude Code, revisão de código por uma 2ª pessoa e 1 h por semana com o Gestor de P&D | 2 desenvolvedores em paralelo a partir do Marco 2 | Gestor de P&D |
| Linguagem e framework | Python 3.12+ com Django (versão LTS vigente), páginas renderizadas no servidor com HTMX | .NET (ASP.NET Core) se a TI só sustenta Microsoft | TI |
| Banco de dados | PostgreSQL 16+ | SQL Server | TI |
| Hospedagem | VM Linux na intranet com Docker Compose e HTTPS interno | VM Windows Server | TI |
| Autenticação | Login de rede via Active Directory (LDAP); perfis e permissões no próprio sistema | Contas locais com política de senha e bloqueio | TI |
| Assinatura | Assinatura eletrônica avançada interna: reautenticação, significado, data/hora e hash do conteúdo; PDF selado com certificado da empresa | Certificado ICP-Brasil (e-CPF) para cada signatário | Garantia da Qualidade e Jurídico |
| Sankhya | API Gateway oficial (OAuth 2.0), gravando em tabelas adicionais e lendo o cadastro de produtos | Exportação de arquivos para importação manual na primeira fase | TI e consultoria Sankhya |
| Regulatório | ANVISA (RDC 830/2023) como padrão; projetos MAPA marcados no projeto, com itens próprios na Saída | — | Assuntos Regulatórios |
| Legado | Projetos concluídos entram como anexos somente leitura; só projetos novos nascem estruturados | Migrar 1 projeto completo como teste | Gestor de P&D |
| Validação | O sistema é tratado como software do sistema da qualidade e validado antes do uso oficial | — | Garantia da Qualidade |

Se uma premissa mudar, ajuste apenas o texto do `/speckit-plan` da feature afetada. As especificações (`/speckit-specify`) não citam tecnologia e continuam válidas.

## O que os modelos atuais mostram

Os seis arquivos seguem um padrão estável: cada subdocumento abre com uma capa padronizada do PSG 20 e repete os tópicos da capa como seções numeradas; o dossiê técnico segue os itens I a XII do art. 58 da RDC 830/2023. Os dados dos modelos são fictícios; só a estrutura foi aproveitada.

### Capa dos subdocumentos

A planilha Capas Projeto tem 10 abas: Entrada de Projeto, Alteração de Projeto, Entrada (formulário opcional), Elaboração de Formulação, Elaboração de Lote Piloto, RAPD, Análise Crítica, Validação do Produto, Verificação Final de Validação e Saída de Projeto. As capas, em A4 retrato, seguem sempre esta ordem:

1. Faixa com o logotipo Bioclin · Quibasa no topo.
2. Título do subdocumento, Calibri 23–24 pt, negrito e centralizado.
3. Nome do produto em caixa alta, Calibri 20 pt negrito.
4. "VERSÃO 01" em Calibri 20 pt; na Alteração, "Versão alterada" e "Nova Versão".
5. "ESTE RELATÓRIO DEVE CONTER:" em 16 pt negrito, seguido dos tópicos numerados em 14 pt, em uma ou duas colunas.
6. Bloco de assinaturas em 12 pt: Analista Responsável (Nome/Função), Gestor de P&D e Data; na Validação, "Gestor de P&D responsável pela Aprovação".
7. Rodapé "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos" em 11 pt; Entrada, Formulação e Lote Piloto também numeram "Página N".

As margens são 1,3 cm nas laterais e 2 cm em cima e embaixo. Duas capas fogem do padrão: a Verificação Final de Validação é uma tabela Previsto × Realizado × Disposição, e a Saída lista os setores de transferência como caixas de seleção.

### Corpo dos documentos de projeto

- Depois de cada capa, os tópicos viram títulos numerados em negrito ("1. Amostras", "2. Funcionalidade") e as tabelas são numeradas em sequência ("Tabela 01 – Comparação de Métodos").
- O projeto Extração Magnética traz duas seções que pertencem ao Plano de Negócios: Viabilidade Financeira (concorrentes, preços, apresentações, custo máximo, preço previsto, venda anual) e Viabilidade Produtiva (estrutura fabril, equipe, controle de qualidade).
- A Validação inclui validação externa com laboratórios parceiros e estudos de estabilidade; a Saída pode ganhar itens extras, como "12. Imagem do produto".
- Os tópicos variam entre capa e corpo: a capa da Análise Crítica lista 3 itens, mas o projeto Extração Magnética usa 4. Isso pede modelos versionados, não formulários fixos no código.

### Formulário opcional de entrada

A aba Entrada (form. opcional) já é um formulário estruturado, com 91 caixas de seleção: amostra, funcionalidade, classificação, automação, usuário, armazenamento, filtros primário e secundário (280 a 800 nm) e classificação de uso. A tabela "Aplica / Não se aplica" lista 16 requisitos, de Metodologia a Efeito prozona, e define quais estudos a Validação e o dossiê precisam conter. O sistema adota essas listas como vocabulários controlados.

### Dossiê técnico

O texto extraído dos dois dossiês indica cabeçalho em itálico "Dossiê Técnico \<PRODUTO>" e rodapé "Quibasa Química Básica Ltda." com número de página. Os itens principais usam algarismos romanos (I. Descrição do produto até XII. Referências bibliográficas), os subitens usam letras (A. Finalidade) e números (1. Analito). O dossiê fecha com a declaração do responsável técnico e legal, com registro no conselho, cidade e data.

Capas, sumário e cabeçalhos dos .docx não vêm completos no texto extraído; por isso a Feature 006 começa com uma prova de layout sobre os arquivos originais.

### Ajustes de estrutura nos formulários

- Os tópicos 6 e 9 da Entrada de Projeto têm o mesmo rótulo, "Classificação de Uso".
- A capa da Saída de Projeto numera dois itens como "11".
- A Análise Crítica tem 3 tópicos na capa e 4 no corpo de um dos projetos.
- Capa e corpo usam rótulos diferentes para o mesmo tópico (ex.: "Apresentações" e "Apresentações e Composições").

O sistema resolve isso com modelos versionados, rótulos únicos por modelo e numeração automática.

## Exigências regulatórias que moldam o sistema

A RDC 665/2022 descreve, artigo por artigo, o fluxo que o PSG 20 já implementa; o sistema materializa esse fluxo, e a RDC 830/2023 define o que o dossiê precisa conter.

> Diagrama: fluxo do projeto · 9 subdocumentos e os artigos da RDC 665/2022 (disponível no documento original).
O caderno de laboratório alimenta formulação, lote piloto, RAPD e validação; a Alteração de Projeto pode surgir em qualquer etapa e reabre o que mudou.

Além do fluxo de projeto, estas exigências viram funções do sistema:

| Requisito | Fonte | O que o sistema faz |
| --- | --- | --- |
| Projeto liberado para produção só após aprovação do pessoal designado | RDC 665/2022, art. 59 | A Saída de Projeto só fecha com a assinatura do Gestor de P&D |
| Alterações documentadas, validadas, revisadas, aprovadas e com avaliação de risco antes de implementar | RDC 665/2022, art. 60 | A Alteração de Projeto exige justificativa e análise de risco e gera nova versão |
| Registro histórico do projeto para cada produto | RDC 665/2022, arts. 3º, XXV, e 61 | O documento completo do projeto é montado a partir dos registros aprovados |
| Software que possa afetar a qualidade do produto ou o sistema da qualidade deve ser validado, verificado periodicamente e alterado sob controle | RDC 665/2022, arts. 104 a 106 | O próprio sistema passa por validação antes do uso oficial |
| Cópia de segurança de todos os documentos e registros digitais | RDC 665/2022, art. 35 | Backup automático com teste de restauração |
| Registros mantidos pelo tempo de vida do produto, nunca menos de 2 anos | RDC 665/2022, art. 37 | Nada é apagado; a retenção é configurada por produto |
| Assinatura manuscrita ou digital, com data, aceita em vários registros | RDC 665/2022, arts. 27, 42, 47, 57 e 59 | Assinatura eletrônica com data e hora do servidor |
| Assinatura eletrônica avançada: ligada ao signatário, sob seu controle e capaz de revelar alterações | Lei 14.063/2020, art. 4º | Reautenticação ao assinar, hash do conteúdo e trilha de auditoria |
| Dossiê com os itens do art. 58, organizados pelo Anexo II conforme a classe de risco | RDC 830/2023, art. 58 e Anexo II | Gerador do dossiê com itens obrigatórios por classe e checagem de completude |
| Classes I e II são notificadas; classes III e IV, registradas | RDC 830/2023, arts. 6º e 7º | A classe de risco do projeto define o regime e os itens exigidos |
| Dossiê de classe I não é enviado, mas fica disponível para inspeção | RDC 830/2023, art. 57, § 1º | O dossiê de classe I é gerado e arquivado, sem pacote de envio |
| Registro válido por 10 anos | RDC 830/2023, art. 12 | Alerta de revalidação com antecedência configurável |
| Responsáveis legal e técnico respondem pelas informações apresentadas | RDC 830/2023, art. 56 | O dossiê sai com a declaração do responsável técnico e legal para assinatura |

Em 25/08/2026 a ANVISA publicou o [Manual para Regularização de Dispositivos para Diagnóstico in Vitro](https://www.pureglobal.com/pt/news/anvisa-ivd-class-i-ii-notification-manuals-2026), com um capítulo sobre o dossiê técnico. A Feature 011 confere a estrutura do gerador contra esse manual, porque documentação obrigatória ausente pode levar ao indeferimento sumário da petição.

Para a assinatura interna, formalize num procedimento (atualização do PSG 20 ou POP do sistema) que a assinatura eletrônica do sistema equivale à manuscrita nos registros de P&D.

## Arquitetura proposta

Um único aplicativo web modular, num servidor da intranet, concentra regras, dados e geração de documentos; as únicas saídas de rede são para o Active Directory, o e-mail interno e o API Gateway do Sankhya.

> Diagrama: arquitetura · componentes no servidor e integrações (disponível no documento original).
O navegador fala só com o Nginx; PDFs, e-mails e envios ao Sankhya rodam em tarefas de fundo, e o backup cobre banco e arquivos.

### Decisões de desenho

1. **Formulários dirigidos por modelo.** Cada subdocumento é uma definição versionada (tópicos, campos, tabelas, regras, capa e rodapé). Trocar "Formulário Versão 05" por 06 é cadastro, não programação, e cada documento guarda a versão de modelo usada.
2. **Fonte única.** Lotes, insumos, kits de referência, amostras, normas e pessoas são cadastrados uma vez e referenciados em todos os documentos.
3. **Cálculo no servidor.** Média, desvio-padrão, CV%, regressão, R² e sensibilidade/especificidade com IC 95% são calculados pelo sistema e congelados na versão assinada.
4. **Nada é apagado.** Exclusão é lógica, a versão assinada é imutável e toda correção gera nova versão com motivo.
5. **Trilha de auditoria encadeada.** Cada evento guarda o hash do anterior, e uma verificação diária revela qualquer adulteração.
6. **Documentos por modelo de layout.** A Qualidade mantém capa, cabeçalho, rodapé e estilos; o sistema só preenche os dados.

### Stack sugerida

| Camada | Escolha | Motivo |
| --- | --- | --- |
| Aplicação web | Django + templates + HTMX | Formulários, permissões, migrações e administração prontos; sem SPA para manter |
| Banco | PostgreSQL | Integridade relacional e JSONB para os dados dos formulários |
| Tarefas em segundo plano | Celery + Redis | PDFs grandes e integração com o Sankhya sem travar a tela |
| Documentos | Modelos Word (docxtpl) + LibreOffice para PDF/A, ou HTML paginado (WeasyPrint) | Decisão na prova de layout da Feature 006 |
| Assinatura de PDF | pyHanko (PAdES) | Selo verificável no próprio arquivo |
| Autenticação | django-auth-ldap | Login de rede e grupos do AD |
| Testes | pytest, pytest-django e Playwright | Regras, cálculos e fluxos de ponta a ponta |
| Implantação | Docker Compose + Nginx | Mesmo ambiente em homologação e produção |

### Modelo de dados central

| Entidade | O que guarda |
| --- | --- |
| Projeto | Código, produto, família, classe de risco, regime (ANVISA ou MAPA), líder, status e versão do projeto |
| TAP e Plano de Negócios | Escopo, objetivos, custos, prazos, mercado-alvo, retorno em 5 anos e viabilidade |
| Membro do projeto | Pessoa, papel e vigência no projeto |
| Modelo de formulário | Tipo, versão do formulário, referência PSG, tópicos, campos, regras e vigência |
| Subdocumento | Tipo, versão do documento, estado, modelo usado e dados validados |
| Versão congelada | Cópia imutável do conteúdo assinado, com hash SHA-256 |
| Assinatura | Pessoa, papel, significado, data/hora, hash assinado e método |
| Entrada do caderno | Pesquisador, data, objetivo, materiais, procedimento, resultados, anexos e testemunha |
| Lote | Código, tipo (piloto ou validação), fabricação, validade, local e responsável |
| Insumo | Matéria-prima ou embalagem: código no Sankhya, descrição, lote, fabricante e certificado |
| Estudo | Tipo controlado, critério de aceitação, dados, resultado calculado e conclusão |
| Evento de auditoria | Quem, quando, o quê, valor anterior e novo, motivo e hash encadeado |
| Documento gerado | Tipo, versão, arquivo, hash e modelo de layout usado |
| Mensagem de integração | Destino, conteúdo, status, tentativas e resposta do Sankhya |

## Spec-kit no Claude Code

A versão 1.x do spec-kit instala dez skills `speckit-*` no repositório; a constituição roda uma vez, e cada feature percorre especificar → esclarecer → planejar → checklist → tarefas → analisar → implementar → convergir.

> Diagrama: ciclo do spec-kit por feature · 8 etapas e o laço de convergência (disponível no documento original).
Clarify, checklist e analyze (tracejados) são opcionais no spec-kit, mas este plano recomenda usá-los em todas as features.

### Instalação

```bash
# Pré-requisitos: Python 3.11+, uv, Git e Claude Code
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
specify version
specify init sgp-pd --integration claude --script sh   # no Windows: --script ps
cd sgp-pd
specify extension add git   # opcional: um branch Git por feature
claude
```

Troque `vX.Y.Z` pela tag mais recente; a 1.0.9 saiu em 21/09/2026. As skills ficam em `.claude/skills/speckit-*/SKILL.md`. Para atualizar depois, use `specify self upgrade` e `specify integration upgrade claude`.

### O que cada skill faz

| Skill | Quando usar | O que produz |
| --- | --- | --- |
| `/speckit-constitution` | Uma vez, no início | `.specify/memory/constitution.md` |
| `/speckit-specify` | Início de cada feature: o quê e por quê, sem tecnologia | `spec.md` da feature e `checklists/requirements.md` |
| `/speckit-clarify` | Logo após especificar | Até 5 perguntas; as respostas vão para o `spec.md` |
| `/speckit-plan` | Depois de esclarecer: tecnologia e arquitetura | `plan.md` e artefatos de apoio |
| `/speckit-checklist` | Opcional, antes das tarefas | Checklists de qualidade dos requisitos |
| `/speckit-tasks` | Depois do plano | `tasks.md` em fases |
| `/speckit-analyze` | Antes de implementar | Relatório de conflitos e lacunas, sem editar arquivos |
| `/speckit-implement` | Execução | Código e testes, fase a fase |
| `/speckit-converge` | Depois de implementar | "Converged" ou novas tarefas no `tasks.md` |
| `/speckit-taskstoissues` | Opcional, se usar GitHub | Issues a partir das tarefas |

Nas versões 0.x os nomes usam ponto (`/speckit.specify`); digite `/` no Claude Code para ver as skills instaladas na sua versão.

### Regras de trabalho

- Uma feature por vez; revise cada artefato antes da etapa seguinte.
- No `/speckit-specify` entram só o quê e o porquê; tecnologia vai no `/speckit-plan`.
- Responda o `/speckit-clarify` com o Gestor de P&D ou a Qualidade quando a pergunta for de processo.
- Use `/speckit-checklist` com os temas sugeridos em cada feature (regulatório, segurança, integridade de dados).
- Faça commit ao fim de cada etapa: o histórico do Git vira evidência para a validação do sistema.
- Repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged.
- Rode a aplicação e teste os fluxos antes de abrir a próxima feature.

Depois do `/speckit-plan`, as etapas `/speckit-tasks`, `/speckit-analyze`, `/speckit-implement` e `/speckit-converge` não precisam de texto extra; cada feature abaixo traz só o que muda.

## Fase 0 — Preparar o repositório e o contexto

Antes da primeira skill, o repositório recebe o kit de contexto que acompanha este plano, para o Claude Code usar os padrões da empresa em vez de inventá-los.

1. Crie um repositório Git interno chamado `sgp-pd` e inicialize o spec-kit com os comandos da seção anterior.
2. Descompacte o kit na raiz do repositório.
3. Copie para `docs/modelos/` os arquivos originais: Capas Projeto.xlsx, os dois projetos, a Saída de Projeto e os dois dossiês.
4. Revise o `CLAUDE.md` do kit (idioma, regras e onde ler o contexto) e junte com o que o `specify init` tiver criado.
5. Rode `/speckit-constitution` com o texto da próxima seção.
6. Faça o commit "chore: contexto e constituição".

| Arquivo do kit | Conteúdo |
| --- | --- |
| `CLAUDE.md` | Regras permanentes para o Claude Code neste repositório |
| `docs/contexto/01-visao-geral.md` | Objetivo, usuários, fluxo do projeto e escopo |
| `docs/contexto/02-dicionario-documentos.md` | Cada documento com tópicos, campos, tipos e regras |
| `docs/contexto/03-padroes-formatacao.md` | Capa, cabeçalho, rodapé, numeração, tabelas e dossiê |
| `docs/contexto/04-requisitos-regulatorios.md` | Artigos da RDC 665/2022 e da RDC 830/2023 ligados a funções |
| `docs/contexto/05-vocabularios.md` | Listas controladas: amostras, automação, filtros, estudos, setores |
| `docs/contexto/06-casos-de-teste.md` | Regras de validação e vetores de cálculo de referência |
| `docs/contexto/07-integracao-sankhya.md` | O que já se sabe da API e o que pedir à consultoria |
| `docs/modelos/` | Pasta para os arquivos originais |
| `prompts/` | Os textos de cada etapa deste plano, um arquivo por feature |

O kit traz também um `README.md` com o passo a passo e `docs/plano-implementacao.md`, este plano em Markdown, para o Claude Code consultar.

Os modelos servem só como referência de estrutura e layout: os dados neles são fictícios e não entram em cálculos nem em testes. Mantenha o repositório privado, na rede da empresa.

## Constituição do projeto

A constituição fixa nove princípios que todas as features precisam respeitar; cole o bloco abaixo no Claude Code, revise o `constitution.md` gerado com a Garantia da Qualidade e registre a data de ratificação.

```text
/speckit-constitution Crie a constituição do SGP-P&D, sistema de gestão de projetos de P&D de produtos para diagnóstico in vitro, usado na intranet da empresa. Antes de escrever, leia todos os arquivos de docs/contexto/. Princípios inegociáveis:

1. Rastreabilidade (ALCOA+): todo dado tem autor, data e hora do servidor, versão e origem. Nenhum registro é apagado fisicamente; correções geram nova versão com motivo obrigatório.
2. Trilha de auditoria imutável: criação, alteração, assinatura, geração de documento, exportação e mudança de permissão geram eventos append-only, encadeados por hash e consultáveis por projeto.
3. Assinatura eletrônica: assinar exige reautenticação e registra pessoa, papel, significado (elaborado, revisado, aprovado), data e hora e o hash do conteúdo. Documento assinado fica bloqueado.
4. Modelos versionados: tipos de subdocumento, tópicos, campos, capas e rodapés ("Formulário Versão", "Referência PSG") são dados configuráveis e versionados. Cada documento guarda a versão de modelo que usou.
5. Fonte única: lotes, insumos, amostras, kits de referência, normas e pessoas são cadastrados uma vez e referenciados. Textos e tabelas gerados nunca redigitam esses dados.
6. Cálculo e numeração automáticos: estatísticas, totais, numeração de tópicos, tabelas, páginas e referências cruzadas são calculados pelo sistema e cobertos por testes.
7. Segurança: só usuários autenticados no domínio; permissões por perfil e por projeto; menor privilégio; HTTPS interno; dados não saem da intranet, exceto para o Sankhya pela API oficial.
8. Qualidade verificável: todo requisito tem critério de aceitação testável e é rastreável até um teste. Regras regulatórias, cálculos e permissões são escritos com testes primeiro (TDD). Isso é evidência para a validação do sistema exigida pela RDC 665/2022, art. 104.
9. Simplicidade: monólito modular, poucas dependências, código e identificadores em inglês, interface, mensagens e documentos em português do Brasil. Nenhuma funcionalidade sem requisito.

Governança: mudanças nesta constituição exigem justificativa, revisão do Gestor de P&D e da Garantia da Qualidade e novo número de versão (semântico). Registre a data de ratificação.
```

Na versão 1.x, `/speckit-constitution` altera só o `constitution.md`; os templates do spec-kit não mudam.

## Roteiro de features

São 12 features em quatro marcos, com estimativa total de 6 a 8 meses; o MVP documental (001 a 006) já substitui planilhas e Word na rotina, e cada marco fecha num portão de aceite.

A ordem segue as dependências: ninguém assina sem perfis (001), nenhum subdocumento existe sem projeto aberto (002) e cadastros (003), e o documento completo e o dossiê só fazem sentido com subdocumentos assinados. O painel (010) pode subir para logo depois da 005 se o Gestor de P&D quiser visibilidade mais cedo.

> Diagrama: roteiro · 4 marcos, validação e 5 portões (disponível no documento original).
As durações supõem um desenvolvedor dedicado; o painel (010) pode migrar para o Marco 2 sem mudar as outras dependências.

## Feature 001 — Fundação: acesso, perfis e trilha de auditoria

A primeira feature entrega o esqueleto seguro: login pela rede, perfis, acesso por projeto e a trilha de auditoria que todas as outras features vão usar.

```text
/speckit-specify Fundação do SGP-P&D: acesso, perfis e trilha de auditoria. Leia docs/contexto/01-visao-geral.md e docs/contexto/04-requisitos-regulatorios.md.

Contexto: o sistema roda na intranet e guarda registros de controle de projeto sujeitos às Boas Práticas de Fabricação (RDC 665/2022). Só pessoas autorizadas entram, e tudo o que acontece precisa ser rastreável.

Perfis: Administrador do sistema; Gestor de P&D; Líder de projeto; Analista/Pesquisador; Qualidade/Assuntos Regulatórios (leitura ampla e revisão); Leitor (consulta). Uma pessoa pode ter mais de um perfil. O acesso a cada projeto depende de ser membro dele, exceto para Gestor de P&D, Qualidade e Administrador.

Histórias:
1. Como colaborador, entro com meu usuário e senha de rede; sem perfil no sistema, vejo como pedir acesso.
2. Como administrador, concedo e revogo perfis; cada mudança de permissão registra quem fez, quando e por quê.
3. Como usuário, minha sessão expira após inatividade configurável e o login bloqueia após tentativas inválidas, conforme a política da TI.
4. Como auditor da Qualidade, consulto a trilha de auditoria por usuário, projeto, período e tipo de evento, e exporto o resultado.
5. Como Garantia da Qualidade, preciso provar que a trilha não foi adulterada: o sistema verifica a integridade da cadeia de eventos e aponta qualquer quebra.

Regras: nenhum registro é apagado fisicamente; data e hora vêm do servidor sincronizado; eventos guardam valor anterior, valor novo e motivo quando houver; colaborador desativado na rede perde o acesso no próximo login.

Fora do escopo: projetos e documentos (features seguintes).
```

Pontos que o `/speckit-clarify` deve fechar:

- Tempo de inatividade e número de tentativas, conforme a política da TI.
- Quem aprova a concessão de perfil.
- Retenção da trilha: tempo de vida do produto, nunca menos de 2 anos (RDC 665/2022, art. 37).
- Necessidade de acesso para consultores externos sem conta na rede.

```text
/speckit-plan Use Python 3.12+ e Django (versão LTS vigente), PostgreSQL 16+, templates do Django com HTMX, sem SPA. Autenticação LDAP/Active Directory com django-auth-ldap e grupos do AD mapeados para perfis; sessões no servidor com expiração configurável. Trilha de auditoria em tabela append-only (sem UPDATE e DELETE por permissão do usuário de banco), cada evento com hash SHA-256 do anterior, e job diário que verifica a cadeia. Datas em UTC no banco, exibidas em America/Sao_Paulo. Monólito modular com apps core, contas e auditoria. Testes com pytest e pytest-django, cobertura mínima de 90% em core e auditoria. Docker Compose com app, banco e Nginx com TLS interno. Configuração por variáveis de ambiente, sem segredos no repositório.
```

Checklists sugeridos: segurança (autenticação e sessão) e integridade de dados (ALCOA+).

Pronto quando:

- [ ] Login pelo AD funciona em homologação e usuário sem perfil é barrado.
- [ ] Uma alteração feita direto no banco é revelada pela verificação da cadeia.
- [ ] A trilha exporta com filtros.
- [ ] `/speckit-converge` reporta Converged.

## Feature 002 — Abertura de projeto: TAP e Plano de Negócios

O líder abre o projeto preenchendo o TAP e o Plano de Negócios; com a aprovação do Gestor de P&D, o projeto recebe código, equipe e marcos e passa a aceitar subdocumentos.

```text
/speckit-specify Abertura de projeto com Termo de Abertura de Projeto (TAP) e Plano de Negócios. Leia docs/contexto/02-dicionario-documentos.md, seções TAP e Plano de Negócios.

Objetivo: o líder abre um projeto de produto para diagnóstico in vitro pelo sistema, em vez de documentos avulsos; o Gestor de P&D aprova; a partir daí o projeto aceita subdocumentos.

Histórias:
1. Como líder de projeto, crio um projeto em rascunho informando o produto: nome, família (quando houver), tecnologia (ex.: bioquímica, imunologia, biologia molecular), órgão regulador (ANVISA ou MAPA), classe de risco prevista e regra de classificação.
2. Preencho o TAP: justificativa, objetivo, escopo incluído e excluído, entregas, premissas, restrições, riscos iniciais, partes interessadas, equipe com papéis e marcos planejados por subdocumento.
3. Preencho o Plano de Negócios: nome do projeto, data, líder, objetivo, descrição geral, custo total do projeto, prazo de execução, mercado-alvo e retorno esperado ano a ano por 5 anos. Incluo a viabilidade financeira (concorrentes, preço por teste dos concorrentes, apresentações dos concorrentes, custo máximo de produção, preço de venda previsto, venda anual prevista) e a viabilidade produtiva (estrutura fabril, equipe de produção, controle de qualidade).
4. Submeto para aprovação; o Gestor de P&D aprova ou devolve com comentário obrigatório. Na aprovação, o projeto recebe código único, fica "Aberto" na versão 01 e a equipe ganha acesso.
5. Como Gestor de P&D, vejo a lista de projetos com filtros por status, líder e produto.

Regras: dados financeiros só aparecem para Gestor de P&D, líder do projeto e perfis autorizados; o retorno total em 5 anos é a soma das previsões anuais; cada marco tem data planejada e, depois, data realizada; toda edição vai para a trilha de auditoria.

Fora do escopo: subdocumentos técnicos (004) e assinatura eletrônica (005). Nesta feature a aprovação é uma confirmação registrada na auditoria; a 005 a substitui por assinatura.
```

Pontos que o `/speckit-clarify` deve fechar:

- Os campos do TAP: o pedido original não os lista, e a lista acima é uma proposta.
- Formato do código do projeto (ex.: PD-2026-001).
- Se "retorno esperado" é receita, margem ou lucro, e se precisa de indicador como payback.
- Se projetos acima de certo custo exigem aprovação da diretoria.

```text
/speckit-plan Reaproveite a base da feature 001. Crie a app "projetos" com Projeto, TermoAbertura, PlanoNegocios, PrevisaoAnual (5 linhas), Marco e MembroProjeto. Valores monetários em Decimal(14,2), moeda BRL e formato brasileiro na tela. Máquina de estados explícita e testada (rascunho, submetido, aprovado, devolvido). Código do projeto gerado por sequência anual no banco, sem colisão em aprovações simultâneas. Permissão por campo para dados financeiros, aplicada também nas consultas e exportações, com testes. Validação no servidor e mensagens em português.
```

Checklists sugeridos: permissões de dados financeiros.

Pronto quando:

- [ ] Um projeto é aberto de ponta a ponta com aprovação do gestor.
- [ ] Usuário sem permissão não vê custo nem retorno, nem pela URL direta.
- [ ] Duas aprovações simultâneas geram códigos diferentes.

## Feature 003 — Cadastros de apoio

Lotes, insumos, kits de referência, amostras e normas passam a existir uma única vez e são referenciados por todos os documentos, o que evita divergências entre documentos.

```text
/speckit-specify Cadastros de apoio usados por todos os subdocumentos: lotes, insumos (matérias-primas e materiais de embalagem), kits de referência, amostras e painéis, normas e referências bibliográficas. Leia docs/contexto/02-dicionario-documentos.md e 05-vocabularios.md.

Problema: hoje o mesmo lote, código ou concentração é redigitado em vários documentos, o que abre espaço para divergências. Cada dado deve existir uma vez e ser referenciado.

Histórias:
1. Como analista, cadastro os lotes do projeto (piloto ou validação) com código, data de fabricação, validade, local de fabricação e responsável pela produção.
2. Cadastro insumos com código, descrição, fabricante, lote do fabricante e certificado de análise anexado; marco se é novo para a empresa, para entrar na Saída de Projeto.
3. Cadastro kits de referência e comparativos com nome, fabricante, lote, validade e número de registro quando houver.
4. Cadastro amostras e painéis com identificador, tipo de amostra (vocabulário controlado), origem, caracterização e condição de armazenamento; uma amostra pode estar em vários estudos.
5. Mantenho bibliotecas de normas (ex.: NBR ISO 13485:2016, NBR ISO 14971:2020, CLSI EP25) e de referências bibliográficas reutilizáveis entre projetos.
6. Importo uma lista de insumos de uma planilha exportada do ERP enquanto a integração com o Sankhya não existe.

Regras: código de insumo é único; o código de um lote não muda depois de usado em documento assinado; cadastro usado em documento assinado só é corrigido por nova versão com motivo, e o documento antigo continua mostrando o valor assinado; buscas rápidas por código e descrição; amostras não guardam dados pessoais de pacientes.

Fora do escopo: integração automática com o Sankhya (feature 012).
```

Pontos que o `/speckit-clarify` deve fechar:

- Padrão de código dos lotes piloto e de validação.
- Quem pode cadastrar e corrigir insumos.
- Que atributos clínicos das amostras precisam ser guardados (LGPD).
- Se certificados vencidos bloqueiam o uso do insumo.

```text
/speckit-plan App "cadastros" com Lote, Insumo, KitReferencia, Amostra, Painel, Norma e Referencia. Amostras identificadas só por código interno, sem dados pessoais. Anexos em armazenamento de arquivos com hash SHA-256 conferido na leitura. Importação CSV/XLSX com pré-visualização, validação linha a linha e relatório de rejeições. Autocomplete com HTMX. Histórico por entidade e bloqueio de alteração in-place quando o registro está referenciado em versão assinada (correção cria nova versão).
```

Checklists sugeridos: integridade de dados e LGPD.

Pronto quando:

- [ ] Corrigir um lote já assinado cria nova versão e o documento assinado continua com o valor original.
- [ ] A importação de 500 insumos gera relatório das linhas rejeitadas.
- [ ] Nenhum campo de amostra aceita nome de paciente.

## Feature 004 — Modelos de formulário versionados e subdocumentos

As abas da planilha de capas viram modelos configuráveis, e o analista passa a preencher os nove subdocumentos com dados estruturados; uma nova versão do formulário não exige programação.

```text
/speckit-specify Modelos de formulário versionados e preenchimento dos subdocumentos do projeto. Leia docs/contexto/02-dicionario-documentos.md (todos os subdocumentos), 03-padroes-formatacao.md e 05-vocabularios.md.

Problema: os formulários do PSG 20 mudam de versão ("Formulário Versão: 05") e cada aba da planilha Capas Projeto tem tópicos próprios. O sistema precisa refletir isso sem programação a cada mudança.

Histórias:
1. Como Garantia da Qualidade, cadastro um modelo de formulário: tipo de subdocumento, versão do formulário, referência (ex.: "PSG 20 - Pesquisa e Desenvolvimento de Produtos"), vigência, título da capa, tópicos numerados da lista "ESTE RELATÓRIO DEVE CONTER" e, para cada tópico, os campos: texto formatado, lista, tabela com colunas definidas, seleção de vocabulário, referência a cadastro, anexo e "não aplicável" com justificativa.
2. Publico uma nova versão do modelo; documentos já iniciados continuam no modelo em que começaram, a menos que o gestor migre o documento.
3. Como analista, crio num projeto aberto os subdocumentos: Entrada de Projeto, Elaboração de Formulação, Elaboração de Lote Piloto, RAPD, Análise Crítica, Validação do Produto, Verificação Final de Validação, Saída de Projeto e, quando necessário, Alteração de Projeto.
4. Na Entrada de Projeto preencho os 13 tópicos e a parte estruturada do formulário opcional (amostras, funcionalidade, classificação, automação, usuário, armazenamento, filtros, classificação de uso) e marco "aplica / não se aplica" em cada requisito de desempenho.
5. A Verificação Final de Validação é montada pelo sistema: uma linha por tópico da Entrada, com "Previsto" vindo da Entrada aprovada, "Realizado" preenchido pelo analista e "Disposição" (aprovado, reprovado ou outros, com justificativa).
6. Na Saída de Projeto escolho os setores que recebem a transferência (Produção, Supply Chain, Controle de Qualidade, SAC, Comercial, Marketing, S&OP); os itens marcados "MAPA" só aparecem em projetos com esse órgão.
7. A Alteração de Projeto registra versão alterada e nova versão, justificativa, requisitos de entrada afetados e outros dados; quando aprovada, a versão do projeto sobe e os subdocumentos afetados ficam marcados para revisão.

Regras: "não aplicável" exige justificativa e bloqueia a lista daquele tópico; a numeração de tópicos e tabelas é automática; requisitos marcados "aplica" na Entrada geram pendências na Validação; o sistema avisa quando a ordem do fluxo não foi seguida (ex.: Lote Piloto antes da Formulação aprovada) e só segue com autorização do gestor.

Fora do escopo: assinatura (005), geração de DOCX/PDF (006) e cálculos estatísticos (007).
```

Pontos que o `/speckit-clarify` deve fechar:

- Se a ordem dos subdocumentos é obrigatória ou só recomendada.
- Quem publica modelos (só a Garantia da Qualidade?).
- O que fazer quando a capa e o corpo usam tópicos diferentes, como na Análise Crítica (3 na capa, 4 no projeto).
- O rótulo do tópico 9 da Entrada, que repete o do tópico 6 ("Classificação de Uso"); confirmar se o tópico 9 é a classe de risco da RDC 830/2023.
- A numeração da capa da Saída, que tem dois itens "11".
- Edição simultânea do mesmo documento por dois analistas.

```text
/speckit-plan App "formularios" com ModeloFormulario versionado e imutável após publicação; a definição (tópicos, campos, tipos, regras) fica em JSON validado por um JSON Schema próprio. App "subdocumentos" com Subdocumento e dados em JSONB validados contra a definição do modelo usado. Formulários gerados no servidor a partir da definição, com HTMX para tabelas editáveis e autocomplete de cadastros. Carga inicial dos modelos versão 05 a partir de docs/contexto/02-dicionario-documentos.md, por migração de dados. Testes do JSON Schema e de cada tipo de campo. Controle otimista de concorrência na edição.
```

Checklists sugeridos: regulatório (RDC 665/2022, arts. 44 a 61) e usabilidade dos formulários.

Pronto quando:

- [ ] Os nove tipos de subdocumento da versão 05 estão carregados e preenchíveis.
- [ ] Publicar um modelo versão 06 não altera documentos já iniciados.
- [ ] A Verificação Final nasce da Entrada aprovada.
- [ ] Marcar "não aplicável" num tópico com itens preenchidos é rejeitado.

## Feature 005 — Revisão, versões e assinatura eletrônica

As assinaturas do analista e do Gestor de P&D passam a ser eletrônicas, com valor de registro, e cada versão aprovada fica congelada; acaba a impressão para assinar.

```text
/speckit-specify Ciclo de revisão, versões e assinatura eletrônica dos subdocumentos, do TAP e do Plano de Negócios. Leia docs/contexto/04-requisitos-regulatorios.md.

Objetivo: eliminar a impressão para assinatura. Todo documento tem versão, Analista Responsável (nome/função), Gestor de P&D e data; as assinaturas desses dois papéis passam a ser eletrônicas.

Histórias:
1. Como analista, envio um documento em rascunho para revisão; ele fica bloqueado para edição enquanto estiver em revisão.
2. Como Gestor de P&D, aprovo ou devolvo com comentário obrigatório; os comentários ficam no histórico do documento.
3. Para assinar, informo de novo minha senha de rede e escolho o significado (elaborado, revisado, aprovado); a assinatura guarda nome, função, data e hora do servidor e a identificação exata do conteúdo assinado.
4. Documento assinado pelos dois papéis fica "Aprovado" e imutável. Para corrigir, crio nova versão (02, 03...) com motivo; a anterior fica "Substituída" e continua consultável.
5. Como qualquer pessoa autorizada, verifico se um documento foi alterado depois de assinado.
6. Como Gestor de P&D, delego a aprovação a outra pessoa por um período, com motivo registrado.

Regras: quem elaborou não aprova o mesmo documento; uma assinatura nunca vale para outra versão; três falhas de senha seguidas bloqueiam a assinatura e geram alerta; a Validação do Produto usa o rótulo "Gestor de P&D responsável pela Aprovação", como no formulário atual.

Fora do escopo: certificado ICP-Brasil individual (avaliar depois) e geração do PDF (006), que exibirá as assinaturas.
```

Pontos que o `/speckit-clarify` deve fechar:

- Os significados de assinatura aceitos pela Garantia da Qualidade.
- Se a delegação de aprovação é permitida pelo PSG 20.
- Se a Qualidade também assina algum documento, como a Saída de Projeto.
- Prazo máximo de revisão antes de gerar alerta.

```text
/speckit-plan Máquina de estados por documento (rascunho, em revisão, aprovado, devolvido, substituído) com transições permitidas por perfil e testadas. Na assinatura, reautentique no AD por bind LDAP, sem guardar a senha. Calcule SHA-256 de uma representação canônica do conteúdo (JSON com chaves ordenadas mais os hashes dos anexos) e grave Assinatura com esse hash. Versão aprovada vira registro imutável (sem UPDATE por permissão de banco). A verificação de integridade recalcula o hash e compara. Eventos de assinatura vão para a trilha da feature 001. Limite de tentativas com bloqueio temporário.
```

Checklists sugeridos: integridade de dados e assinatura eletrônica (Lei 14.063/2020, art. 4º).

Pronto quando:

- [ ] Alterar no banco o conteúdo de uma versão aprovada é detectado.
- [ ] O elaborador não consegue aprovar o próprio documento.
- [ ] A versão substituída continua consultável.

## Feature 006 — Geração de documentos no padrão da empresa

Cada subdocumento sai pronto em DOCX e PDF, com a capa da planilha, tópicos e tabelas numerados, paginação e rodapé do formulário; é aqui que o tempo de montagem desaparece.

```text
/speckit-specify Geração dos documentos no padrão visual da empresa a partir dos dados do sistema. Leia docs/contexto/03-padroes-formatacao.md e veja os arquivos de docs/modelos/.

Objetivo: economizar o tempo de montagem e eliminar erros de cópia; o documento sai pronto, com capa, numeração e rodapé corretos.

Histórias:
1. Como analista, gero o documento de qualquer subdocumento em DOCX (editável, para conferência) e em PDF (oficial).
2. A capa reproduz o padrão da planilha Capas Projeto: logotipo, título do subdocumento, nome do produto, versão, lista "ESTE RELATÓRIO DEVE CONTER", bloco de assinaturas e rodapé "Formulário Versão: NN. Referência: <referência>" com os valores do modelo usado.
3. No corpo, os tópicos aparecem como títulos numerados, as tabelas são numeradas em sequência ("Tabela 01 – ...") e repetem o cabeçalho quando quebram de página; as páginas são numeradas "Página N de M".
4. No PDF oficial, as assinaturas eletrônicas aparecem no bloco de assinaturas com nome, função, data e hora e significado; o arquivo é selado digitalmente e o rodapé mostra um código de verificação.
5. Como Garantia da Qualidade, mantenho os modelos de layout (capa, cabeçalho, rodapé, estilos) sem programador, e cada modelo é versionado.
6. Todo documento gerado fica arquivado com versão, data, autor da geração e hash; gerar de novo uma versão aprovada produz o mesmo conteúdo.

Regras: documento de versão não aprovada sai com marca d'água "RASCUNHO – NÃO VÁLIDO"; o PDF oficial é PDF/A; todo dado vem do sistema, nada é digitado no gerador.

Fora do escopo: documento completo do projeto (009) e dossiê (011), que reutilizam este gerador.
```

Pontos que o `/speckit-clarify` deve fechar:

- Se o DOCX também pode ser documento oficial ou só o PDF.
- Logotipo único ou por marca (Bioclin, Quibasa).
- Paginação "Página N" ou "Página N de M".
- Se subdocumentos isolados levam sumário ou só o documento completo.

```text
/speckit-plan Comece por uma prova de layout de 2 dias: reproduza a capa da Entrada de Projeto e uma tabela de 120 linhas com quebra de página em duas abordagens, (a) modelo Word com docxtpl e conversão para PDF/A pelo LibreOffice headless e (b) HTML com CSS paginado no WeasyPrint. Escolha pela fidelidade aos arquivos de docs/modelos e registre a decisão no research.md. Selo do PDF com pyHanko (PAdES) usando certificado da empresa guardado fora do repositório. Geração assíncrona com Celery e status na tela. Testes de regressão visual comparando PDFs gerados com referências aprovadas pela Qualidade.
```

Checklists sugeridos: fidelidade de layout e regulatório (identificação de versão e assinatura).

Pronto quando:

- [ ] A Qualidade não distingue a capa gerada da capa da planilha.
- [ ] Uma tabela longa quebra a página repetindo o cabeçalho.
- [ ] A assinatura do PDF oficial é validada num leitor de PDF.
- [ ] O rascunho sai com marca d'água.

## Feature 007 — Estudos de desempenho e estabilidade com cálculo automático

Os resultados do RAPD e da Validação passam a ser lançados como dados, e o sistema calcula estatísticas e conclusões; cada cálculo é testado contra vetores de referência de resultado conhecido.

```text
/speckit-specify Estudos de desempenho e estabilidade estruturados, com cálculo automático, que alimentam o RAPD, a Validação do Produto e o dossiê. Leia docs/contexto/05-vocabularios.md e 06-casos-de-teste.md.

Problema: hoje os resultados são tabelas digitadas no Word, com médias, desvios e CV% calculados à mão ou em planilhas soltas, sem um vocabulário comum para os tipos de estudo.

Histórias:
1. Como analista, crio um estudo escolhendo o tipo numa lista controlada: comparação de métodos (exatidão), repetibilidade, reprodutibilidade, entre lotes, sensibilidade analítica, linearidade, interferentes, reatividade cruzada, efeito prozona, cut-off, sensibilidade e especificidade clínicas, estabilidade de longa duração, estabilidade após aberto e estabilidade de transporte.
2. Defino o critério de aceitação antes de lançar resultados (ex.: CV% < 15%, R² > 0,95, diferença média de Ct ≤ 2); o critério fica congelado no estudo.
3. Lanço ou importo resultados (planilha ou arquivo do equipamento), ligando cada linha a amostra, lote, kit de referência, dia, corrida e replicata cadastrados.
4. O sistema calcula média, desvio-padrão, CV%, diferença média, regressão linear com equação e R², concordância e sensibilidade/especificidade com IC 95%, e informa se o critério foi atendido.
5. Para estudo não aplicável (ex.: efeito prozona em método não imunológico), registro "não aplicável" com justificativa, que segue para o dossiê.
6. Tabelas e conclusões entram no RAPD ou na Validação sem redigitação, com numeração automática.

Regras: estudo usado em documento assinado não é editado; recalcular gera nova versão; casas decimais e separador seguem o padrão brasileiro e a configuração do estudo; todo cálculo tem teste com vetores de referência de resultado conhecido.

Fora do escopo: protocolos estatísticos além dos listados (avaliar depois).
```

Pontos que o `/speckit-clarify` deve fechar:

- **Arredondamento.** Truncar ou arredondar, e com quantas casas, por tipo de resultado.
- **Intervalo de confiança.** Método do IC 95% para proporções (exato de Clopper-Pearson, Wilson ou outro).
- Os formatos de arquivo dos equipamentos que precisam de importação.
- Quais estudos são obrigatórios por tecnologia (bioquímica, imunologia, biologia molecular).
- Quem fornece e aprova os vetores de referência usados nos testes de cálculo.

```text
/speckit-plan App "estudos" com Estudo, CriterioAceitacao, Medida e ResultadoCalculado. Cálculos num módulo Python puro, sem dependência da camada web, com numpy e scipy; desvio-padrão amostral (n−1); IC 95% de proporções pelo método definido no clarify; regra de arredondamento configurável e registrada junto do resultado. Importação CSV/XLSX com mapeamento de colunas salvo por equipamento. Testes com os vetores de referência de docs/contexto/06-casos-de-teste.md e testes de propriedade (hypothesis). Tabelas renderizadas pelo gerador da feature 006.
```

Checklists sugeridos: estatística (fórmulas, arredondamento) e regulatório (RDC 830/2023, art. 58, itens VI a VIII).

Pronto quando:

- [ ] Os cálculos reproduzem os vetores de referência do kit (CV%, regressão, IC 95%).
- [ ] Estudo "não aplicável" exige justificativa e aparece no dossiê.
- [ ] Recalcular um estudo assinado gera nova versão.

## Feature 008 — Caderno de laboratório eletrônico

Cada pesquisador registra, por projeto, os experimentos e tentativas anteriores aos resultados oficiais, com a mesma rastreabilidade dos documentos; é o histórico que entra no documento completo.

```text
/speckit-specify Caderno de laboratório eletrônico por pesquisador e por projeto, para registrar experimentos e tentativas antes dos resultados oficiais do RAPD. Leia docs/contexto/01-visao-geral.md.

Objetivo: guardar o histórico científico do desenvolvimento (o que foi tentado, o que falhou e por quê) com a mesma rastreabilidade dos documentos oficiais.

Histórias:
1. Como pesquisador, crio uma entrada num projeto com título, data, objetivo, hipótese, materiais (ligando lotes, insumos e amostras cadastrados), procedimento, resultados (texto, tabelas, fotos, arquivos de equipamento) e conclusão.
2. Uso modelos de entrada por tipo de experimento (ex.: teste de formulação, estabilidade preliminar) para não começar do zero.
3. Ao terminar, assino a entrada e ela fica bloqueada. Correções viram adendos datados e assinados, sem apagar o original.
4. Peço a assinatura de uma testemunha quando o experimento for relevante para propriedade intelectual ou para uma decisão do projeto.
5. Ligo entradas a formulações, lotes piloto e estudos; a partir de uma entrada, promovo dados para um estudo oficial (feature 007), mantendo o vínculo.
6. Como gestor, vejo a linha do tempo do caderno de cada projeto, busco por palavra, amostra, lote ou pesquisador e vejo entradas abertas há mais de N dias.

Regras: entradas não assinadas após o prazo configurado geram lembrete; data e hora vêm do servidor; anexos têm hash; o caderno do projeto é visível para a equipe do projeto, o Gestor de P&D e a Qualidade.

Fora do escopo: integração direta com equipamentos; importar arquivos basta nesta fase.
```

Pontos que o `/speckit-clarify` deve fechar:

- Prazo para assinar uma entrada (fim do dia, 24 h, 7 dias).
- Quando a testemunha é obrigatória.
- Tamanho máximo de anexos e tipos de arquivo aceitos.
- Se existem entradas fora de projeto (pesquisa exploratória).

```text
/speckit-plan App "caderno" com Entrada, Adendo, ModeloEntrada, Vinculo e Anexo. Editor de texto rico com sanitização no servidor (lista branca de tags) e colagem de imagens; anexos com hash e limite de tamanho configurável. Assinatura e bloqueio reaproveitando a feature 005. Busca textual com full-text search do PostgreSQL em português. Linha do tempo paginada com HTMX.
```

Checklists sugeridos: integridade de dados (ALCOA+) e usabilidade em bancada.

Pronto quando:

- [ ] Entrada assinada não pode ser editada, só receber adendo.
- [ ] A busca por lote traz todas as entradas que o usam.
- [ ] Dados promovidos para um estudo mantêm o vínculo nos dois sentidos.

## Feature 009 — Documento completo do projeto

Com um clique, o sistema monta o registro histórico do projeto exigido pelo art. 61 da RDC 665/2022: todos os subdocumentos aprovados, o histórico do caderno, o quadro de versões e o resumo da auditoria.

```text
/speckit-specify Documento completo do projeto, que é o registro histórico do projeto exigido pela RDC 665/2022 (art. 61), montado automaticamente. Leia docs/contexto/03-padroes-formatacao.md e 04-requisitos-regulatorios.md.

Objetivo: gerar com um clique o documento consolidado que hoje é montado à mão, incluindo o histórico de experimentos do caderno de laboratório.

Histórias:
1. Como líder ou gestor, gero o documento completo de um projeto com capa geral, sumário automático, TAP e Plano de Negócios, cada subdocumento aprovado na versão vigente (com sua capa), alterações de projeto, verificação final, saída, histórico do caderno e lista de anexos.
2. Escolho se o histórico do caderno entra completo ou resumido (título, data, autor, conclusão e vínculos).
3. O documento traz um quadro de versões (subdocumento, versão, data de aprovação, signatários) e um resumo da trilha de auditoria do projeto.
4. Versões substituídas aparecem só no quadro de versões, não no corpo, a menos que eu peça o histórico completo.
5. Antes de gerar, o sistema mostra o que falta para o documento estar completo (subdocumentos não aprovados, pendências da Verificação Final).

Regras: só versões aprovadas entram no corpo; o documento gerado é arquivado com hash e versão; sumário e numeração de páginas são automáticos; dados financeiros do Plano de Negócios só entram para quem tem permissão.
```

Pontos que o `/speckit-clarify` deve fechar:

- A ordem oficial das partes; no projeto DBS a Alteração aparece logo após a capa da Entrada.
- Se o Plano de Negócios entra no documento completo ou fica num anexo restrito.
- Formato do resumo da auditoria (eventos por tipo ou lista completa).

```text
/speckit-plan Reutilize o gerador da feature 006 como composição de seções. Geração assíncrona com barra de progresso. PDFs de subdocumentos já gerados são reaproveitados quando a versão não mudou (cache por hash). Sumário com a numeração real das páginas, em duas passagens se a abordagem escolhida exigir. Meta: projeto de 300 páginas gerado em menos de 3 minutos no servidor de homologação.
```

Checklists sugeridos: regulatório (registro histórico do projeto) e desempenho.

Pronto quando:

- [ ] O documento completo de um projeto piloto é aprovado pela Qualidade.
- [ ] O sumário bate com as páginas.
- [ ] As pendências aparecem quando o projeto está incompleto.

## Feature 010 — Painel do gestor e notificações

O Gestor de P&D acompanha todos os projetos sem pedir relatórios, e ninguém perde prazo de revisão ou assinatura.

```text
/speckit-specify Painel do Gestor de P&D e notificações. Leia docs/contexto/01-visao-geral.md.

Objetivo: o gestor vê o andamento de todos os projetos sem pedir relatórios, e ninguém perde prazo de revisão ou assinatura.

Histórias:
1. Como Gestor de P&D, vejo a carteira de projetos com etapa atual, percentual de subdocumentos aprovados, marcos planejados × realizados, atraso em dias e líder.
2. Abro um projeto e vejo a linha do tempo: marcos, subdocumentos e versões, assinaturas, alterações e atividade do caderno.
3. Vejo minha fila de pendências: documentos aguardando minha revisão ou assinatura, com o tempo de espera.
4. Como analista ou líder, vejo minhas pendências e recebo e-mail quando um documento é devolvido, aprovado ou fica parado além do prazo configurado.
5. Exporto a carteira em planilha.

Regras: o painel respeita as permissões (quem não vê dados financeiros não vê custo nem retorno); notificações podem ser desligadas por tipo, exceto as de assinatura pendente.
```

Pontos que o `/speckit-clarify` deve fechar:

- Os indicadores que o gestor quer na primeira tela.
- E-mail imediato ou resumo diário.
- Se haverá custo realizado (vindo do Sankhya) para comparar com o custo planejado do Plano de Negócios.

```text
/speckit-plan Consultas agregadas com índices dedicados e cache de 5 minutos. Gráficos simples em SVG gerado no servidor, sem build de front-end. E-mails pelo SMTP interno em tarefa agendada (Celery beat), com resumo diário. Exportação XLSX com openpyxl.
```

Checklists sugeridos: permissões e usabilidade.

Pronto quando:

- [ ] O painel abre em menos de 2 s com 100 projetos.
- [ ] O e-mail de pendência chega no dia seguinte ao vencimento do prazo.

## Feature 011 — Dossiê técnico para a ANVISA

O dossiê é montado a partir dos dados aprovados do projeto, no formato I a XII usado hoje, depois de uma checagem que mostra item a item o que falta para a classe de risco do produto.

| Item do dossiê | Origem no sistema |
| --- | --- |
| I. Descrição do produto (finalidade, analito, usuário, classificações, amostra, população, metodologia, classe, composição, apresentação, equipamentos, software, acessórios, comercialização) | Entrada de Projeto, Formulação e cadastro do produto |
| II. Imagem do produto | Anexo da Saída de Projeto |
| III. Gerenciamento de risco | Matriz de risco anexada à Entrada e à Saída |
| IV. Normas técnicas | Tópico 11 da Entrada e biblioteca de normas |
| V. Certificado de conformidade | Só para instrumentos sob certificação compulsória |
| VI. Estudo de desempenho | Estudos da Feature 007, lotes e kits de referência |
| VII. Estudo de estabilidade | Estudos de estabilidade e condições de armazenamento |
| VIII. Desempenho clínico | Estudos clínicos (exigidos nas classes III e IV) |
| IX. Rotulagem e instrução de uso | Anexos do tópico 11 da Saída de Projeto |
| X. Unidade fabril | Cadastro da empresa |
| XI. Processo de fabricação | Biblioteca de textos padrão e Lote Piloto |
| XII. Referências bibliográficas | Biblioteca de referências do projeto |

```text
/speckit-specify Geração do dossiê técnico para notificação ou registro na ANVISA, quando todos os dados necessários estiverem presentes. Leia docs/contexto/03-padroes-formatacao.md (seção Dossiê) e 04-requisitos-regulatorios.md.

Objetivo: montar o dossiê a partir dos dados aprovados do projeto, no formato atual da empresa (itens I a XII), sem copiar e colar, mostrando antes o que falta.

Histórias:
1. Como Assuntos Regulatórios, abro o dossiê de um projeto e vejo a checagem de completude: cada item exigido pelo art. 58 e pelo Anexo II da RDC 830/2023 para a classe de risco do produto, com a origem do dado e o status (completo, faltando, não aplicável com justificativa).
2. Gero o dossiê em DOCX e PDF com cabeçalho "Dossiê Técnico <produto>", rodapé com a razão social e numeração de páginas, itens em algarismos romanos, subitens em letras e números e tabelas numeradas.
3. Textos que não vêm de dados (ex.: processo de fabricação, unidade fabril) saem de uma biblioteca de textos padrão aprovados e versionados.
4. O dossiê termina com a declaração de responsabilidade do responsável técnico e legal (nome, registro no conselho, cidade e data) para assinatura.
5. Gero aditamentos: o sistema compara com a última versão enviada e destaca o que mudou.
6. Registro o envio (número do processo ou expediente, data) e o resultado da petição.

Regras: só entram dados de versões aprovadas; produto de classe I gera o dossiê para arquivo, sem envio; itens "não aplicável" saem com a justificativa registrada na Entrada ou no estudo; uma família de produtos gera um dossiê com todos os kits da família.
```

Pontos que o `/speckit-clarify` deve fechar:

- A estrutura final, conferida contra o Manual para Regularização de Dispositivos para Diagnóstico in Vitro (ANVISA, 25/08/2026).
- Anexos (rótulos, instrução de uso, gerenciamento de risco) incorporados ou enviados como PDFs separados.
- Como o responsável técnico e legal assina: certificado ICP-Brasil ou assinatura da plataforma de peticionamento.
- Regras de agrupamento em família.

```text
/speckit-plan App "dossie" com DefinicaoDossie (itens, aplicabilidade por classe e mapeamento item → fonte de dados), BibliotecaTexto versionada e Submissao. O mapeamento fica em arquivo declarativo (YAML) para a Qualidade ajustar sem programar. Reutilize o gerador da feature 006. Comparação entre versões por item (diff de texto e de tabelas) para aditamentos. Testes que geram o dossiê dos dois produtos de docs/modelos a partir de dados de exemplo e comparam a árvore de títulos com a dos originais.
```

Checklists sugeridos: regulatório (RDC 830/2023, art. 58 e Anexo II).

Pronto quando:

- [ ] Assuntos Regulatórios confere o dossiê de um produto real sem retrabalho de estrutura.
- [ ] A checagem de completude impede o PDF final com item obrigatório faltando.
- [ ] O aditamento destaca o que mudou.

## Feature 012 — Integração com o Sankhya

Os dados dos subdocumentos aprovados passam a ser gravados no Sankhya pelo API Gateway oficial, e os códigos de produtos e insumos passam a vir do cadastro do ERP; acesso direto ao banco do ERP não é aceito pela Sankhya.

O que já se sabe da API:

- Autenticação OAuth 2.0 client credentials: `POST https://api.sankhya.com.br/authenticate` com `client_id`, `client_secret`, `grant_type=client_credentials` e o header `X-Token`, obtido na tela "Configurações Gateway" do Sankhya Om.
- Chamadas no padrão `https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=<serviço>&outputType=json`, com o token no header `Authorization`.
- `CRUDServiceProvider.loadRecords` lê registros; `CRUDServiceProvider.saveRecord` insere ou atualiza conforme a chave primária.
- O dicionário de dados marca tabelas e campos criados pela empresa como "adicionais"; é nelas que os registros do P&D devem ficar.

```text
/speckit-specify Integração com o ERP Sankhya para que os dados dos subdocumentos aprovados fiquem armazenados e utilizáveis no ERP, e para que códigos de produtos e insumos venham do cadastro oficial. Leia docs/contexto/07-integracao-sankhya.md.

Histórias:
1. Como analista, ao cadastrar insumos e lotes, busco o código no cadastro de produtos do Sankhya e o sistema traz descrição e unidade, evitando código digitado errado.
2. Quando um subdocumento é aprovado, seus dados estruturados vão para o Sankhya, nas tabelas adicionais definidas com a TI: projeto, subdocumento, versão, data, signatários, campos principais e identificação do PDF oficial.
3. Na Saída de Projeto aprovada, novas matérias-primas e materiais de embalagem viram solicitações de cadastro no Sankhya, com dados e certificados.
4. Como TI, acompanho a fila de integração (enviado, erro, reenviado) e reprocesso falhas sem duplicar registros.
5. Enquanto a API não estiver liberada, exporto os mesmos dados em CSV, XLSX ou JSON no layout combinado.

Regras: integração só pelo API Gateway oficial; credenciais fora do código; cada envio é idempotente e registrado na trilha de auditoria; falha de integração nunca bloqueia o trabalho no sistema.
```

Pontos que o `/speckit-clarify` deve fechar:

- Quais tabelas adicionais e campos a consultoria vai criar no Sankhya.
- Envio imediato na aprovação ou lote noturno.
- Se a nova matéria-prima é cadastrada direto ou entra como solicitação para o cadastro.
- Qual usuário do Sankhya representa o sistema, já que as permissões dele limitam a integração.

```text
/speckit-plan App "integracoes" com cliente HTTP isolado: OAuth 2.0 client credentials em https://api.sankhya.com.br/authenticate (client_id, client_secret e header X-Token) e renovação automática do token. Chamadas ao gateway https://api.sankhya.com.br/gateway/v1/mge/service.sbr com CRUDServiceProvider.loadRecords para consultas e CRUDServiceProvider.saveRecord para gravação. Padrão outbox: MensagemIntegracao gravada na mesma transação da aprovação e enviada por tarefa Celery com retentativas exponenciais e chave de idempotência. Homologação no ambiente de testes da Sankhya antes da produção. Testes com servidor HTTP simulado.
```

Checklists sugeridos: segurança de credenciais e integridade (idempotência).

Pronto quando:

- [ ] A busca de insumo pelo código traz os dados do Sankhya em homologação.
- [ ] Uma aprovação gera um único registro no Sankhya, mesmo com reenvio.
- [ ] A exportação em arquivo funciona como contingência.

## Validação do sistema computadorizado e implantação

Como o sistema guarda registros de controle de projeto, ele precisa ser validado antes do uso oficial (RDC 665/2022, arts. 104 a 106); os artefatos do spec-kit já entregam boa parte da evidência.

| Entregável de validação | De onde sai |
| --- | --- |
| Plano de validação (escopo, abordagem por risco, responsáveis) | Escrito pela Garantia da Qualidade na Fase 0 |
| Especificação de requisitos do usuário | Os `spec.md` de cada feature: requisitos numerados e critérios de aceitação |
| Especificação funcional e de projeto | Os `plan.md`, o modelo de dados e os contratos |
| Análise de risco do sistema | Checklists do spec-kit mais a classificação de risco de cada requisito |
| Matriz de rastreabilidade requisito → teste | Gerada por script a partir dos IDs de requisito dos specs e dos nomes dos testes |
| Qualificação de instalação (IQ) | Roteiro de implantação executado no servidor, com evidências |
| Qualificação de operação (OQ) | Testes automatizados mais roteiros manuais dos fluxos críticos (assinatura, auditoria, geração) |
| Qualificação de desempenho (PQ) | Piloto com projeto real em paralelo e comparação dos documentos gerados com os manuais |
| Relatório de validação e liberação | Garantia da Qualidade |
| Controle de mudanças | Cada nova feature ou correção passa pelo ciclo do spec-kit e por avaliação de impacto na validação (art. 106) |

O [Guia para Validação de Sistemas Computadorizados](https://gmp-compliance.org/gmp-news/new-brazilian-anvisa-guide-for-the-validation-of-computerised-systems) da ANVISA, baseado no GAMP 5, serve de referência de método.

Implantação, depois do Marco 4:

1. Ambiente de homologação espelhando a produção, só com dados fictícios.
2. Treinamento por perfil: analistas, líderes, gestor e Qualidade.
3. Piloto em paralelo: um projeto real nos dois processos durante um ciclo completo de subdocumentos.
4. Ajustes do piloto entram como novas especificações, nunca como edição direta no código.
5. Atualização do PSG 20 e criação do POP do sistema: perfis, assinatura eletrônica, backup e contingência.
6. Entrada em produção: projetos novos só no sistema; planilhas e Word saem de uso.
7. Operação: backup diário com teste de restauração mensal (art. 35), revisão trimestral de acessos e revalidação periódica (art. 105).

## Cronograma, riscos e próximos passos

Com um desenvolvedor dedicado e revisão semanal do Gestor de P&D, o MVP documental fica pronto em cerca de 3 meses e a liberação para uso oficial em 6 a 8 meses; os prazos por marco estão no roteiro.

A estimativa supõe de 1 a 2 semanas por feature, incluindo revisão e testes, mais 5 a 6 semanas para piloto e validação formal. Cada `/speckit-clarify` respondido no mesmo dia evita a maior fonte de atraso: decisões de processo pendentes.

| Risco | Efeito | Mitigação |
| --- | --- | --- |
| TI não aprova a stack ou o servidor | Início atrasado | Validar as premissas na semana 1; o `/speckit-plan` aceita .NET como plano B |
| Credenciais e tabelas do Sankhya demoram | Feature 012 bloqueada | Pedir à consultoria já na Fase 0; exportação em arquivo como contingência |
| Escopo cresce a cada pedido de formulário | Atraso geral | Formulários configuráveis e a regra "nada sem requisito"; pedido novo vira nova feature |
| Fidelidade visual (sumário, quebras de tabela) | Retrabalho na 006 | Prova de layout com 2 documentos reais antes de implementar |
| Baixa adesão ao caderno eletrônico | Histórico incompleto | Grupo piloto e entradas rápidas (texto, foto e arquivo do equipamento) |
| Falha sutil em regra regulatória no código gerado | Não conformidade | TDD nas regras, revisão humana de cada mudança, `/speckit-analyze` e `/speckit-converge` |
| Validação deixada para o fim | Liberação atrasada | Garantia da Qualidade na constituição e rastreabilidade gerada desde a 001 |
| Exposição de resultados e custos | Dano comercial | Permissões por projeto e por campo, intranet e trilha de auditoria |
| Dependência de uma só pessoa | Projeto parado | Especificações vivas no repositório e um segundo revisor |

Próximos passos:

- [ ] Validar as premissas com a TI (stack, servidor, AD) e com a Garantia da Qualidade (assinatura, validação).
- [ ] Pedir à consultoria Sankhya: ambiente de testes, client\_id, client\_secret, X-Token e criação das tabelas adicionais.
- [ ] Criar o repositório, instalar o spec-kit e descompactar o kit.
- [ ] Rodar `/speckit-constitution` e a Feature 001.
- [ ] Escolher o projeto piloto para a qualificação de desempenho.

## Fontes

Modelos internos analisados (projeto "Sistema de gestão de projetos P&D"): Capas Projeto.xlsx; V00 - Projeto Bio Gene Extração Magnética DNA\_RNA Total; Projeto\_BioGeneDBS\_SCID\_AME\_V01; Saída Projeto V01; Dossiê Técnico - Bio Gene Extração Magnética DNA\_RNA; Dossiê Técnico - Família Bio Gene DBS SCID-AME PCR (aditamento).

Regulação

- [RDC 830/2023 — texto integral (Normas Brasil)](https://www.normasbrasil.com.br/norma/resolucao-830-2023_452914.html)
- [RDC 665/2022 — versão em inglês (ANVISA)](https://www.gov.br/anvisa/en/regulation-of-companies/arquivos/rdc-665-2022-english-version.pdf/@@display-file/file)
- [Lei 14.063/2020 (Câmara dos Deputados)](https://www2.camara.leg.br/legin/fed/lei/2020/lei-14063-23-setembro-2020-790659-normaatualizada-pl.pdf)
- [Perguntas e Respostas sobre a RDC 830/2023 (ANVISA)](https://www.gov.br/anvisa/pt-br/centraisdeconteudo/publicacoes/produtos-para-a-saude/manuais/perguntas-respostas-rdc-830-de-2023)
- [Manuais da ANVISA para IVD publicados em 2026 (Pure Global)](https://www.pureglobal.com/pt/news/anvisa-ivd-class-i-ii-notification-manuals-2026)
- [Guia de regularização da ANVISA, 2026 (Maven Regulatory Solutions)](https://www.mavenrs.com/blog/anvisa-medical-device-ivd-regularization-notification-guide-2026)
- [Overview of the Brazil IVD Regulatory Landscape (Emergo by UL)](https://emergobyul.com/sites/default/files/2024-12/Overview-Brazil-IVD-Regulatory-Landscape-Whitepaper.pdf)
- [Guia da ANVISA para validação de sistemas computadorizados (GMP-Compliance)](https://gmp-compliance.org/gmp-news/new-brazilian-anvisa-guide-for-the-validation-of-computerised-systems)

Spec-kit

- [Repositório github/spec-kit](https://github.com/github/spec-kit)
- [Installation Guide](https://github.github.com/spec-kit/installation.html)
- [Agentic SDD — referência do fluxo e das skills](https://github.github.com/spec-kit/reference/agentic-sdd.html)
- [Upgrade Guide](https://github.github.com/spec-kit/upgrade.html)
- [specify-cli 1.0.9 (PyPI)](https://pypi.org/project/specify-cli/1.0.9/)
- [Issue #4273 — skills instaladas pelo specify init](https://github.com/github/spec-kit/issues/4273)

Sankhya

- [API de serviços — requisitos do Gateway](https://developer.sankhya.com.br/docs/api-de-servi%C3%A7os)
- [Requisições via Gateway](https://developer.sankhya.com.br/reference/requisi%C3%A7%C3%B5es-via-gateway)
- [Autenticação com OAuth 2.0 (Client Credentials)](https://developer.sankhya.com.br/reference/post_login)
- [Dicionário de Dados](https://developer.sankhya.com.br/docs/dicionário-de-dados)
