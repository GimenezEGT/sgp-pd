# Procedimento de recuperação a partir da cópia de segurança

Uso: perda ou corrupção do banco de dados ou dos arquivos do SGP-P&D. Executado só pela TI, no
servidor, com registro de incidente e ciência da Garantia da Qualidade. Restaurar sobre o banco em
uso não existe na interface do sistema (FR-009 da feature 014).

## Antes de começar

1. Registrar o incidente (data, hora, sintoma, quem detectou).
2. Escolher a cópia no painel "Operação e validação": a mais recente com teste de restauração
   aprovado, ou a mais recente bem-sucedida. Anotar a pasta (`AAAAMMDD-HHMMSS`) e o resumo do
   manifesto.
3. Parar a aplicação para que ninguém grave durante a recuperação:
   `docker compose -f docker-compose.yml stop web worker nginx`.

## Conferir a cópia

```bash
cd "$BACKUP_HOST_DIR/copias/<pasta>"
sha256sum manifesto.json        # igual ao resumo do manifesto no painel
sha256sum banco.dump            # igual a banco.sha256 dentro do manifesto.json
```

## Restaurar o banco

O papel dono (`DB_OWNER_USER`) recria o banco a partir da cópia; os privilégios do papel da
aplicação são reaplicados pelo próprio sistema ao subir.

```bash
docker compose -f docker-compose.yml exec db psql -U "$DB_OWNER_USER" -d postgres -c 'ALTER DATABASE sgp RENAME TO sgp_anterior_AAAAMMDD'
docker compose -f docker-compose.yml exec db createdb -U "$DB_OWNER_USER" -T template0 sgp
docker compose -f docker-compose.yml run --rm --no-deps -v "$BACKUP_HOST_DIR/copias/<pasta>:/restaurar:ro" web \
  sh -c 'PGPASSWORD="$DB_OWNER_PASSWORD" pg_restore -h db -U "$DB_OWNER_USER" --no-owner --no-privileges --exit-on-error -d sgp /restaurar/banco.dump'
```

O banco antigo fica como `sgp_anterior_AAAAMMDD` (data do incidente) até a Garantia da Qualidade
concluir a análise do incidente (nada é apagado sem decisão registrada).

## Restaurar os arquivos

Os arquivos guardados ficam no acervo `$BACKUP_HOST_DIR/arquivos/aa/bb/<sha256>`, com o mesmo
endereço usado pelo sistema (`MEDIA_ROOT/aa/bb/<sha256>`). Copiar o acervo para o volume de dados
sem sobrescrever arquivos existentes:

```bash
docker compose -f docker-compose.yml run --rm --no-deps -v "$BACKUP_HOST_DIR/arquivos:/acervo:ro" web \
  sh -c 'cp -rn /acervo/. /app/var/media/'
```

## Voltar ao uso

1. `docker compose -f docker-compose.yml up -d` (as migrações e os privilégios rodam ao subir).
2. Executar a verificação de integridade da trilha: a cadeia deve estar íntegra até o último
   evento do manifesto.
3. Executar a qualificação de operação e anexar o relatório ao registro do incidente.
4. Informar às pessoas que o trabalho feito depois do horário da cópia precisa ser refeito (o
   intervalo é a diferença entre o horário da cópia e o do incidente).
