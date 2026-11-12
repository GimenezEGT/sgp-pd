# Feature 006 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-11, dados fictícios. Senhas do LDAP de desenvolvimento;
selo com o certificado autoassinado de teste gerado por `manage.py selo_teste` (`var/certs/`).

## Prova de layout (antes do plano)

Registrada em `specs/006-geracao-documentos/prova-layout/README.md`: capa da Entrada e tabela de
120 linhas nas abordagens docxtpl + LibreOffice e WeasyPrint; escolhido o WeasyPrint (determinismo,
PDF/A-2b validado no veraPDF antes e depois do selo, 3 vezes mais rápido, imagem menor).

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 855 aprovados (todas as features até a 006, com a convergência), 0 falhas |
| Cobertura `sgp/core` / `sgp/audit` | 93,5% / 97,1% |
| Matriz de rastreabilidade | 164 requisitos (001 a 006), 0 sem cobertura |
| SC-002 tabela de 120 linhas | cabeçalho repetido em todas as páginas em que continua |
| SC-003 selo | íntegro e válido (pyHanko); 1 byte alterado acusado |
| SC-004 marca d'água | em todas as páginas do rascunho, em PDF e DOCX |
| SC-005 regeneração | mesmo resumo de conteúdo depois de renomear o produto e um termo de lista |
| SC-007 desempenho | documento de 30+ páginas bem abaixo de 30 s |
| SC-008 regressão visual | 3 páginas iguais às referências de `tests/documents/referencias/` |

## Roteiro do quickstart na pilha real (Nginx HTTPS → Django → worker Celery → PostgreSQL)

| Cenário | Resultado |
| --- | --- |
| `ana.analista` gera PDF e DOCX da Saída (rascunho) e PDF da Verificação Final: pedido na fila, concluído pelo worker em 1 a 2 s, download do arquivo arquivado | aprovado |
| Entrada e TAP do PD-2026-001, aprovados nas features 002 e 004 sem assinatura eletrônica: PDF oficial recusado com mensagem clara ("aprovada sem a assinatura eletrônica") e alerta na trilha | aprovado (mensagem acrescentada no roteiro) |
| TAP e Plano do PD-2026-002 (aprovados com assinatura na 005): PDF oficial selado com código; conteúdo congelado na primeira geração | aprovado |
| `ana.analista` (sem dados financeiros) abre os documentos do Plano de Negócios: 403 | aprovado |
| Formulação 2 (versão 02) enviada e aprovada com as senhas: a aprovação congela o conteúdo (`documents.frozen`); PDF oficial gerado duas vezes com o mesmo resumo de conteúdo e o mesmo código `628G-4NG7-48SE-33ZT`, arquivos diferentes só pelo selo; DOCX de conferência sem código | aprovado |
| Capa oficial: "Analista Responsável (Nome/Função):" e "Gestor de P&D:" com nome, função, significado, data e hora; "Data:" da aprovação; código no rodapé; registro de assinaturas e resumo do conteúdo aprovado ao fim | aprovado |
| Verificação do código: membro vê projeto, situação "Vigente" e download; `leitor.consulta` vê só a validade e os resumos; código inexistente informado; três consultas na trilha | aprovado |
| `leitor.consulta` no histórico de documentos da Saída: 403 | aprovado |
| `qualidade.ar` cria a versão 02 do layout de subdocumentos, pré-visualiza (PDF de exemplo) e publica; `ana.analista` não edita (403); a Saída continua no layout 01 | aprovado |

## Conformidade dos arquivos

| Verificação | Resultado |
| --- | --- |
| veraPDF 1.30.3 (`verapdf/cli`), perfil PDF/A-2b: Formulação oficial (2 gerações), TAP oficial, Plano oficial, Saída e Verificação Final em rascunho | `PASS` nos 6 arquivos |
| `pdfsig` (poppler) no PDF oficial da Formulação e do TAP | "Signature is Valid"; certificado de teste não confiável (esperado em desenvolvimento) |
| `pdfsig` com 1 byte alterado | "Digest Mismatch" |

## Pendências a ratificar

- SC-001: comparação da capa gerada com a planilha Capas Projeto pela Garantia da Qualidade
  (registrada em `docs/validacao/verificacoes-manuais.json`).
- Referências da regressão visual geradas a partir de dados de teste fictícios: precisam da
  aprovação registrada da Qualidade.
- Certificado da empresa para o selo (tipo, emissor e guarda): dependência da TI; em homologação e
  produção, montar o PKCS#12 fora do repositório e definir `DOCUMENT_SEAL_PKCS12` e
  `DOCUMENT_SEAL_PASSWORD`.
- Os .docx originais citados em `docs/modelos/LEIA-ME.md` não estão no repositório: cabeçalho e
  estilos do corpo seguem 03-padroes-formatacao.md até a conferência da Qualidade.
- Decisões provisórias do esclarecimento (DOCX só para conferência, logotipo único, "Página N de M",
  sem sumário, TAP e Plano gerados) e a Saída com tópicos em 11 pt na capa.
