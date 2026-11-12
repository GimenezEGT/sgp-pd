# Contrato: texto formatado e conteúdo assinado (feature 008)

## Texto formatado

Lista branca aplicada pelo servidor a cada gravação e na exibição:

| Item | Aceito |
| --- | --- |
| Tags | `p`, `br`, `strong`, `b`, `em`, `i`, `u`, `s`, `sub`, `sup`, `ul`, `ol`, `li`, `h3`, `h4`, `blockquote`, `pre`, `table`, `thead`, `tbody`, `tr`, `th`, `td`, `img` |
| Atributos | `img`: `src`, `alt`; `td`, `th`: `colspan`, `rowspan` (inteiros de 1 a 20) |
| Imagens | `src` só no formato `/arquivos/<id>/`, com `<id>` de um anexo ativo da própria entrada (ou do adendo, para imagens já anexadas à entrada) |
| Removido | tudo o mais, incluindo `script` e `style` com o conteúdo, atributos de evento, `style`, `class`, links e comentários |

Texto sem nenhuma tag é tratado como texto simples: blocos separados por linha em branco viram
parágrafos e blocos só com linhas iniciadas por "- " viram lista.

## Conteúdo canônico da entrada

Resumo SHA-256 do JSON canônico (`sgp.signatures.canonical.content_hash`) de:

```json
{
  "projeto": "PD-AAAA-NNN",
  "numero": 1,
  "autor": "login",
  "criada_em": "data e hora ISO 8601 em UTC",
  "titulo": "...",
  "objetivo": "HTML sanitizado",
  "hipotese": "HTML sanitizado",
  "procedimento": "HTML sanitizado",
  "resultados": "HTML sanitizado",
  "conclusao": "HTML sanitizado",
  "modelo": {"id": 1, "nome": "...", "versao": 1},
  "materiais": [{"tipo": "lote", "id": 10, "codigo": "...", "versao": 1}],
  "anexos": [{"id": 5, "nome": "...", "sha256": "...", "no_texto": false}]
}
```

Materiais e anexos ativos, ordenados pelo id; `modelo` é `null` sem modelo. A testemunha assina o
mesmo resumo do autor.

## Conteúdo canônico do adendo

```json
{"entrada": 12, "projeto": "PD-AAAA-NNN", "numero_entrada": 3, "adendo": 1,
 "autor": "login", "criado_em": "ISO 8601 UTC", "texto": "HTML sanitizado"}
```
