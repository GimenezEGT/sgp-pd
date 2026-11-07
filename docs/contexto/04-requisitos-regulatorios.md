# 04 — Requisitos regulatórios ligados a funções do sistema

Verifique sempre o texto vigente das normas; este arquivo resume o que foi conferido em novembro de 2026.

## RDC 665/2022 — Boas Práticas de Fabricação de produtos médicos e IVD

Conferido na versão em inglês publicada pela ANVISA. A versão em inglês fala em "design history record"; em português, registro histórico do projeto.

| Artigo | Exigência | Função no sistema |
| --- | --- | --- |
| 44 | Planejamento descreve as atividades de projeto e os responsáveis por cada uma | TAP com equipe, papéis e marcos |
| 46 | Dados de entrada documentados, avaliados e aprovados por pessoa qualificada designada | Entrada de Projeto assinada antes da Formulação |
| 48 | Verificação de projeto por procedimento e pessoa designada | Lote Piloto e RAPD com estudos e responsáveis |
| 49 | Saídas definidas e documentadas de modo a permitir avaliar a conformidade, com critérios de aceitação | Formulação, critérios de aceitação congelados nos estudos, Verificação Final |
| 50 e 51 | Revisões de projeto planejadas, conduzidas e documentadas; resultados no registro histórico | Análise Crítica obrigatória |
| 52 | Projeto traduzido corretamente em especificações de produção | Saída de Projeto e transferência aos setores |
| 53 a 58 | Validação por procedimento, em condições definidas, com uso real ou simulado; validação de software quando couber (56); estudos de estabilidade (58) | Validação do Produto e estudos de estabilidade |
| 59 | Liberação para produção só após aprovação do pessoal designado | Saída fecha com assinatura do Gestor de P&D |
| 60 | Alterações identificadas, documentadas, validadas, revisadas e aprovadas antes de implementar, com avaliação de risco | Alteração de Projeto com análise de risco e nova versão |
| 61 e 3º, XXV | Registro histórico do projeto para cada produto | Documento completo do projeto |
| 104 a 106 | Software que possa afetar a qualidade do produto ou o sistema da qualidade deve ser validado; verificação periódica e revalidação; mudanças sob controle com avaliação de risco | Validação do próprio SGP-P&D e controle de mudanças |
| 34 e 35 | Registros legíveis e protegidos; cópia de segurança de todos os documentos e registros digitais | Backup diário com teste de restauração |
| 37 | Registros guardados pelo tempo de vida do produto, contado da distribuição, nunca menos de 2 anos | Nada é apagado; retenção configurada por produto |
| 27, 29, 42, 47, 57, 59 (§2), 87, 92, 118 | Aceitam assinatura manuscrita ou digital com data | Assinatura eletrônica com data e hora |

## RDC 830/2023 — classificação, notificação e registro de IVD

| Artigo | Conteúdo | Função no sistema |
| --- | --- | --- |
| 6º | Classes I e II sujeitas a notificação | Regime derivado da classe de risco |
| 7º | Classes III e IV sujeitas a registro | Regime derivado da classe de risco |
| 12 | Registro válido por 10 anos | Alerta de revalidação (mercado recomenda pedir de 6 a 12 meses antes) |
| 3º e 4º, XXI | Notificação ou registro por família (mesmo fabricante legal, tecnologia, metodologia e indicação semelhantes) | Dossiê por família |
| 56 | Responsáveis legal e técnico respondem pelas informações | Declaração do RT/RL no dossiê |
| 57 | Detentor mantém o dossiê atualizado; dossiê de classe I não é enviado, mas fica disponível para inspeção (§1º) | Dossiê de classe I arquivado no sistema |
| 58 e Anexo II | Conteúdo do dossiê técnico, organizado por classe | Gerador do dossiê com checagem de completude |

Itens do art. 58: I descrição do produto (finalidade, analito, classificação e regra, componentes, embalagem, software, acessórios, países onde é autorizado); II imagens; III relatório de gerenciamento de risco; IV lista de normas técnicas adotadas; V certificado de conformidade, para instrumentos de certificação compulsória; VI estudos de desempenho (exatidão, precisão, sensibilidade analítica ou limite de detecção, especificidade analítica, efeito gancho de alta dose, faixa de medição, cut-off, validação do ensaio, validação de limpeza e desinfecção de instrumentos, usabilidade para leigos); VII estabilidade (prazo de validade com pelo menos três lotes, em uso e transporte); VIII desempenho clínico (sensibilidade e especificidade clínicas, valores esperados, relatório de evidências clínicas); IX rotulagem e instruções de uso; X e XI locais e processo de fabricação com fluxograma.

Pelo Anexo II, desempenho clínico se aplica só às classes III e IV, desempenho analítico às classes II a IV, e a classe I exige os itens básicos.

Em 25/08/2026 a ANVISA publicou o "Manual para Regularização de Dispositivos para Diagnóstico in Vitro", com capítulo sobre o dossiê técnico; documentação obrigatória ausente pode levar ao indeferimento sumário. A estrutura do gerador deve ser conferida contra esse manual.

## Lei 14.063/2020 — assinaturas eletrônicas

Art. 4º classifica as assinaturas em simples, avançada e qualificada. A avançada usa certificado não emitido pela ICP-Brasil ou outro meio que comprove autoria e integridade, ligada de forma única ao signatário, sob seu controle e capaz de revelar alterações posteriores. A qualificada usa certificado ICP-Brasil.

Decisão do plano: assinatura eletrônica avançada interna (reautenticação, significado, data/hora, hash do conteúdo), formalizada em procedimento interno, e avaliação posterior do uso de ICP-Brasil para documentos externos.

## Validação de sistemas computadorizados

O "Guia para Validação de Sistemas Computadorizados" da ANVISA (baseado no GAMP 5, com abordagem por risco) serve de referência de método para a validação do SGP-P&D.
