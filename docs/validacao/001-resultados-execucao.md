# Feature 001 — resultados de execução (evidência)

Ambiente: desenvolvimento (Docker Desktop 29.1.3, PostgreSQL 17, Redis 7.4, OpenLDAP fictício),
2026-11-07. Os dados do diretório e do banco são fictícios.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 220 aprovados, 0 falhas (2 testes de desempenho executados à parte) |
| Cobertura total | 95% |
| Cobertura `sgp/core` / `sgp/audit` | 92,0% / 97,4% (mínimo 90%) |
| Lint (`ruff check`) | sem apontamentos |
| Matriz de rastreabilidade | 34 requisitos, 0 sem cobertura (SC-001 com verificação manual na homologação) |

## Desempenho (`pytest -m slow`)

| Critério | Medição | Meta |
| --- | --- | --- |
| SC-007 verificação da cadeia | 200 mil eventos em 2,4 s (≈ 12 s para 1 milhão) | < 15 min para 1 milhão |
| SC-005 consulta + exportação de um mês | 0,8 s com 200 mil eventos na base | < 1 min com 500 mil |

## Roteiro do quickstart na pilha real (Nginx HTTPS → Django → OpenLDAP → PostgreSQL → Celery)

| Cenário | Resultado |
| --- | --- |
| `admin.ti` entra com a conta do diretório e vê o início com a administração | aprovado |
| `sem.perfil` entra, é levado a "Solicitar acesso", é recusado no início e registra solicitação | aprovado |
| `ex.colaborador` (conta desativada) recebe a mensagem genérica | aprovado |
| `ana.analista` recebe o perfil Analista pelo grupo da rede e entra no início | aprovado |
| `leitor.consulta`: 5 senhas erradas bloqueiam; a 6ª tentativa, com a senha certa, é recusada | aprovado |
| Verificação sob demanda executada pelo worker Celery: "Íntegra" | aprovado |
| Alteração direta do evento 3 no banco: `verify_audit_chain` aponta `content_altered` no evento 3 e sai com código 1 | aprovado |
| Papel `sgp_app`: DELETE e UPDATE na trilha e DELETE em `accounts_user` recusados (`permission denied`) | aprovado |
| HTTP (porta 8080) redireciona para HTTPS (8443); `/saude/` responde 200 | aprovado |

## Pendências que dependem de terceiros

- Login com o AD real da empresa em homologação (critério de pronto) e medição do SC-001: depende
  da TI (conta de serviço, LDAPS e CA da empresa).
- Os valores de inatividade, tentativas e bloqueio e as demais decisões do clarify aguardam
  ratificação (TI, Gestor de P&D e Garantia da Qualidade).
- Certificado do Nginx: o de desenvolvimento é autoassinado; homologação e produção usam o
  certificado da CA interna.
