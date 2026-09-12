# ADR-003: HMAC-SHA256 com secret por endpoint

## Status

Aceito na reunião técnica.

## Contexto

Os webhooks outbound transportarão eventos com dados de pedidos para endpoints externos. A necessidade registrada foi permitir que o cliente valide a origem da requisição e a integridade do payload [09:19] Sofia. A alternativa de autenticação definida na conversa foi assinar o payload com HMAC e enviar a assinatura em um header para verificação pelo cliente [09:20] Sofia.

O algoritmo escolhido foi SHA-256 [09:20] Sofia. Cada endpoint de webhook deve possuir uma secret própria, pois uma secret global faria o vazamento de uma credencial comprometer todos os endpoints [09:21] Sofia. A configuração conceitual mencionada para o webhook inclui URL, secret, `customer_id` e estado ativo [09:21] Bruno; [09:21] Sofia, mas a tabela de configuração é um artefato proposto e ainda inexistente.

No código existente, `src/middlewares/validate.middleware.ts:11-36` aplica schemas Zod e converte `ZodError` em `ValidationError`. O logger em `src/shared/logger/index.ts:4-20` usa Pino com redaction para credenciais já nomeadas, mas não implementa HMAC nem comprova armazenamento seguro de secrets; secrets não devem ser registradas em claro.

HTTPS obrigatório e rejeição de payload acima de 64 KB foram tratados como validações/RNFs relacionados, não como decisões arquiteturais separadas [09:23] Sofia; [09:24] Diego; [09:24] Larissa.

## Decisão

Adotar HMAC-SHA256 calculado sobre o corpo do request, com a assinatura enviada em header para validação pelo cliente [09:22] Sofia.

Cada endpoint terá uma secret única, sem secret global compartilhada pela plataforma [09:21] Sofia. A secret será rotacionável: durante o grace period, a secret antiga continuará válida por 24 horas em paralelo; depois desse período, deixará de ser válida [09:21] Sofia.

O resumo da reunião confirmou HMAC-SHA256 sobre o payload, secret por endpoint e rotação com grace period de 24 horas [09:48] Larissa.

Esta decisão não define schema, armazenamento criptográfico, endpoint de rotação, formato exato do header ou do payload, nem o fluxo completo de verificação. Esses detalhes permanecem para o FDD. A tabela/configuração de webhook e sua implementação são artefatos propostos e inexistentes neste momento.

## Alternativas consideradas

- **[Discutida na reunião] Secret global da plataforma:** motivo do descarte: o vazamento de uma secret comprometeria todos os endpoints; foi escolhida uma secret única por endpoint [09:21] Sofia.
- **[Plausível, não atribuída à reunião] Assinatura assimétrica:** poderia reduzir a necessidade de compartilhar uma credencial de verificação, mas acrescentaria complexidade operacional para os consumidores. Não consta como alternativa discutida ou decidida na transcrição.

## Consequências positivas

- O cliente pode verificar criptograficamente a origem esperada e a integridade do corpo recebido.
- O isolamento por endpoint limita o impacto de um vazamento de secret a uma configuração, em vez de comprometer todos os endpoints.
- A rotação com grace period de 24 horas permite a migração coordenada entre secret antiga e nova.
- A decisão mantém o contrato arquitetural concentrado em HMAC-SHA256, deixando o schema e os detalhes de implementação para o FDD.

## Consequências negativas e trade-offs

- Secrets compartilhadas exigem armazenamento, entrega, rotação e proteção contra exposição em logs; esses mecanismos não foram fechados neste ADR.
- Uma secret antiga válida por 24 horas mantém temporariamente uma credencial adicional aceita, como custo operacional do grace period.
- A gestão por endpoint aumenta a quantidade de credenciais e operações de rotação em comparação com uma secret global.
- Consumidores precisam implementar a verificação HMAC-SHA256 e acompanhar a rotação dentro da janela de 24 horas.

## Rastreabilidade

### Transcrição

- Necessidade de validar origem e integridade: [09:19] Sofia.
- HMAC e assinatura em header: [09:20] Sofia.
- Algoritmo SHA-256: [09:20] Sofia.
- Secret única por endpoint e rotação com validade paralela de 24 horas: [09:21] Sofia.
- Fechamento de HMAC-SHA256, secret por endpoint e grace period de 24 horas: [09:22] Sofia.
- Confirmação no resumo da reunião: [09:48] Larissa.
- HTTPS e limite de 64 KB como validações/RNFs relacionados: [09:23] Sofia; [09:24] Diego; [09:24] Larissa.

### Código existente

- `src/middlewares/validate.middleware.ts:11-36` — padrão existente de validação com Zod e conversão de `ZodError` em `ValidationError`.
- `src/shared/logger/index.ts:4-20` — configuração existente do Pino com redaction de authorization, cookie, password e token; não há implementação de HMAC nem redaction específica de `secret`.
- `docs/mapping.md:54` — relaciona a decisão ao RNF-10 e registra que não há implementação HMAC nem armazenamento de secrets.
- `docs/mapping.md:135` — confirma o padrão de logging Pino e a orientação de não registrar secrets em claro.

### Classificação e limites

- `Fechado na reunião`: HMAC-SHA256 sobre o corpo, secret única por endpoint e rotação com secret antiga válida por 24 horas.
- `Inferência do código`: os padrões Zod e Pino existem e podem orientar a implementação, mas não demonstram que a feature de webhook ou o tratamento de secrets já exista.
- `Artefato proposto`: tabela/configuração de webhook e endpoint de rotação; permanecem inexistentes até implementação futura.
- `FDD`: armazenamento seguro, schema, formato exato do header/payload e verificação completa.
