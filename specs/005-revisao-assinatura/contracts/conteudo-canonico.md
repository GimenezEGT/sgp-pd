# Contrato: conteúdo canônico assinado

JSON com chaves ordenadas, separadores `,` e `:`, UTF-8, sem ponto flutuante (decimais como texto,
datas ISO); resumo = SHA-256 em hexadecimal.

| Documento | Conteúdo |
| --- | --- |
| Subdocumento | `{documento, tipo, numero, versao, projeto, modelo: {id, tipo, versao, referencia}, topicos, anexos: [{id, nome, sha256}]}` |
| TAP | `{documento, versao, projeto, produto: {...}, tap: {campos do TAP}, equipe: [{pessoa, papel, inicio, fim}], marcos: [{subdocumento, planejado, realizado, cancelado}]}` |
| Plano de Negócios | `{documento, versao, projeto, plano: {campos do plano}, previsoes: {"1".."5"}, total}` |

`topicos` são os dados gravados (referências a cadastros por id da versão, bloqueadas na aprovação).
