---
name: adr-writer
description: Produz ADRs em português, em Markdown, para este desafio, usando TRANSCRICAO.md, docs/mapping.md, código existente e ADRs prévios como evidências. Gera um ADR isolado ou um pacote de 5 a 8 decisões rastreáveis em docs/adrs/.
---

# ADR Writer

## Objetivo e fronteira

Use esta skill para registrar decisões arquiteturais fechadas da reunião técnica sobre o Sistema de Webhooks de Notificação de Pedidos. O resultado é um ou mais arquivos Markdown prontos em `docs/adrs/`, no formato `ADR-NNN-titulo-em-kebab-case.md`.

Esta skill documenta o **porquê da decisão**, seus limites e trade-offs. Não substitui o FDD: não detalha SQL, modelos Prisma completos, contratos HTTP, assinaturas de funções, fluxos passo a passo ou plano de implementação, salvo o mínimo necessário para tornar a decisão inequívoca.

Não altere `src/`, `prisma/`, `tests/`, `package.json`, configurações ou ADRs existentes. Nesta tarefa, a única saída de produto da skill são ADRs em `docs/adrs/`; a validação pode criar apenas arquivos temporários fora da entrega.

## Modos de uso

Interprete o pedido do usuário antes de escrever:

- **ADR isolado:** quando o usuário indicar uma decisão, gere ou atualize somente o ADR correspondente. Não crie placeholders para as demais decisões. Valide a estrutura do arquivo; a contagem de pacote não se aplica até a geração completa.
- **Pacote completo:** quando o usuário pedir o pacote, gere inicialmente os seis ADRs-base abaixo. O pacote final deve ter de 5 a 8 ADRs no padrão de nome exigido. ADRs adicionais só entram se houver uma decisão arquitetural fechada ou uma necessidade de compatibilidade claramente evidenciada.
- **Revisão/validação:** quando o usuário pedir revisão, não reescreva automaticamente. Inspecione os arquivos, reporte falhas por arquivo e corrija apenas se isso tiver sido solicitado.

Antes de escrever, inventarie `docs/adrs/`. Preserve arquivos existentes e seus números. Não renomeie nem sobrescreva um ADR preexistente sem pedido explícito. Para novos arquivos, use o próximo número de três dígitos livre (`ADR-001`, `ADR-002`, ...), verificando colisões inclusive com nomes fora do padrão.

## Fontes obrigatórias e ordem de descoberta

Leia e use, nesta ordem:

1. `TRANSCRICAO.md`: fonte primária para o que foi dito e decidido. Extraia falas no formato `[hh:mm] Nome`.
2. `docs/mapping.md`: índice de evidências, decisões fechadas, alternativas, questões abertas e caminhos de código. Use-o para orientar a busca, mas confirme referências importantes no arquivo original ou no caminho real.
3. Os caminhos reais do código citados no mapping: confirme com o filesystem e, quando possível, consulte as linhas indicadas. O código descreve padrões existentes; não prova que a feature de webhooks já existe.
4. ADRs já existentes em `docs/adrs/`: respeite vocabulário, status, numeração e decisões anteriores. Verifique conflitos; não trate um ADR existente como fonte da reunião sem evidência primária.

Se alguma fonte estiver ausente ou inconsistente, registre a lacuna e reduza a afirmação. Não complete a lacuna com conhecimento de mercado ou suposição silenciosa.

## Classificação da evidência

Separe explicitamente quatro classes, tanto durante a análise quanto no texto final:

- **Decisão fechada:** houve consenso explícito, normalmente marcado por “decidido”, “anotado” ou confirmação no resumo. Pode aparecer na seção `Decisão`.
- **Alternativa descartada na reunião:** foi colocada em discussão e rejeitada. Cite o timestamp e o nome do participante.
- **Questão aberta/adiada:** não é decisão. Não a transforme em escolha; mencione-a apenas como limite ou trabalho futuro quando for relevante.
- **Inferência do código:** leitura estrutural de um arquivo existente. Rotule como inferência, nunca como decisão tomada na reunião.

Uma alternativa plausível que não aparece na transcrição pode ser usada para completar a comparação, mas deve ser marcada exatamente como **“Plausível, não atribuída à reunião”**. Não diga ou sugira que ela foi discutida, proposta ou descartada pelos participantes. Alternativas discutidas devem ser marcadas como **“Discutida na reunião”** e conter fonte `[hh:mm] Nome`.

