# SGP-P&D — instruções permanentes para o Claude Code

Sistema de gestão de projetos de P&D de produtos para diagnóstico in vitro (IVD), usado na intranet, com rastreabilidade exigida pelas Boas Práticas de Fabricação (RDC 665/2022).

## Antes de especificar ou planejar

- Leia `.specify/memory/constitution.md` e todos os arquivos de `docs/contexto/`.
- O plano completo, com o contexto de cada feature, está em `docs/plano-implementacao.md`; os textos de cada etapa estão em `prompts/`.
- Os arquivos de `docs/modelos/` servem só como referência de estrutura e layout. Os dados neles são fictícios: não os analise e não os use em cálculos, fixtures ou testes.

## Regras permanentes

- Interface, mensagens, documentos gerados e mensagens de commit em português do Brasil; código e identificadores em inglês.
- Não invente campos de formulário, artigos de norma ou textos regulatórios. Se faltar informação, registre a dúvida como pendência de esclarecimento no `spec.md` em vez de supor.
- Nada é apagado fisicamente. Versões assinadas são imutáveis; correção gera nova versão com motivo.
- Todo evento relevante (criação, alteração, assinatura, geração, exportação, permissão) vai para a trilha de auditoria.
- Todo cálculo estatístico tem teste com os vetores de referência de `docs/contexto/06-casos-de-teste.md`.
- Mudança de modelo de dados vem sempre com migração e teste.
- Integração com o Sankhya só pelo API Gateway oficial; acesso direto ao banco do ERP é proibido (ver `docs/contexto/07-integracao-sankhya.md`).
- Segredos só em variáveis de ambiente, nunca no repositório.
- Números exibidos no padrão brasileiro (vírgula decimal), com a regra de arredondamento definida na feature 007.

## Spec-kit neste repositório

- spec-kit 1.3.2 com integração Claude: skills em `.claude/skills/speckit-*/SKILL.md`, scripts PowerShell em `.specify/scripts/powershell/` (inicializado com `--script ps`).
- Extensão `git`: o hook antes do `/speckit-specify` cria um branch por feature (`NNN-slug`); a feature volta para `main` quando o `/speckit-converge` indicar Converged.
- Artefatos de cada feature em `specs/NNN-slug/` (spec, plan, research, data-model, contracts, quickstart, checklists, tasks).

## Fluxo de trabalho

- Uma feature por vez, na ordem dos arquivos de `prompts/`.
- Ao fim de cada etapa do spec-kit, pare e aguarde revisão humana antes da etapa seguinte.
- Rode a suíte de testes antes de marcar qualquer tarefa como concluída.
- Repita `/speckit-implement` e `/speckit-converge` até o relatório indicar Converged.
