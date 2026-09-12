# RFC: Sistema de Webhooks de Notificação de Pedidos

## Metadados

- Autor: não informado na transcrição
- Status: Proposto para revisão
- Data: quinta-feira (data completa não informada na transcrição)
- Revisores: Larissa, Marcos, Bruno, Diego e Sofia

## Resumo executivo (TL;DR)

Três clientes B2B — Atlas Comercial, MaxDistribuição e Nova Cargo — precisam
receber notificações quando o status de seus pedidos mudar. Hoje eles consultam
periodicamente `GET /orders`, o que torna a integração lenta e cara. A reunião
aceitou qualquer latência inferior a 10 segundos como suficiente para o conceito
de tempo real ([09:00]–[09:02] Marcos).

Propõe-se um webhook outbound baseado em transactional outbox no MySQL já
existente. A mudança de status e o registro de um snapshot do evento ocorrerão
na mesma transação; um worker separado fará o envio HTTP por polling a cada dois
segundos. Falhas terão cinco tentativas com backoff e, depois, serão persistidas
em uma DLQ para replay administrativo.

A proposta combina HMAC-SHA256 com secret exclusiva por endpoint, entrega
at-least-once com `X-Event-Id` e reuso dos padrões do projeto. O principal
benefício é desacoplar a disponibilidade dos clientes da transação de pedidos,
sem perder o evento quando a mudança de status for confirmada.

## Contexto e problema

O escopo é exclusivamente outbound: a plataforma envia eventos para os clientes;
eles não enviam webhooks de volta ([09:02] Sofia e Marcos). A necessidade surgiu
porque os clientes precisam reagir às transições de status sem fazer polling
contínuo ([09:00] Marcos). O OMS existente possui uma máquina de estados de
pedidos, histórico de mudanças e atualização transacional de estoque. O ponto de
integração é `changeStatus` em
[`src/modules/orders/order.service.ts`](../src/modules/orders/order.service.ts),
que hoje concentra essas operações em uma transação Prisma.

O código atual usa MySQL via Prisma em
[`prisma/schema.prisma`](../prisma/schema.prisma), organização modular em
`src/modules`, autenticação JWT, schemas Zod, `AppError`, middleware de erros e
Pino. O levantamento do repositório não encontrou emissor de webhook, outbox,
DLQ, worker ou módulo `src/modules/webhooks`; esses são artefatos propostos, não
componentes já implementados.

A chamada HTTP não pode ocorrer dentro da transação de `changeStatus`: um
cliente lento bloquearia outras mudanças, e sua indisponibilidade não deve
causar rollback do pedido ([09:04] Bruno; [09:06] Diego). Ao mesmo tempo, não se
aceita confirmar uma mudança sem registrar o evento correspondente ([09:40]–[09:41]
Bruno e Diego).

### Escopo arquitetural

Inclui a publicação de eventos de mudança de status, configurações de webhook
por customer, seleção de status por endpoint, histórico de deliveries, retry,
DLQ e replay administrativo. O CRUD de configuração usará autenticação normal;
o replay exigirá `ADMIN` e deverá registrar o executor ([09:31]–[09:37] Marcos,
Larissa e Sofia).

Email como fallback e dashboard visual não fazem parte desta fase: email foi
adiado e o dashboard foi separado como projeto de frontend ([09:37]–[09:40]
Larissa e Marcos).

## Proposta técnica

### Visão geral

```text
changeStatus
    └─ transação MySQL: pedido + histórico + snapshot filtrado na webhook_outbox
                                      │ commit
                                      ▼
                         worker separado (polling de 2 s)
                                      │
                         HTTP + HMAC + retry / DLQ
                                      ▼
                             endpoint do cliente
```

1. Quando `changeStatus` for confirmado, a aplicação verificará os status
   assinados pelos endpoints ativos do customer. Para cada endpoint elegível,
   registrará na outbox um evento com UUID e payload renderizado naquele momento.
   Se o enqueue falhar, a transação inteira deverá sofrer rollback. O snapshot
   evita que uma alteração posterior do pedido mude o significado do evento
   original ([09:33]–[09:34] Marcos, Bruno e Diego; [09:40]–[09:41] Bruno e
   Diego; [09:51]–[09:52] Larissa e Diego).

