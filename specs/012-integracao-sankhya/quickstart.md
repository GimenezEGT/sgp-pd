# Quickstart: Integração com o Sankhya

```bash
docker compose build web worker && docker compose up -d
docker compose run --rm web sh scripts/verificar.sh
```

Sem credenciais (desenvolvimento), a integração fica desligada (`SANKHYA_ENABLED=false`).

1. Uma aprovação de subdocumento no desenvolvimento gera a mensagem "documento" na fila, que fica
   "aguardando configuração"; `admin.ti` a vê na fila.
2. `admin.ti` exporta os documentos em CSV (";", vírgula decimal), XLSX e JSON com o envelope do
   contexto.
3. No cadastro de insumos, "Consultar no Sankhya" avisa que o código não foi conferido (integração
   desligada) e o cadastro continua.
4. Nos testes, com o servidor simulado: token, renovação, envio único com reenvio, falha com nova
   tentativa e reprocessamento.
5. Homologação: preencher o mapeamento com a consultoria e as credenciais do ambiente de testes da
   Sankhya; conferir a consulta de um insumo real (SC-002).
