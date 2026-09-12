# ADR-004: Entrega at-least-once com X-Event-Id

## Status

Aceito na reunião técnica.

## Contexto

A entrega de webhooks terá semântica at-least-once, portanto o mesmo evento poderá ser recebido mais de uma vez pelo cliente. Fonte: `[09:24] Diego`.

Para permitir a identificação dessas repetições, foi definido que cada evento terá um `event_id` enviado no cabeçalho `X-Event-Id`, com um UUID gerado quando o evento entrar na outbox e único por evento. Fonte: `[09:25] Diego`.

A deduplicação ficará sob responsabilidade do cliente consumidor. Fonte: `[09:25] Sofia` e `[09:25] Diego`. A documentação de integração deve explicar explicitamente a possibilidade de duplicidade. Fonte: `[09:26] Marcos`.

O código atual oferece padrões relacionados, mas não contém emissor de webhook nem implementa `X-Event-Id`; essa é uma inferência da inspeção do código e do mapping, não uma decisão já implementada.

## Decisão

Adotar entrega at-least-once com `X-Event-Id`. O valor do cabeçalho será o `event_id` do evento, representado por um UUID único por evento e gerado quando o evento entrar na outbox. Fonte: `[09:25] Diego`.

O cliente deverá usar esse identificador para deduplicar entregas repetidas. Fonte: `[09:25] Diego` e `[09:26] Larissa`.

Exactly-once fica fora da solução: a plataforma não oferecerá essa garantia adicional nem assumirá a deduplicação realizada pelo cliente. A escolha foi fechada como “at-least-once com X-Event-Id”. Fontes: `[09:25] Diego` e `[09:26] Larissa`.

Os detalhes do schema e do armazenamento de `event_id` permanecem no escopo do FDD. `X-Event-Id` e `event_id` no webhook são artefatos e comportamento propostos, ainda inexistentes no código atual.

## Alternativas consideradas

- **[Discutida na reunião] Exactly-once:** descartada porque exigiria coordenação mais complexa entre os dois lados. Fontes: `[09:25] Sofia` e `[09:25] Diego`.
- **[Plausível, não atribuída à reunião] Sem identificador estável:** seria menos adequada porque não permitiria deduplicação confiável pelo consumidor. Essa alternativa não consta na transcrição e não foi atribuída a participante.

## Consequências positivas

- O cliente pode reconhecer uma mesma ocorrência lógica mesmo quando receber reenvios, usando o `event_id` do `X-Event-Id`. Fonte: `[09:25] Diego`.
- A decisão torna explícita para os consumidores a semântica de entrega e a necessidade de deduplicação. Fontes: `[09:24] Diego`, `[09:25] Sofia` e `[09:26] Marcos`.
- Evita a coordenação adicional necessária para buscar exactly-once entre plataforma e cliente. Fonte: `[09:25] Diego`.

## Consequências negativas e trade-offs

- Duplicidades são possíveis e a deduplicação passa a ser responsabilidade do cliente. Fontes: `[09:24] Diego` e `[09:25] Sofia`.
- A plataforma não fornece exactly-once; clientes que não implementarem deduplicação poderão processar o mesmo evento mais de uma vez. Fontes: `[09:24] Diego` e `[09:25] Diego`.
- A documentação de integração precisa destacar a possibilidade de duplicidade e o uso do identificador. Fonte: `[09:26] Marcos`.

## Rastreabilidade

### Transcrição

- Semântica at-least-once e possibilidade de duplicidade: `[09:24] Diego`.
- `event_id` no `X-Event-Id`, UUID gerado na entrada da outbox, único por evento e deduplicação pelo cliente: `[09:25] Diego`.
- Responsabilidade de deduplicação atribuída ao cliente: `[09:25] Sofia`.
- Complexidade adicional de exactly-once: `[09:25] Diego`.
- Fechamento da decisão como at-least-once com `X-Event-Id`: `[09:26] Larissa`.
- Resumo confirmando idempotência por `X-Event-Id` e at-least-once: `[09:48] Larissa`.

### Código existente

- `src/middlewares/request-logger.middleware.ts:5-24` — gera ou propaga um UUID e o envia como `X-Request-Id`. **Inferência do código:** é um padrão existente de geração/propagação de identificador de correlação, não uma implementação de `X-Event-Id`.
- `prisma/schema.prisma:25-130` — entidades existentes usam IDs UUID. **Inferência do código:** sustenta a compatibilidade com o padrão UUID, mas não comprova a existência de `event_id`.
- `docs/mapping.md` — registra que não existe emissor de webhook no código atual e que `X-Event-Id`/`event_id` são artefatos propostos.

### Classificação e limites

- **Fechado na reunião:** entrega at-least-once, uso de `X-Event-Id`, UUID único por evento e deduplicação pelo cliente.
- **Inferência do código:** os padrões de UUID e de cabeçalho de correlação existentes não implementam o contrato de webhook.
- **Artefatos propostos:** `X-Event-Id`, `event_id` no webhook e a outbox que os originará ainda precisam ser implementados; não existem no código verificado.
- **Questões abertas:** a documentação deve explicar a duplicidade; schema e armazenamento de `event_id` pertencem ao FDD; a responsabilidade do cliente não deve ser convertida em garantia adicional da plataforma.
