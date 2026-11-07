# 03 — Padrões de formatação dos documentos

Extraído da planilha "Capas Projeto.xlsx" (renderizada em A4) e da estrutura dos projetos e dossiês, cujos dados são fictícios. Os .docx originais devem ser conferidos na prova de layout da feature 006, porque o texto extraído não traz capas, cabeçalhos e sumários completos.

## Página

- A4 retrato.
- Margens: 1,3 cm à esquerda e à direita; 2,0 cm em cima e embaixo.
- Fonte: Calibri.

## Capa dos subdocumentos (todas as abas, exceto o formulário opcional)

Ordem dos elementos, de cima para baixo:

| Elemento | Formato |
| --- | --- |
| Faixa com o logotipo "Bioclin · Quibasa" | imagem de 1112 × 162 px, centralizada no topo |
| Título do subdocumento | Calibri 24 pt negrito, centralizado (23 pt em RAPD, Análise Crítica, Validação, Verificação Final e Saída) |
| Nome do produto | Calibri 20 pt negrito, caixa alta, centralizado |
| "VERSÃO" + número ("01") | Calibri 20 pt; na Alteração: "Versão alterada:" e "Nova Versão:" |
| "ESTE RELATÓRIO DEVE CONTER:" | Calibri 16 pt negrito |
| Tópicos numerados ("1 - Amostras") | Calibri 14 pt; duas colunas na Entrada de Projeto (1–6 e 7–13), uma coluna nas demais |
| "Analista Responsável (Nome/Função):" + linha | Calibri 12 pt, rótulo em negrito |
| "Gestor de P&D:" + linha | Calibri 12 pt, rótulo em negrito |
| "Data: ____" | Calibri 12 pt negrito |
| Rodapé "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos" | Calibri 11 pt, à esquerda |
| "Página N" | rodapé da página nas abas Entrada, Formulação e Lote Piloto |

Títulos exatos das capas: "Entrada de Projeto", "Alteração de Projeto", "Elaboração de Formulação", "Elaboração de Lote Piloto", "Relatório de Avaliação de Produto em Desenvolvimento (RAPD)", "Análise Crítica", "Validação do Produto", "VERIFICAÇÃO FINAL DE VALIDAÇÃO", "Saída de Projeto".

Particularidades:

- Verificação Final de Validação: abaixo da versão, tabela "CHECK LIST" com cabeçalho em 11 pt negrito e colunas "REQUISITOS DE ENTRADA", "PREVISTO", "REALIZADO", "DISPOSIÇÃO (APROVADO, REPROVADO OU OUTROS)".
- Saída de Projeto: depois dos tópicos, setores de transferência em duas colunas (Produção I, Supply Chain, Controle de Qualidade, SAC | Comercial, Marketing, S&OP).
- Formulário opcional de entrada: layout próprio, com cabeçalho em faixa colorida, caixas de seleção agrupadas e tabela "Aplica / Não se aplica".

Hoje várias abas usam escala de impressão (65% a 95%) para caber no A4; o sistema deve gerar direto em A4, sem escala.

## Corpo dos documentos de projeto

- Cada subdocumento começa pela sua capa e segue com os tópicos como títulos numerados em negrito ("1. Amostras", "2. Funcionalidade").
- Subtítulos internos em negrito sem número ("Critérios de aceitação", "Resultados", "Conclusão", "Metodologia", "Lotes utilizados").
- Tabelas numeradas em sequência no documento, com título acima: "Tabela 01 – Comparação de Métodos". Notas e legendas abaixo da tabela, com referências em sobrescrito (¹, ²).
- Listas de lotes no formato "Lote <código> – Fabricação: MM/AAAA – Validade: MM/AAAA".
- Referências bibliográficas numeradas ao fim do documento.
- O sistema usa vírgula decimal em todo documento gerado.

## Documento completo do projeto

Ordem observada no projeto DBS: capa da Entrada, capa da Alteração, conteúdo da Entrada (com a justificativa da alteração), Lote Piloto, Validação, Análise Crítica com referências, Saída. A ordem oficial deve ser confirmada na feature 009.

## Dossiê técnico

- Cabeçalho em itálico: "Dossiê Técnico <NOME DO PRODUTO>".
- Rodapé em itálico: "Quibasa Química Básica Ltda." e número da página.
- Título "DOSSIÊ TÉCNICO" em negrito, seguido do nome do produto em itálico.
- Itens principais em algarismos romanos e caixa alta; subitens em letras (A., B., C.); itens de terceiro nível em números (1., 2., 3.).
- Nome do produto sempre em itálico no texto.
- Fecha com a declaração: "O abaixo assinado <nome>, inscrito no Conselho Regional de Farmácia de <UF> sob nº <número>, assume a responsabilidade pelas informações fornecidas nesse Dossiê Técnico.", seguida de cidade, data e bloco de assinatura (nome, cargo, "Responsável Técnico e Legal").

Estrutura observada (alinhada ao art. 58 da RDC 830/2023):

```text
I. DESCRIÇÃO DO PRODUTO
   A. Finalidade (Indicação de Uso)
      1. Analito  2. Funcionalidade  3. Detecção (Fator de Risco)  4. Usuário  5. Local de Uso
      6. Classificação do Uso (Único ou Múltiplo)  7. Classificação da Automação
      8. Classificação do Teste (Qualitativo ou Quantitativo)  9. Tipo de Amostra  10. População Alvo
   B. Metodologia
   C. Classe de Risco
   D. Composição
   E. Apresentação e Embalagem (apresentação comercial; embalagens primária e secundária)
   Equipamentos, Software, Configurações, Acessórios, Comercialização
II. IMAGEM DO PRODUTO (II.I Imagem do acessório, quando houver)
III. GERENCIAMENTO DE RISCO
IV. NORMAS TÉCNICAS (internacionais e nacionais)
V. CERTIFICADO DE CONFORMIDADE (INSTRUMENTOS DE CERTIFICAÇÃO COMPULSÓRIA)
VI. ESTUDO DE DESEMPENHO
   lotes piloto, kits comparativos, quantidade de testes
   A. Amostra Biológica (1. Caracterização e validação das amostras clínicas; 2. Condições de armazenamento e estabilidade)
   Rastreabilidade metrológica de calibradores e controles, Exatidão, Precisão (repetibilidade, reprodutibilidade, interensaio),
   Sensibilidade analítica, Interferentes, Reatividade cruzada, Efeito prozona de alta dose, Linearidade, Valor de cut-off,
   Validação do procedimento de ensaio, Validação do procedimento de limpeza e desinfecção, Relatório de usabilidade
VII. ESTUDO DE ESTABILIDADE
   A. Longa duração (e transporte)  B. Após aberto / on board  C. Transporte  D. Condições de armazenamento e transporte
VIII. DESEMPENHO CLÍNICO
   Sensibilidade e especificidade clínicas, Valor esperado ou de referência, Relatório de avaliação de evidências clínicas
IX. ROTULAGEM E INSTRUÇÃO DE USO (A. Rótulos primário e secundário; B. Instrução de uso)
X. UNIDADE FABRIL
XI. PROCESSO DE FABRICAÇÃO (descrição das etapas e fluxograma)
XII. REFERÊNCIAS BIBLIOGRÁFICAS
```

As letras e números de subitem foram reconstruídos a partir do texto extraído e das referências internas ("item E deste dossiê", "item VI-A-1", "item VII - A"); confirme nos originais.

Itens não aplicáveis aparecem com o título e uma justificativa ("Não aplicável. …"), em vez de serem omitidos.
