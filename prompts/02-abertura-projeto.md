# Feature 002 — Abertura de projeto: TAP e Plano de Negócios

O líder abre o projeto preenchendo o TAP e o Plano de Negócios; com a aprovação do Gestor de P&D, o projeto recebe código, equipe e marcos e passa a aceitar subdocumentos.

```text
/speckit-specify Abertura de projeto com Termo de Abertura de Projeto (TAP) e Plano de Negócios. Leia docs/contexto/02-dicionario-documentos.md, seções TAP e Plano de Negócios.

Objetivo: o líder abre um projeto de produto para diagnóstico in vitro pelo sistema, em vez de documentos avulsos; o Gestor de P&D aprova; a partir daí o projeto aceita subdocumentos.

Histórias:
1. Como líder de projeto, crio um projeto em rascunho informando o produto: nome, família (quando houver), tecnologia (ex.: bioquímica, imunologia, biologia molecular), órgão regulador (ANVISA ou MAPA), classe de risco prevista e regra de classificação.
2. Preencho o TAP: justificativa, objetivo, escopo incluído e excluído, entregas, premissas, restrições, riscos iniciais, partes interessadas, equipe com papéis e marcos planejados por subdocumento.
3. Preencho o Plano de Negócios: nome do projeto, data, líder, objetivo, descrição geral, custo total do projeto, prazo de execução, mercado-alvo e retorno esperado ano a ano por 5 anos. Incluo a viabilidade financeira (concorrentes, preço por teste dos concorrentes, apresentações dos concorrentes, custo máximo de produção, preço de venda previsto, venda anual prevista) e a viabilidade produtiva (estrutura fabril, equipe de produção, controle de qualidade).
4. Submeto para aprovação; o Gestor de P&D aprova ou devolve com comentário obrigatório. Na aprovação, o projeto recebe código único, fica "Aberto" na versão 01 e a equipe ganha acesso.
5. Como Gestor de P&D, vejo a lista de projetos com filtros por status, líder e produto.

Regras: dados financeiros só aparecem para Gestor de P&D, líder do projeto e perfis autorizados; o retorno total em 5 anos é a soma das previsões anuais; cada marco tem data planejada e, depois, data realizada; toda edição vai para a trilha de auditoria.

Fora do escopo: subdocumentos técnicos (004) e assinatura eletrônica (005). Nesta feature a aprovação é uma confirmação registrada na auditoria; a 005 a substitui por assinatura.
```

Pontos que o `/speckit-clarify` deve fechar:

- Os campos do TAP: o pedido original não os lista, e a lista acima é uma proposta.
- Formato do código do projeto (ex.: PD-2026-001).
- Se "retorno esperado" é receita, margem ou lucro, e se precisa de indicador como payback.
- Se projetos acima de certo custo exigem aprovação da diretoria.

```text
/speckit-plan Reaproveite a base da feature 001. Crie a app "projetos" com Projeto, TermoAbertura, PlanoNegocios, PrevisaoAnual (5 linhas), Marco e MembroProjeto. Valores monetários em Decimal(14,2), moeda BRL e formato brasileiro na tela. Máquina de estados explícita e testada (rascunho, submetido, aprovado, devolvido). Código do projeto gerado por sequência anual no banco, sem colisão em aprovações simultâneas. Permissão por campo para dados financeiros, aplicada também nas consultas e exportações, com testes. Validação no servidor e mensagens em português.
```

Checklists sugeridos: permissões de dados financeiros.

Pronto quando:

- [ ] Um projeto é aberto de ponta a ponta com aprovação do gestor.
- [ ] Usuário sem permissão não vê custo nem retorno, nem pela URL direta.
- [ ] Duas aprovações simultâneas geram códigos diferentes.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
