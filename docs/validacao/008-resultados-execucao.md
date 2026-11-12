# Feature 008 — resultados de execução (evidência)

Ambiente de desenvolvimento, 2026-11-11, dados fictícios. Senhas do LDAP de desenvolvimento.

## Suíte automatizada

| Item | Resultado |
| --- | --- |
| Testes (`pytest`) | 1.064 aprovados (todas as features até a 008 e a 013), 0 falhas; cobertura `sgp/core` 93,5% e `sgp/audit` 97,1% |
| Testes da feature (`tests/notebook`) | 39 aprovados |
| Matriz de rastreabilidade | 229 requisitos, 0 sem cobertura |
| SC-001 entrada assinada | edição, material e anexo recusados no serviço e no banco (gatilho); só adendo assinado; o resumo do original não muda |
| SC-002 busca por lote | lote em materiais e em vínculos: todas as entradas que o usam |
| SC-003 promoção | CSV e XLSX promovidos para estudo em elaboração; vínculo `promoted` visível na entrada e no estudo; evento `studies.imported` com a origem (entrada, anexo e SHA-256) |
| SC-004 desempenho | busca em português num caderno de 1.000 entradas em menos de 2 s |
| Sanitização | script, estilo, eventos, classes, links, iframes, comentários e imagens externas ou de outra entrada removidos; `div` do navegador vira parágrafo |

## Roteiro do quickstart na pilha real

| Cenário | Resultado |
| --- | --- |
| `qualidade.ar` cria o modelo "Teste de formulação (smoke)" e altera o procedimento com motivo: versões 1 e 2 (vigente); `ana.analista` tentando criar modelo: 403 | aprovado |
| `ana.analista` cria no PD-2026-001 a entrada 1 a partir do modelo (versão 2), relevante: número, data e hora do servidor; procedimento do modelo copiado | aprovado |
| Gravação com `<sup>`, tabela, `<script>`, `onclick` e `style`: sobrescrito e tabela preservados; script, evento e estilo removidos | aprovado |
| Lote LP-SMK-01 e amostra AM-SMK-1 ligados pelo código; lote inexistente recusado com o motivo | aprovado |
| Anexos: CSV aceito com SHA-256; TXT recusado ("Tipo de arquivo não aceito"); imagem colada pelo editor (resposta JSON) entra no texto, download 200; imagem externa removida | aprovado |
| Assinatura com senha errada recusada ("Senha de rede incorreta"); com a senha certa: assinada e bloqueada; editar e anexar depois: 403; `UPDATE` direto no banco recusado pelo gatilho | aprovado |
| Adendo assinado: 1 adendo, 2 assinaturas (entrada e adendo); original sem mudança | aprovado |
| Autor tentando testemunhar: 403; `lider.projeto` testemunha: "testemunhada"; tela mostra "Conteúdo confere com as assinaturas" | aprovado |
| Vínculo com a Formulação (versão 02): a entrada aparece na tela da Formulação | aprovado |
| Promoção do CSV para o estudo "Repetibilidade promovida do caderno": 4 linhas aceitas e gravadas; vínculo `promoted`; "Dados promovidos" na tela do estudo | aprovado |
| `gestor.pd`: busca "solucao" (sem acento) acha a entrada com "Solução"; filtros por lote, situação "testemunhada" e "abertas há mais de 7 dias"; linha do tempo do projeto | aprovado |
| `leitor.consulta` sem acesso ao projeto: 403 | aprovado |
| Trilha: `notebook.template_created`, `template_updated`, `created`, `updated`, `material_added`, `attachment_added`, `signed`, `addendum_added`, `witnessed`, `linked`, `promoted` | aprovado |
| Editor no navegador (página local com o `editor.js`): barra e área editável criadas, campo original oculto; sobrescrito e tabela pela barra; Enter gera parágrafo; colar imagem envia `POST` com o token CSRF e `no_texto=1` e insere `<img>` com o endereço devolvido; sem endereço de envio (adendo), avisa e não cola | aprovado |

Observação: depois de recriar o contêiner `web`, o nginx respondeu 502 até ser reiniciado (o
endereço do contêiner mudou); o roteiro foi repetido com sucesso. Textos acentuados foram enviados
por arquivo (`--data-urlencode campo@arquivo`) para não sofrer a conversão cp1252 do `curl` do
Windows.

## Convergência (`/speckit-converge`)

Converged: FR-001 a FR-014 e SC-001 a SC-004 implementados e cobertos por testes
(`req("008:…")`); tarefas T001 a T015 concluídas; nenhuma tarefa nova. O lembrete por e-mail da
entrada atrasada fica na feature 010, como registrado na especificação.

## Pendências a ratificar

- Prazo de assinatura de 7 dias corridos (`NOTEBOOK_SIGN_DAYS`), com lembrete por e-mail na
  feature 010 (Gestor de P&D).
- Testemunha obrigatória quando a entrada é marcada como relevante pelo autor ou pelo Gestor; a
  testemunha é qualquer pessoa com acesso ao projeto, diferente do autor (Gestor de P&D e Jurídico).
- Anexos nos tipos PDF, PNG, JPEG, CSV e XLSX, com o limite `FILE_MAX_MB` (TI).
- Nenhuma entrada fora de projeto (Gestor de P&D).
- Modelos de entrada mantidos pela Qualidade/AR e pelo Gestor fora do ciclo da 013 (Garantia da
  Qualidade).
- Adendo feito por qualquer editor do projeto (com a própria assinatura), não só pelo autor.
