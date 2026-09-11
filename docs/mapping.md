# Matriz de evidências e levantamento de fontes

## 1. Objetivo e método

Este documento cruza a reunião registrada em [`TRANSCRICAO.md`](../TRANSCRICAO.md) com o código existente. Ele serve como mapa de evidências para a feature de webhooks outbound de mudança de status de pedidos.

- Informações originadas na reunião usam a localização `[hh:mm] Participante` e, quando útil, o intervalo de linhas da transcrição.
- Informações originadas no repositório usam caminho e linhas do arquivo.
- `Fechado` significa que houve consenso explícito na reunião.
- `Proposto` significa que foi sugerido para implementação, mas ainda não existe no código-base.
- `Inferência do código` é uma leitura estrutural do repositório, não uma decisão tomada na reunião.

## 2. Contexto da fonte primária

| Campo | Evidência |
| --- | --- |
| Reunião | Sistema de Webhooks de Notificação de Pedidos |
| Data registrada | Quinta-feira, sem data calendárica explícita no arquivo |
| Duração/local | Aproximadamente 55 minutos, call remota via Meet |
| Participantes | Larissa (Tech Lead), Marcos (Product Manager), Bruno (Engenheiro Pleno — Pedidos), Diego (Engenheiro Sênior — Plataforma), Sofia (Engenheira de Segurança) |
| Evidência de participação | `[09:00] Larissa`, `[09:00] Marcos`, `[09:04] Bruno`, `[09:19] Sofia`, `[09:05] Diego` (entrada na call) |
| Fonte | [`TRANSCRICAO.md`](../TRANSCRICAO.md), linhas 1–12 e registros de entrada acima |

## 3. Requisitos funcionais

| ID | Requisito | Evidência da transcrição | Relação com o código |
| --- | --- | --- | --- |
| RF-01 | Enviar notificações outbound quando o status de um pedido mudar. Os clientes recebem; não enviam webhooks para a plataforma. | `[09:00] Marcos`, `[09:02] Marcos` (linhas 18, 24–28) | O domínio de pedidos está em `src/modules/orders/`; não há módulo de webhooks implementado. |
| RF-02 | Permitir cadastrar um webhook por API, via `POST`, informando `url` e a lista de status/eventos desejados; a secret é gerada pela plataforma e devolvida na criação. | `[09:31] Marcos` (linhas 182–184) | O padrão de criação por controller/service/repository/schema aparece, por exemplo, em `src/modules/customers/`. O endpoint de webhook é proposto. |
| RF-03 | Associar o cadastro a um `customer_id` informado no body ou no path; ele não deve ser derivado do JWT atual. | `[09:32] Bruno`, `[09:32] Marcos`, `[09:32] Larissa` (linhas 186–190) | `customerId` é um campo existente em `prisma/schema.prisma:74–96` e em `src/modules/orders/order.schemas.ts:11–16`. |
| RF-04 | Permitir editar a configuração via `PATCH`, removê-la via `DELETE` e listar os webhooks de um customer via `GET`. | `[09:33] Bruno` (linha 192) | O padrão de rotas CRUD autenticadas está em `src/modules/customers/customer.routes.ts:12–24`. |
| RF-05 | Permitir escolher, por endpoint, quais status de pedido serão recebidos; filtrar o evento na inserção da outbox. | `[09:33] Marcos`, `[09:34] Bruno`, `[09:34] Diego` (linhas 194–200) | Os status válidos existentes são o enum `OrderStatus` em `prisma/schema.prisma:16–23`; a transição é centralizada em `src/modules/orders/order.status.ts`. |
| RF-06 | Disponibilizar histórico dos últimos 100 deliveries, incluindo sucesso/falha, payload, resposta e tempo de resposta, em `GET /webhooks/:id/deliveries`. | `[09:34] Marcos` (linha 202) | Não há tabela, rota ou controller de deliveries no código atual. |
| RF-07 | Disponibilizar replay manual de item na DLQ por `POST /admin/webhooks/dead-letter/:id/replay`, recolocando o evento na outbox como pendente. | `[09:18] Diego`, `[09:35] Larissa` (linhas 112–116, 204–206) | O mecanismo de autorização por papel existe em `src/middlewares/auth.middleware.ts:49–61`; a rota de replay ainda não existe. |
| RF-08 | Exigir papel `ADMIN` no replay e registrar quem executou o replay para auditoria. | `[09:35] Sofia`, `[09:36] Larissa` (linhas 208–212) | `requireRole('ADMIN')` é usado em `src/modules/users/user.routes.ts:12–18`; o logger/auditoria existente está em `src/shared/logger/index.ts` e `src/middlewares/request-logger.middleware.ts`. |
| RF-09 | Permitir, por endpoint, rotação da secret; manter a antiga válida por 24 horas e depois invalidá-la. | `[09:21] Sofia`, `[09:22] Sofia` (linhas 126–134) | Não há modelo ou endpoint de secret no código atual. |
| RF-10 | Na mudança de status, criar o evento na mesma transação da atualização do pedido e do histórico; falha ao inserir o evento deve causar rollback. | `[09:40] Bruno`, `[09:41] Diego` (linhas 238–240) | O ponto de extensão real é `src/modules/orders/order.service.ts:126–179`, dentro de `prisma.$transaction`. |
| RF-11 | Persistir na outbox um snapshot do payload no momento da mudança de status, em vez de renderizá-lo durante o envio. | `[09:51] Bruno`, `[09:51] Larissa`, `[09:52] Diego`, `[09:52] Bruno` (linhas 308–314) | O código atual já trabalha com uma transação Prisma e dados relacionais do pedido; a estrutura de snapshot ainda não existe. |
| RF-12 | Entregar o evento com payload JSON contendo `event_id`, `event_type`, timestamp ISO 8601, pedido, customer, status anterior/novo e dados básicos como `total_cents`; não incluir `items`. | `[09:43] Diego`, `[09:44] Bruno` (linhas 254–258) | `Order`, `OrderStatus`, `Customer` e `OrderItem` estão em `prisma/schema.prisma:40–130`; a exclusão de items é regra da feature, não comportamento atual. |

