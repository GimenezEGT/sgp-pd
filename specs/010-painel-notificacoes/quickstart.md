# Quickstart: Painel do gestor e notificações

```bash
docker compose build web worker && docker compose up -d
docker compose run --rm web sh scripts/verificar.sh
```

No desenvolvimento os e-mails vão para arquivos em `var/emails` (`EMAIL_BACKEND` de arquivo).

1. `gestor.pd` abre o painel: os quatro totais e a carteira (etapa, percentual, marcos, atraso,
   líder, custo e retorno); exporta a planilha.
2. `ana.analista` abre o painel: vê só os projetos de que participa, sem custo nem retorno; a
   planilha também não traz essas colunas.
3. `gestor.pd` abre a linha do tempo do PD-2026-001: marcos planejados e eventos (subdocumentos,
   assinaturas, caderno) do mais recente para o mais antigo.
4. `ana.analista` envia um subdocumento para revisão; `gestor.pd` devolve com comentário: o e-mail
   imediato chega para a elaboradora com o comentário.
5. `ana.analista` desliga "Documento aprovado" nas preferências; a aprovação seguinte não gera
   e-mail para ela (situação "omitida"), mas gera para o líder.
6. Com um documento em revisão há mais que o prazo, a rotina diária manda o resumo ao gestor
   (assinatura pendente) e à elaboradora (documento parado).
7. "Minhas pendências" de cada pessoa mostra o que está com ela.
