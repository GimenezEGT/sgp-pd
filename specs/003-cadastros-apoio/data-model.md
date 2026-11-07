# Data Model: Cadastros de apoio

## Campos comuns — `catalog.VersionedRecord` (abstrato, `ProtectedModel`)

| Campo | Tipo | Regras |
| --- | --- | --- |
| lineage | UUID, indexado | o mesmo cadastro em todas as versões |
| version | inteiro ≥ 1 | único por linhagem |
| is_current | booleano | uma única vigente por linhagem |
| is_active | booleano | desativado sai da busca para novas referências |
| locked_at / locked_by / lock_reason | data/hora, FK, texto | preenchidos quando documento assinado referencia a versão |
| version_reason | texto | obrigatório a partir da versão 2 |
| row_version | inteiro | controle otimista: edição com versão de linha antiga é recusada |
| created_by / created_at / updated_by / updated_at | | |

## Cadastros

| Modelo | Campos próprios | Unicidade (entre vigentes) |
| --- | --- | --- |
| `Lot` (Lote) | project (FK), code, lot_type (`pilot` Piloto, `validation` Validação, `production` Produção), manufacture_date, expiry_date (> fabricação), manufacturing_site, production_responsible (FK pessoa) | (project, code) |
| `Material` (Insumo) | code, description, material_type (`raw` matéria-prima, `packaging` material de embalagem), manufacturer, manufacturer_lot, certificate (FK StoredFile), certificate_valid_until, new_to_company | code |
| `ReferenceKit` (Kit de referência) | name, manufacturer, lot, expiry_date, registration_number (opcional) | — |
| `Sample` (Amostra) | identifier (código interno), sample_type (FK Term `tipo-amostra`), origin, characterization, storage (FK Term `armazenamento`), storage_detail, collection_date (opcional) | identifier |
| `Panel` (Painel) | code, description, amostras por `PanelSample` (panel, versão de `Sample`, position, removed_at/removed_by: retirada marcada, sem exclusão) | code |
| `Standard` (Norma) | identifier (ex.: "NBR ISO 13485:2016"), title, scope (`national`, `international`) | identifier |
| `BibliographicReference` | citation, year (opcional), doi_or_url (opcional) | — |

Exibição do lote: `Lote <code> – Fabricação: MM/AAAA – Validade: MM/AAAA`.

## files.StoredFile (*append-only*)

| Campo | Tipo |
| --- | --- |
| sha256 | char(64), indexado |
| original_name / content_type / size | texto / texto / inteiro |
| storage_name | caminho relativo `aa/bb/<sha256>` |
| uploaded_by / uploaded_at | FK / data/hora |

## catalog.ImportBatch

| Campo | Tipo |
| --- | --- |
| source_file | FK StoredFile (CSV ou XLSX) |
| uploaded_by / uploaded_at | |
| status | `preview` ou `confirmed` |
| rows | JSONB: lista de `{linha, dados, erros}` |
| valid_count / rejected_count / created_count | inteiros |
| confirmed_at / confirmed_by | |

## Listas controladas novas (carga inicial)

- `tipo-amostra`: Soro, Plasma, Sangue total, Urina, Líquor, DNA, RNA, Outros.
- `armazenamento`: −20 °C, 2 a 8 °C, 2 a 30 °C, 15 a 30 °C, 37 °C.
