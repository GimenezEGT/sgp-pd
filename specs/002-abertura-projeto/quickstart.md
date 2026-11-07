# Quickstart: Abertura de projeto

Pré-requisito: ambiente da feature 001 no ar (`docker compose up -d`) e perfis concedidos em
Administração › Pessoas e perfis: `lider.projeto` → Líder de projeto; `gestor.pd` → Gestor de
P&D (via grupo); `ana.analista` → Analista (via grupo); `qualidade.ar` → Qualidade (via grupo).

## Cenários

1. **Abrir de ponta a ponta (SC-001)**: como `lider.projeto`, Projetos › Novo projeto; preencher
   produto (ANVISA, classe II → regime Notificação), TAP (escopo, entregas, riscos, partes
   interessadas), incluir `ana.analista` na equipe, dois marcos e o Plano de Negócios com as cinco
   previsões (total calculado). Submeter. Como `gestor.pd`, devolver com comentário; como líder,
   corrigir e submeter; como gestor, aprovar → código `PD-2026-001`, versão 01, situação Aberto.
2. **Equipe ganha acesso**: `ana.analista` não abre o rascunho (403); depois da aprovação, abre.
3. **Dados financeiros (SC-002)**: como `ana.analista` e `qualidade.ar`, o detalhe mostra
   "Restrito" no lugar de custo, retornos e preços; `/projetos/<id>/plano-de-negocios/` dá 403;
   na trilha, os eventos do plano mostram `[restrito]`.
4. **Códigos sem colisão (SC-003)**: coberto pelo teste automatizado de aprovações concorrentes.

## Testes

```bash
docker compose run --rm web sh scripts/verificar.sh
docker compose run --rm web pytest tests/projects -q
```
