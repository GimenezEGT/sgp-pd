# Contrato: destino, manifesto, teste de restauração e comandos (feature 014)

## Destino (`BACKUP_DIR`)

```text
<BACKUP_DIR>/
├── copias/<AAAAMMDD-HHMMSS>/banco.dump        # pg_dump -Fc do instantâneo
├── copias/<AAAAMMDD-HHMMSS>/manifesto.json
└── arquivos/aa/bb/<sha256>                     # acervo de arquivos, nunca podado
```

Recusado: diretório inexistente, sem permissão de gravação, igual a `MEDIA_ROOT` ou dentro dele.

## Manifesto (`manifesto.json`, formato 1)

```json
{
  "formato": 1,
  "sistema": {"versao": "0.1.0", "commit": "<hash ou vazio>"},
  "criado_em": "<ISO 8601 UTC>",
  "banco": {"arquivo": "banco.dump", "tamanho": 0, "sha256": "<64 hex>", "servidor": "17.x", "nome": "<banco>"},
  "tabelas": {"<tabela>": 0},
  "trilha": {"seq": 0, "hash": "<64 hex>"},
  "arquivos": {"total": 0, "novos": 0, "bytes": 0, "lista": [["<sha256>", 0]]}
}
```

O SHA-256 do próprio manifesto fica em `BackupRun.manifest_sha256`.

## Teste de restauração

| Código | Conferência |
| --- | --- |
| C1 | resumo do `manifesto.json` igual ao registrado na cópia |
| C2 | resumo do `banco.dump` igual ao do manifesto |
| C3 | `pg_restore --no-owner --no-privileges --exit-on-error` no banco isolado sem erro |
| C4 | contagem de linhas de cada tabela igual à do manifesto |
| C5 | cadeia da trilha íntegra no banco restaurado e último evento igual ao do manifesto |
| C6 | todo arquivo do manifesto presente no acervo, com o SHA-256 conferido |

Banco isolado: `<NAME>_restauracao`, descartado antes (se sobrou) e ao fim.

## Comandos (TI, no servidor)

| Comando | Efeito |
| --- | --- |
| `python manage.py copia_seguranca` | cópia manual imediata (mesmo serviço da tarefa diária) |
| `python manage.py teste_restauracao` | teste de restauração da cópia mais recente |
| `python manage.py qualificacao_instalacao --usuario <login>` | IQ, canal "linha de comando"; a pessoa precisa ter o perfil Administrador ativo |
| `python manage.py qualificacao_operacao --usuario <login>` | OQ, canal "linha de comando"; Administrador ou Garantia da Qualidade |

Saída com código 1 quando a cópia, o teste ou a qualificação reprova.

## Variáveis de ambiente

`BACKUP_DIR`, `BACKUP_HOST_DIR` (Compose), `BACKUP_HOUR`, `BACKUP_MINUTE`, `BACKUP_KEEP_DAYS`
(35), `RESTORE_TEST_DAY` (1), `RESTORE_TEST_HOUR` (3), `BACKUP_MAX_AGE_HOURS` (26),
`DB_OWNER_USER` e `DB_OWNER_PASSWORD` (já usadas pelas migrações), `SGP_COMMIT` (build).
