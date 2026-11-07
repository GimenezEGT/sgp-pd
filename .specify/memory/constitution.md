# Constituição do SGP-P&D

Sistema de gestão de projetos de P&D de produtos para diagnóstico in vitro (IVD), usado na
intranet da empresa, que substitui os formulários avulsos do PSG 20 - Pesquisa e Desenvolvimento
de Produtos. Esta constituição vale para todas as features e prevalece sobre qualquer outra prática
do repositório.

## Princípios fundamentais

### I. Rastreabilidade (ALCOA+)

- Todo dado DEVE registrar autor, data e hora do servidor, versão e origem.
- Nenhum registro DEVE ser apagado fisicamente; exclusão é sempre lógica.
- Toda correção DEVE gerar nova versão com motivo obrigatório; a versão anterior continua
  consultável.
- Data e hora DEVEM vir do servidor sincronizado, nunca do navegador ou do usuário.

Justificativa: a RDC 665/2022 exige registros legíveis, protegidos e guardados pelo tempo de vida
do produto (arts. 34, 35 e 37); os atributos ALCOA+ são a base da integridade de dados exigida das
Boas Práticas de Fabricação.

### II. Trilha de auditoria imutável

- Criação, alteração, assinatura, geração de documento, exportação e mudança de permissão DEVEM
  gerar eventos de auditoria append-only.
- Cada evento DEVE guardar quem, quando, o quê, valor anterior, valor novo e motivo quando houver.
- Os eventos DEVEM ser encadeados por hash (cada evento guarda o hash do anterior) e a integridade
  da cadeia DEVE ser verificável a qualquer momento, apontando qualquer quebra.
- A trilha DEVE ser consultável por projeto, usuário, período e tipo de evento.

Justificativa: a trilha é a prova de que os registros de controle de projeto não foram adulterados
e sustenta a validação do sistema computadorizado (RDC 665/2022, arts. 104 a 106).

### III. Assinatura eletrônica

- Assinar DEVE exigir reautenticação do signatário no momento da assinatura.
- A assinatura DEVE registrar pessoa, papel, significado (elaborado, revisado, aprovado), data e
  hora do servidor e o hash do conteúdo assinado.
- Documento assinado DEVE ficar bloqueado; uma assinatura NUNCA vale para outra versão.
- Quem elaborou um documento NÃO DEVE aprová-lo.

Justificativa: a assinatura eletrônica avançada da Lei 14.063/2020, art. 4º, precisa estar ligada
de forma única ao signatário, sob seu controle e ser capaz de revelar alterações posteriores; a
RDC 665/2022 aceita assinatura com data em vários registros (arts. 27, 42, 47, 57 e 59).

### IV. Modelos versionados

- Tipos de subdocumento, tópicos, campos, capas e rodapés ("Formulário Versão", "Referência PSG")
  DEVEM ser dados configuráveis e versionados, nunca fixos no código.
- Cada documento DEVE guardar a versão de modelo (de formulário e de layout) que usou.
- Publicar nova versão de modelo NÃO DEVE alterar documentos já iniciados ou assinados.

Justificativa: os formulários do PSG 20 mudam de versão; trocar "Formulário Versão 05" por 06
precisa ser cadastro, não programação.

### V. Fonte única

- Lotes, insumos, amostras, kits de referência, normas, referências bibliográficas e pessoas DEVEM
  ser cadastrados uma única vez e referenciados por todos os documentos.
- Textos e tabelas gerados NUNCA DEVEM redigitar esses dados; DEVEM lê-los do cadastro.
- Cadastro usado em documento assinado só DEVE ser corrigido por nova versão; o documento assinado
  continua mostrando o valor assinado.

Justificativa: a redigitação do mesmo lote, código ou concentração em vários documentos é a
principal fonte de divergência no processo atual.

### VI. Cálculo e numeração automáticos

- Estatísticas (média, desvio-padrão, CV%, regressão, R², proporções com IC 95%), totais,
  numeração de tópicos, tabelas e páginas e referências cruzadas DEVEM ser calculados pelo sistema.
- NÃO DEVE existir campo para digitar um valor que o sistema calcula.
- Todo cálculo DEVE ser coberto por testes com os vetores de referência de
  `docs/contexto/06-casos-de-teste.md`, e o resultado assinado DEVE ficar congelado na versão.

Justificativa: cálculos manuais e numeração digitada geram erros que só aparecem na revisão ou na
inspeção.

### VII. Segurança

- Só usuários autenticados no domínio (Active Directory) DEVEM acessar o sistema.
- Permissões DEVEM ser por perfil e por projeto, com menor privilégio; dados financeiros têm
  permissão por campo, aplicada também em consultas e exportações.
- O tráfego DEVE usar HTTPS interno; os dados NÃO DEVEM sair da intranet, exceto para o Sankhya
  pelo API Gateway oficial.
- Segredos DEVEM ficar só em variáveis de ambiente ou cofre, nunca no repositório.

Justificativa: o sistema guarda resultados, custos e projeções comerciais cuja exposição causa dano
comercial, além de registros regulatórios.

