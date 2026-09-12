# ADR-001: Outbox transacional no MySQL

## Status

Aceito na reunião técnica. A decisão foi fechada por Larissa em `[09:08] Larissa` e confirmada no resumo em `[09:48] Larissa`.

## Contexto

`changeStatus` já executa uma transação que altera `order`, registra `order_status_history` e atualiza o estoque; uma chamada HTTP síncrona poderia bloquear outros pedidos quando o cliente estivesse lento ou indisponível, conforme `[09:04] Bruno`.

**Inferência do código:** `src/modules/orders/order.service.ts:126–179` confirma que `changeStatus` usa `prisma.$transaction` e que as alterações de pedido, histórico e estoque ocorrem dentro desse fluxo transacional.

Na reunião, Diego definiu o padrão outbox como o registro do evento na mesma transação SQL de `orders` e `order_status_history`, com entrega posterior por um worker separado: `[09:06] Diego`. O datasource existente usa MySQL, conforme `prisma/schema.prisma:5–9`.

`webhook_outbox` não existe no código-base; é um artefato proposto para a solução, conforme a verificação registrada em `docs/mapping.md`.

## Decisão

Persistir o evento de mudança de status em uma outbox no MySQL existente, dentro da mesma transação de `changeStatus` que atualiza o pedido, o histórico e o estoque. O enqueue deve usar a transação atual; se o registro do evento falhar, a transação deve sofrer rollback, conforme `[09:40] Bruno` e `[09:41] Diego`.

A entrega HTTP ficará desacoplada dessa transação e será realizada posteriormente por um worker separado, conforme `[09:06] Diego`. Esta decisão é arquitetural: nomes finais de colunas, schema final, estratégia de claim/lock e demais detalhes de implementação ficam para o FDD. Retenção e arquivamento de eventos entregues permanecem fora do escopo, conforme `[09:08] Diego`.

## Alternativas consideradas

- **[Discutida na reunião]** HTTP síncrono dentro de `changeStatus`: motivo do descarte — um cliente lento poderia bloquear outras mudanças de status e a indisponibilidade do cliente não deve provocar rollback do status. Fontes: `[09:04] Bruno` e `[09:06] Diego`.
- **[Discutida na reunião]** Redis Streams/Redis Cluster: motivo do descarte — exigiria infraestrutura adicional e foi considerado overengineering para um time pequeno; o MySQL existente resolve a necessidade. Fonte: `[09:07] Larissa` e `[09:07] Diego`.

## Consequências positivas

- O commit do status e o registro do evento ficam atômicos: se a transação principal confirmar, o evento foi registrado; se houver rollback, o registro acompanha o rollback, conforme `[09:06] Diego` e `[09:48] Larissa`.
- A mudança de status não depende da disponibilidade ou do tempo de resposta do cliente durante a transação, conforme `[09:04] Bruno`.
- A solução reutiliza o MySQL já existente e evita adicionar Redis à infraestrutura, conforme `[09:07] Larissa` e `[09:07] Diego`.
- O worker pode fazer a entrega depois do commit da transação, conforme `[09:06] Diego`.

## Consequências negativas e trade-offs

- A entrega deixa de ser síncrona com a mudança de status: manter o evento persistido não significa que a chamada HTTP ao cliente já foi concluída; a entrega depende do worker separado, conforme `[09:06] Diego`.
- A solução introduz o custo operacional de manter uma outbox e um worker, além do fluxo transacional já existente; esse custo é aceito para evitar bloqueios e inconsistências.
- Retenção e arquivamento dos eventos entregues não são resolvidos por este ADR e deverão ser definidos posteriormente; esse ponto foi deixado fora do escopo por `[09:08] Diego`.
- A estratégia final de claim/lock e os nomes finais do schema permanecem em aberto para o FDD; este ADR não define esses detalhes.

## Rastreabilidade

### Transcrição

- Decisão de usar outbox no MySQL: `[09:08] Larissa` e confirmação no resumo `[09:48] Larissa`.
- Registro na mesma transação e rollback em caso de falha do enqueue: `[09:40] Bruno` e `[09:41] Diego`.
- Definição do padrão outbox e do worker separado: `[09:06] Diego`.
- Rejeição da chamada HTTP síncrona: `[09:04] Bruno`.
- Rejeição de Redis por infraestrutura adicional/overengineering: `[09:07] Larissa` e `[09:07] Diego`.
- Retenção/arquivamento fora do escopo: `[09:08] Diego`.

### Código existente

- `src/modules/orders/order.service.ts:126–179` — **Inferência do código:** `changeStatus` usa `prisma.$transaction` e atualiza `order`, `orderStatusHistory` e estoque no mesmo fluxo.
- `prisma/schema.prisma:5–9` — datasource existente configurado para MySQL.
- `prisma/schema.prisma:74–130` — modelos existentes `Order` e `OrderStatusHistory`, incluindo a relação semântica do histórico de status.
- `docs/mapping.md` — relaciona DEC-01 ao ponto transacional de `OrderService.changeStatus` e confirma que `webhook_outbox` ainda não existe.

### Classificação e limites

- `Fechado na reunião`: persistir a outbox no MySQL existente e no mesmo fluxo transacional da mudança de status.
- `Inferência do código`: o ponto de integração é o `prisma.$transaction` existente em `changeStatus`; o código atual não implementa a outbox.
- `Artefato proposto`: `webhook_outbox`; não existe em `prisma/schema.prisma` nem deve ser tratado como já implementado.
- `FDD`: schema final, nomes de colunas, claim/lock do worker e retenção/arquivamento.
