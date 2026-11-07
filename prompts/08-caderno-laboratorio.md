# Feature 008 — Caderno de laboratório eletrônico

Cada pesquisador registra, por projeto, os experimentos e tentativas anteriores aos resultados oficiais, com a mesma rastreabilidade dos documentos; é o histórico que entra no documento completo.

```text
/speckit-specify Caderno de laboratório eletrônico por pesquisador e por projeto, para registrar experimentos e tentativas antes dos resultados oficiais do RAPD. Leia docs/contexto/01-visao-geral.md.

Objetivo: guardar o histórico científico do desenvolvimento (o que foi tentado, o que falhou e por quê) com a mesma rastreabilidade dos documentos oficiais.

Histórias:
1. Como pesquisador, crio uma entrada num projeto com título, data, objetivo, hipótese, materiais (ligando lotes, insumos e amostras cadastrados), procedimento, resultados (texto, tabelas, fotos, arquivos de equipamento) e conclusão.
2. Uso modelos de entrada por tipo de experimento (ex.: teste de formulação, estabilidade preliminar) para não começar do zero.
3. Ao terminar, assino a entrada e ela fica bloqueada. Correções viram adendos datados e assinados, sem apagar o original.
4. Peço a assinatura de uma testemunha quando o experimento for relevante para propriedade intelectual ou para uma decisão do projeto.
5. Ligo entradas a formulações, lotes piloto e estudos; a partir de uma entrada, promovo dados para um estudo oficial (feature 007), mantendo o vínculo.
6. Como gestor, vejo a linha do tempo do caderno de cada projeto, busco por palavra, amostra, lote ou pesquisador e vejo entradas abertas há mais de N dias.

Regras: entradas não assinadas após o prazo configurado geram lembrete; data e hora vêm do servidor; anexos têm hash; o caderno do projeto é visível para a equipe do projeto, o Gestor de P&D e a Qualidade.

Fora do escopo: integração direta com equipamentos; importar arquivos basta nesta fase.
```

Pontos que o `/speckit-clarify` deve fechar:

- Prazo para assinar uma entrada (fim do dia, 24 h, 7 dias).
- Quando a testemunha é obrigatória.
- Tamanho máximo de anexos e tipos de arquivo aceitos.
- Se existem entradas fora de projeto (pesquisa exploratória).

```text
/speckit-plan App "caderno" com Entrada, Adendo, ModeloEntrada, Vinculo e Anexo. Editor de texto rico com sanitização no servidor (lista branca de tags) e colagem de imagens; anexos com hash e limite de tamanho configurável. Assinatura e bloqueio reaproveitando a feature 005. Busca textual com full-text search do PostgreSQL em português. Linha do tempo paginada com HTMX.
```

Checklists sugeridos: integridade de dados (ALCOA+) e usabilidade em bancada.

Pronto quando:

- [ ] Entrada assinada não pode ser editada, só receber adendo.
- [ ] A busca por lote traz todas as entradas que o usam.
- [ ] Dados promovidos para um estudo mantêm o vínculo nos dois sentidos.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
