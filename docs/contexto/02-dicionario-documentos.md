# 02 — Dicionário de documentos e campos

Fonte: planilha "Capas Projeto.xlsx" (formulário versão 05), projetos "V00 - Projeto Bio Gene Extração Magnética DNA_RNA Total" e "Projeto_BioGeneDBS_SCID_AME_V01", "Saída Projeto V01" e o pedido original do sistema. Os textos entre aspas são os rótulos exatos do formulário atual; os tipos de campo são propostas. Só a estrutura dos modelos foi usada; os dados neles são fictícios.

## Campos comuns a todos os documentos

| Campo | Tipo | Regra |
| --- | --- | --- |
| Nome do produto | referência ao projeto | Exibido em caixa alta na capa |
| Versão do documento | inteiro com 2 dígitos ("01") | Sobe a cada nova versão aprovada |
| "Analista Responsável (Nome/Função):" | assinatura eletrônica | Pessoa, função, data/hora, significado "elaborado" |
| "Gestor de P&D:" | assinatura eletrônica | Na Validação do Produto o rótulo é "Gestor de P&D responsável pela Aprovação:" |
| "Data:" | data | Data da aprovação da versão |
| Rodapé | texto do modelo | "Formulário Versão: {versao_formulario}. Referência: {referencia}" — hoje "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos" |

Tipos de campo usados abaixo: texto formatado, lista, tabela (colunas definidas), seleção (vocabulário de `05-vocabularios.md`), referência (cadastro de lote, insumo, kit, amostra, norma, referência bibliográfica), anexo, "não aplicável" (com justificativa obrigatória).

## TAP — Termo de Abertura de Projeto

O pedido original não lista os campos do TAP. Proposta a confirmar no `/speckit-clarify`:

| Campo | Tipo |
| --- | --- |
| Código do projeto | gerado na aprovação |
| Produto: nome, família, tecnologia, órgão regulador (ANVISA ou MAPA), classe de risco prevista e regra de classificação | texto + seleção |
| Justificativa | texto formatado |
| Objetivo | texto formatado |
| Escopo incluído / excluído | listas |
| Entregas | lista |
| Premissas e restrições | listas |
| Riscos iniciais | tabela (risco, impacto, resposta) |
| Partes interessadas | tabela (nome/área, interesse) |
| Equipe | tabela (pessoa, papel no projeto) |
| Marcos planejados | tabela (subdocumento, data prevista, data realizada) |

## Plano de Negócios

Campos do pedido original:

| Campo | Tipo |
| --- | --- |
| Nome do projeto | texto |
| Data | data |
| Líder do projeto | pessoa |
| Objetivo | texto formatado |
| Descrição geral | texto formatado |
| Custo total do projeto | valor em R$ |
| Prazo de execução | data ou meses |
| Mercado-alvo | texto formatado |
| Retorno esperado (5 anos) | tabela ano 1 a ano 5, em R$, com total calculado |

Campos encontrados no projeto Extração Magnética, que pertencem ao Plano de Negócios:

"Análise de Viabilidade Financeira": 1. Principais concorrentes (lista); 2. Preço dos concorrentes (faixa em R$ por teste); 3. Principais apresentações dos kits dos concorrentes (lista); 4. Custo máximo de produção, considerando matéria-prima (R$); 5. Previsão de preço de venda (faixa em R$); 6. Previsão de venda anual (testes por ano).

"Análise de Viabilidade Produtiva": 1. Avaliação da estrutura fabril para produção do kit; 2. Avaliação da equipe de Produção; 3. Avaliação do Controle de Qualidade (textos).

Regra: dados financeiros visíveis só para Gestor de P&D, líder do projeto e perfis autorizados.

## Entrada de Projeto

Capa: "Entrada de Projeto", produto, "VERSÃO", lista "ESTE RELATÓRIO DEVE CONTER:" em duas colunas.