## 4. Requisitos não funcionais e restrições

| ID | Requisito/restrição | Evidência da transcrição | Relação com o código |
| --- | --- | --- | --- |
| RNF-01 | Latência percebida inferior a 10 segundos é suficiente para os clientes. | `[09:02] Marcos` (linhas 20–22) | `GET /orders` e `GET /orders/:id` existem em `src/modules/orders/order.routes.ts:16–17`; webhook é uma alternativa ao polling dos clientes. |
| RNF-02 | Não fazer chamada HTTP síncrona durante a transação de mudança de status; cliente lento ou indisponível não pode travar nem provocar rollback do status por causa da entrega. | `[09:04] Bruno`, `[09:05] Larissa`, `[09:06] Diego` (linhas 30–48) | `src/modules/orders/order.service.ts:131–178` é transacional e contém estoque, pedido e histórico; a entrega deve ficar fora desse processo. |
| RNF-03 | Usar padrão transactional outbox em MySQL, com índice por status e `created_at`, leitura de pendentes em batches pequenos e posterior marcação como entregue. | `[09:06] Diego`, `[09:07] Larissa`, `[09:08] Diego` (linhas 48–58) | O datasource atual é MySQL em `prisma/schema.prisma:5–9`; não existem ainda os modelos/tabelas `webhook_outbox`. |
| RNF-04 | Worker em polling a cada 2 segundos, processando os eventos pendentes mais antigos. | `[09:09] Diego`, `[09:10] Larissa` (linhas 60–68) | `package.json` não possui script `worker`; `src/server.ts` é a única entry point atual. |
| RNF-05 | Worker em processo separado da API, com mesmo banco e mesma stack, mas com instância Prisma própria por processo. | `[09:11] Diego`, `[09:11] Larissa`, `[09:11] Bruno`, `[09:11] Diego`, `[09:29] Diego`, `[09:30] Bruno` (linhas 70–76, 176–180) | `src/server.ts:1–27` inicializa a API; `src/config/database.ts:4–10` cria o PrismaClient; a nova entry point `src/worker.ts` é proposta e ainda inexistente. |
| RNF-06 | Manter ordenação por `order_id` enquanto houver um único worker e processar pela ordem de `created_at`; não prometer ordering global nem ordering após escala horizontal. | `[09:12] Diego`, `[09:13] Diego`, `[09:13] Larissa` (linhas 78–86) | `OrderStatusHistory` é indexado por pedido/data em `prisma/schema.prisma:116–130`; a outbox ainda não existe. |
| RNF-07 | Usar retry com backoff e limite de cinco tentativas: 1 minuto, 5 minutos, 30 minutos, 2 horas e 12 horas; depois, considerar falha permanente. | `[09:15] Diego`, `[09:16] Larissa`, `[09:17] Diego`, `[09:17] Larissa` (linhas 90–108) | Não existe worker/retry no repositório atual. |
| RNF-08 | Persistir falha permanente em tabela separada `webhook_dead_letter`, com payload, motivo e timestamp, para debug e reprocessamento. | `[09:17] Larissa`, `[09:18] Diego` (linhas 108–114) | Não existe modelo correspondente em `prisma/schema.prisma` nem migration. |
| RNF-09 | Timeout da chamada HTTP do worker de 10 segundos; timeout conta como falha e entra no retry. | `[09:42] Sofia`, `[09:42] Diego` (linhas 248–252) | Não há cliente HTTP ou worker no código atual. |
| RNF-10 | Assinar o corpo do request com HMAC-SHA256 e enviar a assinatura em header; usar uma secret única por endpoint. | `[09:19] Sofia`, `[09:20] Sofia`, `[09:21] Sofia`, `[09:22] Sofia` (linhas 118–134) | Não há implementação HMAC nem armazenamento de secrets. |
| RNF-11 | Exigir URL HTTPS e rejeitar HTTP na validação; rejeitar payload acima de 64 KB, sem truncamento. | `[09:23] Sofia`, `[09:24] Diego`, `[09:24] Larissa` (linhas 136–144) | Schemas Zod são usados em `src/middlewares/validate.middleware.ts:11–36`; o parser global aceita 1 MB em `src/app.ts:55–60`, portanto o limite de 64 KB da feature precisa ser específico. |
| RNF-12 | Garantir semântica at-least-once; permitir duplicidade e fornecer `X-Event-Id` com UUID único para deduplicação no cliente. | `[09:24] Diego`, `[09:25] Diego`, `[09:26] Larissa` (linhas 146–158) | O padrão de UUID já é usado nos IDs Prisma (`prisma/schema.prisma:25–130`) e pela biblioteca `uuid` em `src/middlewares/request-logger.middleware.ts:2,6`. |
| RNF-13 | Enviar headers `X-Event-Id`, `X-Signature`, `X-Timestamp`, `X-Webhook-Id` e `Content-Type: application/json`. | `[09:44] Diego`, `[09:44] Sofia`, `[09:45] Diego` (linhas 260–266) | Não há emissor HTTP de webhook no código atual. |
| RNF-14 | Reutilizar `AppError`, Pino, middleware de erro, módulos em camadas, schemas Zod e prefixo `WEBHOOK_` para os códigos de erro. | `[09:27] Bruno`, `[09:28] Bruno`, `[09:29] Larissa`, `[09:30] Larissa` (linhas 160–180) | `AppError`/erros HTTP: `src/shared/errors/app-error.ts:3–15` e `src/shared/errors/http-errors.ts:3–63`; Pino: `src/shared/logger/index.ts:1–32`; erro central: `src/middlewares/error.middleware.ts:14–65`. |
| RNF-15 | CRUD de configuração usa autenticação normal; a restrição `ADMIN` é específica do replay. | `[09:35] Sofia`, `[09:36] Marcos`, `[09:37] Sofia` (linhas 208–216) | `authenticate`/`requireRole` estão em `src/middlewares/auth.middleware.ts:27–61`; rotas de domínio usam `router.use(authenticate)`, por exemplo `src/modules/orders/order.routes.ts:12–24`. |
| RNF-16 | Revisão de segurança deve ocorrer antes do deploy, com pelo menos dois dias úteis reservados; estimativa total de três sprints. | `[09:45] Marcos`, `[09:46] Larissa`, `[09:46] Sofia`, `[09:47] Larissa` (linhas 268–276) | Restrição de planejamento; não há artefato de cronograma no código. |