## Decisões-base do pacote

No modo pacote completo, cubra inicialmente estas seis decisões, mantendo estes termos do domínio:

1. **Outbox transacional no MySQL existente.** Evidências principais: `[09:06] Diego`, `[09:08] Larissa`, resumo em `[09:48] Larissa`; código relacionado: `src/modules/orders/order.service.ts`, `prisma/schema.prisma`.
2. **Retry com backoff e DLQ.** Evidências principais: `[09:15] Diego` a `[09:18] Diego/Larissa`; política fechada de cinco tentativas `1m/5m/30m/2h/12h` e DLQ separada.
3. **Autenticação HMAC-SHA256 com secret por endpoint.** Evidência principal: `[09:19] Sofia` a `[09:22] Sofia`; código relacionado: `src/middlewares/validate.middleware.ts`, `src/shared/logger/index.ts`.
4. **Entrega at-least-once com `X-Event-Id`.** Evidências principais: `[09:24] Diego` a `[09:26] Larissa`; código relacionado: `src/middlewares/request-logger.middleware.ts`, `prisma/schema.prisma`.
5. **Worker separado da API em polling.** Evidências principais: `[09:09] Diego` a `[09:11] Diego`, confirmação em `[09:48] Larissa`; código relacionado: `src/server.ts`, `src/config/database.ts`.
6. **Reuso dos padrões existentes do projeto.** Evidência principal: `[09:27] Bruno` a `[09:30] Larissa`; código relacionado: `src/modules/orders/order.routes.ts`, `src/modules/orders/order.schemas.ts`, `src/shared/errors/app-error.ts`, `src/middlewares/error.middleware.ts`, `src/shared/logger/index.ts`.

Esses caminhos são exemplos de arquivos existentes que devem ser confirmados. Artefatos citados na reunião como `src/worker.ts`, `src/modules/webhooks/`, `webhook_outbox` e `webhook_dead_letter` são **propostos/inexistentes no código-base**, conforme o mapping. Se forem mencionados, escreva “artefato proposto” ou “ainda inexistente”; nunca escreva como se já existissem.

## Processo de análise

### 1. Montar o inventário de evidências

Para cada decisão candidata, registre internamente:

- formulação curta da decisão;
- fonte de fechamento na transcrição;
- alternativas discutidas e motivo do descarte;
- alternativas plausíveis adicionais, somente se úteis e rotuladas;
- questões abertas que limitam o escopo da decisão;
- pelo menos um padrão ou arquivo existente do código;
- inferências, com a etiqueta `Inferência do código`;
- qualquer artefato novo como proposto, nunca como existente.

Não use uma fala exploratória isolada como decisão. Prefira a fala de fechamento e o resumo final. Não use prazos, data, participantes, linhas ou nomes de arquivos que não possam ser encontrados nas fontes.

### 2. Delimitar o nível arquitetural

Mantenha no ADR apenas o necessário para responder “por que esta opção foi escolhida?”. Pode registrar invariantes e parâmetros que foram explicitamente fechados, por exemplo polling de 2 segundos, cinco tentativas, backoff `1m/5m/30m/2h/12h`, grace period de 24 horas e semântica at-least-once.

Remeta ao FDD, sem inventar conteúdo, para detalhes como schema final, claim/lock do worker, nomes finais de colunas, endpoints completos, códigos HTTP, formato detalhado do payload, métricas e testes. Se um detalhe não estiver fechado na reunião, escreva que permanece aberto.

### 3. Escolher o arquivo e o título

Use títulos curtos em kebab-case, apenas com letras minúsculas, números e hífens. Exemplos preferenciais:

- `ADR-001-outbox-transacional-no-mysql.md`
- `ADR-002-retry-com-backoff-e-dlq.md`
- `ADR-003-hmac-sha256-com-secret-por-endpoint.md`
- `ADR-004-entrega-at-least-once-com-x-event-id.md`
- `ADR-005-worker-separado-em-polling.md`
- `ADR-006-reuso-dos-padroes-existentes.md`

Adapte o número se já houver colisão. Não use acentos, espaços, underscores ou nomes genéricos como `ADR-001-decisao.md` quando um título de domínio for possível.

## Formato obrigatório de cada ADR

Use exatamente estas seções de segundo nível, nesta ordem. Subtítulos internos são permitidos:

```markdown
# ADR-NNN: Título legível

## Status

Aceito na reunião técnica.

## Contexto

Problema e restrições observáveis. Diferencie fatos da reunião de inferências do código.

## Decisão

Decisão fechada, em termos arquiteturais, incluindo limites conhecidos.

## Alternativas consideradas

- **[Discutida na reunião]** Alternativa: motivo do descarte. Fonte: `[hh:mm] Nome`.
- **[Plausível, não atribuída à reunião]** Alternativa: trade-off que a torna menos adequada neste contexto. Não consta na transcrição.

## Consequências positivas

- Efeito positivo diretamente sustentado pelas evidências.

## Consequências negativas e trade-offs

- Custo, limitação ou risco aceito, sem esconder o trade-off.

## Rastreabilidade

### Transcrição

- Decisão fechada: `[hh:mm] Nome`.

### Código existente

- `src/caminho/arquivo.ts:linha` — padrão ou comportamento observado.
- `docs/mapping.md` — relação entre a decisão e a evidência, quando aplicável.

### Classificação e limites

- `Fechado na reunião`: ...
- `Inferência do código`: ...
- `Artefato proposto`: ... (somente se necessário; nunca dizer que existe).
```

Regras adicionais do conteúdo:

- Todo ADR deve ter pelo menos uma alternativa e pelo menos um trade-off negativo explícito.
- Todo ADR deve ter consequências positivas e negativas separadas; não esconda ambas em um parágrafo de “Consequências”.
- Todo ADR deve ter ao menos uma fonte da transcrição no formato exato `[hh:mm] Nome`, quando registrar uma decisão fechada da reunião.
- Todo ADR deve referenciar explicitamente pelo menos um arquivo, módulo ou padrão **existente** do projeto. O caminho deve ser real; inclua linha quando possível.
- A seção `Rastreabilidade` deve ligar a decisão ao timestamp e ao código. Se a decisão também depender do mapping, cite `docs/mapping.md`.
- Use o vocabulário encontrado nas fontes: `order`, `customer`, `order_status_history`, `outbox`, `DLQ`, `worker`, `polling`, `secret`, `endpoint`, `delivery`, `at-least-once`, `X-Event-Id`, `AppError`, `Pino`, `Zod` e `requireRole` apenas quando sustentado.
- Não acrescente autor, data calendárica, versão, SLA, participante ou restrição que não esteja nas fontes. A transcrição informa “quinta-feira”, mas não informa uma data completa.
- Não transforme questões abertas em decisões. Exemplos de pontos adiados: rate limiting, escala para múltiplos workers, retenção/arquivamento, endurecimento do CRUD, e-mail e dashboard.

## Validação

Antes de entregar, faça uma revisão semântica e execute o validador incluído em `scripts/validate_adrs.py`.

### Validação semântica

Confira que:

- cada afirmação de reunião tem timestamp e nome;
- cada caminho de código citado existe, com linha conferida quando declarada;
- caminhos ou tabelas novas estão marcados como propostos/inexistentes;
- alternativas estão classificadas como discutidas ou plausíveis;
- decisão, alternativa, consequência e fonte não se contradizem;
- detalhes de implementação foram mantidos no FDD;
- nenhum código, teste, Prisma ou configuração foi alterado.

### Validação automatizada do pacote

No pacote completo, execute na raiz do repositório:

```text
python .agents/skills/adr-writer/scripts/validate_adrs.py
```

O validador deve aprovar somente quando:

- existem entre 5 e 8 arquivos `ADR-NNN-titulo-em-kebab-case.md` em `docs/adrs/`;
- todos têm as seções obrigatórias, alternativas, consequências positivas, consequências negativas/trade-offs e rastreabilidade;
- o conjunto cobre ao menos 5 das 6 decisões-base;
- cada alternativa está presente e cada ADR tem trade-off explícito;
- cada caminho de código existente citado é válido;
- cada decisão tem rastreabilidade para transcrição e código.

Durante a geração incremental, valide um único arquivo com:

```text
python .agents/skills/adr-writer/scripts/validate_adrs.py --mode single --file docs/adrs/ADR-NNN-titulo-em-kebab-case.md
```

No final, rode novamente sem `--mode single`. Corrija falhas e repita a validação antes de reportar conclusão. Não conte `docs/adrs/README.md` como ADR.
