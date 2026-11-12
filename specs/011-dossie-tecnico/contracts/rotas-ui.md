# Contrato: telas, rotas e eventos (feature 011)

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/projetos/<id>/dossie/` | GET | acesso ao projeto | checagem item a item (classe, família, origem, status), versões geradas, envios | — |
| `/projetos/<id>/dossie/` | POST | Qualidade/AR | gera a versão (final se nada obrigatório faltar; senão rascunho): PDF, DOCX e pacote | `dossier.generated` |
| `/projetos/<id>/dossie/complementos/<item>/` | GET, POST | Qualidade/AR | texto do item, ou não aplicável com justificativa | `dossier.supplement_saved` |
| `/dossie/versoes/<id>/<arquivo>/` | GET | acesso ao projeto | baixa `pdf`, `docx` ou `pacote` com conferência do resumo | `dossier.downloaded` |
| `/dossie/versoes/<id>/envio/` | POST | Qualidade/AR | protocolo, data e PDF assinado (opcional); classe I não tem envio | `dossier.submitted` |
| `/dossie/envios/<id>/resultado/` | POST | Qualidade/AR | resultado e data | `dossier.result_recorded` |
| `/dossie/versoes/<id>/aditamento/` | GET | acesso ao projeto | itens que mudaram desde a última versão enviada; `?pdf=1` gera o PDF do aditamento | `dossier.addendum_generated` |
| `/dossie/textos/` | GET, POST | consulta: qualquer perfil; edição: Qualidade/AR | biblioteca de textos padrão | `dossier.text_saved` |
| `/dossie/textos/<id>/aprovar/` | POST | Qualidade/AR ou Gestor de P&D, diferente de quem escreveu | senha de rede (005) | `dossier.text_approved` |
| `/dossie/definicao/` | GET, POST | consulta: qualquer perfil; publicação: Qualidade/AR | YAML validado, nova versão | `dossier.definition_published` |
| `/dossie/empresa/` | GET, POST | consulta: qualquer perfil; edição: Qualidade/AR | razão social, cidade e responsável técnico e legal | `dossier.company_updated` |
