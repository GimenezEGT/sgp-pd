# Relatório final da execução do plano (SGP-P&D)

Data: 12/11/2026. Plano executado: `docs/plano-implementacao.md` ("Plano de Implementação com
Spec-Driven Development"), features 001 a 012 na ordem de `prompts/`, mais a feature 013 pedida
pelo usuário e a feature 014 com os entregáveis de operação e validação. Repositório local, privado,
sem remoto (regra do plano: na rede da empresa).

## Situação

- Portão de qualidade (`scripts/verificar.sh`) no `main`: ruff sem erros, 1.255 testes aprovados,
  cobertura mínima atendida e matriz de rastreabilidade com 309 requisitos, nenhum sem cobertura
  ([docs/validacao/matriz-rastreabilidade.md](validacao/matriz-rastreabilidade.md)).
- Cada feature passou pelo ciclo do spec-kit (especificar, esclarecer, planejar, checklist, tarefas,
  analisar, implementar, convergir até "Converged"), com commit a cada etapa, roteiro executado na
  pilha real (Docker: PostgreSQL 17, Redis, worker, Nginx com TLS, LDAP de desenvolvimento) e
  evidência em `docs/validacao/NNN-resultados-execucao.md`; depois, merge no `main`.
- Pacote de validação: [docs/validacao/README.md](validacao/README.md) (entregável → onde está),
  roteiros de IQ e OQ e procedimento de recuperação.

| Feature | Entrega | Evidência |
| --- | --- | --- |
| 001 | Fundação: acesso pela rede (AD/LDAP), perfis com motivo e aprovação, sessão, trilha de auditoria encadeada por SHA-256 e verificação de integridade | [001-resultados-execucao.md](validacao/001-resultados-execucao.md) |
| 002 | Abertura de projeto: TAP, Plano de Negócios (financeiro restrito), submissão, devolução e aprovação com código PD-AAAA-NNN | [002-resultados-execucao.md](validacao/002-resultados-execucao.md) |
| 003 | Cadastros de apoio versionados, anexos com SHA-256 conferido, importação de insumos e listas controladas | [003-resultados-execucao.md](validacao/003-resultados-execucao.md) |
| 004 | Modelos de formulário versionados (versão 05 dos nove subdocumentos) e subdocumentos preenchidos a partir do modelo | [004-resultados-execucao.md](validacao/004-resultados-execucao.md) |
| 005 | Revisão e assinatura eletrônica com senha de rede, significado, data e hora do servidor e conteúdo congelado | [005-resultados-execucao.md](validacao/005-resultados-execucao.md) |
| 006 | Geração de documentos: PDF/A-2b oficial selado com código de verificação e DOCX de conferência | [006-resultados-execucao.md](validacao/006-resultados-execucao.md) |
| 007 | Estudos de desempenho e estabilidade com cálculo automático e vetores de referência | [007-resultados-execucao.md](validacao/007-resultados-execucao.md) |
| 008 | Caderno de laboratório eletrônico com assinatura do autor e da testemunha, adendos e busca | [008-resultados-execucao.md](validacao/008-resultados-execucao.md) |
| 009 | Documento completo do projeto (registro histórico) com sumário e páginas reais | [009-resultados-execucao.md](validacao/009-resultados-execucao.md) |
| 010 | Painel do gestor, linha do tempo, pendências e notificações por e-mail | [010-resultados-execucao.md](validacao/010-resultados-execucao.md) |
| 011 | Dossiê técnico para a ANVISA (estrutura I a XII), checagem por classe, PDF/A, DOCX e pacote | [011-resultados-execucao.md](validacao/011-resultados-execucao.md) |
| 012 | Integração com o Sankhya pelo API Gateway oficial, fila com reprocessamento e contingência em arquivo | [012-resultados-execucao.md](validacao/012-resultados-execucao.md) |
| 013 | Revisão controlada dos modelos de subdocumento e de layout (pedido do usuário) | [013-resultados-execucao.md](validacao/013-resultados-execucao.md) |
| 014 | Operação e validação: cópia diária e teste de restauração, IQ, OQ e revisão de acessos | [014-resultados-execucao.md](validacao/014-resultados-execucao.md) |

## Como as paradas de revisão foram tratadas

O pedido foi seguir o plano "fielmente até a conclusão". As paradas "aguarde revisão humana" do
`CLAUDE.md` e as perguntas do `/speckit-clarify` foram tratadas assim: a opção recomendada foi
adotada e registrada no `spec.md` como resposta provisória "ratificar com …"; os checklists de
requisitos (de quem revisa) ficaram sem marcação; nenhum campo de formulário, artigo de norma ou
texto regulatório foi inventado (o que faltou virou pendência). Por isso, antes do uso oficial, as
decisões abaixo precisam ser ratificadas e os checklists revisados.

## Decisões provisórias a ratificar (60)

### Garantia da Qualidade (31)

| Feature | Pergunta | Resposta provisória | Ratificar com |
| --- | --- | --- | --- |
| 001 | Quem aprova a concessão de um perfil antes de o Administrador registrá-la no sistema? | O Administrador registra a concessão com a referência da aprovação; o aprovador esperado é o Gestor de P&D para os perfis Gestor de P&D, Líder de projeto, Analista/Pesquisador e Leitor, a Garantia da Qualidade para o perfil Qualidade/AR e a gestão da TI para o perfil Administrador; o sistema registra a referência informada, sem fluxo de aprovação interno nesta feature | o Gestor de P&D e a Garantia da Qualidade |
| 001 | Por quanto tempo a trilha de auditoria e os registros desta feature devem ser mantidos? | Por tempo indeterminado: o sistema não oferece expurgo; a retenção por produto (tempo de vida do produto, nunca menos de 2 anos, RDC 665/2022, art. 37) só será aplicada quando existir procedimento aprovado de arquivamento | a Garantia da Qualidade |
| 003 | Qual é o padrão de código dos lotes piloto e de validação? | Não há padrão imposto nesta versão: código alfanumérico que pode ter hífen, barra ou ponto, sem espaços, único entre os lotes vigentes do projeto; quando a Qualidade definir o padrão, ele entra como expressão configurável | a Garantia da Qualidade |
| 003 | Quem pode cadastrar e corrigir insumos? | Analista/Pesquisador, Líder de projeto, Gestor de P&D e Qualidade/AR; Leitor e Administrador só consultam; correção de insumo bloqueado exige motivo e gera nova versão | o Gestor de P&D e a Garantia da Qualidade |
| 003 | Que atributos clínicos das amostras precisam ser guardados, considerando a LGPD? | Só identificador interno, tipo de amostra, origem (instituição ou banco, sem identificador do paciente), caracterização analítica (resultado de referência, concentração, status), condição de armazenamento e data de coleta; nenhum dado demográfico ou de identificação do paciente | a Garantia da Qualidade e o encarregado de dados |
| 003 | Certificados de análise vencidos bloqueiam o uso do insumo? | Não; o sistema registra a validade do certificado e mostra alerta de certificado vencido onde o insumo aparece, sem bloquear | a Garantia da Qualidade |
| 004 | Na Análise Crítica, vale a lista da capa (3 tópicos) ou a do projeto (4)? | O modelo versão 05 segue a capa, com 3 tópicos; um quarto tópico só entra por nova versão do modelo publicada pela Qualidade | a Garantia da Qualidade |
| 004 | O "Realizado" da Verificação Final é pré-preenchido? | Não nesta versão: o analista preenche cada linha e a tela mostra, ao lado, o acesso à Validação e à Saída do projeto; a regra de correspondência para o pré-preenchimento fica pendente de definição pela Qualidade (pendência a esclarecer). | Garantia da Qualidade (pendência a esclarecer) |
| 005 | Quais significados de assinatura são aceitos e quais são obrigatórios? | Elaborado (obrigatório; Analista Responsável, quem envia para revisão), Aprovado (obrigatório; Gestor de P&D ou delegado) e Revisado (opcional; qualquer pessoa com acesso ao projeto que não seja a elaboradora nem a aprovadora) | a Garantia da Qualidade |
| 005 | A delegação de aprovação é permitida? Para quem? | Sim, provisoriamente: o Gestor de P&D delega, com motivo, por até 30 dias, a pessoa com perfil Gestor de P&D, Líder de projeto ou Qualidade/AR; a assinatura do delegado registra "em delegação de" | a Garantia da Qualidade e o PSG 20 |
| 005 | A Qualidade assina algum documento obrigatoriamente (ex.: Saída)? | Não nesta versão; a Qualidade pode assinar "Revisado" em qualquer documento em revisão; Elaborado e Aprovado continuam os únicos obrigatórios | a Garantia da Qualidade |
| 006 | O DOCX também pode ser documento oficial ou só o PDF? | Só o PDF/A selado da versão aprovada é oficial; o DOCX é sempre cópia para conferência, sem selo nem código de verificação, com a indicação "Cópia para conferência – o documento oficial é o PDF" no rodapé quando a versão está aprovada (nas demais vale a marca d'água de rascunho) | a Garantia da Qualidade |
| 006 | O logotipo é único ou por marca (Bioclin, Quibasa)? | Único: a faixa "Bioclin · Quibasa" da planilha Capas Projeto, guardada no modelo de layout; trocar o logotipo é publicar nova versão do modelo de layout; logotipo por marca exigiria a marca no cadastro do produto, que não existe | a Garantia da Qualidade |
| 006 | A paginação é "Página N" ou "Página N de M"? | "Página N de M" em todas as páginas de todos os documentos gerados, também nos tipos em que a planilha usa "Página N" (Entrada, Formulação e Lote Piloto), porque o total revela página faltando | a Garantia da Qualidade |
| 006 | Subdocumentos isolados levam sumário? | Não; a capa já lista os tópicos em "ESTE RELATÓRIO DEVE CONTER:", e o sumário fica só no documento completo do projeto (feature 009) | a Garantia da Qualidade |
| 006 | O TAP e o Plano de Negócios, que já têm versões e assinaturas (feature 005), também geram documento? | Sim, em DOCX e PDF, com modelo de layout próprio de cada um no mesmo padrão visual (faixa do logotipo, título "Termo de Abertura de Projeto" ou "Plano de Negócios", nome do produto, versão, bloco de assinaturas com os significados Elaborado e Aprovado da feature 005) e rodapé com a paginação; sem "Formulário Versão" e "Referência" enquanto a Qualidade não definir formulário e referência para eles (o modelo de layout tem texto de rodapé configurável, vazio por padrão); o documento do Plano de Negócios só é gerado e baixado por quem vê dados financeiros | o Gestor de P&D e a Garantia da Qualidade |
| 007 | Truncar ou arredondar, e com quantas casas, por tipo de resultado? | Arredondar "meio para o par" (a regra da ABNT NBR 5891; conferir o texto vigente), aplicado só na exibição e nos documentos, sobre o valor completo; casas padrão: 2 para média, desvio-padrão, diferenças, CV% e percentuais (sensibilidade, especificidade, concordância, detecção, desvio percentual e IC), 4 para R², correlação, inclinação e intercepto; regra e casas configuráveis por estudo (truncar, meio para cima ou meio para o par) e registradas junto do resultado | a Garantia da Qualidade |
| 007 | Qual o método do IC 95% para proporções? | Exato de Clopper-Pearson, como na proposta de docs/contexto/05-vocabularios.md; Wilson disponível como opção do estudo | a Garantia da Qualidade |
| 007 | Quais estudos são obrigatórios por tecnologia? | Nenhuma obrigatoriedade fixa nesta feature: os estudos exigidos continuam sendo os requisitos de desempenho marcados "aplica" na Entrada, que viram pendências na Validação (feature 004); a lista por tecnologia fica para a Qualidade definir | a Garantia da Qualidade e o Gestor de P&D |
| 007 | Quem fornece e aprova os vetores de referência dos testes de cálculo? | A Garantia da Qualidade aprova a lista de docs/contexto/06-casos-de-teste.md (V1 a V8) como evidência da validação; vetores novos entram por mudança controlada da lista | a Garantia da Qualidade |
| 008 | Quem mantém os modelos de entrada e eles passam pela revisão controlada da feature 013? | Qualidade/AR e Gestor de P&D mantêm os modelos; como são só textos de partida (a entrada copia o texto ao nascer e o registro é a entrada assinada), cada alteração gera nova versão sem o ciclo de aprovação da 013 | a Garantia da Qualidade |
| 009 | Qual a ordem oficial das partes? | A ordem da história 1: capa geral, sumário, pendências (só no rascunho), TAP, Plano de Negócios, subdocumentos na ordem do fluxo do PSG 20 (Entrada, Formulação, Lote Piloto, RAPD, Análise Crítica, Validação), Alterações de Projeto em ordem cronológica, Verificação Final, Saída, quadro de versões, resumo da trilha, histórico do caderno e lista de anexos; a variante observada no projeto DBS (Alteração logo após a capa da Entrada) fica registrada para a decisão | a Garantia da Qualidade |
| 009 | Qual o formato do resumo da trilha de auditoria? | Período coberto, contagem de eventos por tipo e a lista dos eventos-chave (assinaturas, aprovações, devoluções, novas versões, alterações de projeto e documentos oficiais gerados) com data e hora, pessoa e registro; a lista completa continua na exportação da trilha (feature 001) | a Garantia da Qualidade |
| 013 | Quais perfis elaboram e quais aprovam revisões de modelos? | Qualidade/AR elabora (abre, altera, envia e descarta); o Gestor de P&D, dono do processo PSG 20, aprova ou devolve; Administrador do sistema não elabora nem aprova; os demais perfis só consultam | a Garantia da Qualidade e o Gestor de P&D |
| 013 | A aprovação exige assinatura de quem elaborou também? | Não; o envio da elaboradora fica registrado na trilha com a sessão autenticada, e só a aprovação exige assinatura eletrônica com reautenticação e significado "aprovado" | a Garantia da Qualidade |
| 013 | A vigência pode ser futura? | Sim; na aprovação, o aprovador escolhe vigência imediata (padrão) ou uma data futura; até a data, a versão aprovada aguarda vigência e novos documentos continuam na anterior | a Garantia da Qualidade |
| 013 | Como um modelo é retirado de uso? | Qualidade/AR pede a retirada com motivo e o Gestor de P&D a aprova com assinatura eletrônica, como numa revisão; o modelo retirado continua consultável e não é oferecido a novos documentos | a Garantia da Qualidade |
| 013 | Um modelo de layout (de subdocumentos, TAP ou Plano de Negócios) pode ser retirado de uso? | Não: todo documento precisa de um layout para ser gerado, então o layout de um tipo de documento só muda por nova versão; a retirada de uso vale para os modelos de subdocumento | a Garantia da Qualidade |
| 014 | Por quanto tempo ficam as cópias diárias e as mensais? | As diárias por 35 dias; a primeira cópia bem-sucedida de cada mês fica sem remoção automática | a TI e a Garantia da Qualidade |
| 014 | O sistema cifra as cópias ou o controle de acesso do destino protege o conteúdo? | O sistema não cifra; o destino tem acesso restrito à TI e cifragem do armazenamento feita pela infraestrutura | a TI e a Garantia da Qualidade |
| 014 | Quem executa as qualificações de instalação e de operação, e por onde? | A de instalação só a TI, pela linha de comando no servidor ou pela tela de operação; a de operação a TI (linha de comando ou tela) e a Garantia da Qualidade (tela) | a TI e a Garantia da Qualidade |

### Gestor de P&D (19)

| Feature | Pergunta | Resposta provisória | Ratificar com |
| --- | --- | --- | --- |
| 001 | Consultores externos sem conta na rede precisam acessar o sistema? | Não; quem precisar de acesso recebe da TI uma conta de rede temporária e entra pelo login de rede, sem contas locais no sistema | a TI e o Gestor de P&D |
| 002 | Quais campos o TAP deve ter, já que o pedido original não os lista? | Os da proposta de `docs/contexto/02-dicionario-documentos.md`: produto (nome, família, tecnologia, órgão regulador, classe de risco e regra), justificativa, objetivo, escopo incluído e excluído, entregas, premissas, restrições, riscos iniciais (risco, impacto, resposta), partes interessadas (nome/área, interesse), equipe (pessoa, papel) e marcos (subdocumento, data prevista, data realizada); código gerado na aprovação | o Gestor de P&D |
| 002 | Qual é o formato do código do projeto? | PD-AAAA-NNN, com o ano da aprovação e sequência de 3 dígitos que recomeça a cada ano (ex.: PD-2026-001), configurável no prefixo | o Gestor de P&D |
| 002 | O "retorno esperado" é receita, margem ou lucro, e precisa de indicador como payback? | Receita líquida prevista de cada ano, em R$, com o total calculado; nenhum indicador adicional (payback) nesta versão | o Gestor de P&D |
| 002 | Projetos acima de certo custo exigem aprovação da diretoria? | Não nesta versão; o Gestor de P&D aprova todos os projetos, e uma alçada por custo vira nova feature se for exigida | o Gestor de P&D |
| 002 | Quem além do Gestor de P&D e do líder do projeto vê os dados financeiros? | Ninguém por padrão; a lista de perfis autorizados é uma configuração da implantação | o Gestor de P&D |
| 004 | A ordem dos subdocumentos é obrigatória ou só recomendada? | Recomendada: criar um subdocumento com o antecessor ainda não aprovado mostra aviso e só segue com autorização registrada do Gestor de P&D, com motivo | o Gestor de P&D |
| 004 | Como tratar a edição simultânea do mesmo documento por dois analistas? | Controle otimista: os dois podem abrir; a segunda gravação feita sobre a versão desatualizada é recusada com aviso para recarregar, sem bloqueio exclusivo | o Gestor de P&D |
| 005 | Qual o prazo máximo de revisão antes do alerta? | 5 dias corridos, configurável; o documento aparece como atrasado na fila de revisão e o e-mail vem na feature 010 | o Gestor de P&D |
| 007 | Quais formatos de arquivo de equipamento precisam de importação? | CSV (separador ponto e vírgula ou vírgula) e XLSX, com mapeamento de colunas salvo por equipamento; formatos próprios de equipamento entram quando P&D fornecer arquivos de exemplo (dependência registrada) | o Gestor de P&D |
| 008 | Qual o prazo para assinar uma entrada? | 7 dias corridos depois da criação, configurável; depois disso a entrada aparece como atrasada (o e-mail vem na feature 010) | o Gestor de P&D |
| 008 | Quando a testemunha é obrigatória? | Quando o autor marca a entrada como relevante para propriedade intelectual ou para uma decisão do projeto; o Gestor de P&D também pode marcar; a testemunha é qualquer pessoa com acesso ao projeto, diferente do autor | o Gestor de P&D e o Jurídico |
| 008 | Existem entradas fora de projeto (pesquisa exploratória)? | Não nesta versão: toda entrada pertence a um projeto; pesquisa exploratória usa um projeto aberto para esse fim | o Gestor de P&D |
| 009 | O Plano de Negócios entra no documento completo ou fica num anexo restrito? | Entra no documento; os campos financeiros só aparecem quando quem gera tem permissão de dados financeiros; sem permissão, o Plano de Negócios sai sem esses campos, com a observação de acesso restrito, e o documento arquivado registra se contém dados financeiros; o documento com dados financeiros só é baixado por quem tem essa permissão | o Gestor de P&D |
| 010 | Quais indicadores o gestor quer na primeira tela? | Quatro totais no topo (projetos abertos por etapa, projetos com marco vencido não realizado, documentos aguardando a revisão ou assinatura do gestor com a espera mais longa em dias e entradas do caderno atrasadas) e, abaixo, a carteira da história 1 | o Gestor de P&D |
| 010 | E-mail imediato ou resumo diário? | Devolução e aprovação de documento: e-mail imediato; prazos vencidos (documento em revisão além do prazo de revisão, entrada do caderno aberta além do prazo de assinatura e testemunha pendente além do mesmo prazo): resumo diário às 7h, um e-mail por pessoa com tudo o que venceu | o Gestor de P&D |
| 010 | Haverá custo realizado (vindo do Sankhya) para comparar com o planejado? | Não nesta versão: o painel mostra o custo planejado e o retorno esperado do Plano de Negócios a quem tem permissão; o custo realizado depende de uma consulta do API Gateway do Sankhya ainda não definida e fica registrado como dependência | o Gestor de P&D e a TI |
| 012 | A nova matéria-prima é cadastrada direto ou entra como solicitação para o cadastro? | Entra como solicitação de cadastro (registro "Insumo novo" com situação "solicitado"); o cadastro no Sankhya continua com a equipe responsável | o Gestor de P&D, a Produção e a TI |
| 013 | TAP e Plano de Negócios passam a ter modelo de formulário revisável? | Não nesta feature: os campos do TAP e do Plano de Negócios continuam os da feature 002; só os modelos de layout deles (capa, cabeçalho, rodapé, estilos) entram na revisão controlada | o Gestor de P&D |

### TI (6)

| Feature | Pergunta | Resposta provisória | Ratificar com |
| --- | --- | --- | --- |
| 001 | Quais valores a política da TI define para o tempo de inatividade da sessão, o número de tentativas inválidas seguidas e o período de bloqueio? | 30 minutos de inatividade, bloqueio após 5 tentativas inválidas seguidas e bloqueio de 15 minutos, todos configuráveis na implantação | a TI |
| 005 | Por quanto tempo a assinatura fica bloqueada depois de três falhas? | 15 minutos, configurável, como o bloqueio de login da feature 001 | a TI |
| 008 | Tamanho máximo de anexos e tipos aceitos? | O mesmo limite configurável da feature 003 (20 MB) e os tipos PDF, PNG, JPEG, CSV e XLSX (fotos, laudos e arquivos exportados de equipamento) | a TI |
| 012 | Quais tabelas adicionais e campos a consultoria vai criar no Sankhya? | Ainda não definidos; o sistema monta os registros do modelo lógico do contexto (Projeto P&D, Documento P&D, Lote P&D, Insumo novo, Resultado de estudo) e um mapeamento configurável, mantido pela TI, liga cada registro à entidade e aos campos do Sankhya; sem mapeamento, as mensagens ficam "aguardando configuração" e a exportação em arquivo funciona | a TI e a consultoria Sankhya |
| 012 | Envio imediato na aprovação ou lote noturno? | Imediato, logo depois da aprovação, com novas tentativas automáticas em espera crescente e reprocessamento manual pela TI | a TI |
| 014 | Onde as cópias são gravadas, separadas dos dados do sistema? | Num diretório definido pela TI e montado de outro servidor ou compartilhamento da rede da empresa, nunca no disco dos dados; a segunda cópia fora do prédio é procedimento da TI sobre esse destino | a TI |

### Assuntos Regulatórios (4)

| Feature | Pergunta | Resposta provisória | Ratificar com |
| --- | --- | --- | --- |
| 004 | O tópico 9 da Entrada, que repete o rótulo do tópico 6 ("Classificação de Uso"), é a classe de risco da RDC 830/2023? | Sim; no modelo versão 05 do sistema o tópico 9 passa a se chamar "Classificação de Risco (RDC 830/2023)", com a classe (I a IV) e a regra de classificação; a linha 9 da Verificação Final acompanha | Assuntos Regulatórios e a Garantia da Qualidade |
| 011 | A estrutura final foi conferida contra o Manual para Regularização de Dispositivos para Diagnóstico in Vitro (ANVISA, 25/08/2026)? | Ainda não; adota-se a estrutura I a XII do contexto (alinhada ao art. 58 e ao Anexo II), guardada numa definição declarativa que a Qualidade/AR ajusta sem programação; a conferência contra o Manual fica pendente com Assuntos Regulatórios antes do primeiro envio | Assuntos Regulatórios |
| 011 | Os anexos (rótulos, instrução de uso, gerenciamento de risco, imagens) são incorporados ao documento ou enviados como PDFs separados? | Seguem como arquivos separados num pacote junto com o dossiê; o dossiê traz a lista de anexos (número, nome, origem e resumo criptográfico) e cada item cita o anexo correspondente | Assuntos Regulatórios |
| 011 | Como o responsável técnico e legal assina? | O sistema gera a declaração com os dados do responsável e o bloco de assinatura; a assinatura é feita fora do sistema (certificado ICP-Brasil no PDF ou na plataforma de peticionamento) e, no registro do envio, Assuntos Regulatórios anexa o PDF assinado, arquivado com resumo criptográfico | Assuntos Regulatórios e o Jurídico |

Além das respostas do esclarecimento: a constituição está na versão 1.0.0 com a data de
ratificação em aberto (`TODO(RATIFICATION_DATE)` em `.specify/memory/constitution.md`) — Gestor de
P&D e Garantia da Qualidade.

## Dependências de terceiros

### TI

- Validar as premissas do plano (stack, servidor, AD) e prover os servidores de homologação e produção com Docker.
- AD real: conta de serviço, LDAPS e CA da empresa (`LDAP_*`); login em homologação é o critério de pronto da 001 (SC-001 manual).
- Certificado TLS do Nginx emitido pela CA interna para o nome do servidor.
- Certificado da empresa para o selo dos PDFs oficiais (tipo, emissor, guarda): PKCS#12 fora do repositório em `DOCUMENT_SEAL_PKCS12` e `DOCUMENT_SEAL_PASSWORD`.
- SMTP interno (`EMAIL_*`, `DEFAULT_FROM_EMAIL`) e `SITE_URL` da intranet, para notificações e avisos de cópia.
- Destino das cópias de segurança em outro servidor ou compartilhamento (`BACKUP_HOST_DIR`), cópia fora do prédio e acesso restrito; imagem construída com `SGP_COMMIT`.
- Executar a IQ em homologação e produção (`docs/validacao/iq-roteiro.md`).

### Consultoria Sankhya e TI

- Ambiente de testes da Sankhya, `client_id`, `client_secret` e `X-Token` (homologação e produção) e usuário de integração com permissões mínimas.
- Criação das tabelas adicionais e definição das entidades, campos e chaves de cada registro (projeto, documento, lote, insumo novo, resultado de estudo) e da entidade de produtos; a TI publica o mapeamento na tela de integração.
- Confirmar o corpo das chamadas `CRUDServiceProvider.saveRecord` e `loadRecords` (provisório) e conferir a consulta de um insumo real (012:SC-002).
- Custo realizado vindo do Sankhya para o painel (fora desta versão; depende de consulta do API Gateway a definir).

### Garantia da Qualidade

- Plano de validação, relatório de validação e liberação; ratificação da constituição.
- Procedimento (PSG 20 ou POP do sistema) que declara a equivalência da assinatura eletrônica à manuscrita, perfis, backup e contingência.
- Revisar os checklists de requisitos e aprovar as referências de regressão visual e os vetores de referência V1 a V8 dos cálculos.
- Executar a OQ (incluindo os roteiros manuais de assinatura, auditoria e geração) e as verificações manuais pendentes em homologação.
- Regra de pré-preenchimento do "Realizado" da Verificação Final (pendência a esclarecer da 004) e estudos obrigatórios por tecnologia (007).
- Decidir sobre a aprovação retroativa das versões de modelo publicadas antes da 013 e sobre o tratamento, como incidente, de arquivo guardado ou trilha com divergência.

### Assuntos Regulatórios e Jurídico

- Conferir a estrutura I a XII do dossiê contra o Manual para Regularização de Dispositivos para Diagnóstico in Vitro (ANVISA), incluindo as letras atribuídas pelo sistema, a aplicabilidade por classe e a regra de família.
- Assinatura do responsável técnico e legal do dossiê fora do sistema (ICP-Brasil ou plataforma de peticionamento).
- Regras da testemunha no caderno de laboratório (Gestor de P&D e Jurídico) e dados mínimos das amostras (com o encarregado de dados, LGPD).

### Gestor de P&D e P&D

- Ratificar as decisões de processo listadas acima (TAP, ordem do fluxo, prazos, painel, notificações).
- Escolher o projeto piloto para a qualificação de desempenho (PQ) e conduzir o piloto em paralelo.
- Fornecer arquivos de exemplo dos equipamentos para os formatos próprios de importação de estudos.

### Materiais de referência ausentes

- Os `.docx` originais citados em `docs/modelos/LEIA-ME.md` (dossiês e documentos de projeto) não estão no repositório; a comparação de fidelidade com os originais fica para quando forem disponibilizados (hoje a referência é `docs/contexto/03-padroes-formatacao.md` e a planilha Capas Projeto, só como estrutura e layout).

## Verificações manuais pendentes (8)

Requisitos sem teste automatizado possível no desenvolvimento, registrados em
[docs/validacao/verificacoes-manuais.json](validacao/verificacoes-manuais.json):

| Requisito | Verificação |
| --- | --- |
| 001:SC-001 | Medição do tempo de login com o AD real na homologação (roteiro de OQ; quickstart da feature 001). |
| 006:SC-001 | Comparação da capa gerada da Entrada de Projeto com a planilha Capas Projeto pela Garantia da Qualidade (pendente de ratificação; evidência em docs/validacao/006-resultados-execucao.md). |
| 006:SC-006 | Validação PDF/A-2b do PDF oficial selado no veraPDF (contêiner verapdf/cli; quickstart da feature 006 e docs/validacao/006-resultados-execucao.md); os testes conferem os marcadores estruturais. |
| 009:SC-004 | Aprovação, pela Garantia da Qualidade, do documento completo de um projeto piloto gerado na homologação (ordem das partes, sumário, quadro de versões, resumo da trilha e caderno); evidência do rascunho e do oficial gerados nos testes e na pilha real em docs/validacao/009-resultados-execucao.md. |
| 011:SC-004 | Conferência, por Assuntos Regulatórios, do dossiê de um produto real gerado na homologação, sem retrabalho de estrutura, e da estrutura I a XII contra o Manual de Regularização de IVD da ANVISA (25/08/2026); evidência dos testes e do roteiro em docs/validacao/011-resultados-execucao.md. |
| 012:SC-002 | Consulta de um insumo real pelo código no ambiente de testes da Sankhya (homologação), depois de a TI preencher o mapeamento com a consultoria e as credenciais SANKHYA_*; evidência a registrar em docs/validacao/012-resultados-execucao.md. |
| 013:SC-005 | Ciclo completo (abrir revisão, alterar um rótulo, enviar, aprovar e publicar) cronometrado na pilha real por quem conhece a tela (docs/validacao/013-resultados-execucao.md); repetir na homologação. |
| 014:SC-004 | IQ e OQ executadas no servidor de homologação, com os relatórios guardados no painel Operação e validação e os roteiros docs/validacao/iq-roteiro.md e docs/validacao/oq-roteiro.md executados e assinados pela Garantia da Qualidade. |

## Checklists de requisitos aguardando revisão (24 checklists, 290 itens)

| Feature | Checklist | Revisados | Público |
| --- | --- | --- | --- |
| 001 | `integridade-dados.md` | 0/23 | Garantia da Qualidade (revisão antes do `/speckit-implement`) |
| 001 | `seguranca.md` | 0/29 | revisor (TI e Garantia da Qualidade) antes do `/speckit-implement` |
| 002 | `permissoes-financeiras.md` | 0/14 | Gestor de P&D (revisão antes do `/speckit-implement`) |
| 003 | `integridade-lgpd.md` | 0/12 | Garantia da Qualidade e encarregado de dados |
| 004 | `regulatorio.md` | 0/12 | Garantia da Qualidade e Assuntos Regulatórios |
| 004 | `usabilidade.md` | 0/10 | analistas, líderes e Garantia da Qualidade |
| 005 | `assinatura.md` | 0/8 | Garantia da Qualidade e Jurídico |
| 005 | `integridade.md` | 0/7 | Garantia da Qualidade e Jurídico |
| 006 | `fidelidade-layout.md` | 0/14 | Garantia da Qualidade e Gestor de P&D |
| 006 | `regulatorio.md` | 0/15 | Garantia da Qualidade, Jurídico e TI |
| 007 | `estatistica.md` | 0/8 | Garantia da Qualidade e P&D |
| 007 | `regulatorio.md` | 0/8 | Garantia da Qualidade e Assuntos Regulatórios |
| 008 | `integridade-alcoa.md` | 0/14 | Garantia da Qualidade |
| 008 | `usabilidade-bancada.md` | 0/10 | pesquisadores do grupo piloto e Gestor de P&D |
| 009 | `desempenho.md` | 0/6 | TI e Gestor de P&D |
| 009 | `regulatorio.md` | 0/10 | Garantia da Qualidade e Assuntos Regulatórios |
| 010 | `permissoes.md` | 0/7 | TI, Garantia da Qualidade e Gestor de P&D |
| 010 | `usabilidade.md` | 0/7 | Gestor de P&D, líderes e analistas |
| 011 | `regulatorio.md` | 0/10 | Assuntos Regulatórios e Garantia da Qualidade |
| 012 | `integridade-idempotencia.md` | 0/6 | TI e Garantia da Qualidade |
| 012 | `seguranca-credenciais.md` | 0/6 | TI e segurança da informação |
| 013 | `controle-mudancas.md` | 0/12 | Garantia da Qualidade e Gestor de P&D |
| 014 | `evidencias-validacao.md` | 0/20 | Garantia da Qualidade e TI |
| 014 | `recuperacao-integridade.md` | 0/22 | TI e Garantia da Qualidade |

## Observações sobre o ambiente de desenvolvimento

- Os dados do banco de desenvolvimento são fictícios e incluem adulterações feitas de propósito pelos roteiros: o evento 3 da trilha (roteiro da 001) continua alterado e por isso a verificação da trilha, o teste de restauração (C5) e a OQ (OQ-01, OQ-09) reprovam no desenvolvimento — comportamento correto; a trilha nunca é alterada por fora do sistema.
- O arquivo `cert.pdf` adulterado no roteiro da 003 (10 bytes acrescentados) foi reparado no roteiro da 014 truncando-o para o tamanho registrado, o que devolveu exatamente o SHA-256 registrado.
- A homologação deve começar com banco novo (só dados fictícios), conforme o plano.
- O ambiente de desenvolvimento não é qualificado: a IQ reprova itens como depuração ligada, e-mail em arquivo e estáticos não coletados.

## Próximos passos (plano, "Implantação")

1. Ratificar as decisões provisórias e a constituição; revisar os checklists (Gestor de P&D, TI, Garantia da Qualidade).
2. Montar a homologação espelhando a produção, só com dados fictícios; executar IQ e OQ pelos roteiros.
3. Treinamento por perfil: analistas, líderes, gestor e Qualidade.
4. Piloto em paralelo (PQ) com um projeto real durante um ciclo completo de subdocumentos; ajustes viram novas especificações.
5. Atualizar o PSG 20 e criar o POP do sistema (perfis, assinatura eletrônica, backup e contingência).
6. Entrada em produção: projetos novos só no sistema.
7. Operação: cópia diária com teste de restauração mensal (automáticos), revisão trimestral de acessos e revalidação periódica.
