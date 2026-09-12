---
name: rfc-writer
description: Produz ou revisa o RFC arquitetural em português para o desafio de Webhooks de Notificação de Pedidos, usando TRANSCRICAO.md como fonte primária e os ADRs como base consolidada das decisões. Valida os requisitos do CHALLENGE.md e mantém o RFC separado do FDD, PRD e ADRs.
---

# RFC Writer

## Objetivo e fronteira

Use esta skill para produzir ou revisar `docs/RFC.md` no desafio do Sistema de Webhooks de Notificação de Pedidos.

O RFC é uma proposta arquitetural submetida à revisão. Ele consolida as decisões registradas nos ADRs, explica o contexto, a abordagem escolhida, as alternativas descartadas, as questões ainda abertas e os impactos da solução. Não substitui:

- o **PRD**, que trata de produto, público, escopo e métricas;
- o **FDD**, que detalha fluxos de implementação, contratos HTTP, erros, observabilidade e integração linha a linha;
- os **ADRs**, que registram cada decisão arquitetural isolada e suas consequências.

O RFC deve ser derivado dos ADRs existentes, mas os ADRs não são fonte independente da reunião: toda decisão importante deve ser conferida na `TRANSCRICAO.md`. Se um ADR contradizer a transcrição, não esconda o conflito nem invente uma resolução; registre a inconsistência e interrompa a geração final até que o escopo seja esclarecido.

Não altere código, Prisma, testes, configurações, `TRANSCRICAO.md`, `CHALLENGE.md` ou ADRs durante a criação do RFC. Preserve um `docs/RFC.md` existente, salvo pedido explícito de atualização.

## Quando usar

Use para:

- criar o RFC desta feature a partir da transcrição, dos ADRs e do contexto do repositório;
- revisar um RFC existente contra o `CHALLENGE.md`, a transcrição, o mapping, os ADRs e o código citado;
- corrigir inconsistências no RFC quando o usuário pedir explicitamente a correção.

Não use para gerar PRD, FDD ou ADR isolado. Se o pedido misturar documentos, delimite a parte do RFC e não produza os demais artefatos sem solicitação.

## Fontes e ordem de descoberta

Leia as fontes nesta ordem, distinguindo contrato do desafio de evidência do domínio:

1. `TRANSCRICAO.md`: fonte primária para decisões, alternativas, requisitos, questões abertas e pontos adiados.
2. `CHALLENGE.md`: contrato de entrega. Confira especialmente a seção de RFC, os critérios de aceite e a consistência geral.
3. `docs/mapping.md`: índice para localizar decisões, requisitos, questões abertas e arquivos do código. Confirme referências relevantes na fonte original ou no arquivo real.
4. `docs/adrs/`: base arquitetural obrigatória do RFC. Leia todos os ADRs do pacote, confira se cobrem as decisões e vincule as decisões relacionadas no RFC. Não copie os ADRs integralmente.
5. Caminhos reais de código citados nos ADRs, mapping ou RFC: confirme que existem antes de mencioná-los como existentes. O código contextualiza a proposta; não prova que a feature de webhook já foi implementada.
6. Outros documentos já produzidos, como `docs/PRD.md` e `docs/FDD.md`, somente para evitar contradições e duplicação. Eles não substituem a transcrição nem os ADRs.

Se uma fonte estiver ausente, inconsistente ou incompleta, reduza a afirmação e registre a lacuna. Não complete a informação com conhecimento de mercado ou suposição silenciosa.

## Relação obrigatória com os ADRs

Antes de escrever, faça uma matriz interna que conecte cada decisão do RFC a pelo menos um ADR e à evidência primária:

| Decisão no RFC | ADR relacionado | Evidência na transcrição | Limites que permanecem no FDD |
| --- | --- | --- | --- |
| Outbox transacional no MySQL | link para o ADR correspondente | timestamp e participante | schema, claim/lock e retenção |
| Retry, backoff e DLQ | link para o ADR correspondente | timestamp e participante | contratos e fluxo detalhado |

No pacote atual, verifique as seis decisões principais quando os ADRs existirem:

- outbox transacional no MySQL;
- retry com backoff e DLQ;
- HMAC-SHA256 com secret por endpoint;
- entrega at-least-once com `X-Event-Id`;
- worker separado da API em polling;
- reuso dos padrões existentes do projeto.

