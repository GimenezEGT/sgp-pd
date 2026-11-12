# Quickstart: Revisão controlada dos modelos

## Testes

```bash
docker compose run --rm web sh scripts/verificar.sh
```

## Validação ponta a ponta (pilha de desenvolvimento)

1. `qualidade.ar`, em **Modelos de formulário**, abre nova versão da Entrada de Projeto, muda o rótulo
   de um tópico e salva; envia sem motivo (recusado) e com motivo e impacto.
2. `gestor.pd`, em **Revisões de modelos**, abre a revisão, vê a comparação com a versão vigente,
   devolve com comentário; `qualidade.ar` corrige e reenvia; `gestor.pd` aprova com a senha de rede e
   vigência imediata. A versão nova fica vigente e a anterior substituída.
3. `qualidade.ar` tenta aprovar a própria revisão: recusado. Senha errada três vezes na aprovação:
   bloqueio da feature 005.
4. Histórico da Entrada: versões com situação, etapas, pessoas, motivo, impacto e documentos
   iniciados em cada versão; comparação entre a 05 e a nova.
5. Layout: o mesmo ciclo com vigência futura; até a data, documentos novos continuam no layout
   vigente.
6. Retirada de uso do modelo da Alteração de Projeto: pedida pela Qualidade, aprovada pelo Gestor com
   senha; criar nova Alteração passa a ser recusado; as existentes continuam consultáveis.
7. Verificação de integridade de uma versão publicada: íntegra; depois de alterar a definição direto
   no banco (papel dono), divergência apontada.
