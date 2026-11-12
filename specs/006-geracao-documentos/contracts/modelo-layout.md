# Contrato: definição do modelo de layout (feature 006)

JSON validado por JSON Schema (Draft 2020-12) em `sgp/documents/layout_schema.py`; nenhuma chave
extra é aceita. Padrões da versão 01 (prova de layout e docs/contexto/03-padroes-formatacao.md):

```json
{
  "page": {"margin_top_cm": 2.0, "margin_bottom_cm": 2.0, "margin_left_cm": 1.3, "margin_right_cm": 1.3},
  "font": {"family": "Calibri", "body_pt": 11},
  "logo": {"width_cm": 12.84, "height_cm": 1.8},
  "cover": {
    "indent_cm": 2.44,
    "second_column_cm": 5.09,
    "title_pt": 24,
    "title_pt_by_type": {"rapd": 23, "analise-critica": 23, "validacao": 23, "verificacao-final": 23, "saida": 23},
    "variant_by_type": {"verificacao-final": "checklist", "saida": "sectors"},
    "topics_pt_by_type": {"saida": 11},
    "product_pt": 20,
    "version_pt": 20,
    "contains_pt": 16,
    "topics_pt": 14,
    "signature_pt": 12,
    "checklist_header_pt": 11
  },
  "header": {"text": "{titulo} – {produto} – Versão {versao}", "pt": 9},
  "footer": {"text": "", "pt": 11},
  "body": {"heading_pt": 12, "table_pt": 10, "table_header_fill": "#D9D9D9"},
  "watermark": {"text": "RASCUNHO – NÃO VÁLIDO", "pt": 54, "color": "#D0D0D0"}
}
```

Regras:

- Margens de 0,5 a 4,0 cm; tamanhos de fonte de 6 a 40 pt; logotipo de 2 a 18 cm de largura e
  0,5 a 5 cm de altura; cores no formato `#RRGGBB`.
- `font.family`: só fontes instaladas no servidor (`Calibri`, servida pela Carlito).
- `title_pt_by_type`, `topics_pt_by_type` e `variant_by_type` (opcionais): chaves são códigos
  ativos da lista `tipo-subdocumento`; variantes `topics` (padrão), `checklist` e `sectors`; só no
  alvo `subdocument`. A Saída usa tópicos em 11 pt, o tamanho impresso da aba da planilha (escala de
  79%), para a capa caber numa página A4 sem escala de impressão.
- `header.text` e `footer.text` aceitam só os marcadores `{titulo}`, `{produto}`, `{versao}` e
  `{projeto}`; marcador desconhecido recusa a publicação.
- `watermark.text` é obrigatório.
- No alvo `subdocument`, o rodapé do formulário ("Formulário Versão: NN. Referência: …") vem do
  modelo de formulário e `footer.text`, quando preenchido, sai numa segunda linha; no TAP e no Plano
  de Negócios, `footer.text` é o único texto do rodapé (vazio por padrão).
- Publicar exige definição válida; a vigência não pode ser anterior à da versão vigente.