| Nº | Tópico | Tipo sugerido | Observações |
| --- | --- | --- | --- |
| 1 | "Amostras" | seleção múltipla de tipos de amostra + texto + tabela de coleta, armazenamento e transporte por tipo | No dossiê vira o item "Tipo de Amostra" |
| 2 | "Funcionalidade" | seleção (triagem, monitoramento, diagnóstico, auxílio diagnóstico) + texto | |
| 3 | "Apresentações" | tabela reagente × apresentação (volumes ou unidades) | Corpo usa "Apresentações e Composições" |
| 4 | "Armazenamento" | seleção de faixa por reagente + texto | Inclui condição após aberto |
| 5 | "Automação" | seleção (manual, automático, semiautomático, outros) + texto | |
| 6 | "Classificação de uso" | seleção (único, múltiplo) + texto | |
| 7 | "Tipo de usuário" | seleção (profissional, leigo) + local de uso | |
| 8 | "Filtros primário e secundário (se aplicável)" | seleção de comprimento de onda (280 a 800 nm) ou tabela alvo × detector × quencher (biologia molecular) | "Não aplicável" permitido |
| 9 | "Classificação de Uso" | seleção de classe de risco (I a IV) + regra de classificação da RDC 830/2023 (a confirmar) | O rótulo repete o do tópico 6; confirmar se o tópico 9 é a classe de risco e ajustar o rótulo |
| 10 | "Requisitos de desempenho" | tabela requisito × critério de aceitação + "aplica / não se aplica" dos 16 requisitos do formulário opcional | Gera pendências na Validação |
| 11 | "Requisitos regulatórios" | referência múltipla à biblioteca de normas (internacionais e nacionais) | No dossiê vira "Normas Técnicas" |
| 12 | "Gerenciamento de risco" | anexo (matriz de risco, NBR ISO 14971) + texto | |
| 13 | "Outros dados pertinentes" | texto formatado (metodologia, equipamentos, comercialização, fabricante, população alvo) | |

Formulário opcional de entrada (aba "ENTRADA (FORM.OPCIONAL)"): cabeçalho com "Nome do Projeto", "Versão", "Data" e "Analito", e as seleções listadas em `05-vocabularios.md`. Nota fixa do formulário: "Outras características do produto poderão ser avaliadas e discutidas durante o desenvolvimento do projeto seguindo os requisitos da RDC 665/2022 e RDC 830/2023 da ANVISA, ISO 13485/2016".

## Elaboração de Formulação

| Nº | Tópico | Tipo sugerido |
| --- | --- | --- |
| 1 | "Nome do Produto" | referência ao projeto |
| 2 | "Nome e número do(s) Reagente(s)" | tabela (número R1…Rn, nome, composição resumida) |
| 3 | "Lista de matérias-primas utilizadas, conforme cadastro" | tabela por reagente com referência a insumos (o pedido original chama de "lista de materiais de preparo") |
| 4 | "Modo detalhado de preparo do(s) Reagente(s)" | por reagente: tabela de componentes (componente, peso molecular, mg/L, g/L, mM, código), passos numerados, densidade, armazenamento e validade |
| 5 | "Informações complementares, quando aplicável" | texto ou "não aplicável" |

## Elaboração de Lote Piloto

| Nº | Tópico | Tipo sugerido |
| --- | --- | --- |
| 1 | "Nome do Produto e Lote de Produção" | referência a lotes (código, fabricação, validade) |
| 2 | "Nome e número do(s) Reagente(s)" | herdado da Formulação aprovada |
| 3 | "Lista de matérias-primas utilizadas, com código, lote e fabricante" | tabela com referência a insumos (código, descrição, lote, fabricante) |
| 4 | "Modo detalhado de preparo do(s) Reagente(s)" | herdado da Formulação, editável com registro do que mudou |
| 5 | "Responsável pela Produção do lote piloto e local de fabricação" | pessoa + local |
| 6 | "Informações complementares, quando aplicável" | texto; o projeto DBS inclui envase e tabela de materiais de embalagem (reagente, volume por apresentação, frasco, tampa, colmeia, caixa, rótulo) |

## RAPD — Relatório de Avaliação de Produto em Desenvolvimento

| Nº | Tópico | Tipo sugerido |
| --- | --- | --- |
| 1 | "Formulações propostas" | referência à Formulação + texto |
| 2 | "Testes e avaliações preliminares" | estudos (feature 007): painel utilizado, origem e qualificação das amostras, tipos de amostra, armazenamento, equipamentos, critérios, resultados, conclusão |
| 3 | "Referências bibliográficas consultadas (quando aplicável)" | referência à biblioteca |
| 4 | "Análise de Exatidão / Inexatidão (Comparativo de métodos)" | estudo do tipo comparação de métodos, com kits de referência |

## Análise Crítica

| Nº | Tópico (capa, versão 05) | Tipo sugerido |
| --- | --- | --- |
| 1 | "Análise sistemática da evolução do projeto (Cumprimento das atividades delineadas no planejamento)" | texto + comparação automática marcos planejados × realizados |
| 2 | "Comparação dos resultados iniciais com os dados de entrada" | tabela gerada (requisito da Entrada × resultado) + texto |
| 3 | "Dados complementares, quando aplicável" | texto |

O projeto Extração Magnética usou 4 tópicos: "Análise sistemática da evolução do projeto", "Adequação das saídas do projeto às entradas determinadas", "Avaliação das técnicas estatísticas utilizadas, comparação com dados de entrada, critérios de aceitação utilizados" e "Dados complementares". Decidir no `/speckit-clarify` qual lista vale.

