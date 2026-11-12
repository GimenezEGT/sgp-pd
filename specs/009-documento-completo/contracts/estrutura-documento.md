# Contrato: estrutura do documento completo (feature 009)

Ordem das partes (esclarecimento provisório de 2026-11-11). Cada parte começa em página nova e
entra no sumário com a página real; o cabeçalho corrente mostra o título da parte e o rodapé mostra
"Documento completo do projeto <código> – versão <n>", o código de verificação (oficial) e
"Página X de Y" do documento inteiro.

| Nº | Parte | Conteúdo |
| --- | --- | --- |
| 1 | Capa geral | logotipo, "DOCUMENTO COMPLETO DO PROJETO", código e título do projeto, produto, versão do projeto, data e hora da geração, situação (oficial ou rascunho) |
| 2 | Sumário | partes e subdocumentos com a página real |
| 3 | Pendências | só no rascunho: lista do contrato de pendências (research R8) |
| 4 | Termo de Abertura do Projeto | conteúdo congelado na aprovação do projeto, com a capa |
| 5 | Plano de Negócios | idem; campos financeiros só com permissão (research R7) |
| 6 | Subdocumentos | Entrada, Formulação, Lote Piloto, RAPD, Análise Crítica, Validação (cada um na versão aprovada vigente, com a capa; mais de um do mesmo tipo em ordem de sequência) |
| 7 | Alterações de Projeto | versões aprovadas vigentes, em ordem cronológica de aprovação |
| 8 | Verificação Final e Saída | idem |
| 9 | Quadro de versões | documento, versão, data de aprovação, signatários (nome, significado, data e hora), situação (vigente ou substituída) |
| 10 | Resumo da trilha de auditoria | período, eventos por tipo, eventos-chave |
| 11 | Histórico do caderno de laboratório | entradas assinadas, completo ou resumido |
| 12 | Lista de anexos | nome, origem, SHA-256 |

Com histórico completo de versões, cada versão substituída entra logo depois da vigente do mesmo
documento, com a faixa "Versão substituída – aprovada em <data>".

Rascunho: marca d'água do layout ("RASCUNHO – NÃO VÁLIDO") em todas as páginas, sem selo nem código
de verificação. Oficial: PDF/A-2b, selo da empresa e código de verificação no rodapé.
