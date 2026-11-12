# Roteiro de qualificação de operação (OQ)

Objetivo: demonstrar que o SGP-P&D instalado funciona como especificado nos fluxos críticos
(assinatura, auditoria, geração) e nas funções de operação. Executado em homologação, com dados
fictícios, depois da IQ aprovada. Partes: A (suíte automatizada), B (conferências no ambiente
instalado) e C (roteiros manuais executados e assinados pela Garantia da Qualidade).

## A. Suíte automatizada da mesma versão

| Nº | Passo | Resultado esperado | Obtido / evidência | Executor e data |
| --- | --- | --- | --- | --- |
| A1 | No commit qualificado, `docker compose build web` com o override de desenvolvimento (imagem `dev`) e `docker compose run --rm web sh scripts/verificar.sh` | ruff sem erros; todos os testes aprovados; cobertura mínima atendida; matriz gravada sem requisito descoberto | anexar a saída | |
| A2 | Conferir `docs/validacao/matriz-rastreabilidade.md` gerada | cada requisito FR/SC com teste ou verificação manual | | |

## B. Conferências no ambiente instalado

| Nº | Passo | Resultado esperado | Obtido / evidência | Executor e data |
| --- | --- | --- | --- | --- |
| B1 | Ter cópia de segurança nas últimas 26 horas e teste de restauração aprovado nos últimos 32 dias (painel "Operação e validação") | ambos em dia | | |
| B2 | A Garantia da Qualidade pede "Executar a qualificação de operação" no painel (ou a TI executa `python manage.py qualificacao_operacao --usuario <login>`) | OQ-01 a OQ-11 aprovados (OQ-10 "não aplicável" com a integração desligada); relatório PDF no painel | | |

Itens da qualificação de operação: OQ-01 cadeia da trilha íntegra; OQ-02 e OQ-03 alteração e
exclusão de evento da trilha recusadas pelo banco; OQ-04 alteração de versão assinada recusada;
OQ-05 exclusão de registro protegido recusada; OQ-06 PDF de teste gerado e selado, selo íntegro;
OQ-07 agendamentos ativos; OQ-08 cópia em dia; OQ-09 teste de restauração em dia; OQ-10 Sankhya;
OQ-11 nenhum dado alterado pela qualificação.

## C. Roteiros manuais dos fluxos críticos

Usar contas de teste da homologação (analista, líder, gestor, Qualidade, leitor) e dados fictícios.

### C1. Assinatura eletrônica (features 005 e 013)

| Nº | Passo | Resultado esperado | Obtido / evidência | Executor e data |
| --- | --- | --- | --- | --- |
| C1.1 | Analista preenche um subdocumento e envia para revisão com a senha de rede | situação "em revisão"; assinatura "Elaborado" com data e hora do servidor | | |
| C1.2 | Gestor devolve com comentário | situação "devolvido"; comentário visível; evento na trilha | | |
| C1.3 | Analista corrige e reenvia; gestor aprova com a senha de rede | situação "aprovado"; versão congelada; assinatura "Aprovado" com resumo SHA-256 do conteúdo | | |
| C1.4 | Tentar aprovar com senha errada três vezes | recusa a cada tentativa; bloqueio da assinatura depois da terceira; alerta na trilha | | |
| C1.5 | Tentar editar a versão aprovada | edição impossível; só "nova versão" com motivo | | |
| C1.6 | Criar nova versão com motivo | versão anterior intacta e consultável; nova versão em rascunho | | |

### C2. Trilha de auditoria (feature 001)

| Nº | Passo | Resultado esperado | Obtido / evidência | Executor e data |
| --- | --- | --- | --- | --- |
| C2.1 | Consultar a trilha filtrando pelo subdocumento do C1 | criação, alterações, envio, devolução, assinaturas e aprovação, com pessoa, data e hora | | |
| C2.2 | Exportar a trilha filtrada | arquivo exportado; a exportação também vira evento | | |
| C2.3 | Executar a verificação de integridade da trilha | cadeia íntegra, com número de eventos e último resumo | | |
| C2.4 | Pessoa sem o perfil exigido tenta abrir a trilha e telas restritas | acesso negado com registro | | |

### C3. Geração de documentos (features 006 e 009)

| Nº | Passo | Resultado esperado | Obtido / evidência | Executor e data |
| --- | --- | --- | --- | --- |
| C3.1 | Gerar o PDF da versão aprovada do C1 | PDF/A oficial com selo da empresa e código de verificação no rodapé | | |
| C3.2 | Conferir o selo do PDF num leitor de PDF | assinatura íntegra, titular da empresa | | |
| C3.3 | Em "Verificar documento", informar o código impresso | documento, versão e resumo identificados | | |
| C3.4 | Gerar de novo o mesmo documento | conteúdo idêntico ao da primeira geração | | |
| C3.5 | Gerar o PDF de um rascunho | marca d'água de rascunho, sem selo | | |
| C3.6 | Gerar o documento completo do projeto | capa, sumário com páginas, subdocumentos aprovados e quadro de versões | | |

### C4. Cópia e restauração (feature 014)

| Nº | Passo | Resultado esperado | Obtido / evidência | Executor e data |
| --- | --- | --- | --- | --- |
| C4.1 | TI pede "Fazer cópia agora" | cópia bem-sucedida com manifesto, arquivos e resumo | | |
| C4.2 | TI pede "Testar a restauração da cópia mais recente" | C1 a C6 aprovadas | | |
| C4.3 | Pessoa sem perfil de TI tenta pedir cópia | acesso negado | | |

## Critério de aceite

Partes A e B aprovadas e todos os passos de C com o resultado esperado. Desvio: registrar,
avaliar o impacto, corrigir pelo ciclo do spec-kit (nova feature ou correção) e repetir os passos
afetados.

| Executado por | Data | Revisado e aprovado por (Garantia da Qualidade) | Data |
| --- | --- | --- | --- |
| | | | |