## Validação do Produto

| Nº | Tópico | Tipo sugerido |
| --- | --- | --- |
| 1 | "Dados de desenvolvimento incluindo estudo de precisão, linearidade, sensibilidade analítica, sensibilidade e especificidade clínica, interferentes, reatividade cruzada, efeito pró-zona (quando aplicável)" | estudos (feature 007), um por requisito marcado "aplica" na Entrada |
| 2 | "Lotes utilizados no processo de validação" | referência a lotes |
| 3 | "Dados de Estabilidade Acelerada e Após Aberto" | estudos de estabilidade (longa duração, após aberto/on board, transporte) |
| 4 | "Estudo do custo do produto final" | tabela de custo (insumos, embalagem, mão de obra) com total |
| 5 | "Outras informações pertinentes" | texto; inclui validação externa (laboratório parceiro, equipamento, kit referência, metodologia, resultados, conclusão do cliente, observações) |

## Verificação Final de Validação

Tabela "CHECK LIST" com colunas "REQUISITOS DE ENTRADA", "PREVISTO", "REALIZADO" e "DISPOSIÇÃO (APROVADO, REPROVADO OU OUTROS)". Linhas da capa: 1 Amostras; 2 Funcionalidade; 3 Apresentações; 4 Armazenamento; 5 Automação; 6 Classificação de uso; 7 Tipo de usuário; 8 Filtros primário e secundário (se aplicável); 9 Classificação de Uso; 10 Requisitos de desempenho; 11 Outros dados pertinentes.

Regras: "Previsto" vem da Entrada aprovada; "Realizado" é preenchido (pré-preenchido quando o dado existe na Validação ou na Saída); "Disposição" diferente de Aprovado exige justificativa.

## Saída de Projeto

| Nº | Tópico | Tipo sugerido |
| --- | --- | --- |
| 1 | "Lotes utilizados no processo de validação" | referência a lotes |
| 2 | "Prazos de validade do produto" | prazo + condição de armazenamento |
| 3 | "Cadastro de nova(s) matéria(s)-prima(s), quando aplicável (anexar certificado)" | lista de insumos novos com certificado, ou "não aplicável" |
| 4 | "Cadastro de novo(s) material(is) de embalagem(ns), quando aplicável (especificar)" | lista de insumos de embalagem, ou "não aplicável" |
| 5 | "Matriz de Gerenciamento de Risco" | anexo |
| 6 | "Solicitação de lote(s) piloto(s) para Produção, quando aplicável (MAPA)" | só em projetos MAPA |
| 7 | "Teste(s) preliminar(es) do(s) lote(s) piloto(s) pelo Controle de Qualidade, quando aplicável (MAPA)" | só em projetos MAPA |
| 8 | "Dados de envio de lote(s) piloto(s) para clientes ou assessores externos, se aplicável" | tabela (destino, lote, data, retorno) |
| 9 | "Prazo de Transferência (Imediata ou não)" | seleção + texto (ex.: "após registro") |
| 10 | "Formulário de Validação de Produto em anexo" | referência ao documento de Validação |
| 11 | "Instrução de Uso, FISPQ, Dossiê Técnico, modelo de rótulos e Bula Prática (quando aplicável)" | anexos |
| 12 | "Setores que receberão a Transferência:" | seleção múltipla: Produção I, Supply Chain, Controle de Qualidade, SAC, Comercial, Marketing, S&OP |

A capa atual numera os dois últimos itens como "11"; a numeração automática corrige. Itens extras observados: "12. Imagem do produto" (projeto Extração Magnética) e "Aditamento feito ao peticionamento na ANVISA" (projeto DBS).

## Alteração de Projeto (opcional)

Capa: "Versão alterada:" e "Nova Versão:" no lugar de "VERSÃO".

| Nº | Tópico | Tipo sugerido |
| --- | --- | --- |
| 1 | "Justificativa de alteração" | texto formatado (lista de alterações) |
| 2 | "Requisitos de entrada (quando aplicável)" | seleção dos tópicos da Entrada afetados + novo conteúdo |
| 3 | "Outros dados pertinentes" | texto |

Regras: exige análise de risco (RDC 665/2022, art. 60); na aprovação, a versão do projeto sobe e os subdocumentos afetados ficam marcados para revisão.

## Caderno de laboratório (novo)

Entrada: título, data, pesquisador, projeto, objetivo, hipótese, materiais (referências a lotes, insumos e amostras), procedimento, resultados (texto, tabelas, imagens, arquivos de equipamento), conclusão, vínculos (formulação, lote, estudo), assinatura do autor e, quando exigida, da testemunha. Correções só por adendo assinado.
