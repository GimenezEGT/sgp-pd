# Feature 011 — Dossiê técnico para a ANVISA

O dossiê é montado a partir dos dados aprovados do projeto, no formato I a XII usado hoje, depois de uma checagem que mostra item a item o que falta para a classe de risco do produto.

| Item do dossiê | Origem no sistema |
| --- | --- |
| I. Descrição do produto (finalidade, analito, usuário, classificações, amostra, população, metodologia, classe, composição, apresentação, equipamentos, software, acessórios, comercialização) | Entrada de Projeto, Formulação e cadastro do produto |
| II. Imagem do produto | Anexo da Saída de Projeto |
| III. Gerenciamento de risco | Matriz de risco anexada à Entrada e à Saída |
| IV. Normas técnicas | Tópico 11 da Entrada e biblioteca de normas |
| V. Certificado de conformidade | Só para instrumentos sob certificação compulsória |
| VI. Estudo de desempenho | Estudos da Feature 007, lotes e kits de referência |
| VII. Estudo de estabilidade | Estudos de estabilidade e condições de armazenamento |
| VIII. Desempenho clínico | Estudos clínicos (exigidos nas classes III e IV) |
| IX. Rotulagem e instrução de uso | Anexos do tópico 11 da Saída de Projeto |
| X. Unidade fabril | Cadastro da empresa |
| XI. Processo de fabricação | Biblioteca de textos padrão e Lote Piloto |
| XII. Referências bibliográficas | Biblioteca de referências do projeto |

```text
/speckit-specify Geração do dossiê técnico para notificação ou registro na ANVISA, quando todos os dados necessários estiverem presentes. Leia docs/contexto/03-padroes-formatacao.md (seção Dossiê) e 04-requisitos-regulatorios.md.

Objetivo: montar o dossiê a partir dos dados aprovados do projeto, no formato atual da empresa (itens I a XII), sem copiar e colar, mostrando antes o que falta.

Histórias:
1. Como Assuntos Regulatórios, abro o dossiê de um projeto e vejo a checagem de completude: cada item exigido pelo art. 58 e pelo Anexo II da RDC 830/2023 para a classe de risco do produto, com a origem do dado e o status (completo, faltando, não aplicável com justificativa).
2. Gero o dossiê em DOCX e PDF com cabeçalho "Dossiê Técnico <produto>", rodapé com a razão social e numeração de páginas, itens em algarismos romanos, subitens em letras e números e tabelas numeradas.
3. Textos que não vêm de dados (ex.: processo de fabricação, unidade fabril) saem de uma biblioteca de textos padrão aprovados e versionados.
4. O dossiê termina com a declaração de responsabilidade do responsável técnico e legal (nome, registro no conselho, cidade e data) para assinatura.
5. Gero aditamentos: o sistema compara com a última versão enviada e destaca o que mudou.
6. Registro o envio (número do processo ou expediente, data) e o resultado da petição.

Regras: só entram dados de versões aprovadas; produto de classe I gera o dossiê para arquivo, sem envio; itens "não aplicável" saem com a justificativa registrada na Entrada ou no estudo; uma família de produtos gera um dossiê com todos os kits da família.
```

Pontos que o `/speckit-clarify` deve fechar:

- A estrutura final, conferida contra o Manual para Regularização de Dispositivos para Diagnóstico in Vitro (ANVISA, 25/08/2026).
- Anexos (rótulos, instrução de uso, gerenciamento de risco) incorporados ou enviados como PDFs separados.
- Como o responsável técnico e legal assina: certificado ICP-Brasil ou assinatura da plataforma de peticionamento.
- Regras de agrupamento em família.

```text
/speckit-plan App "dossie" com DefinicaoDossie (itens, aplicabilidade por classe e mapeamento item → fonte de dados), BibliotecaTexto versionada e Submissao. O mapeamento fica em arquivo declarativo (YAML) para a Qualidade ajustar sem programar. Reutilize o gerador da feature 006. Comparação entre versões por item (diff de texto e de tabelas) para aditamentos. Testes que geram o dossiê dos dois produtos de docs/modelos a partir de dados de exemplo e comparam a árvore de títulos com a dos originais.
```

Checklists sugeridos: regulatório (RDC 830/2023, art. 58 e Anexo II).

Pronto quando:

- [ ] Assuntos Regulatórios confere o dossiê de um produto real sem retrabalho de estrutura.
- [ ] A checagem de completude impede o PDF final com item obrigatório faltando.
- [ ] O aditamento destaca o que mudou.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
