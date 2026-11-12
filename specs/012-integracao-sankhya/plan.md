# Implementation Plan: Integração com o Sankhya

**Branch**: `012-integracao-sankhya` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-integracao-sankhya/spec.md`

## Summary

Integração só pelo API Gateway oficial da Sankhya: cliente HTTP isolado com OAuth 2.0 client
credentials e renovação automática do token; mensagens de integração (outbox) criadas na mesma
transação das aprovações (projeto, documento, lotes, insumos novos como solicitação de cadastro,
resultados de estudo), enviadas em segundo plano por `CRUDServiceProvider.saveRecord` com chave
de idempotência e novas tentativas em espera crescente; mapeamento configurável das entidades e
campos (mantido pela TI, sem nomes inventados); consulta de produto pelo código no cadastro de
insumos; fila para a TI com reprocessamento; exportação de contingência em CSV, XLSX e JSON.

Abordagem técnica (entrada do `/speckit-plan`): app "integracoes" com cliente HTTP isolado
(OAuth 2.0 client credentials em `https://api.sankhya.com.br/authenticate` com `client_id`,
`client_secret` e header `X-Token`, renovação automática do token); gateway
`https://api.sankhya.com.br/gateway/v1/mge/service.sbr` com `CRUDServiceProvider.loadRecords` e
`CRUDServiceProvider.saveRecord`; padrão outbox com `MensagemIntegracao` gravada na transação da
aprovação e enviada por tarefa Celery com retentativas exponenciais e chave de idempotência;
homologação no ambiente de testes da Sankhya antes da produção; testes com servidor HTTP simulado.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: as anteriores; cliente HTTP da biblioteca padrão (`urllib.request`),
PyYAML (mapeamento), openpyxl (contingência); nenhuma nova

**Storage**: PostgreSQL 17 (mensagens e versões do mapeamento); token no cache do Django

**Testing**: pytest com servidor HTTP simulado em thread; marcador `req("012:…")`

**Target Platform / Project Type**: os mesmos; aplicação web com worker e beat

**Performance Goals**: envio logo depois da aprovação; varredura da fila a cada 5 minutos

**Constraints**: só o API Gateway; credenciais só em variáveis de ambiente; falha de integração
nunca bloqueia o trabalho; reenvio nunca duplica registro

**Scale/Scope**: dezenas de mensagens por dia

## Constitution Check

| Princípio | Como o plano atende | Situação |
| --- | --- | --- |
| I. Rastreabilidade | Mensagem com registro de origem, chave de idempotência, conteúdo e versão do mapeamento | Atende |
| II. Trilha imutável | Envio, falha, reprocessamento, exportação e mapeamento geram eventos | Atende |
| III. Assinatura | Só aprovações assinadas geram mensagens; signatários no registro do documento | Atende |
| IV. Modelos versionados | Mapeamento versionado | Atende |
| V. Fonte única | Registros montados dos dados aprovados; produtos consultados no cadastro oficial do ERP | Atende |
| VI. Cálculo automático | Resultados de estudo como calculados na 007 | Atende |
| VII. Segurança | Credenciais em variáveis de ambiente, nunca no repositório nem na trilha; fila e mapeamento só para o Administrador | Atende |
| VIII. Qualidade verificável | Testes com servidor simulado: token, renovação, idempotência, falha, reprocessamento, exportação | Atende |
| IX. Simplicidade | Biblioteca padrão para HTTP; outbox numa tabela | Atende |

## Project Structure

```text
specs/012-integracao-sankhya/  plan.md, research.md, data-model.md, quickstart.md, contracts/, tasks.md
sgp/integrations/
├── mapeamento_padrao.yaml  # registros e campos lógicos; entidades do Sankhya vazias até a TI preencher
├── mapping.py      # leitura e validação do mapeamento
├── sankhya.py      # cliente do gateway (token, renovação, loadRecords, saveRecord)
├── payloads.py     # corpo das chamadas (provisório até a confirmação da consultoria)
├── records.py      # registros do modelo lógico (projeto, documento, lote, insumo novo, resultado)
├── services.py     # outbox, envio com retentativas, reprocessamento, consulta de produto, exportação
├── signals.py / tasks.py / views.py / urls.py / templates/integrations/
tests/integrations/
```

## Complexity Tracking

Sem violações da constituição a justificar.
