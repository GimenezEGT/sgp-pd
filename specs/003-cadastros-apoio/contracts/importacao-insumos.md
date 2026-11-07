# Contrato: planilha de importação de insumos

Formato: CSV (UTF-8 com ou sem BOM, ou Latin-1; separador `;` ou `,`) ou XLSX (primeira
planilha). A primeira linha é o cabeçalho; os nomes são comparados sem acento e sem diferença de
caixa.

| Coluna | Obrigatória | Regra |
| --- | --- | --- |
| `codigo` | sim | sem espaços; único no cadastro e na planilha |
| `descricao` | sim | até 300 caracteres |
| `tipo` | sim | `materia-prima`, `matéria-prima`, `MP` ou `embalagem`, `material de embalagem`, `ME` |
| `fabricante` | não | até 200 caracteres |
| `lote_fabricante` | não | até 100 caracteres |
| `novo` | não | `sim`/`não`, `s`/`n`, `1`/`0`, `true`/`false`; vazio = não |

Até 5.000 linhas por arquivo. Faltando coluna obrigatória, o arquivo inteiro é recusado com a
lista das colunas esperadas. O certificado de análise é anexado depois, no cadastro de cada
insumo.

Relatório de rejeições (CSV `;`, UTF-8 com BOM): `linha;codigo;descricao;motivos`.
