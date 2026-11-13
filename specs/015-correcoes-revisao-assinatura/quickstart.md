# Quickstart: Correções do ciclo de revisão e assinatura

```bash
docker compose run --rm web sh scripts/verificar.sh
```

Na pilha local (https://localhost:8443, usuários de desenvolvimento, senha `Senha#Dev01`):

1. A Entrada do PD-2026-003, enviada pelo `gestor.pd`: entrando como `gestor.pd`, o bloco de
   assinaturas mostra o aviso, o link para Delegações e o formulário "Devolver"; a Fila de revisão
   mostra a Entrada na seção "Elaborados por você".
2. `gestor.pd` devolve com comentário; `ana.analista` reenvia com a senha; `gestor.pd` aprova pela
   Fila de revisão.
3. Em outro documento em revisão, `ana.analista` assina "Revisado": a opção some; um segundo envio do
   formulário é recusado com a mensagem.
4. As telas de envio e aprovação mostram "Em revisão", "Rascunho"… e nunca o código interno.
