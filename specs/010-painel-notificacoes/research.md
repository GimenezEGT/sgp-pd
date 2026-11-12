# Research: Painel do gestor e notificações

## R1. Indicadores calculados por consultas agregadas com cache

- **Decision**: `sgp/dashboard/portfolio.py` monta a carteira com poucas consultas agregadas
  (projetos acessíveis, versões aprovadas por tipo, marcos ativos, pedidos de revisão), sem laço de
  consulta por projeto; o resultado por pessoa fica no cache do Django (Redis) por 5 minutos, com a
  chave invalidada quando a pessoa pede atualização. Índices dedicados nas colunas usadas nos
  filtros (marcos por projeto e data planejada; versões aprovadas por tipo e objeto).
- **Rationale**: atende 100 projetos em < 2 s (SC-001) sem tabelas de agregação.

## R2. Etapa atual, percentual e atraso

- **Decision**: etapa atual = primeiro tipo do fluxo do PSG 20 sem versão aprovada (ou "Concluído"
  com a Saída aprovada; para projetos não abertos, a situação do projeto); percentual = tipos do
  fluxo com versão aprovada ÷ 8; marcos planejados × realizados = marcos ativos com data realizada ÷
  marcos ativos; atraso em dias = maior atraso entre marcos vencidos não realizados (hoje − data
  planejada) e marcos realizados depois da data planejada.

## R3. Gráficos em SVG no servidor

- **Decision**: barras horizontais de percentual e de marcos geradas como SVG inline por template
  (sem JavaScript, sem build de front-end); cores e textos acessíveis (título e rótulo em texto).

## R4. Notificações

- **Decision**: modelo `Notification` (pessoa, tipo, registro, assunto, corpo, situação, tentativas)
  criado por sinal dos eventos de negócio (devolução, aprovação) e pela rotina diária de prazos
  (documentos parados em revisão além de `REVIEW_ALERT_DAYS`, entradas do caderno abertas além de
  `NOTEBOOK_SIGN_DAYS`, testemunha pendente); envio pelo `django.core.mail` com o SMTP interno
  (variáveis de ambiente), em tarefa Celery com novas tentativas; preferências por pessoa e tipo,
  com "assinatura pendente" sempre ligada.

## R5. Exportação

- **Decision**: XLSX com openpyxl (já dependência), mesmas colunas e permissões do painel, evento
  `dashboard.exported` na trilha.

## R6. Linha do tempo pela trilha

- **Decision**: a linha do tempo do projeto lê os eventos da trilha com o projeto (marcos,
  subdocumentos e versões, assinaturas, alterações, caderno, estudos e documentos gerados), do mais
  recente para o mais antigo, com filtro por categoria e paginação; mostra data e hora, pessoa,
  evento e registro, sem valores anteriores e novos (nenhum dado financeiro aparece); os marcos
  planejados ainda não realizados aparecem no topo.
- **Rationale**: a trilha já é a fonte única e imutável do que aconteceu.

## R7. Destinatários

- **Decision**: devolução de documento: quem assinou como elaborador a versão (ou quem criou o
  subdocumento; o líder no TAP e no Plano); aprovação: o elaborador e o líder do projeto; resumo
  diário: o Gestor de P&D e quem tem delegação ativa (documentos em revisão além de
  `REVIEW_ALERT_DAYS`), o elaborador desses documentos (documento parado), o autor das entradas
  abertas além de `NOTEBOOK_SIGN_DAYS` e o líder do projeto das entradas relevantes aguardando
  testemunha além do mesmo prazo. Pessoa sem e-mail: a notificação fica "omitida" com o motivo.

## R8. Envio e preferências

- **Decision**: tipos `returned` (devolução), `approved` (aprovação), `stalled` (documento parado
  na revisão) e `pending_signature` (assinatura pendente: aprovação do gestor, assinatura do autor
  no caderno e testemunha); só os três primeiros podem ser desligados. A notificação é criada na
  mesma transação do evento (sinal da trilha) e o envio vai para a fila depois do commit; o worker
  tenta até 3 vezes; o resumo diário roda pelo Celery beat às `NOTIFICATION_DIGEST_HOUR` (7h) e
  usa uma chave por pessoa e dia para não repetir. SMTP por `EMAIL_*`; no desenvolvimento, arquivo
  em `var/emails` (`EMAIL_BACKEND` de arquivo).
