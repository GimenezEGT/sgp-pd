# Feature 010 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-11, dados fictícios. Senhas do LDAP de desenvolvimento. No
desenvolvimento os e-mails vão para arquivos em `var/emails` (backend de arquivo do Django).

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.122 aprovados (todas as features até a 010 e a 013), 0 falhas; cobertura `sgp/core` 93,5% e `sgp/audit` 97,1%. Depois do gate, o documento completo ganhou um nome legível na trilha (sem mudança de dados); as pastas `tests/fulldoc`, `tests/dashboard` e `tests/notifications` foram rodadas de novo |
| Testes da feature (`tests/dashboard`, `tests/notifications`) | 15 aprovados |
| Matriz de rastreabilidade | 260 requisitos, 0 sem cobertura |
| SC-001 desempenho | carteira de 100 projetos (com marcos) montada em menos de 2 s, sem cache |
| SC-002 resumo diário | no dia do prazo nada é enviado; no dia seguinte, assinatura pendente para o gestor e documento parado para a elaboradora; o mesmo resumo não se repete no dia |
| SC-003 dados financeiros | custo e retorno só para quem tem a permissão, na tela e na planilha |
| E-mail imediato | devolução com o comentário para a elaboradora; aprovação para elaboradora e líder; preferência desligada omite com o motivo; assinatura pendente não desliga |
| Falhas | pessoa sem e-mail: omitida com o motivo; SMTP fora do ar: 3 tentativas e situação "falhou" com o erro, evento na trilha |

## Roteiro do quickstart na pilha real

| Cenário | Resultado |
| --- | --- |
| `gestor.pd` abre o painel (sem cache): 200 em 244 ms; totais "2 projetos abertos (Elaboração de Lote Piloto 1; Entrada de Projeto 1)", 0 com marco vencido, 0 aguardando, 0 entradas atrasadas | aprovado |
| Linha do PD-2026-001: etapa "Elaboração de Lote Piloto", 25% (2 de 8), marcos 0/1, em dia, custo e retorno do Plano de Negócios | aprovado |
| `ana.analista`: 1 projeto, sem as colunas de custo e retorno | aprovado |
| Exportação: planilha do gestor com 2 projetos e custo planejado; da analista com 1 projeto e sem custo; 2 eventos `dashboard.exported` | aprovado |
| Linha do tempo do PD-2026-001: eventos do mais recente para o mais antigo (documentos completos, caderno, promoção para estudo); filtro "Caderno de laboratório" | aprovado |
| `ana.analista` desliga "Documento aprovado" (evento `notifications.preference_changed`) | aprovado |
| Devolução de um subdocumento pelo gestor (serviço da 005 no contêiner): o worker enviou o e-mail imediato para ana.analista@sgp.dev.local com o comentário; notificação "enviada" | aprovado |
| Resumo diário simulado para daqui a 10 dias, com o RAPD em revisão e uma entrada do caderno aberta: resumo para gestor.pd (assinatura pendente) e para ana.analista (documento parado e entrada a assinar), enviados pelo worker; corpo em UTF-8 com acentos, travessão e endereço da tela | aprovado |
| "Minhas pendências": ana.analista com o documento devolvido; gestor.pd sem pendências antes do resumo | aprovado |

Ajuste feito depois do roteiro: o documento completo da 009 aparecia como "FullDocument object
(n)" na linha do tempo; agora tem nome legível (os eventos antigos guardam o texto da época, a
trilha não muda).

## Convergência (`/speckit-converge`)

Converged: FR-001 a FR-009 e SC-001 a SC-003 implementados e cobertos por testes
(`req("010:…")`); tarefas T001 a T010 concluídas; nenhuma tarefa nova.

## Pendências a ratificar e dependências

- Indicadores da primeira tela (quatro totais e carteira) — Gestor de P&D.
- E-mail imediato para devolução e aprovação e resumo diário às 7h — Gestor de P&D.
- Custo realizado vindo do Sankhya: fora desta versão; depende de consulta do API Gateway ainda não
  definida (TI e Gestor de P&D).
- SMTP interno: endereço, porta e conta de envio a fornecer pela TI (`EMAIL_*`), e `SITE_URL` da
  intranet; medir o painel com 100 projetos na homologação.
