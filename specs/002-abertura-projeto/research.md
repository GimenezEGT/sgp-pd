# Research: Abertura de projeto — TAP e Plano de Negócios

## R1. Máquina de estados

- **Decision**: estados `draft` (Rascunho), `submitted` (Submetido), `returned` (Devolvido) e
  `open` (Aberto — o "aprovado" do plano). Tabela explícita de transições em
  `projects/workflow.py`: `draft→submitted`, `returned→submitted` (ação `submit`, só o líder),
  `submitted→open` (`approve`, Gestor de P&D que não é o líder) e `submitted→returned` (`return`,
  Gestor de P&D, comentário obrigatório). Qualquer outra transição lança erro de validação.
- **Rationale**: o plano pede máquina explícita e testada; o nome "Aberto" é o do pedido.
- **Alternatives considered**: django-fsm (dependência a mais para quatro estados).

## R2. Código do projeto sem colisão

- **Decision**: tabela `projects_projectcodesequence (year PK, last_value)`; na aprovação,
  `INSERT … VALUES (ano, 1) ON CONFLICT (year) DO UPDATE SET last_value = last_value + 1
  RETURNING last_value`, na mesma transação da aprovação. Código = `{prefixo}-{ano}-{n:03d}`,
  prefixo `PROJECT_CODE_PREFIX` (padrão `PD`), ano da aprovação no horário de Brasília.
- **Rationale**: uma única instrução atômica serializa aprovações concorrentes pela trava de
  linha; se a aprovação falhar, a transação desfaz o incremento e não sobra lacuna.
- **Alternatives considered**: `SEQUENCE` do PostgreSQL por ano (criação dinâmica e lacunas em
  rollback); `MAX()+1` (colide).

## R3. Dinheiro em formato brasileiro

- **Decision**: `DecimalField(max_digits=14, decimal_places=2)` com validador de não negativo;
  campo de formulário `BRLMoneyField` que aceita `1.234.567,89`, `1234567,89` e `R$ 1.234,00`
  e recusa mais de 2 casas; filtro de template `brl` que exibe `R$ 1.234.567,89`.
- **Rationale**: o plano pede Decimal(14,2), BRL e formato brasileiro; sem ponto flutuante.

## R4. Permissão por campo dos dados financeiros

- **Decision**: `projects/permissions.py` define `FINANCIAL_FIELDS` e
  `can_view_financials(user, project)` = perfil Gestor de P&D, líder do projeto ou perfil em
  `FINANCIAL_DATA_PROFILES` (configuração, vazio por padrão). As telas recebem um objeto de
  apresentação que troca os campos financeiros por "Restrito"; a página de edição do plano é só do
  líder. Na trilha, `sgp/audit/masking.py` guarda, por tipo de evento, as chaves sensíveis e a
  regra de visibilidade; a consulta e a exportação aplicam a máscara por evento, conforme o
  projeto do evento e quem consulta. O hash usa sempre o valor gravado (a máscara é só de
  apresentação).
- **Rationale**: "permissão por campo aplicada também nas consultas e exportações"; a trilha da
  001 é vista por Qualidade e Administrador, que não têm permissão financeira.

## R5. Listas e tabelas do TAP sem exclusão física

- **Decision**: listas (escopo, entregas, premissas, restrições) e tabelas (riscos, partes
  interessadas) ficam em JSONB dentro do `ProjectCharter`; editar é atualizar o documento, com
  valor anterior e novo na trilha. Equipe e marcos são registros próprios (acesso e
  acompanhamento dependem deles) e saem de uso por encerramento de vigência e cancelamento.
- **Rationale**: o papel de banco não tem DELETE; JSONB é a decisão do plano para dados de
  formulário (feature 004).

## R6. Concorrência na edição

- **Decision**: campo `row_version` em `Project`, `ProjectCharter` e `BusinessPlan`; o
  formulário devolve a versão lida; o serviço trava a linha (`select_for_update`), compara e
  incrementa; diferença gera erro "Outra pessoa gravou este documento; recarregue a página".
- **Rationale**: FR-020; mesma técnica que a 004 usará nos subdocumentos.

## R7. Listas controladas

- **Decision**: app `vocab` com `Vocabulary` (código, nome, versão) e `Term` (código, rótulo,
  ordem, ativo), sem exclusão. Carga inicial por migração de dados: `tecnologia` (Bioquímica,
  Imunologia, Biologia molecular, Outras) e `tipo-subdocumento` (os 9 subdocumentos do PSG 20). A
  manutenção pela Qualidade entra na feature 003 (cadastros).
- **Rationale**: princípio IV e `05-vocabularios.md` ("cadastráveis e versionadas pela
  Qualidade, não fixas no código").

## R8. Acesso ao projeto e regra única

- **Decision**: `Project.is_member(user)` = líder, ou membro com vigência ativa em projeto
  `open`. `can_access_project` da 001 continua a regra única; as views usam
  `get_project_or_deny`, que recusa com 403 e registra.
- **Rationale**: FR-003 (rascunho só do líder e dos perfis globais) e "a equipe ganha acesso na
  aprovação".

## R9. Nomes do plano

Projeto → `Project`; TermoAbertura → `ProjectCharter`; PlanoNegocios → `BusinessPlan`;
PrevisaoAnual → `AnnualForecast`; Marco → `Milestone`; MembroProjeto → `ProjectMember`.