O RFC deve apontar para pelo menos dois ADRs, conforme o `CHALLENGE.md`; preferencialmente, deve relacionar todos os ADRs que sustentam a proposta. Use links relativos a partir de `docs/RFC.md`, por exemplo:

```markdown
- [ADR-001: Outbox transacional no MySQL](adrs/ADR-001-outbox-transacional-no-mysql.md)
```

Não crie links para arquivos inexistentes. Se o pacote de ADRs estiver incompleto, informe a cobertura real em vez de criar decisões ou placeholders.

## Classificação da evidência

Mantenha estas distinções no conteúdo e na revisão:

- **Decisão fechada:** consenso explícito ou confirmação no resumo da reunião. Pode aparecer como parte da proposta escolhida.
- **Alternativa discutida:** opção mencionada na transcrição e descartada, sempre com timestamp e participante.
- **Questão aberta/adiada:** ponto sem decisão ou explicitamente deixado para depois. Não pode ser escrito como compromisso da solução.
- **Inferência do código:** comportamento observado em arquivo existente. Rotule como inferência e não como decisão da reunião.
- **Artefato proposto:** tabela, módulo, worker, endpoint ou arquivo futuro. Nunca o apresente como já existente.

Alternativas plausíveis que não aparecem na transcrição só podem ser incluídas se forem úteis e devem ser marcadas como **Plausível, não atribuída à reunião**. O requisito de alternativas do desafio é atendido preferencialmente com alternativas reais discutidas na reunião.

## Requisitos do RFC

O arquivo final deve ser Markdown, conciso e arquitetural, aproximadamente entre 2 e 4 páginas quando renderizado. Deve conter, no mínimo, as seções abaixo:

1. **Metadados**: autor, status, data e revisores. Use os participantes da reunião como revisores. Se a transcrição não informar autor ou data completa, escreva `não informado na transcrição` ou `quinta-feira (data completa não informada)`; não invente nomes ou datas.
2. **Resumo executivo (TL;DR)**: problema, proposta e principal benefício em poucos parágrafos.
3. **Contexto e problema**: necessidade dos clientes, limites outbound e relação com o OMS existente, sempre sustentados por fontes.
4. **Proposta técnica**: visão arquitetural escolhida, incluindo somente os parâmetros fechados necessários para compreender a solução, como outbox transacional, worker separado, polling, retry/DLQ, HMAC e semântica at-least-once.
5. **Alternativas consideradas**: pelo menos duas alternativas reais discutidas e descartadas na reunião, cada uma com trade-off/motivo do descarte e fonte. Exemplos possíveis: HTTP síncrono em `changeStatus`, Redis Streams/Redis Cluster, trigger/listener de banco, retry indefinido ou exactly-once, desde que confirmados na transcrição.
6. **Questões em aberto**: pelo menos duas questões não decididas ou adiadas na reunião, com sua fonte e impacto. Exemplos possíveis: rate limiting de saída, retenção/arquivamento, escala para múltiplos workers e ordering futuro. Não trate email, dashboard ou outro item explicitamente fora de escopo como questão aberta.
7. **Impacto e riscos**: impactos técnicos e operacionais, riscos, limites conhecidos e mitigação somente quando sustentada pelas fontes ou claramente identificada como consequência da proposta.
8. **Decisões relacionadas**: links para pelo menos dois ADRs; inclua todos os ADRs usados como base quando possível.

O RFC pode ter uma seção curta de escopo e não escopo quando isso evitar ambiguidade, mas não deve duplicar o PRD. Também pode indicar que contratos, schemas finais, códigos HTTP, claim/lock, métricas detalhadas e testes pertencem ao FDD quando esses pontos não foram fechados na reunião.

## Nível adequado de detalhe

Inclua no RFC:

- composição dos componentes e responsabilidades em alto nível;
- decisões arquiteturais e razões da escolha;
- garantias e limitações aceitas;
- alternativas e riscos relevantes;
- dependências com o código e infraestrutura existentes.

Deixe para o FDD, sem inventar conteúdo:

- schema completo de tabelas e nomes finais de colunas;
- contratos HTTP completos, payloads extensos, códigos de status e assinaturas;
- algoritmo detalhado de claim/lock do worker;
- matriz completa de erros, métricas, logs, tracing e testes;
- sequência passo a passo de implementação.

Parâmetros explicitamente fechados na reunião podem aparecer no RFC, como polling de 2 segundos, cinco tentativas, backoff `1m/5m/30m/2h/12h`, timeout de 10 segundos, grace period de 24 horas e limite de 64 KB. Não transforme questões adiadas em especificação fechada.

## Modelo de saída

Use esta estrutura como base, adaptando os títulos sem remover os requisitos:

```markdown
# RFC: Sistema de Webhooks de Notificação de Pedidos

## Metadados

- Autor: [nome ou não informado na transcrição]
- Status: Proposto para revisão
- Data: [data disponível; não inventar a data completa]
- Revisores: Larissa, Marcos, Bruno, Diego e Sofia

## Resumo executivo (TL;DR)

...

## Contexto e problema

...

## Proposta técnica

### Visão geral

...

### Decisões arquiteturais consolidadas

...

## Alternativas consideradas

- **[Discutida na reunião]** Alternativa — trade-off e motivo do descarte. Fonte: `[hh:mm] Nome`.

## Questões em aberto

- **[Aberta/adiada]** Questão — impacto e fonte: `[hh:mm] Nome`.

## Impacto e riscos

...

## Decisões relacionadas

- [ADR-001](adrs/ADR-001-...md)
- [ADR-002](adrs/ADR-002-...md)
```

Não deixe placeholders no arquivo final. Substitua-os por conteúdo verificado ou remova o bloco quando ele não se aplicar.

## Processo de criação

1. Inventarie `docs/adrs/` e confirme quais ADRs existem, seus números e seus títulos.
2. Leia `TRANSCRICAO.md` e extraia decisões fechadas, alternativas, questões abertas, exclusões e participantes.
3. Leia a seção de RFC e os critérios de aceite em `CHALLENGE.md`.
4. Leia `docs/mapping.md` para orientar a busca e confira os arquivos citados.
5. Leia todos os ADRs e monte a matriz decisão → ADR → evidência. Resolva ou reporte qualquer conflito antes de redigir.
6. Escreva uma proposta coerente com os ADRs, sem copiar detalhes de implementação que pertencem ao FDD.
7. Inclua pelo menos duas alternativas discutidas, duas questões abertas/adiadas e dois links válidos para ADRs.
8. Revise o RFC contra a transcrição, os ADRs, o mapping, o código citado e os critérios do desafio.
9. Só salve ou altere `docs/RFC.md` quando o usuário tiver solicitado a geração ou correção. Em modo de revisão, reporte falhas sem reescrever automaticamente.

## Validação antes da entrega

Confirme todos os itens abaixo:

- [ ] `docs/RFC.md` existe e está em Markdown.
- [ ] Metadados incluem autor, status, data e revisores sem dados inventados.
- [ ] O resumo executivo explica problema, proposta e benefício.
- [ ] A proposta técnica é baseada nos ADRs existentes e não contradiz a transcrição.
- [ ] Há pelo menos duas alternativas reais discutidas na reunião, cada uma com trade-off e fonte.
- [ ] Há pelo menos duas questões abertas ou adiadas, sem convertê-las em decisões.
- [ ] Há impacto e riscos coerentes com a proposta.
- [ ] Há links válidos para pelo menos dois ADRs, preferencialmente para todos os ADRs relacionados.
- [ ] Caminhos de código citados existem; artefatos futuros estão marcados como propostos/inexistentes.
- [ ] O RFC não apresenta como existente a feature de webhooks, a outbox, o worker ou o módulo de webhooks.
- [ ] O RFC não contém detalhes que deveriam estar no FDD, salvo parâmetros arquiteturais explicitamente fechados.
- [ ] Itens fora de escopo da reunião, como email e dashboard, não aparecem como requisitos da proposta.
- [ ] Nenhum código, teste, Prisma, configuração, transcrição, mapping ou ADR foi alterado durante a revisão do RFC.

Se a validação encontrar conflito entre um ADR e a transcrição, reporte o arquivo, a afirmação conflitante e as fontes. Não corrija silenciosamente o ADR ou o RFC.

