# Kit inicial do SGP-P&D (spec-kit + Claude Code)

Este kit acompanha o plano "Sistema de Gestão de Projetos de P&D (IVD) — Plano de Implementação com Spec-Driven Development". Ele dá ao Claude Code o contexto da empresa (documentos, campos, padrões visuais, normas e casos de teste) antes da primeira especificação.

## Como usar

1. Crie o repositório e inicialize o spec-kit:

   ```bash
   uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z   # tag mais recente
   specify init sgp-pd --integration claude --script sh   # no Windows: --script ps
   cd sgp-pd
   specify extension add git   # opcional: um branch por feature
   ```

2. Copie o conteúdo deste kit para a raiz do repositório, mantendo as pastas.
3. Coloque os arquivos originais em `docs/modelos/` (veja o LEIA-ME da pasta).
4. Junte este `CLAUDE.md` com o que o `specify init` tiver criado.
5. Abra o Claude Code (`claude`) e rode `/speckit-constitution` com o bloco de `prompts/00-constituicao.md`.
6. Para cada feature, na ordem dos arquivos de `prompts/`:
   - `/speckit-specify` com o primeiro bloco do arquivo;
   - `/speckit-clarify`, respondendo os pontos listados;
   - `/speckit-plan` com o segundo bloco;
   - `/speckit-checklist` com os temas sugeridos;
   - `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`;
   - `/speckit-converge` até o relatório dizer Converged.
7. Faça commit ao fim de cada etapa.

## Estrutura

```text
CLAUDE.md                          regras permanentes para o Claude Code
docs/plano-implementacao.md        o plano completo, em Markdown
docs/contexto/
  01-visao-geral.md                objetivo, perfis, fluxo e siglas
  02-dicionario-documentos.md      documentos, tópicos, campos e regras
  03-padroes-formatacao.md         capa, corpo, documento completo e dossiê
  04-requisitos-regulatorios.md    RDC 665/2022, RDC 830/2023, Lei 14.063/2020
  05-vocabularios.md               listas controladas
  06-casos-de-teste.md             regras de validação e vetores de referência
  07-integracao-sankhya.md         API Gateway e pendências com a consultoria
docs/modelos/                      arquivos originais da empresa
prompts/                           um arquivo por etapa: 00 constituição, 01 a 12 features
```

Os nomes das skills seguem o spec-kit 1.x (`/speckit-specify`); nas versões 0.x o separador é ponto (`/speckit.specify`).
