# ADR-006: Reuso dos padrões existentes

## Status

Aceito na reunião técnica.

## Contexto

O código existente organiza o domínio de pedidos em um módulo com rotas autenticadas e validação por schemas, conforme a inferência do código em `src/modules/orders/order.routes.ts:12-24`. Os contratos de entrada usam Zod, UUID e `z.nativeEnum`, conforme `src/modules/orders/order.schemas.ts:1-34`.

Na reunião, Bruno descreveu o padrão de módulos em `src/modules`, com `controller`, `service`, `repository`, `routes` e `schemas`, e propôs que o webhook seguisse a mesma estrutura: `[09:27] Bruno`. Também foi definido que o tratamento de erros deveria seguir `AppError` e códigos específicos, com o prefixo `WEBHOOK_`: `[09:28] Bruno` e `[09:29] Larissa`.

O projeto já possui Pino e middleware de erro centralizado para `AppError`, Zod e Prisma, segundo Bruno: `[09:29] Bruno`. Larissa reforçou o reuso máximo, incluindo schemas Zod e o mesmo padrão de módulo: `[09:29] Larissa`.

## Decisão

Reutilizar os padrões e a infraestrutura existentes do projeto para a solução de webhooks. O artefato proposto `src/modules/webhooks/` deverá seguir, quando implementado, a organização `controller`, `service`, `repository`, `routes` e `schemas`, como os demais módulos: `[09:27] Bruno` e `[09:30] Larissa`.

Os erros específicos do domínio deverão usar `AppError` e códigos com o prefixo `WEBHOOK_`. O módulo deverá reutilizar o Pino existente, o `error middleware` centralizado e schemas Zod, sem criar convenções, logger ou middleware paralelos: `[09:28] Bruno`, `[09:29] Larissa` e `[09:30] Larissa`.

O worker proposto, embora seja um processo separado, deverá usar a mesma stack e o mesmo banco; cada processo terá sua própria instância de `PrismaClient`: `[09:30] Bruno`. O replay da DLQ reutilizará `requireRole` e exigirá `ADMIN`; o CRUD normal autenticado permanece fora do foco deste ADR: `[09:36] Larissa`. O endurecimento desse CRUD foi adiado: `[09:37] Sofia`.

Esta decisão não cria nem afirma a existência do módulo `src/modules/webhooks/` ou de seus controllers, services, repositories, routes, schemas e códigos `WEBHOOK_*`; esses artefatos permanecem propostos/inexistentes. Detalhes de endpoints, composição final do módulo e testes pertencem ao FDD.

## Alternativas consideradas

- **[Plausível, não atribuída à reunião]** Criar convenções, middleware e logger próprios para webhooks: o trade-off seria aumentar a duplicação de infraestrutura e a divergência entre módulos, tornando essa opção menos adequada. Essa alternativa não consta como discutida na transcrição.

## Consequências positivas

- A implementação futura poderá manter a organização já reconhecida no domínio de pedidos, conforme o padrão descrito por Bruno em `[09:27] Bruno`.
- O tratamento de erros preservará o contrato existente de `AppError`, que contém `statusCode`, `errorCode` e `details`, conforme a inferência do código em `src/shared/errors/app-error.ts:3-15`.
- O uso do middleware centralizado permite integrar `AppError`, Zod e Prisma ao pipeline já existente, conforme `src/middlewares/error.middleware.ts:14-65` e a decisão de reuso registrada em `[09:29] Bruno`.
- O logging poderá reutilizar Pino, timestamp ISO e redaction já configurados, conforme `src/shared/logger/index.ts:1-32`, alinhado ao reuso máximo confirmado em `[09:30] Larissa`.

## Consequências negativas e trade-offs

- O módulo de webhooks ficará acoplado às convenções atuais: mudanças futuras nesses padrões poderão exigir ajustes na feature.
- O worker separado precisa manter uma instância própria de `PrismaClient` por processo, apesar de compartilhar stack e banco; isso preserva o isolamento por processo, mas exige configuração e operação coerentes nos dois processos, conforme `[09:30] Bruno`.
- Reutilizar o middleware de erro não define automaticamente os endpoints, a composição final do módulo ou os testes; esses detalhes continuam dependentes do FDD.
- O endurecimento do CRUD de configuração não é resolvido por este ADR e foi adiado para momento posterior, conforme `[09:37] Sofia`.

## Rastreabilidade

### Transcrição

- Estrutura de módulos com `controller`, `service`, `repository`, `routes` e `schemas`: `[09:27] Bruno`.
- Uso de `AppError` e códigos específicos para webhook: `[09:28] Bruno`.
- Prefixo `WEBHOOK_`: `[09:29] Larissa`.
- Reuso de Pino e do middleware de erro centralizado: `[09:29] Bruno`.
- Reuso máximo, schemas Zod e módulo igual aos demais: `[09:29] Larissa`.
- Fechamento da decisão de reuso: `[09:30] Larissa`.
- Mesmo banco e stack, com `PrismaClient` separado por processo: `[09:30] Bruno`.
- Replay com `ADMIN` e reuso de `requireRole`: `[09:36] Larissa`.
- Endurecimento do CRUD adiado: `[09:37] Sofia`.
- Confirmação no resumo da reunião: `[09:48] Larissa`.

### Código existente

- `src/modules/orders/order.routes.ts:12-24` — router autenticado com validação por schema e delegação ao controller.
- `src/modules/orders/order.schemas.ts:1-34` — schemas Zod com UUID e `z.nativeEnum`.
- `src/shared/errors/app-error.ts:3-15` — contrato existente de `AppError` com `statusCode`, `errorCode` e `details`.
- `src/middlewares/error.middleware.ts:14-65` — tratamento central de `AppError`, Zod, Prisma e erros não tratados.
- `src/shared/logger/index.ts:1-32` — logger Pino com timestamp ISO e redaction.
- `docs/mapping.md` — relaciona DEC-07 e DEC-08 aos padrões existentes, ao replay com `requireRole` e aos artefatos de webhooks ainda não implementados.

### Classificação e limites

- `Fechado na reunião`: reuso de padrões de módulos, `AppError`, Pino, `error middleware`, schemas Zod e prefixo `WEBHOOK_`.
- `Fechado na reunião, decisão relacionada`: replay exige `ADMIN` e reutiliza `requireRole`; o CRUD normal autenticado e seu endurecimento não são definidos aqui.
- `Inferência do código`: os arquivos citados demonstram padrões existentes; não demonstram que a feature de webhooks já esteja implementada.
- `Artefato proposto`: `src/modules/webhooks/` e seus artefatos internos; permanecem inexistentes até implementação futura.
- `FDD`: endpoints, composição final do módulo e testes.