## 5. Decisões fechadas

| ID | Decisão | Evidência de fechamento | Consequência/mapeamento |
| --- | --- | --- | --- |
| DEC-01 | Outbox transacional no MySQL existente. | `[09:08] Larissa` e confirmação no resumo `[09:48] Larissa` (linhas 58, 280–282) | Criar persistência dentro da transação de `OrderService.changeStatus`; não adicionar Redis. |
| DEC-02 | Worker separado da API, em polling de 2 segundos. | `[09:10] Larissa`, confirmação `[09:48] Larissa` (linhas 60–72, 280–282) | Nova entry point proposta `src/worker.ts`; mesmo banco, processo distinto. |
| DEC-03 | Single-worker inicialmente, com ordenação por pedido; ordering global não é garantia. | `[09:13] Larissa` (linhas 78–88) | Escala futura exigirá particionamento por `order_id` ou lock pessimista; ambos ficaram para o futuro. |
| DEC-04 | Cinco tentativas com backoff `1m/5m/30m/2h/12h`; falha permanente vai para DLQ separada. | `[09:17] Larissa` e resumo `[09:48] Larissa` (linhas 102–114, 280–282) | Criar `webhook_dead_letter` e endpoint de replay administrativo. |
| DEC-05 | HMAC-SHA256, secret única por endpoint e rotação com grace period de 24 horas. | `[09:22] Sofia` (linha 134) | Secret não pode ser global; modelo precisa suportar secret atual e anterior com expiração. |
| DEC-06 | Entrega at-least-once com `X-Event-Id` UUID para deduplicação pelo cliente. | `[09:26] Larissa` (linha 158) | Exactly-once não será implementado; a documentação de integração deve explicar duplicidade. |
| DEC-07 | Reaproveitar padrões e infraestrutura existentes: `AppError`, Pino, error middleware, schemas Zod, módulos em `src/modules` e códigos `WEBHOOK_*`. | `[09:30] Larissa` (linha 180) | O módulo deve seguir a organização controller/service/repository/routes/schemas e usar o Prisma existente. |
| DEC-08 | Replay de DLQ exige `ADMIN`; CRUD de configuração aceita qualquer role autenticada nesta fase. | `[09:36] Larissa`, `[09:37] Sofia` (linhas 208–216) | Reusar `requireRole`; endurecimento do CRUD fica para depois. |
| DEC-09 | Inserir evento na mesma transação de mudança de status e armazenar snapshot renderizado na inserção. | `[09:40] Bruno`, `[09:41] Diego`, `[09:52] Larissa`, `[09:52] Bruno` (linhas 238–244, 308–314) | A integração deve receber o `tx` atual; o evento não pode ser reconstruído com o estado futuro do pedido. |
| DEC-10 | Payload enxuto, sem `items`, e headers de identificação, assinatura, timestamp e tipo de conteúdo definidos. | `[09:43] Diego`, `[09:44] Diego`, `[09:44] Sofia` (linhas 254–266) | Detalhes adicionais continuam disponíveis via `GET /orders/:id`; o consumidor identifica o endpoint por `X-Webhook-Id`. |
| DEC-11 | IDs de outbox usam UUID, seguindo o restante do projeto. | `[09:51] Diego`, `[09:51] Larissa` (linhas 302–306) | Não usar auto incremento na nova entidade. |

