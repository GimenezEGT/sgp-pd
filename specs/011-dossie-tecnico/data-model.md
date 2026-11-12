# Data Model: Dossiê técnico para a ANVISA

App `sgp.dossier`.

| Modelo | Tipo | Campos principais |
| --- | --- | --- |
| DossierDefinition | `AppendOnlyModel` | version, yaml (texto), parsed (JSON), note, created_by/at |
| StandardText | `ProtectedModel` | key, lineage, version, title, text, status (`draft`, `approved`, `superseded`), created_by/at, approved_by/at |
| CompanyProfile | `ProtectedModel` (linha única) | legal_name, city, rt_name, rt_council, rt_uf, rt_number, rt_title, updated_by/at |
| DossierSupplement | `ProtectedModel` | project, item_key, text, not_applicable, justification, updated_by/at; único por (project, item_key) |
| DossierVersion | `AppendOnlyModel` | subject (projeto ou família), project, number, definition, risk_class, final, checklist (JSON), content (JSON por item), content_hash, texts_used (JSON), sources (JSON: versões de origem), pdf, docx, package (FK `StoredFile`, nulos), generated_by/at |
| Submission | `ProtectedModel` | version (FK), protocol, submitted_on, signed_pdf (FK `StoredFile`, nulo), result (`pending`, `granted`, `rejected`, `requirement`), result_on, notes, created_by/at, updated_by/at |

Eventos: `dossier.definition_published`, `dossier.text_saved`, `dossier.text_approved`,
`dossier.company_updated`, `dossier.supplement_saved`, `dossier.generated`,
`dossier.submitted`, `dossier.result_recorded`, `dossier.addendum_generated`, `dossier.downloaded`.

Arquivos: `files.storage` passa a aceitar o pacote ZIP gerado pelo sistema (como PDF e DOCX).