2. Um processo separado da API lerá pequenos batches de eventos pendentes,
   priorizando os mais antigos por `created_at`, e fará polling a cada dois
   segundos. Inicialmente haverá um único worker, com a mesma stack e banco da
   API, mas com seu próprio `PrismaClient` por processo. `src/worker.ts` e o
   script `npm run worker` são entradas propostas para implementação futura,
   ainda inexistentes ([09:08]–[09:13] Diego e Larissa; [09:29]–[09:30] Diego e
   Bruno).

3. O envio usará timeout de 10 segundos. Timeout ou indisponibilidade será
   tratado como falha e seguirá a política de cinco tentativas, com backoff de
   `1m/5m/30m/2h/12h`. Depois do limite, o evento irá para uma tabela DLQ
   separada, preservando payload, motivo e timestamp para diagnóstico e replay
   administrativo ([09:15]–[09:18] Diego, Bruno e Larissa; [09:42] Sofia e
   Diego).

### Segurança e semântica de entrega

- O corpo JSON será assinado com HMAC-SHA256 e a assinatura será enviada em
  header. Cada endpoint terá uma secret própria; na rotação, a secret antiga
  continuará válida por 24 horas antes de ser invalidada ([09:19]–[09:22]
  Sofia).
- O endpoint cadastrado deverá ser HTTPS. Payloads acima de 64 KB serão
  rejeitados, sem truncamento ([09:23]–[09:24] Sofia, Diego e Larissa).
- O evento será entregue com semântica at-least-once. `X-Event-Id` carregará o
  UUID criado na entrada da outbox, e o cliente será responsável por deduplicar
  reenvios. Exactly-once não faz parte da proposta ([09:24]–[09:26] Diego,
  Sofia e Larissa).
- O payload será enxuto: incluirá identificação do evento, timestamps, pedido,
  customer e transição de status, além de dados básicos como `total_cents`; não
  incluirá `items`. Os headers previstos incluem `X-Event-Id`, `X-Signature`,
  `X-Timestamp`, `X-Webhook-Id` e `Content-Type: application/json`
  ([09:43]–[09:45] Diego, Bruno e Sofia).

### Integração com os padrões existentes

A implementação proposta seguirá o padrão de módulos com controller, service,
repository, routes e schemas dentro de `src/modules/webhooks`. Reutilizará
`AppError`, códigos com prefixo `WEBHOOK_`, schemas Zod, middleware de erro e o
logger Pino já existentes. O replay reutilizará `requireRole('ADMIN')`. Essa
integração é uma decisão de reuso e não significa que o novo módulo já exista
([09:27]–[09:30] e [09:35]–[09:36] Bruno, Larissa e Sofia).

O FDD deverá detalhar o schema final das entidades, os contratos HTTP completos,
os códigos de resposta, a estratégia de claim/lock, a matriz de erros, a
observabilidade e os testes. Esses detalhes não são fixados por este RFC.

## Alternativas consideradas

- **[Discutida na reunião] HTTP síncrono dentro de `changeStatus`:** descartada
  porque um endpoint lento ou indisponível bloquearia a transação e poderia
  tornar a entrega uma causa indevida de rollback do pedido. A outbox mantém a
  mudança de status independente da resposta do cliente ([09:04] Bruno; [09:06]
  Diego).
- **[Discutida na reunião] Redis Streams/Redis Cluster:** descartada por exigir
  infraestrutura adicional e ser considerada overengineering para um time
  pequeno. O MySQL já utilizado atende ao padrão outbox ([09:07] Larissa e
  Diego).
- **[Discutida na reunião] Trigger/listener de banco:** não adotada porque
  triggers do MySQL executam SQL, mas não notificam diretamente um processo
  externo; improvisar arquivo ou chamada a endpoint foi considerado inadequado.
  Polling de dois segundos atende à latência aceita ([09:09] Diego; [09:10]
  Marcos e Larissa).
- **[Discutida na reunião] Retry indefinido:** descartado porque poderia manter
  para sempre eventos de um cliente que desapareceu. O teto de cinco tentativas
  estabelece uma falha permanente e permite DLQ ([09:15] Diego).
