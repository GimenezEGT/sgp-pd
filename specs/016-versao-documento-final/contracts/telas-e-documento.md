# Contrato: telas e documento (feature 016)

Sem rota nova.

| Onde | O que aparece |
| --- | --- |
| Documento completo do projeto (tela da 009) | Seção "Versões do documento final": número, data e hora, aprovado por, o que mudou ("Formulação: 01 → 02"), motivo (Aprovação, Recomposição, Reconstruída) e a composição de cada versão (parte, versão, aprovada em, resumo); na tabela de documentos gerados, a coluna "Versão do documento final" |
| PDF do documento completo | Capa com "VERSÃO DO DOCUMENTO FINAL NN" e "VERSÃO DO PROJETO NN"; nome do arquivo "Documento completo <código> vNN.pdf", com NN = versão do documento final (antes da 016, a do projeto); parte "Versões do documento final" depois do "Quadro de versões" |
| Tela do subdocumento, TAP e Plano de Negócios | "Histórico de versões": versão, situação, aberta por/em e motivo, aprovada por/em, versões do documento final em que entrou |
| Verificação pública do código (tela da 006) | Versão "NN do documento final (projeto NN)" para documento gerado a partir da 016 |
| Trilha | `fulldoc.version_created` a cada nova versão |
