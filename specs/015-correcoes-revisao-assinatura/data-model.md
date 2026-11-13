# Data Model: Correções do ciclo de revisão e assinatura

Sem mudança de modelo de dados e sem migração. Regras sobre os dados da feature 005:

- `signatures.Signature` (somente de inclusão): no máximo uma assinatura de significado `reviewed`
  por pessoa em cada versão de cada documento, garantida pelo serviço (as repetidas gravadas antes
  desta correção ficam como estão).
- Devolução: mesma regra da 005 (`ReviewComment` com comentário obrigatório, evento
  `signatures.returned`), agora também acessível pela tela a quem elaborou e tem poder de aprovação.
