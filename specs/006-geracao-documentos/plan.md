# Implementation Plan: Geração de documentos no padrão da empresa

**Branch**: `006-geracao-documentos` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-geracao-documentos/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Cada subdocumento, o TAP e o Plano de Negócios saem em PDF (oficial, quando aprovados) e em DOCX
(conferência) no padrão da planilha Capas Projeto: capa com faixa do logotipo, tópicos e tabelas
numerados, "Página N de M", rodapé do formulário, marca d'água nas versões não aprovadas e, no PDF
oficial, assinaturas, selo PAdES e código de verificação. A Qualidade mantém modelos de layout
versionados; cada versão de documento guarda o layout em que começou; o conteúdo exibido é congelado
na aprovação para que gerar de novo produza o mesmo conteúdo.

Abordagem técnica (entrada do `/speckit-plan`): começou pela prova de layout de duas abordagens
(pasta `prova-layout/`): (a) modelo Word com docxtpl e PDF/A pelo LibreOffice headless e (b) HTML
com CSS paginado no WeasyPrint. A fidelidade à planilha empatou; escolhida a (b) para o PDF, pelo
determinismo, PDF/A-2b validado no veraPDF antes e depois do selo, velocidade e imagem menor, com
o DOCX montado por python-docx do mesmo conteúdo (research R1). Selo com pyHanko (PAdES) e
certificado da empresa fora do repositório; geração assíncrona com Celery e situação na tela por
HTMX; testes de regressão visual contra referências aprovadas pela Qualidade.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as das features anteriores, mais WeasyPrint (PDF/A-2b), pyHanko (selo
PAdES) e python-docx (DOCX); pypdfium2 e pypdf só nos testes; pacotes Debian de Pango, HarfBuzz,
fontconfig, Carlito e DejaVu na imagem (research R15)

**Storage**: PostgreSQL 17 (modelos de layout, vínculos, conteúdo congelado, pedidos e documentos
gerados); arquivos gerados no armazenamento por conteúdo da 003 (`var/media`)

**Testing**: pytest + pytest-django; Celery síncrono nos testes; certificado de teste temporário;
regressão visual por rasterização (pypdfium2) e comparação com PNGs de referência; marcadores
estruturais de PDF/A; validação veraPDF no quickstart; marcador `req("006:…")`

**Target Platform**: a mesma da 001 (Docker Compose; worker Celery já existente)

**Project Type**: aplicação web monolítica

**Performance Goals**: subdocumento de 30 páginas em PDF em < 30 s (SC-007); a prova fez 4 páginas
em 0,37 s

**Constraints**: PDF oficial só de versão aprovada, PDF/A-2b, selado; nenhum PDF oficial sem selo;
certificado e senha só em variáveis de ambiente; regeneração determinística; a geração não altera o
documento; Plano de Negócios só com permissão financeira

**Scale/Scope**: dezenas de documentos por projeto, poucas gerações por versão; tabelas de centenas
de linhas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Cada geração registra documento, versão, situação, modelos, autor, data e hora do servidor e resumos; nada é apagado | Atende |
| II. Trilha imutável | Pedido, geração, falha, divergência de regeneração, congelamento, download, consulta de código e mudanças de layout geram eventos | Atende |
| III. Assinatura | O PDF oficial mostra as assinaturas da 005 da versão aprovada e é selado; nenhuma assinatura nova é criada pelo gerador | Atende |
| IV. Modelos versionados | Layout (capa, cabeçalho, rodapé, estilos, variantes de capa) é dado versionado; cada versão de documento guarda o layout em que começou; o rodapé do formulário vem do modelo de formulário | Atende |
| V. Fonte única | Todo valor vem do documento e dos cadastros; o aprovado é congelado como exibido | Atende |
| VI. Cálculo e numeração automáticos | Numeração de tópicos, tabelas e páginas e totais calculados; nada digitado no gerador | Atende |
| VII. Segurança | Geração e download só para quem vê o documento (financeiro no Plano); certificado fora do repositório; consulta de código sem expor projeto a quem não tem acesso | Atende |
| VIII. Qualidade verificável | TDD nas permissões, no determinismo, no selo e na adulteração, na marca d'água e na regressão visual | Atende |
| IX. Simplicidade | Um gerador (HTML → PDF) e um montador DOCX sobre o mesmo conteúdo; sem LibreOffice; três dependências de runtime | Atende |

Reavaliado depois da Fase 1: sem mudanças.

## Project Structure

### Documentation (this feature)

```text
specs/006-geracao-documentos/
├── plan.md, research.md, data-model.md, quickstart.md
├── prova-layout/            # prova das duas abordagens (scripts e resultados)
├── contracts/rotas-ui.md, eventos-auditoria.md, modelo-layout.md, conteudo-renderizacao.md
└── tasks.md
```

### Source Code (repository root)

```text
sgp/documents/
├── models.py          # LayoutTemplate, LayoutBinding, FrozenRendering, GenerationRequest, GeneratedDocument
├── layout_schema.py   # JSON Schema e validação da definição do layout
├── layouts.py         # vigente, rascunho, edição, publicação, vínculo da versão do documento
├── content.py         # conteúdo de renderização (subdocumento, TAP, Plano) e congelamento
├── render_pdf.py      # HTML + CSS → PDF/A-2b (WeasyPrint), determinístico
├── render_docx.py     # DOCX de conferência (python-docx), normalizado
├── seal.py            # selo PAdES (pyHanko) e leitura do certificado
├── services.py        # pedir, gerar, arquivar, código de verificação, permissões
├── tasks.py           # tarefa Celery documents.generate
├── views.py / forms.py / urls.py / event_types.py
├── management/commands/selo_teste.py
├── static/documents/logo-bioclin-quibasa.png
└── templates/documents/ (telas, pdf/*.html, pdf/*.css)
sgp/files/storage.py           # tipo docx e store_bytes
sgp/subdocuments/, sgp/signatures/, sgp/projects/   # vínculo de layout e congelamento na aprovação
tests/documents/ (+ referencias/*.png)
scripts/atualizar_referencias_visuais.sh
```

**Structure Decision**: app `documents` com o gerador e os modelos de layout; as apps existentes só
chamam o vínculo de layout e o congelamento.

## Complexity Tracking

Sem violações da constituição a justificar.