### VIII. Qualidade verificável

- Todo requisito DEVE ter critério de aceitação testável e DEVE ser rastreável até ao menos um
  teste (identificador do requisito no nome ou na marcação do teste).
- Regras regulatórias, cálculos e permissões DEVEM ser escritos com testes primeiro (TDD).
- A suíte de testes DEVE passar antes de qualquer tarefa ser marcada como concluída.
- Toda mudança de modelo de dados DEVE vir com migração e teste.

Justificativa: especificações, planos, tarefas e testes são evidência para a validação do sistema
exigida pela RDC 665/2022, art. 104.

### IX. Simplicidade

- A aplicação DEVE ser um monólito modular, com poucas dependências e sem SPA.
- Código e identificadores DEVEM estar em inglês; interface, mensagens, documentos gerados e
  mensagens de commit DEVEM estar em português do Brasil.
- Nenhuma funcionalidade DEVE ser construída sem requisito especificado.

Justificativa: um desenvolvedor sustenta o sistema; menos peças significam menos risco de
validação e de manutenção.

## Restrições regulatórias e de plataforma

- Normas de referência: RDC 665/2022 (Boas Práticas de Fabricação), RDC 830/2023 (classificação,
  notificação e registro de IVD, art. 58 e Anexo II para o dossiê), Lei 14.063/2020 (assinaturas
  eletrônicas) e LGPD. O resumo vigente está em `docs/contexto/04-requisitos-regulatorios.md`; o
  texto das normas DEVE ser conferido na fonte oficial antes de virar regra no código.
- Nenhum campo de formulário, artigo de norma ou texto regulatório DEVE ser inventado; informação
  faltante vira pendência de esclarecimento no `spec.md`.
- Amostras NÃO DEVEM guardar dados pessoais de pacientes; são identificadas só por código interno.
- Retenção: registros DEVEM ser mantidos pelo tempo de vida do produto e nunca menos de 2 anos
  (RDC 665/2022, art. 37); a retenção é configurada por produto.
- Cópia de segurança diária de banco e arquivos, com teste de restauração, é obrigatória
  (RDC 665/2022, art. 35).
- Integração com o ERP Sankhya só pelo API Gateway oficial; acesso direto ao banco do ERP é
  proibido.
- Datas e horas DEVEM ser gravadas em UTC e exibidas em America/Sao_Paulo; números DEVEM ser
  exibidos no padrão brasileiro (vírgula decimal), com a regra de arredondamento registrada junto
  do resultado.
- Os arquivos de `docs/modelos/` servem só como referência de estrutura e layout; seus dados são
  fictícios e NÃO DEVEM ser usados em cálculos, fixtures ou testes.
- O próprio SGP-P&D é software do sistema da qualidade e DEVE ser validado antes do uso oficial,
  verificado periodicamente e alterado sob controle de mudanças (RDC 665/2022, arts. 104 a 106).

## Fluxo de desenvolvimento e portões de qualidade

- Uma feature por vez, na ordem de `prompts/`, pelo ciclo do spec-kit: especificar → esclarecer →
  planejar → checklist → tarefas → analisar → implementar → convergir.
- `/speckit-specify` registra só o quê e o porquê, sem tecnologia; tecnologia entra no
  `/speckit-plan`.
- Cada artefato DEVE ser revisado por uma pessoa antes da etapa seguinte; respostas de processo do
  `/speckit-clarify` vêm do Gestor de P&D ou da Qualidade.
- Commit ao fim de cada etapa, com mensagem em português; o histórico do Git é evidência de
  validação. Código passa por revisão de uma segunda pessoa.
- `/speckit-implement` e `/speckit-converge` se repetem até o relatório indicar "Converged"; a
  aplicação é executada e os fluxos testados antes de abrir a próxima feature.
- Cada marco fecha num portão de aceite com o Gestor de P&D e a Garantia da Qualidade.

## Governança

- Esta constituição prevalece sobre qualquer outra prática do repositório. Todo `plan.md` DEVE
  passar pelo "Constitution Check" e todo `/speckit-analyze` DEVE tratar violação de princípio como
  achado crítico.
- Mudanças nesta constituição exigem justificativa escrita, revisão do Gestor de P&D e da Garantia
  da Qualidade e novo número de versão semântico: MAJOR para remoção ou redefinição incompatível de
  princípio; MINOR para princípio ou seção nova ou ampliação material; PATCH para esclarecimentos e
  correções de redação.
- Exceções a um princípio só valem se registradas na tabela "Complexity Tracking" do `plan.md`, com
  justificativa e aprovação da Garantia da Qualidade.
- A conformidade é revisada a cada feature (Constitution Check do plano, analyze e converge) e a
  cada portão de marco; mudanças no sistema passam por avaliação de impacto na validação
  (RDC 665/2022, art. 106).

**Versão**: 1.0.0 | **Ratificada em**: TODO(RATIFICATION_DATE): registrar a data após a revisão do
Gestor de P&D e da Garantia da Qualidade (rascunho de 2026-11-07) | **Última alteração**: 2026-11-07
