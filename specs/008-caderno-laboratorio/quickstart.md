# Quickstart: Caderno de laboratório eletrônico

```bash
docker compose build web worker && docker compose up -d
docker compose run --rm web sh scripts/verificar.sh
```

1. `qualidade.ar` cria o modelo de entrada "Teste de formulação" com textos de objetivo e
   procedimento; altera o procedimento (nova versão com motivo).
2. `ana.analista` cria no PD-2026-001 uma entrada a partir do modelo: número e hora do servidor,
   textos do modelo copiados. Grava resultados com tabela e sobrescrito; um `<script>` colado some.
3. Liga dois lotes e uma amostra pelo código (código inexistente recusado) e anexa um CSV de
   repetibilidade e uma foto (PNG); a foto colada no texto aparece no detalhe.
4. Marca como relevante, assina com a senha de rede (senha errada conta tentativa da 005) e tenta
   editar: recusado. Acrescenta um adendo assinado; o original não muda.
5. `ana.analista` tenta testemunhar a própria entrada: recusado; `lider.projeto` testemunha.
6. Liga a entrada à Formulação e promove o CSV para um estudo de repetibilidade em elaboração: as
   linhas entram no estudo e o vínculo aparece na entrada e no estudo.
7. `gestor.pd` busca por "repetibilidade" (sem acento também), pelo código do lote e por entradas
   abertas há mais de 7 dias; `leitor.consulta` sem acesso ao projeto não vê as entradas.
