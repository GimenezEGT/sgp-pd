# Research: Dossiê técnico para a ANVISA

## R1. Definição declarativa em YAML, versionada no banco

- **Decision**: a estrutura I a XII (títulos do contexto, `docs/contexto/03-padroes-formatacao.md`),
  a aplicabilidade por classe e a fonte de cada item ficam num YAML; a versão inicial vem de
  `sgp/dossier/definicao_padrao.yaml` (migração de dados) e a Qualidade/AR publica novas versões
  pela tela, colando o YAML, que é validado (numeração, classes e tipos de fonte) antes de valer.
  Cada versão do dossiê guarda a versão da definição usada.
- **Rationale**: ajuste sem programar e com histórico; o YAML é legível para quem não programa.
- **Note**: as letras dos subitens sem letra no contexto (VI depois de "A. Amostra Biológica" e
  "Equipamentos, software…" em I) foram atribuídas em sequência pelo sistema e ficam para conferência
  de Assuntos Regulatórios, como o próprio contexto pede ("confirme nos originais").

## R2. Fontes de dados

- **Decision**: tipos de fonte: `subdocumento` (tópico e, opcionalmente, campos, do conteúdo
  congelado da versão aprovada vigente), `estudos` (tipos de estudo da 007, versão mais recente
  bloqueada), `normas` (referências a normas da Entrada), `referencias` (referências bibliográficas
  citadas nos subdocumentos aprovados), `anexos` (arquivos de um tópico), `texto_padrao` (versão
  aprovada vigente da biblioteca), `complemento` (texto do projeto escrito por Assuntos
  Regulatórios para o item, com opção de "não aplicável" e justificativa) e `classe` (classe de
  risco da Entrada). Onde o sistema não tem um campo próprio (ex.: analito, população alvo), a fonte
  é `complemento`: nada é inventado nem deduzido.

## R3. Classe de risco e aplicabilidade

- **Decision**: a classe vem do tópico "Classificação de Risco" da Entrada aprovada. Item fora das
  classes da definição sai como "Não aplicável" com a justificativa da definição (ex.: desempenho
  clínico só nas classes III e IV, desempenho analítico nas classes II a IV, conforme o resumo do
  Anexo II no contexto). Item da classe sem dado: "faltando"; com "não aplicável" registrado na
  origem e justificativa: "não aplicável"; sem justificativa: "faltando".

## R4. Geração reaproveitando a 006

- **Decision**: um montador comum produz a árvore do dossiê (itens, blocos de texto, tabelas
  numeradas, anexos, declaração); o PDF sai pelo WeasyPrint em PDF/A-2b (como a 006), com
  cabeçalho "Dossiê Técnico <produto>" e rodapé com a razão social e a página, em itálico; o DOCX
  sai pelo python-docx com cabeçalho, rodapé e campo de página. Os blocos dos subdocumentos vêm do
  conteúdo congelado da 006 (mesmos rótulos e tabelas). O nome do produto aparece em itálico no
  texto. Com item obrigatório faltando, só sai rascunho (marca d'água e lista do que falta).

## R5. Pacote de anexos

- **Decision**: o dossiê final gera um ZIP com o PDF, o DOCX e os anexos (arquivos dos tópicos de
  origem, conferidos pelo resumo na leitura), numerados como na lista de anexos do dossiê.

## R6. Aditamento

- **Decision**: cada versão guarda o conteúdo canônico por item (textos e tabelas em texto); o
  aditamento compara com a última versão com envio registrado, item a item, e mostra só os itens
  que mudaram, com o texto anterior e o novo (`difflib`), na tela e num PDF de aditamento.

## R7. Família

- **Decision**: projetos com o mesmo nome de família do produto, a mesma tecnologia e a mesma
  classe formam a família; o dossiê da família repete o item para cada kit com o nome do kit e só
  fica completo quando todos os kits estão completos.

## R8. Empresa e responsável técnico e legal

- **Decision**: razão social, cidade e responsável técnico e legal (nome, conselho, UF, número)
  ficam num cadastro mantido pela Qualidade/AR, com evento a cada mudança; a declaração usa o texto
  do contexto. Sem esse cadastro, a checagem aponta a pendência.

## R9. Referência da árvore de títulos

- **Decision**: os testes geram o dossiê de um projeto de exemplo (dados fictícios criados nos
  testes) e comparam a árvore de títulos do PDF e do DOCX com a estrutura do contexto; os `.docx`
  originais não estão em `docs/modelos` (dependência registrada) e os arquivos de lá não são lidos.
