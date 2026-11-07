# Contrato: exportação da trilha (CSV e XLSX)

Os dois formatos têm o mesmo conteúdo e a mesma ordem (cronológica, por `seq`).

Bloco de identificação (linhas 1 a 5, seguidas de uma linha em branco):

| Linha | Coluna A | Coluna B |
| --- | --- | --- |
| 1 | `Trilha de auditoria — SGP-P&D` | |
| 2 | `Exportado em` | data e hora do servidor em `dd/mm/aaaa hh:mm:ss` (America/Sao_Paulo) |
| 3 | `Exportado por` | `login — nome` |
| 4 | `Filtros` | `Usuário: …; Projeto: …; De: …; Até: …; Tipo: …` (`todos` quando vazio) |
| 5 | `Eventos` | quantidade |

Cabeçalho (linha 7) e uma linha por evento:

`Sequência`; `Data e hora`; `Usuário`; `Tipo de evento`; `Código do tipo`; `Objeto`;
`ID do objeto`; `Projeto`; `Valor anterior`; `Valor novo`; `Motivo`; `Origem`; `Hash`

- CSV: UTF-8 com BOM, separador `;`, aspas duplas quando necessário, fim de linha `\r\n`.
- XLSX: uma planilha "Trilha", datas como texto no formato acima, valores anterior e novo como JSON
  compacto.
- Nome do arquivo: `trilha-auditoria-AAAAMMDD-HHMMSS.csv` ou `.xlsx`.
- Sem eventos no filtro: o arquivo sai com o bloco de identificação, `Eventos` = 0 e o cabeçalho.