## 6. Alternativas descartadas

| ID | Alternativa | Motivo do descarte | Evidência |
| --- | --- | --- | --- |
| ALT-01 | Chamada HTTP síncrona dentro de `changeStatus`. | Poderia bloquear outras mudanças de pedido por cliente lento e criaria a decisão indevida de fazer rollback quando o cliente estivesse fora do ar. | `[09:04] Bruno`, `[09:05] Larissa`, `[09:06] Diego` (linhas 30–48) |
| ALT-02 | Redis Streams/Redis Cluster como fila. | Exigiria infraestrutura adicional e foi considerado overengineering para um time pequeno; o MySQL existente atende. | `[09:07] Larissa`, `[09:07] Diego` (linhas 50–52) |
| ALT-03 | Trigger/listener do banco para acordar o worker. | MySQL não fornece listener externo equivalente a `NOTIFY/LISTEN`; trigger só executaria SQL e soluções improvisadas seriam inadequadas. | `[09:09] Bruno`, `[09:09] Diego` (linhas 62–64) |
| ALT-04 | Retry indefinido. | Poderia deixar evento pendurado indefinidamente quando o cliente desaparecesse; adotou-se teto de cinco tentativas. | `[09:15] Diego` (linha 96) |
| ALT-05 | Apenas três tentativas. | Janela curta demais para indisponibilidades planejadas de até duas horas; cinco tentativas cobrem uma janela de aproximadamente 15 horas. | `[09:16] Bruno`, `[09:16] Diego`, `[09:17] Diego` (linhas 98–104) |
| ALT-06 | Marcar falha na própria outbox em vez de usar tabela de DLQ separada. | A tabela separada mantém a outbox principal mais limpa e preserva evidência para debug/reprocessamento. | `[09:17] Larissa`, `[09:18] Diego` (linhas 108–110) |
| ALT-07 | Exactly-once. | Exigiria coordenação complexa entre plataforma e cliente; at-least-once com `event_id` resolve o caso de uso com deduplicação no consumidor. | `[09:25] Sofia`, `[09:25] Diego`, `[09:26] Larissa` (linhas 152–158) |
| ALT-08 | Secret global da plataforma. | Vazamento de uma secret comprometeria todos os endpoints; foi escolhida secret única por endpoint. | `[09:21] Sofia` (linha 126) |
| ALT-09 | Renderizar payload apenas no momento do envio. | O pedido poderia mudar depois, fazendo o evento representar estado diferente daquele que causou a notificação; adotou-se snapshot na inserção. | `[09:51] Bruno`, `[09:51] Larissa`, `[09:52] Diego` (linhas 308–314) |

