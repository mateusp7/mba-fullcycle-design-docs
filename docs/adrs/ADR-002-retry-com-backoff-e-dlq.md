# ADR-002: Retry com backoff e DLQ

## Status

Aceito na reunião técnica.

## Contexto

A entrega de um webhook pode encontrar um cliente offline ou indisponível. Diego
propôs retry com backoff e um teto de tentativas, pois o retry indefinido poderia
deixar o evento pendurado para sempre quando o cliente desaparecesse ([09:15]
Diego). Bruno e Diego avaliaram que três tentativas cobririam uma janela curta
demais para indisponibilidades prolongadas, incluindo uma manutenção de duas horas
([09:16] Bruno; [09:16] Diego).

O timeout HTTP de 10 segundos foi definido como falha da entrega e, portanto,
deve entrar no retry ([09:42] Sofia; [09:42] Diego). O código atual possui
persistência em MySQL, mas não possui worker, mecanismo de retry ou os artefatos
de webhook; essas referências são inferências do levantamento do código, não
implementações existentes.

## Decisão

Adotar no worker de delivery um máximo de cinco tentativas, com a progressão de
backoff `1m/5m/30m/2h/12h`, conforme decidido na reunião ([09:17] Diego; [09:17]
Larissa). Depois do limite, a entrega será considerada uma falha permanente e
persistida em uma DLQ separada, o artefato proposto/inexistente
`webhook_dead_letter` ([09:17] Larissa; [09:18] Diego).

A DLQ deverá preservar, em nível conceitual, o payload, o motivo da falha e o
timestamp para debug e reprocessamento ([09:18] Diego). O replay administrativo
foi anotado como forma de reprocessamento ([09:18] Larissa), mas seu endpoint,
schema, autorização detalhada e fluxo de implementação pertencem ao FDD.

Esta decisão não fecha nomes de colunas, estratégia de claim/lock, política de
retenção ou arquivamento da DLQ, códigos HTTP, nem o contrato completo. A
política de retenção/arquivamento permanece aberta ([09:08] Diego; [09:08]
Diego), e a escala para múltiplos workers foi adiada ([09:12] Diego; [09:13]
Diego).

## Alternativas consideradas

- **[Discutida na reunião]** Retry indefinido: descartado porque poderia deixar
  um evento pendurado para sempre quando o cliente desaparecesse. Motivo do
  descarte. Fonte: [09:15] Diego.
- **[Discutida na reunião]** Três tentativas: descartadas porque a janela seria
  curta demais para indisponibilidades de até duas horas. Motivo do descarte.
  Fontes: [09:16] Bruno; [09:16] Diego.
- **[Discutida na reunião]** Marcar a falha permanente como `failed` na outbox
  principal: descartado em favor de uma tabela separada, para manter a outbox
  limpa e preservar evidência para debug e reprocessamento. Motivo do descarte.
  Fontes: [09:17] Larissa; [09:18] Diego.

## Consequências positivas

- O teto de cinco tentativas evita retenção indefinida de eventos, enquanto a
  progressão definida cobre uma janela significativamente maior que três
  tentativas ([09:15] Diego; [09:16] Diego; [09:17] Diego; [09:17] Larissa).
- Timeouts e indisponibilidades seguem o mesmo tratamento de falha/retry, com
  timeout HTTP de 10 segundos explicitamente incluído ([09:42] Sofia; [09:42]
  Diego).
- A DLQ separada mantém a leitura da `webhook_outbox` mais limpa e conserva
  evidências para debug e reprocessamento ([09:18] Diego).

## Consequências negativas e trade-offs

- Uma entrega pode permanecer sem sucesso por quase 15 horas entre a primeira
  falha e a última tentativa; essa espera foi aceita na reunião ([09:17] Diego;
  [09:17] Marcos).
- Após cinco tentativas, a falha passa a ser permanente para o fluxo automático;
  o reprocessamento depende do replay administrativo anotado ([09:17] Larissa;
  [09:18] Diego).
- A DLQ introduz persistência e operação adicionais, e sua retenção/arquivamento
  ainda não foi definida ([09:08] Diego).

## Rastreabilidade

### Transcrição

- Decisão fechada: cinco tentativas e backoff `1m/5m/30m/2h/12h` ([09:17] Diego;
  [09:17] Larissa).
- Confirmação do resumo: retry com backoff, cinco tentativas e DLQ em tabela
  separada ([09:48] Larissa).
- Timeout de 10 segundos conta como falha e entra no retry ([09:42] Sofia;
  [09:42] Diego).
- DLQ separada com payload, motivo, timestamp e replay administrativo ([09:18]
  Diego; [09:18] Larissa).

### Código existente

- `prisma/schema.prisma:5-9` — datasource MySQL existente, base de persistência
  da solução; não há modelo `webhook_dead_letter` no código-base.
- `src/shared/logger/index.ts:13-29` — Pino existente com timestamp ISO e
  redaction; deve ser reutilizado para observabilidade sem tratar isso como uma
  decisão nova desta ADR.
- `docs/mapping.md` — confirma a relação com RNF-07/RNF-08 e que
  `webhook_dead_letter` é artefato proposto/inexistente.

### Classificação e limites

- `Fechado na reunião`: máximo de cinco tentativas, progressão de backoff
  `1m/5m/30m/2h/12h`, falha permanente após o limite e DLQ separada.
- `Fechado na reunião`: timeout HTTP de 10 segundos é falha e entra no retry.
- `Questão aberta/adiada`: retenção/arquivamento da DLQ e escala para múltiplos
  workers.
- `Inferência do código`: MySQL e Pino são padrões existentes; worker, retry,
  `webhook_outbox` e `webhook_dead_letter` ainda não existem.
- `Artefato proposto`: `webhook_dead_letter`; nomes de colunas, claim/lock,
  retenção, códigos HTTP e contrato completo permanecem para o FDD.
