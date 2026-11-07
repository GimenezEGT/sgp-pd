# Feature 006 — Geração de documentos no padrão da empresa

Cada subdocumento sai pronto em DOCX e PDF, com a capa da planilha, tópicos e tabelas numerados, paginação e rodapé do formulário; é aqui que o tempo de montagem desaparece.

```text
/speckit-specify Geração dos documentos no padrão visual da empresa a partir dos dados do sistema. Leia docs/contexto/03-padroes-formatacao.md e veja os arquivos de docs/modelos/.

Objetivo: economizar o tempo de montagem e eliminar erros de cópia; o documento sai pronto, com capa, numeração e rodapé corretos.

Histórias:
1. Como analista, gero o documento de qualquer subdocumento em DOCX (editável, para conferência) e em PDF (oficial).
2. A capa reproduz o padrão da planilha Capas Projeto: logotipo, título do subdocumento, nome do produto, versão, lista "ESTE RELATÓRIO DEVE CONTER", bloco de assinaturas e rodapé "Formulário Versão: NN. Referência: <referência>" com os valores do modelo usado.
3. No corpo, os tópicos aparecem como títulos numerados, as tabelas são numeradas em sequência ("Tabela 01 – ...") e repetem o cabeçalho quando quebram de página; as páginas são numeradas "Página N de M".
4. No PDF oficial, as assinaturas eletrônicas aparecem no bloco de assinaturas com nome, função, data e hora e significado; o arquivo é selado digitalmente e o rodapé mostra um código de verificação.
5. Como Garantia da Qualidade, mantenho os modelos de layout (capa, cabeçalho, rodapé, estilos) sem programador, e cada modelo é versionado.
6. Todo documento gerado fica arquivado com versão, data, autor da geração e hash; gerar de novo uma versão aprovada produz o mesmo conteúdo.

Regras: documento de versão não aprovada sai com marca d'água "RASCUNHO – NÃO VÁLIDO"; o PDF oficial é PDF/A; todo dado vem do sistema, nada é digitado no gerador.

Fora do escopo: documento completo do projeto (009) e dossiê (011), que reutilizam este gerador.
```

Pontos que o `/speckit-clarify` deve fechar:

- Se o DOCX também pode ser documento oficial ou só o PDF.
- Logotipo único ou por marca (Bioclin, Quibasa).
- Paginação "Página N" ou "Página N de M".
- Se subdocumentos isolados levam sumário ou só o documento completo.

```text
/speckit-plan Comece por uma prova de layout de 2 dias: reproduza a capa da Entrada de Projeto e uma tabela de 120 linhas com quebra de página em duas abordagens, (a) modelo Word com docxtpl e conversão para PDF/A pelo LibreOffice headless e (b) HTML com CSS paginado no WeasyPrint. Escolha pela fidelidade aos arquivos de docs/modelos e registre a decisão no research.md. Selo do PDF com pyHanko (PAdES) usando certificado da empresa guardado fora do repositório. Geração assíncrona com Celery e status na tela. Testes de regressão visual comparando PDFs gerados com referências aprovadas pela Qualidade.
```

Checklists sugeridos: fidelidade de layout e regulatório (identificação de versão e assinatura).

Pronto quando:

- [ ] A Qualidade não distingue a capa gerada da capa da planilha.
- [ ] Uma tabela longa quebra a página repetindo o cabeçalho.
- [ ] A assinatura do PDF oficial é validada num leitor de PDF.
- [ ] O rascunho sai com marca d'água.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