## 7. Questões abertas ou adiadas

| ID | Questão/status | Evidência | Impacto atual |
| --- | --- | --- | --- |
| QA-01 | Rate limiting de envio por cliente ainda não foi decidido; deve ser observado e decidido se virar problema. | `[09:38] Diego`, `[09:39] Larissa`, resumo `[09:48] Larissa` (linhas 224–230, 282) | A primeira versão pode enviar muitas chamadas para um customer em uma janela curta. |
| QA-02 | Estratégia de escala para múltiplos workers e ordering futuro. Foram citados particionamento por `order_id` e lock pessimista, mas adiados. | `[09:12] Diego`, `[09:13] Diego` (linhas 78–86) | A solução inicial depende de single-worker; não há garantia global. |
| QA-03 | Política de arquivamento de linhas entregues foi apenas sugerida como “depois de 30 dias ou assim” e ficou fora desta feature. | `[09:08] Diego` (linha 56) | A retenção e o job de arquivamento precisam ser definidos em trabalho posterior. |
| QA-04 | Endurecer permissões do CRUD de configuração foi deixado para mais tarde. | `[09:36] Marcos`, `[09:37] Sofia` (linhas 214–216) | Nesta fase, qualquer role autenticada pode usar o CRUD. |
| QA-05 | Aviso por e-mail para falhas consecutivas foi adiado para próxima fase. | `[09:37] Marcos`, `[09:37] Larissa`, `[09:38] Marcos` (linhas 218–222) | Não haverá fallback de e-mail no escopo atual. |
| QA-06 | Painel visual para o cliente foi separado como projeto do time de frontend. | `[09:39] Marcos`, `[09:40] Larissa` (linhas 232–236) | A entrega atual expõe endpoints; não inclui dashboard. |
| QA-07 | Prazo foi estimado, mas a transcrição não registra uma data calendárica completa para “fim de novembro”. | `[09:45] Marcos`, `[09:47] Marcos` (linhas 268–278) | O compromisso externo precisa ser confirmado por Marcos; a estimativa interna é de três sprints. |

## 8. Itens fora de escopo

