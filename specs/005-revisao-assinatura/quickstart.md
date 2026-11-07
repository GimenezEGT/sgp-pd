# Quickstart: Revisão, versões e assinatura

Pré-requisito: ambiente das features 001 a 004, projeto aberto com Entrada e Formulação.

1. **Envio (US1, US3)**: como `ana.analista`, enviar a Formulação completa para revisão com a
   senha de rede (`Senha#Dev01`); conferir "Em revisão" e a assinatura "Elaborado"; a edição é
   recusada.
2. **Devolução e aprovação (US2)**: como `gestor.pd`, devolver sem comentário (recusado) e com
   comentário; `ana.analista` corrige e reenvia (assina de novo); `gestor.pd` aprova com a senha.
3. **Falhas (FR-008)**: errar a senha três vezes: assinatura bloqueada e alerta na trilha.
4. **Nova versão (US4)**: criar a versão 02 com motivo, aprovar e consultar a 01 "Substituída".
5. **Integridade (US5)**: verificar (íntegro); alterar no banco o conteúdo congelado e verificar de
   novo: divergência apontada.
6. **Projeto (FR-012)**: submeter e aprovar um projeto novo com as assinaturas no TAP e no Plano.

```bash
docker compose run --rm web sh scripts/verificar.sh
```
