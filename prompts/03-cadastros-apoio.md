# Feature 003 — Cadastros de apoio

Lotes, insumos, kits de referência, amostras e normas passam a existir uma única vez e são referenciados por todos os documentos, o que evita divergências entre documentos.

```text
/speckit-specify Cadastros de apoio usados por todos os subdocumentos: lotes, insumos (matérias-primas e materiais de embalagem), kits de referência, amostras e painéis, normas e referências bibliográficas. Leia docs/contexto/02-dicionario-documentos.md e 05-vocabularios.md.

Problema: hoje o mesmo lote, código ou concentração é redigitado em vários documentos, o que abre espaço para divergências. Cada dado deve existir uma vez e ser referenciado.

Histórias:
1. Como analista, cadastro os lotes do projeto (piloto ou validação) com código, data de fabricação, validade, local de fabricação e responsável pela produção.
2. Cadastro insumos com código, descrição, fabricante, lote do fabricante e certificado de análise anexado; marco se é novo para a empresa, para entrar na Saída de Projeto.
3. Cadastro kits de referência e comparativos com nome, fabricante, lote, validade e número de registro quando houver.
4. Cadastro amostras e painéis com identificador, tipo de amostra (vocabulário controlado), origem, caracterização e condição de armazenamento; uma amostra pode estar em vários estudos.
5. Mantenho bibliotecas de normas (ex.: NBR ISO 13485:2016, NBR ISO 14971:2020, CLSI EP25) e de referências bibliográficas reutilizáveis entre projetos.
6. Importo uma lista de insumos de uma planilha exportada do ERP enquanto a integração com o Sankhya não existe.

Regras: código de insumo é único; o código de um lote não muda depois de usado em documento assinado; cadastro usado em documento assinado só é corrigido por nova versão com motivo, e o documento antigo continua mostrando o valor assinado; buscas rápidas por código e descrição; amostras não guardam dados pessoais de pacientes.

Fora do escopo: integração automática com o Sankhya (feature 012).
```

Pontos que o `/speckit-clarify` deve fechar:

- Padrão de código dos lotes piloto e de validação.
- Quem pode cadastrar e corrigir insumos.
- Que atributos clínicos das amostras precisam ser guardados (LGPD).
- Se certificados vencidos bloqueiam o uso do insumo.

```text
/speckit-plan App "cadastros" com Lote, Insumo, KitReferencia, Amostra, Painel, Norma e Referencia. Amostras identificadas só por código interno, sem dados pessoais. Anexos em armazenamento de arquivos com hash SHA-256 conferido na leitura. Importação CSV/XLSX com pré-visualização, validação linha a linha e relatório de rejeições. Autocomplete com HTMX. Histórico por entidade e bloqueio de alteração in-place quando o registro está referenciado em versão assinada (correção cria nova versão).
```

Checklists sugeridos: integridade de dados e LGPD.

Pronto quando:

- [ ] Corrigir um lote já assinado cria nova versão e o documento assinado continua com o valor original.
- [ ] A importação de 500 insumos gera relatório das linhas rejeitadas.
- [ ] Nenhum campo de amostra aceita nome de paciente.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
