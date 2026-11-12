# Quickstart: Dossiê técnico para a ANVISA

```bash
docker compose build web worker && docker compose up -d
docker compose run --rm web sh scripts/verificar.sh
```

1. `qualidade.ar` cadastra a empresa e o responsável técnico e legal; escreve os textos padrão
   "Unidade fabril" e "Processo de fabricação"; `gestor.pd` aprova com a senha de rede.
2. `qualidade.ar` abre o dossiê do PD-2026-001: checagem por item para a classe da Entrada, com
   origem e status; itens sem dado aparecem como faltando.
3. Preenche complementos (ex.: analito) e marca um item como não aplicável com justificativa.
4. Gera: com item faltando, sai rascunho com marca d'água; baixa PDF e DOCX e confere cabeçalho,
   rodapé, romanos e letras.
5. Num projeto completo (testes), gera o dossiê final com o pacote de anexos; registra o envio com
   protocolo e o resultado.
6. Aprova uma mudança num subdocumento e gera de novo: o aditamento mostra só o item alterado.
7. `leitor.consulta` sem acesso ao projeto: 403.
