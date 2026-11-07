# 01 — Visão geral do SGP-P&D

## Objetivo

Transformar o processo atual de projetos de P&D de produtos para diagnóstico in vitro, hoje feito em planilhas e documentos Word avulsos (procedimento PSG 20 - Pesquisa e Desenvolvimento de Produtos), num sistema web na intranet que:

1. recebe e guarda o Termo de Abertura de Projeto (TAP) e o Plano de Negócios;
2. permite ao líder abrir e conduzir o projeto, e ao Gestor de P&D acompanhar o andamento;
3. guarda os subdocumentos do projeto como dados estruturados, versionados e assinados eletronicamente;
4. mantém um caderno de laboratório eletrônico por pesquisador e por projeto;
5. gera os documentos no padrão visual da empresa, o documento completo do projeto (registro histórico) e o dossiê técnico para a ANVISA;
6. envia os dados aprovados ao ERP Sankhya.

## Usuários e perfis

| Perfil | O que faz |
| --- | --- |
| Analista / Pesquisador | Registra experimentos no caderno, preenche e assina como elaborador os subdocumentos |
| Líder de projeto | Abre o projeto (TAP e Plano de Negócios), conduz as etapas e a equipe |
| Gestor de P&D | Aprova a abertura, revisa e assina como aprovador, acompanha a carteira |
| Qualidade / Assuntos Regulatórios | Mantém os modelos de formulário e de layout, revisa, monta o dossiê |
| Leitor | Consulta, sem editar |
| Administrador do sistema | Perfis, parâmetros e integrações |

## Fluxo de um projeto

1. TAP e Plano de Negócios → aprovação do Gestor de P&D → projeto aberto (versão 01).
2. Entrada de Projeto.
3. Elaboração de Formulação.
4. Elaboração de Lote Piloto.
5. Relatório de Avaliação de Produto em Desenvolvimento (RAPD).
6. Análise Crítica.
7. Validação do Produto.
8. Verificação Final de Validação (previsto × realizado × disposição).
9. Saída de Projeto (transferência para Produção, Supply Chain, Controle de Qualidade, SAC, Comercial, Marketing e S&OP).
10. Alteração de Projeto: opcional, em qualquer etapa; gera nova versão do projeto e reabre os subdocumentos afetados.

Em paralelo, o caderno de laboratório registra os experimentos que antecedem os resultados oficiais e alimenta formulação, lote piloto, RAPD e validação.

Saídas finais: documento completo do projeto, dossiê técnico (ANVISA) e registros no Sankhya.

## Requisitos gerais

- Roda na intranet, numa aplicação web acessada pelo navegador.
- Acesso só para usuários autorizados (login de rede) e por projeto.
- Todos os documentos têm versão, Analista Responsável (Nome/Função), Gestor de P&D e data; as duas assinaturas são eletrônicas.
- Todos os documentos têm o rodapé "Formulário Versão: NN. Referência: <referência>", que muda quando o formulário é revisado (hoje: "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos").
- O processo precisa ser rastreável, mais robusto e com mais informação que o atual.

## Siglas

| Sigla | Significado |
| --- | --- |
| TAP | Termo de Abertura de Projeto |
| RAPD | Relatório de Avaliação de Produto em Desenvolvimento |
| PSG 20 | Procedimento do sistema de gestão para Pesquisa e Desenvolvimento de Produtos |
| MP | Matéria-prima |
| IFU / IUSO | Instrução de uso |
| FISPQ | Ficha de Informações de Segurança de Produtos Químicos |
| CQ | Controle de Qualidade |
| SAC | Serviço de Atendimento ao Cliente |
| S&OP | Sales and Operations Planning |
| MAPA | Ministério da Agricultura e Pecuária (produtos de uso veterinário) |
| ANVISA | Agência Nacional de Vigilância Sanitária |
| RT / RL | Responsável técnico / Responsável legal |
| ALCOA+ | Atribuível, Legível, Contemporâneo, Original, Exato, mais Completo, Consistente, Duradouro e Disponível |
