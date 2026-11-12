# Quickstart: Estudos com cálculo automático

```bash
docker compose build web worker && docker compose up -d
docker compose run --rm web sh scripts/verificar.sh
```

1. `ana.analista` cria no PD-2026-001 um estudo de repetibilidade vinculado ao RAPD (tópico
   "Testes e avaliações preliminares"), com critério "CV% < 15".
2. Lança as medidas 2, 4, 4, 4, 5, 5, 7 e 9: média 5,00; DP 2,14; CV 42,76% (meio para o par);
   "critério não atendido". Tentar mudar o critério: recusado.
3. Importa um CSV de linearidade (x;y) com o mapeamento do equipamento "Leitor de teste": a
   pré-visualização mostra linhas recusadas e o motivo; confirmar grava; R² calculado.
4. Marca um estudo de efeito prozona como não aplicável: sem justificativa recusado.
5. Gera o PDF do RAPD (006): o tópico traz as tabelas do estudo numeradas e a conclusão.
6. Envia e aprova o RAPD (005): os estudos vinculados ficam bloqueados; editar é recusado; nova
   versão com motivo copia os dados.