| ID | Item excluído | Evidência da transcrição |
| --- | --- | --- |
| OOS-01 | Webhooks inbound enviados pelos clientes para a plataforma. A feature é somente outbound. | `[09:02] Sofia`, `[09:02] Marcos`, `[09:03] Sofia` (linhas 24–28) |
| OOS-02 | Arquivamento/limpeza de linhas entregues da outbox nesta fase. | `[09:08] Diego` (linha 56) |
| OOS-03 | Garantia de ordering global ou solução de escala para múltiplos workers. | `[09:13] Larissa` (linha 86) |
| OOS-04 | E-mail de alerta/fallback quando o webhook falhar repetidamente. | `[09:37] Larissa`, `[09:38] Marcos` (linhas 218–222) |
| OOS-05 | Dashboard/painel visual para o cliente. | `[09:40] Larissa` (linhas 232–236) |
| OOS-06 | Rate limiting de saída na primeira fase; será observado antes de decidir. | `[09:39] Diego`, `[09:39] Larissa` (linhas 224–230) |
| OOS-07 | Exactly-once. É uma alternativa rejeitada, não uma propriedade da solução. | `[09:25] Diego`, `[09:26] Larissa` (linhas 154–158) |

## 9. Mapeamento do código existente

### 9.1 Arquivos e módulos que existem e devem ser reutilizados

