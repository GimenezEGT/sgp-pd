# Contrato: mudanças de comportamento nas telas da feature 005 (feature 015)

Sem rota nova; as rotas da 005 continuam no contrato de `tests/core/test_route_scan.py`.

| Tela | Mudança |
| --- | --- |
| Bloco de assinaturas (Entrada e demais subdocumentos, TAP, Plano de Negócios) | Documento em revisão elaborado pela própria pessoa com poder de aprovação: aviso "Você assinou esta versão como Elaborado; a aprovação precisa de outro Gestor de P&D ou de quem tem delegação vigente.", link "Delegações de aprovação" (só perfil Gestor de P&D) e formulário "Devolver" com comentário obrigatório (POST na rota de devolução existente). "Assinar como revisor" não aparece para quem já assinou a versão. |
| Envio para revisão | Situação pelo nome; para quem tem poder de aprovação, aviso de que não poderá aprovar a mesma versão (sem bloqueio). |
| Aprovar ou devolver | Situação pelo nome; para quem elaborou: sem o formulário de aprovação, com o aviso e a devolução. |
| Fila de revisão | Nova seção "Elaborados por você — aguardam outro aprovador": documento, projeto, enviado em, dias em revisão, link para o documento. |
| Assinar como revisor (POST) | Segunda tentativa da mesma pessoa na mesma versão: recusada com "Você já assinou como revisor esta versão." |
