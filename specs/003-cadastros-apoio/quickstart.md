# Quickstart: Cadastros de apoio

Pré-requisito: ambiente das features 001 e 002 no ar e um projeto aberto (quickstart da 002).

1. **Lote (US1)**: como `ana.analista`, Cadastros › Lotes › Novo, no projeto aberto: código
   `LP-001`, Piloto, fabricação e validade. Conferir "Lote LP-001 – Fabricação: MM/AAAA –
   Validade: MM/AAAA".
2. **Versões (US2)**: bloquear o lote pelo comando de teste
   `docker compose exec web python manage.py shell -c "..."` (ou pelos testes automatizados) e
   corrigir a validade: sem motivo é recusado; com motivo nasce a versão 2 e a 1 fica igual.
3. **Insumos e importação (US3)**: baixar `/cadastros/insumos/modelo.csv`, preencher, importar,
   conferir a pré-visualização e o relatório de rejeições; anexar um certificado PDF e baixá-lo.
4. **Amostras (US4)**: tentar `Maria Silva` como identificador e "paciente João, CPF
   123.456.789-00" na caracterização: ambos recusados.
5. **Listas (US5)**: como `qualidade.ar`, Listas controladas › Tipo de amostra: incluir "Swab
   nasal" e desativar "Líquor"; a versão da lista sobe.

```bash
docker compose run --rm web sh scripts/verificar.sh
```
