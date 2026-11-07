# Feature 004 — Modelos de formulário versionados e subdocumentos

As abas da planilha de capas viram modelos configuráveis, e o analista passa a preencher os nove subdocumentos com dados estruturados; uma nova versão do formulário não exige programação.

```text
/speckit-specify Modelos de formulário versionados e preenchimento dos subdocumentos do projeto. Leia docs/contexto/02-dicionario-documentos.md (todos os subdocumentos), 03-padroes-formatacao.md e 05-vocabularios.md.

Problema: os formulários do PSG 20 mudam de versão ("Formulário Versão: 05") e cada aba da planilha Capas Projeto tem tópicos próprios. O sistema precisa refletir isso sem programação a cada mudança.

Histórias:
1. Como Garantia da Qualidade, cadastro um modelo de formulário: tipo de subdocumento, versão do formulário, referência (ex.: "PSG 20 - Pesquisa e Desenvolvimento de Produtos"), vigência, título da capa, tópicos numerados da lista "ESTE RELATÓRIO DEVE CONTER" e, para cada tópico, os campos: texto formatado, lista, tabela com colunas definidas, seleção de vocabulário, referência a cadastro, anexo e "não aplicável" com justificativa.
2. Publico uma nova versão do modelo; documentos já iniciados continuam no modelo em que começaram, a menos que o gestor migre o documento.
3. Como analista, crio num projeto aberto os subdocumentos: Entrada de Projeto, Elaboração de Formulação, Elaboração de Lote Piloto, RAPD, Análise Crítica, Validação do Produto, Verificação Final de Validação, Saída de Projeto e, quando necessário, Alteração de Projeto.
4. Na Entrada de Projeto preencho os 13 tópicos e a parte estruturada do formulário opcional (amostras, funcionalidade, classificação, automação, usuário, armazenamento, filtros, classificação de uso) e marco "aplica / não se aplica" em cada requisito de desempenho.
5. A Verificação Final de Validação é montada pelo sistema: uma linha por tópico da Entrada, com "Previsto" vindo da Entrada aprovada, "Realizado" preenchido pelo analista e "Disposição" (aprovado, reprovado ou outros, com justificativa).
6. Na Saída de Projeto escolho os setores que recebem a transferência (Produção, Supply Chain, Controle de Qualidade, SAC, Comercial, Marketing, S&OP); os itens marcados "MAPA" só aparecem em projetos com esse órgão.
7. A Alteração de Projeto registra versão alterada e nova versão, justificativa, requisitos de entrada afetados e outros dados; quando aprovada, a versão do projeto sobe e os subdocumentos afetados ficam marcados para revisão.

Regras: "não aplicável" exige justificativa e bloqueia a lista daquele tópico; a numeração de tópicos e tabelas é automática; requisitos marcados "aplica" na Entrada geram pendências na Validação; o sistema avisa quando a ordem do fluxo não foi seguida (ex.: Lote Piloto antes da Formulação aprovada) e só segue com autorização do gestor.

Fora do escopo: assinatura (005), geração de DOCX/PDF (006) e cálculos estatísticos (007).
```

Pontos que o `/speckit-clarify` deve fechar:

- Se a ordem dos subdocumentos é obrigatória ou só recomendada.
- Quem publica modelos (só a Garantia da Qualidade?).
- O que fazer quando a capa e o corpo usam tópicos diferentes, como na Análise Crítica (3 na capa, 4 no projeto).
- O rótulo do tópico 9 da Entrada, que repete o do tópico 6 ("Classificação de Uso"); confirmar se o tópico 9 é a classe de risco da RDC 830/2023.
- A numeração da capa da Saída, que tem dois itens "11".
- Edição simultânea do mesmo documento por dois analistas.

```text
/speckit-plan App "formularios" com ModeloFormulario versionado e imutável após publicação; a definição (tópicos, campos, tipos, regras) fica em JSON validado por um JSON Schema próprio. App "subdocumentos" com Subdocumento e dados em JSONB validados contra a definição do modelo usado. Formulários gerados no servidor a partir da definição, com HTMX para tabelas editáveis e autocomplete de cadastros. Carga inicial dos modelos versão 05 a partir de docs/contexto/02-dicionario-documentos.md, por migração de dados. Testes do JSON Schema e de cada tipo de campo. Controle otimista de concorrência na edição.
```

Checklists sugeridos: regulatório (RDC 665/2022, arts. 44 a 61) e usabilidade dos formulários.

Pronto quando:

- [ ] Os nove tipos de subdocumento da versão 05 estão carregados e preenchíveis.
- [ ] Publicar um modelo versão 06 não altera documentos já iniciados.
- [ ] A Verificação Final nasce da Entrada aprovada.
- [ ] Marcar "não aplicável" num tópico com itens preenchidos é rejeitado.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
