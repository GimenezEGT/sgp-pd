# Quickstart: Versionamento do documento final do projeto

```bash
docker compose run --rm web sh scripts/verificar.sh
```

Na pilha local (https://localhost:8443, senha `Senha#Dev01`):

1. Depois da migração, a tela "Documento completo" do PD-2026-001, 002 e 003 mostra as versões do
   documento final reconstruídas das aprovações registradas (marcadas "Reconstruída").
2. Abra uma nova versão de um subdocumento do PD-2026-003 (como `ana.analista`), envie e aprove como
   `gestor.pd`: o documento final ganha a versão seguinte com "parte: NN → NN" e a composição.
3. Gere o documento completo: capa e nome do arquivo com a versão do documento final; parte
   "Versões do documento final" no PDF.
4. Na tela do subdocumento, o "Histórico de versões" mostra cada versão e as versões do documento
   final em que entrou.
