# Feature 003 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-07, dados fictícios.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 558 aprovados (todas as features até a 003, com a convergência), 0 falhas |
| Cobertura `sgp/core` / `sgp/audit` | 93,5% / 97,1% |
| Matriz de rastreabilidade | 84 requisitos (001 a 003), 0 sem cobertura |
| SC-002 importação de 500 linhas | 480 criadas e 20 rejeitadas, bem abaixo de 30 s |
| SC-004 busca com 10 mil insumos | abaixo de 1 s |

## Roteiro do quickstart na pilha real (Nginx HTTPS → Django → OpenLDAP → PostgreSQL)

| Cenário | Resultado |
| --- | --- |
| `ana.analista` (equipe do projeto `PD-2026-001`) cadastra o lote `LP-SMK-01`; exibição "Lote LP-SMK-01 – Fabricação: 09/2026 – Validade: 09/2027" | aprovado |
| Validade anterior à fabricação e código repetido no projeto recusados com mensagem | aprovado |
| `leitor.consulta` (sem acesso ao projeto) recebe 403 no detalhe do lote e no cadastro de insumo | aprovado |
| Lote bloqueado como na assinatura: sem motivo recusado; mudança de código recusada; com motivo nasce a versão 02 | aprovado |
| Versão 01 continua com "Validade: 09/2027" e aponta para a vigente; versão 02 mostra "Validade: 12/2027" e o motivo | aprovado |
| Planilha modelo com o cabeçalho do contrato | aprovado |
| Importação de 500 linhas (480 válidas, 10 repetidas, 10 com tipo inválido): pré-visualização sem gravar, confirmação com 480 criados e relatório com 20 rejeições, em 1,7 s (envio e confirmação) | aprovado |
| Insumo com certificado PDF vencido: alerta "Certificado vencido" para o Leitor; download com SHA-256 igual ao do arquivo enviado | aprovado |
| Arquivo alterado direto no volume de armazenamento: download recusado (409) e evento "Arquivo com resumo divergente" na trilha | aprovado |
| Amostra com "Maria Silva" como identificador e com "paciente João, CPF 123.456.789-00" na caracterização: recusadas; amostra com código interno aceita | aprovado |
| `qualidade.ar` inclui "Swab nasal" e desativa "Líquor": a lista vai da versão 1 para a 3; "Líquor" sai do formulário de nova amostra | aprovado |
| `ana.analista` nas listas controladas: 403 | aprovado |

## Pendências que dependem de terceiros

- Ratificar com a Garantia da Qualidade: padrão do código de lote (hoje configurável em
  `LOT_CODE_PATTERN`), dados mínimos das amostras (com o encarregado de dados) e o alerta sem
  bloqueio para certificado vencido.
- Ratificar com o Gestor de P&D: perfis que cadastram e corrigem e o responsável pela produção
  escolhido entre as pessoas com conta no sistema.
- O bloqueio por documento assinado é acionado pela feature 005; aqui foi simulado pelo serviço.
