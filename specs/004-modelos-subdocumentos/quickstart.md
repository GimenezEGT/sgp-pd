# Quickstart: Modelos de formulário e subdocumentos

Pré-requisito: ambiente das features 001 a 003 no ar, projeto aberto `PD-2026-001` com
`ana.analista` na equipe, lotes e insumos cadastrados.

1. **Modelos (US1, US2)**: como `qualidade.ar`, Modelos › Entrada de Projeto: conferir a capa e os
   13 tópicos numerados da versão 05. Criar a versão 06, mudar o rótulo de um tópico e publicar.
2. **Entrada (US3, US4)**: como `ana.analista`, no projeto, criar a Entrada (deve nascer na versão
   de modelo vigente), preencher amostras, requisitos "aplica / não se aplica" (um "não se aplica"
   sem justificativa é recusado) e salvar. Como `gestor.pd`, aprovar.
3. **Fluxo (FR-016)**: criar o Lote Piloto antes da Formulação aprovada: aviso; `gestor.pd`
   autoriza com motivo e a criação segue.
4. **Verificação Final (US5)**: criar a Validação (pendências dos requisitos "aplica") e a
   Verificação Final (linhas com o "Previsto" da Entrada).
5. **Saída e Alteração (US6, US7)**: Saída sem itens MAPA num projeto ANVISA; Alteração afetando a
   Formulação, aprovada pelo gestor: projeto passa à versão 02 e a Formulação fica marcada para
   revisão.

```bash
docker compose run --rm web sh scripts/verificar.sh
```
