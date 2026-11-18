# Roteiro de qualificação de instalação (IQ)

Objetivo: demonstrar, com evidência, que o SGP-P&D foi instalado no servidor (homologação ou
produção) conforme o especificado no repositório. Executado pela TI; revisado pela Garantia da
Qualidade. Versão do sistema a qualificar: o commit do `main` liberado.

## Pré-requisitos (TI)

| Item | Conferência |
| --- | --- |
| Servidor Linux com Docker e Docker Compose | `docker version` e `docker compose version` registrados |
| Repositório clonado da rede da empresa no commit a qualificar | `git rev-parse HEAD` registrado |
| `.env` preenchido a partir do `.env.example` (sem valores no repositório) | segredos, AD (`LDAPS`), SMTP, selo, banco |
| Certificado TLS do Nginx em `deploy/nginx/certs/` | emitido para o nome do servidor |
| Certificado PKCS#12 do selo da empresa e CA do AD na pasta protegida `SGP_SECRETS_DIR` (montada em `/run/sgp-segredos`), apontados por `DOCUMENT_SEAL_PKCS12` e `LDAP_CA_CERT_FILE` | senha em `DOCUMENT_SEAL_PASSWORD`; pasta legível só pela TI e pelo uid 1000 |
| Destino das cópias montado de outro servidor ou compartilhamento (`BACKUP_HOST_DIR`), acesso só da TI | nunca no disco dos dados |

## Passos

| Nº | Passo | Resultado esperado | Resultado obtido / evidência | Executor e data |
| --- | --- | --- | --- | --- |
| 1 | `SGP_COMMIT=$(git rev-parse HEAD) docker compose -f docker-compose.yml build` | imagens `sgp-pd:latest` e `sgp-pd-nginx:latest` construídas sem erro | | |
| 2 | `docker compose -f docker-compose.yml up -d` | `db`, `redis`, `web`, `worker` e `nginx` no ar; `web` saudável | | |
| 3 | Abrir o endereço HTTPS do servidor e entrar com uma conta da TI | página inicial; HTTP redireciona para HTTPS | | |
| 4 | Conceder o perfil Administrador do sistema à pessoa da TI (conforme o procedimento de acessos) | perfil ativo, evento na trilha | | |
| 5 | `docker compose -f docker-compose.yml exec web python manage.py qualificacao_instalacao --usuario <login>` | itens IQ-01 a IQ-24 listados; "Qualificação de instalação (IQ) aprovada" | | |
| 6 | Em "Operação e validação", baixar o PDF da qualificação de instalação | relatório com data, executor, versão (commit), resultado de cada item e resumo SHA-256 na tela | | |
| 7 | `docker compose -f docker-compose.yml exec web python manage.py copia_seguranca` | cópia concluída no destino; aparece no painel | | |
| 8 | `docker compose -f docker-compose.yml exec web python manage.py teste_restauracao` | C1 a C6 aprovadas | | |

## Itens conferidos pela qualificação de instalação

IQ-01 versão e commit; IQ-02 Python 3.12; IQ-03 pacotes iguais ao `uv.lock`; IQ-04 PostgreSQL 17
com fuso UTC e UTF8; IQ-05 migrações aplicadas; IQ-06 verificações de implantação do Django (HTTPS
e HSTS pelo Nginx); IQ-07 depuração desligada; IQ-08 chave secreta de produção; IQ-09 cookies
seguros e endereço HTTPS; IQ-10 fuso de exibição, datas em UTC e idioma; IQ-11 variáveis
obrigatórias presentes (valores nunca exibidos); IQ-12 gatilhos de imutabilidade; IQ-13
privilégios do papel da aplicação; IQ-14 papel dono habilitado para o teste de restauração; IQ-15
certificado do selo; IQ-16 destino de cópias separado dos dados; IQ-17 `pg_dump` e `pg_restore` da
versão do servidor; IQ-18 ferramentas e fontes da geração; IQ-19 armazenamento gravável; IQ-20
fila de tarefas; IQ-21 worker e agendamentos; IQ-22 diretório (LDAP); IQ-23 servidor de e-mail;
IQ-24 arquivos estáticos coletados.

## Critério de aceite

Todos os itens aprovados (ou "não aplicável" com justificativa aceita pela Garantia da Qualidade),
cópia e teste de restauração aprovados. Item reprovado: corrigir a instalação, executar de novo e
manter as duas execuções no histórico.

| Executado por (TI) | Data | Revisado por (Garantia da Qualidade) | Data |
| --- | --- | --- | --- |
| | | | |
