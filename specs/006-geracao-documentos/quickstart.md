# Quickstart: Geração de documentos no padrão da empresa

## Preparação

```bash
docker compose build web worker
docker compose up -d
docker compose run --rm web python manage.py selo_teste
docker compose restart web worker
```

`selo_teste` cria `var/certs/selo-teste.p12` (autoassinado, só com `DEBUG` ligado); o
`docker-compose.override.yml` aponta `DOCUMENT_SEAL_PKCS12` e `DOCUMENT_SEAL_PASSWORD` para ele.
Homologação e produção montam o certificado da empresa e definem as duas variáveis.

## Testes

```bash
docker compose run --rm web sh scripts/verificar.sh
```

Inclui a regressão visual (`tests/documents/referencias/`), o determinismo, o selo e a adulteração,
os marcadores de PDF/A, as permissões e as rotas do contrato `rotas-ui.md`.

## Validação ponta a ponta

1. Como analista, abrir um subdocumento em rascunho › "Documentos gerados" › "Gerar PDF": a tela
   mostra "Na fila"/"Gerando" e depois o link; o PDF tem a capa no padrão da planilha, "Página N de
   M" e a marca d'água "RASCUNHO – NÃO VÁLIDO" em todas as páginas. "Gerar DOCX" baixa a cópia
   editável com a mesma marca.
2. Enviar, aprovar (feature 005) e gerar o PDF oficial: assinaturas no bloco da capa e na relação
   final, "Data:" com a data da aprovação, código de verificação no rodapé, sem marca d'água.
3. Conferir o selo e o PDF/A:

   ```bash
   docker compose cp web:/tmp/oficial.pdf var/oficial.pdf   # ou baixar pela tela
   docker run --rm -v "$PWD/var:/data" verapdf/cli:latest --format text /data/oficial.pdf
   ```

   O veraPDF responde `PASS … 2b`; num leitor de PDF, o selo aparece íntegro (certificado de teste
   não confiável em desenvolvimento). Alterar um byte do arquivo faz o leitor acusar a alteração.
4. Gerar de novo o PDF oficial: o histórico mostra o mesmo resumo do conteúdo e "igual à primeira".
   Renomear o produto numa nova versão do TAP e o rótulo de um termo de lista e gerar de novo: o
   resumo continua o mesmo.
5. Em "Verificar documento", informar o código: aparecem tipo, versão, situação, data de aprovação,
   assinaturas e resumo do arquivo; com acesso ao projeto, o link de download.
6. Como Qualidade/AR, em "Modelos de layout", criar nova versão do layout de subdocumentos, mudar o
   tamanho do título, pré-visualizar e publicar; um subdocumento já iniciado continua na versão 01
   (histórico de gerações mostra o layout usado) e um subdocumento novo nasce na 02.
7. Como pessoa sem acesso ao projeto, tentar `/documentos/subdocument/<id>/` e o download direto:
   403 e evento `auth.permission_denied` na trilha.
