# Constituição do projeto

A constituição fixa nove princípios que todas as features precisam respeitar; cole o bloco abaixo no Claude Code, revise o `constitution.md` gerado com a Garantia da Qualidade e registre a data de ratificação.

```text
/speckit-constitution Crie a constituição do SGP-P&D, sistema de gestão de projetos de P&D de produtos para diagnóstico in vitro, usado na intranet da empresa. Antes de escrever, leia todos os arquivos de docs/contexto/. Princípios inegociáveis:

1. Rastreabilidade (ALCOA+): todo dado tem autor, data e hora do servidor, versão e origem. Nenhum registro é apagado fisicamente; correções geram nova versão com motivo obrigatório.
2. Trilha de auditoria imutável: criação, alteração, assinatura, geração de documento, exportação e mudança de permissão geram eventos append-only, encadeados por hash e consultáveis por projeto.
3. Assinatura eletrônica: assinar exige reautenticação e registra pessoa, papel, significado (elaborado, revisado, aprovado), data e hora e o hash do conteúdo. Documento assinado fica bloqueado.
4. Modelos versionados: tipos de subdocumento, tópicos, campos, capas e rodapés ("Formulário Versão", "Referência PSG") são dados configuráveis e versionados. Cada documento guarda a versão de modelo que usou.
5. Fonte única: lotes, insumos, amostras, kits de referência, normas e pessoas são cadastrados uma vez e referenciados. Textos e tabelas gerados nunca redigitam esses dados.
6. Cálculo e numeração automáticos: estatísticas, totais, numeração de tópicos, tabelas, páginas e referências cruzadas são calculados pelo sistema e cobertos por testes.
7. Segurança: só usuários autenticados no domínio; permissões por perfil e por projeto; menor privilégio; HTTPS interno; dados não saem da intranet, exceto para o Sankhya pela API oficial.
8. Qualidade verificável: todo requisito tem critério de aceitação testável e é rastreável até um teste. Regras regulatórias, cálculos e permissões são escritos com testes primeiro (TDD). Isso é evidência para a validação do sistema exigida pela RDC 665/2022, art. 104.
9. Simplicidade: monólito modular, poucas dependências, código e identificadores em inglês, interface, mensagens e documentos em português do Brasil. Nenhuma funcionalidade sem requisito.

Governança: mudanças nesta constituição exigem justificativa, revisão do Gestor de P&D e da Garantia da Qualidade e novo número de versão (semântico). Registre a data de ratificação.
```

Na versão 1.x, `/speckit-constitution` altera só o `constitution.md`; os templates do spec-kit não mudam.