- **[Discutida na reunião] Exactly-once:** descartado por exigir coordenação
  complexa entre plataforma e consumidor. At-least-once com `X-Event-Id` foi
  considerado suficiente ([09:25] Diego; [09:26] Larissa).

## Questões em aberto

- **Rate limiting de saída:** a reunião decidiu observar o comportamento antes
  de definir uma política. Um customer com muitos pedidos pode receber várias
  chamadas em curto intervalo; a decisão futura afetará o worker e a experiência
  dos consumidores ([09:38]–[09:39] Diego e Larissa).
- **Retenção e arquivamento:** a reunião mencionou arquivar eventos entregues
  depois de algum tempo, mas deixou o tema fora do escopo. A duração exata, o
  tratamento da DLQ e os critérios de limpeza continuam sem decisão
  ([09:08] Diego).
- **Escala para múltiplos workers e ordering futuro:** o arranjo inicial é
  single-worker. Particionamento por `order_id`, lock pessimista, claim/lock e a
  garantia de ordenação após escala foram adiados; por isso, a proposta não
  oferece ordering global ([09:12]–[09:13] Diego e Larissa).

## Impacto e riscos

### Impactos esperados

- A mudança de status passa a gravar também um evento na mesma transação, com
  custo adicional de persistência, mas preserva a consistência entre pedido,
  histórico e notificação.
- API e worker tornam-se processos operacionais distintos. Isso desacopla a
  entrega do ciclo de reinício da API, mas exige executar, monitorar e desligar
  uma unidade adicional.
- Polling introduz uma latência mínima aceita de dois segundos e consultas
  periódicas mesmo quando não houver eventos. Com um único worker, espera-se
  ordenação dos eventos do mesmo pedido por `created_at`; essa expectativa não é
  garantia global e pode não sobreviver à escala horizontal.
- Consumidores precisam lidar com duplicidade, verificar HMAC e acompanhar a
  rotação da secret. A plataforma não promete exactly-once.

### Riscos e limites conhecidos

- **Cliente externo indisponível:** eventos podem permanecer em retry por uma
  janela de quase 15 horas e depois ir para a DLQ. A mitigação definida é
  backoff com limite, persistência separada e replay administrativo; não há
  email automático nesta fase ([09:15]–[09:18] e [09:37] Diego e Larissa).
- **Vazamento de credencial:** uma secret exposta pode permitir falsificação de
  chamadas daquele endpoint. O isolamento por endpoint, HMAC, HTTPS e rotação
  com grace period de 24 horas reduzem o escopo e permitem a migração, mas o
  armazenamento seguro e a proteção completa de logs ainda precisam ser
  detalhados no FDD e revisados por Sofia ([09:19]–[09:24] Sofia; [09:46]
  Sofia).
- **Crescimento da outbox/DLQ:** retenção não definida pode gerar custo e
  dificultar operação. A decisão de arquivamento e limpeza permanece pendente,
  portanto não deve ser tratada como requisito fechado.
- **Escala horizontal:** múltiplos workers podem alterar a ordem dos eventos e
  exigem uma estratégia de claim/lock ainda não escolhida. O primeiro release
  assume single-worker e explicita essa limitação ([09:12]–[09:13] Diego e
  Larissa).

O plano registrado na reunião foi de três sprints, incluindo a revisão de
segurança, com pelo menos dois dias úteis reservados antes do deploy ([09:45]–
[09:47] Marcos, Larissa e Sofia). Trata-se de uma estimativa de planejamento,
não de garantia técnica deste RFC.

## Decisões relacionadas

- [ADR-001: Outbox transacional no MySQL](adrs/ADR-001-outbox-transacional-no-mysql.md)
- [ADR-002: Retry com backoff e DLQ](adrs/ADR-002-retry-com-backoff-e-dlq.md)
- [ADR-003: HMAC-SHA256 com secret por endpoint](adrs/ADR-003-hmac-sha256-com-secret-por-endpoint.md)
- [ADR-004: Entrega at-least-once com X-Event-Id](adrs/ADR-004-entrega-at-least-once-com-x-event-id.md)
- [ADR-005: Worker separado em polling](adrs/ADR-005-worker-separado-em-polling.md)
- [ADR-006: Reuso dos padrões existentes](adrs/ADR-006-reuso-dos-padroes-existentes.md)
