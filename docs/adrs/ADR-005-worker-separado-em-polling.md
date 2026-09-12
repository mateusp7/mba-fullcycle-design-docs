# ADR-005: Worker separado em polling

## Status

Aceito na reunião técnica.

## Contexto

O worker precisa ler os eventos pendentes da outbox e disparar as entregas sem
ficar dentro do processo da API. Diego propôs polling em loop a cada 2 segundos,
buscando os eventos pendentes mais antigos, e Larissa registrou a decisão de
aceitar a latência mínima de 2 segundos no pior caso ([09:09] Diego; [09:10]
Larissa). Marcos confirmou que 2 segundos atende ao requisito ([09:10] Marcos).

Diego também definiu que o worker deve rodar como processo separado da API para
não depender do reinício da API ([09:11] Diego). Larissa propôs uma nova
entry point `src/worker.ts` (**artefato proposto/inexistente**) e o script `npm run worker` ([09:11] Larissa). Esses
artefatos são propostos e ainda inexistentes no código-base, conforme
`docs/mapping.md`.

O processo separado deve usar o mesmo banco e a mesma stack, mas com uma
instância própria de `PrismaClient` por processo ([09:11] Diego; [09:29] Diego;
[09:30] Bruno). **Inferência do código:** `src/server.ts:1-27` é a entry point
HTTP atual, enquanto `src/config/database.ts:1-10` expõe
`createPrismaClient()` e um singleton por processo.

## Decisão

Adotar um worker separado da API, executado como processo próprio, que faça
polling da outbox em loop a cada 2 segundos e busque os eventos pendentes mais
antigos ([09:09] Diego; [09:10] Larissa). O worker e a API apontarão para o
mesmo banco por meio da mesma `DATABASE_URL` e usarão a mesma stack, mantendo
uma instância nova de `PrismaClient` em cada processo ([09:11] Diego; [09:29]
Diego; [09:30] Bruno).

Inicialmente, o arranjo será single-worker. O processamento seguirá a ordem de
`created_at` da outbox, com ordering por `order_id` enquanto houver um único
worker; não será prometido ordering global ([09:12] Diego; [09:13] Larissa).

`src/worker.ts` e o script `npm run worker` permanecem artefatos propostos e
inexistentes, destinados a uma implementação futura ([09:11] Larissa).
Detalhes de claim/lock, particionamento por `order_id` e eventual escala para
múltiplos workers ficam adiados para o FDD ([09:12] Diego; [09:13] Diego;
[09:13] Larissa).

## Alternativas consideradas

- **[Discutida na reunião]** Trigger/listener do banco: descartado porque o MySQL não fornece um listener externo equivalente a `NOTIFY/LISTEN`; triggers executam SQL, mas não notificam um processo externo, e os improvisos mencionados foram considerados inadequados. Fonte: [09:09] Diego.
- **[Discutida na reunião]** Worker dentro do processo da API: descartado porque o reinício da API faria o worker depender da disponibilidade desse processo. Fonte: [09:11] Diego.
- **[Plausível, não atribuída à reunião]** Scheduler externo: não adotado neste ADR porque introduziria um componente operacional adicional para disparar uma rotina que o polling contínuo já cobre; essa alternativa não consta na transcrição.

## Consequências positivas

- O polling de 2 segundos atende ao limite de latência aceito na reunião, inferior a 10 segundos ([09:09] Diego; [09:10] Marcos; [09:10] Larissa).
- A disponibilidade do worker fica desacoplada do ciclo de reinício da API, pois são processos distintos ([09:11] Diego).
- O worker reutiliza o banco e a stack existentes, mantendo uma instância de `PrismaClient` própria para seu processo ([09:11] Diego; [09:29] Diego; [09:30] Bruno).
- A leitura dos pendentes mais antigos e o processamento inicial single-worker estabelecem um comportamento previsível por `created_at` e `order_id` dentro dos limites registrados ([09:09] Diego; [09:12] Diego; [09:13] Larissa).

## Consequências negativas e trade-offs

- O polling introduz uma latência mínima aceita de 2 segundos e pode consultar a outbox mesmo quando não houver novos eventos ([09:10] Larissa; [09:09] Diego).
- Manter a API e o worker como processos separados acrescenta uma unidade operacional de execução, observabilidade e desligamento; o custo é aceito para evitar a dependência do worker em relação ao reinício da API ([09:11] Diego).
- O arranjo inicial depende de um único worker e não oferece ordering global; escalar horizontalmente pode perder a garantia de ordenação, e particionamento por `order_id` ou lock pessimista foi deixado para o futuro ([09:12] Diego; [09:13] Diego; [09:13] Larissa).
- A estratégia detalhada de claim/lock não é definida por este ADR e permanece uma pendência do FDD ([09:12] Diego; [09:13] Larissa).

## Rastreabilidade

### Transcrição

- Polling em loop a cada 2 segundos e busca dos pendentes mais antigos: [09:09] Diego.
- Aceite da latência mínima de 2 segundos: [09:10] Marcos; [09:10] Larissa.
- Processo separado da API: [09:11] Diego; proposta de `src/worker.ts` e `npm run worker`: [09:11] Larissa.
- Mesmo banco e mesma stack, sem compartilhar o processo: [09:11] Diego.
- `PrismaClient` separado por processo: [09:29] Diego; [09:30] Bruno.
- Single-worker, ordenação por `created_at`/`order_id` e ausência de ordering global: [09:12] Diego; [09:13] Diego; [09:13] Larissa.
- Confirmação no resumo da reunião: [09:48] Larissa.

### Código existente

- `src/server.ts:1-27` — entry point HTTP atual, com bootstrap, shutdown e disconnect do Prisma; **inferência do código**, usada como referência para separar a entry point do worker.
- `src/config/database.ts:1-10` — define `createPrismaClient()` e o singleton `prisma`; **inferência do código**, sustentando uma instância por processo.
- `docs/mapping.md` — relaciona RNF-04/RNF-05/RNF-06 à decisão e confirma que `src/worker.ts`, `npm run worker` e os artefatos de outbox ainda não existem.

### Classificação e limites

- `Fechado na reunião`: worker separado da API, polling de 2 segundos, mesmo banco/stack e `PrismaClient` próprio por processo.
- `Fechado na reunião`: single-worker inicial, processamento por `created_at` e ordering por `order_id`, sem garantia de ordering global.
- `Questão aberta/adiada`: múltiplos workers, particionamento por `order_id`, lock pessimista, claim/lock detalhado e ordering futuro.
- `Inferência do código`: `src/server.ts` é a entry point HTTP atual e `src/config/database.ts` fornece o padrão de cliente Prisma por processo.
- `Artefato proposto`: `src/worker.ts` e o script `npm run worker`; ambos ainda inexistentes.
