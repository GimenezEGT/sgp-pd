# Quickstart: Cópia de segurança, restauração e qualificação do sistema

```bash
docker compose build web worker && docker compose up -d
docker compose run --rm web sh scripts/verificar.sh
```

No desenvolvimento o destino de cópias é `var/backups` (montado em `/app/var/backups`).

1. `admin.ti` abre "Operação e validação" e pede uma cópia: a cópia aparece bem-sucedida, com o
   tamanho do banco, os arquivos (total e novos) e o resumo do manifesto; no destino há
   `copias/<data>/banco.dump`, `manifesto.json` e o acervo `arquivos/`. Uma segunda cópia não
   copia arquivos de novo (novos = 0).
2. `admin.ti` pede o teste de restauração: C1 a C6 aprovadas; o banco `sgp_restauracao` não existe
   ao fim.
3. Dano: alterar um arquivo do acervo e repetir o teste: C6 reprova, o e-mail de aviso chega aos
   administradores (`var/emails`) e a trilha registra o teste reprovado. Restaurar o arquivo.
4. `docker compose exec web python manage.py qualificacao_instalacao --usuario admin.ti`: relatório
   em PDF guardado; no desenvolvimento, itens como depuração e segredo de desenvolvimento aparecem
   reprovados (esperado: o ambiente de desenvolvimento não é qualificado).
5. `qualidade.ar` executa a qualificação de operação pela tela: trilha íntegra, alterações recusadas,
   PDF de teste selado, cópia e teste em dia.
6. `qualidade.ar` exporta a revisão de acessos em CSV e XLSX; `ana.analista` recebe 403 no painel.
7. Homologação (SC-004): seguir `docs/validacao/iq-roteiro.md` e `docs/validacao/oq-roteiro.md`
   no servidor, com os roteiros manuais executados e assinados pela Garantia da Qualidade.