| Caminho existente | Evidência verificável no código | Uso esperado na feature |
| --- | --- | --- |
| `src/modules/orders/order.service.ts:126–179` | `changeStatus` abre `prisma.$transaction`, valida transição, atualiza estoque, `order` e `orderStatusHistory`. | Inserir o enqueue/snapshot da outbox dentro do mesmo `tx`, antes do commit. |
| `src/modules/orders/order.status.ts:1–38` | Define `OrderStatus`, transições permitidas e regras de débito/reposição de estoque. | Usar os status existentes como catálogo de filtros e eventos; não duplicar regra de transição. |
| `src/modules/orders/order.routes.ts:12–24` | Todas as rotas de pedidos usam `authenticate`, `validate` e controllers. | Seguir o mesmo padrão de composição para rotas de webhook. |
| `src/modules/orders/order.schemas.ts:1–34` | Usa Zod, UUID e `z.nativeEnum(OrderStatus)` para contratos. | Criar schemas de webhook com o mesmo padrão, incluindo URL HTTPS e limite de payload específico. |
| `src/modules/orders/order.repository.ts:18–68` | Repository recebe `PrismaClient` e encapsula consultas de pedido. | Referência para repositories de webhook e deliveries; o enqueue transacional deve aceitar `Prisma.TransactionClient`. |
| `src/app.ts:22–52` | `buildControllers` instancia repositories/services/controllers e retorna o conjunto de controllers. | Registrar o novo módulo nessa composição quando ele for implementado. |
| `src/app.ts:55–73` | Configura JSON, request logger, `/api/v1`, 404 e middleware de erro. | Montar rotas de configuração/replay sob `/api/v1` e respeitar o pipeline global. |
| `src/routes/index.ts:13–30` | Declara `Controllers` e monta `/auth`, `/users`, `/customers`, `/products` e `/orders`. | Adicionar o router de webhooks e os tipos correspondentes. |
| `src/middlewares/auth.middleware.ts:27–61` | Implementa JWT `authenticate` e `requireRole`. | Proteger CRUD com `authenticate` e replay com `requireRole('ADMIN')`. |
| `src/middlewares/validate.middleware.ts:11–36` | Faz parse dos schemas e converte `ZodError` em `ValidationError`. | Validar URL, status, IDs, rotação e payload antes dos controllers. |
| `src/shared/errors/app-error.ts:3–15` | Define `statusCode`, `errorCode` e `details`. | Criar erros específicos com códigos `WEBHOOK_*` mantendo o contrato de resposta. |
| `src/shared/errors/http-errors.ts:3–63` | Oferece erros HTTP reutilizáveis, incluindo 400/401/403/404/409/422. | Subclassificar/reutilizar para URL inválida, webhook inexistente, secret etc. |
| `src/middlewares/error.middleware.ts:14–65` | Trata `AppError`, Zod, conflitos/not-found Prisma e loga erros não tratados. | Evitar novo middleware de erro; integrar os erros do módulo ao pipeline existente. |
| `src/shared/logger/index.ts:1–32` | Configura Pino, ISO timestamp e redaction de authorization, passwords e tokens. | Reutilizar para logs de delivery e auditoria; não registrar secrets em claro. |
| `src/middlewares/request-logger.middleware.ts:5–27` | Gera/propaga `X-Request-Id` e registra duração, status, rota e usuário. | Usar o mesmo padrão de correlação nas rotas administrativas. |
| `src/config/database.ts:1–10` | Expõe `createPrismaClient()` e um `prisma` singleton por processo. | A API e o worker devem criar uma instância cada, apontando para a mesma `DATABASE_URL`. |
| `src/server.ts:1–27` | Entry point HTTP, bootstrap, shutdown e disconnect do Prisma. | Modelo para a nova entry point de worker; não executar worker dentro deste processo. |
| `prisma/schema.prisma:5–9` | Datasource MySQL com `DATABASE_URL`. | Adicionar modelos da feature em mudança futura de schema, sem introduzir Redis. |
| `prisma/schema.prisma:16–23` | Enum `OrderStatus`: `PENDING`, `PAID`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`. | Base para a lista de status que cada webhook pode assinar. |
| `prisma/schema.prisma:40–96` | Modelos `Customer` e `Order`, relação por `customerId`, total e status. | Dados mínimos para compor o payload e relacionar configurações ao customer. |
| `prisma/schema.prisma:116–130` | `OrderStatusHistory` com `fromStatus`, `toStatus`, `changedAt` e índice por pedido/data. | Referência semântica para o evento de mudança; não substitui a outbox. |
| `package.json:7–20` | Scripts de `dev`, `build`, `start`, migração, teste e lint; não há `worker`. | Incluir script separado `worker` em implementação futura. |
| `tests/orders.test.ts` e `tests/auth.test.ts` | Testes existentes cobrem pedidos, estoque, histórico e autenticação. | Acrescentar testes de integração da mudança transacional, autorização e endpoints em trabalho futuro. |

### 9.2 Arquivos citados na reunião, mas ainda inexistentes

| Artefato proposto | Fonte | Situação encontrada |
| --- | --- | --- |
| `src/modules/webhooks/` com controller, service, repository, routes e schemas | `[09:27] Bruno` (linhas 160–166) | Não existe no repositório; é a estrutura alvo. |
| `src/modules/webhooks/webhook.worker.ts` ou `webhook.processor.ts` | `[09:28] Bruno` (linhas 164–168) | Não existe; nome final ainda não foi fixado. |
| `src/worker.ts` | `[09:11] Larissa`, `[09:28] Bruno` (linhas 70–72, 164–166) | Não existe; será entry point separada proposta. |
| Script `npm run worker` | `[09:11] Larissa` (linha 72) | Não existe em `package.json`; é requisito de execução proposto. |
| Tabela/modelo `webhook_outbox` | `[09:06] Diego` (linha 48) | Não existe em `prisma/schema.prisma` nem na migration atual. |
| Tabela/modelo `webhook_dead_letter` | `[09:18] Diego` (linha 110) | Não existe em `prisma/schema.prisma` nem na migration atual. |
| Tabela de configuração de webhook | `[09:21] Bruno`, `[09:21] Sofia` (linhas 128–130) | Não existe; campos discutidos: URL, secret, `customer_id` e estado ativo. |

## 10. Lacunas e cuidados de rastreabilidade

1. A transcrição não informa a data calendárica da reunião; “fim de novembro” aparece como prazo de negócio, mas não como data completa.
2. A reunião define o contrato conceitual, mas não fecha todos os detalhes de persistência: nomes finais de colunas, estratégia de claim/lock do worker, formato exato de resposta HTTP e política de retenção da DLQ continuam pendentes.
3. O código atual não contém a feature de webhooks. Portanto, qualquer referência a `webhook_outbox`, `webhook_dead_letter`, `src/modules/webhooks` ou `src/worker.ts` neste documento é explicitamente uma referência proposta pela reunião, nunca uma afirmação de que o artefato já exista.
4. Não foram feitas alterações em `src/`, `prisma/`, `tests/` ou nos arquivos existentes; este levantamento adiciona somente este arquivo de documentação.
