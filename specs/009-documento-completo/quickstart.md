# Quickstart: Documento completo do projeto

```bash
docker compose build web worker && docker compose up -d
docker compose run --rm web sh scripts/verificar.sh
docker compose run --rm web pytest -m slow tests/fulldoc
```

1. `lider.projeto` abre o documento completo do PD-2026-001: as pendências aparecem (subdocumentos
   sem versão aprovada, itens da Verificação Final).
2. Gera com o caderno resumido: o pedido mostra o progresso; sai um rascunho com marca d'água, a
   lista de pendências depois do sumário e o sumário com as páginas reais.
3. Gera de novo sem mudar nada: o documento é reaproveitado (evento `fulldoc.reused`).
4. `gestor.pd` gera com o caderno completo e o histórico de versões: o Plano de Negócios traz os
   dados financeiros; `ana.analista` (membro sem permissão financeira) consegue baixar o documento
   sem dados financeiros e recebe 403 no que tem.
5. Num projeto completo dos testes, o documento sai oficial com selo e código de verificação; a
   tela de verificação reconhece o código.
6. `leitor.consulta` sem acesso ao projeto: 403 na tela e no download.
