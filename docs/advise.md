1. Fazer o levantamento das fontes
Ler TRANSCRICAO.md e mapear o código sem modificá-lo. Criar uma matriz de evidências com:
- requisitos funcionais;
- requisitos não funcionais;
- decisões fechadas;
- alternativas descartadas;
- questões abertas ou adiadas;
- itens fora de escopo;
- referências a módulos e arquivos existentes;
- timestamp e nome do participante para cada informação da transcrição.
A matriz pode ser temporária ou mantida como material de trabalho. Ela será a base do TRACKER.md.

2. Identificar as decisões arquiteturais
Recomendo produzir seis ADRs, cobrindo todas as decisões principais:
- ADR-001-outbox-no-mysql.md
- ADR-002-retry-backoff-e-dlq.md
- ADR-003-autenticacao-hmac-por-endpoint.md
- ADR-004-entrega-at-least-once-e-event-id.md
- ADR-005-worker-separado-com-polling.md
- ADR-006-reuso-dos-padroes-existentes.md
Cada ADR deve conter contexto, decisão, alternativa, consequências positivas e negativas, além da origem rastreável.

3. Produzir o RFC
O RFC deve consolidar a arquitetura escolhida, sem repetir o detalhamento do FDD. Deve conter:
- proposta técnica em nível geral;
- pelo menos duas alternativas realmente discutidas e descartadas;
- pelo menos duas questões deixadas em aberto;
- links para os ADRs;
- participantes da reunião como revisores.

4. Usar a fdd-writer para gerar o FDD
A entrevista da skill deve ser conduzida com uma regra adicional:
Use somente informações identificáveis em TRANSCRICAO.md ou no código. Quando algo não tiver fonte, marque como hipótese durante a entrevista e não inclua no documento final sem confirmação.

O FDD precisa detalhar:
- criação do evento na outbox;
- polling do worker;
- autenticação HMAC;
- entrega com X-Event-Id;
- retries, backoff e DLQ;
- pelo menos quatro endpoints com request, response e status codes;
- erros com prefixo WEBHOOK_*;
- métricas, logs e tracing;
- integração com pelo menos quatro caminhos reais do código.

5. Usar a prd-writer para consolidar o PRD
Eu usaria a skill depois do RFC e do FDD, porque nesse momento as decisões já estarão estabilizadas. O prompt precisa substituir a regra genérica de inferência por:
Não inferir requisitos, metas ou restrições sem fonte na transcrição ou no código. Caso uma informação não esteja disponível, registrar como questão em aberto ou removê-la.

O PRD deve conter pelo menos oito requisitos funcionais, uma métrica quantitativa, duas exclusões explícitas, dois riscos com probabilidade, impacto e mitigação, requisitos não funcionais, dependências, critérios de aceitação e estratégia de testes.

6. Montar o Tracker
O Tracker deve ser construído enquanto os documentos são produzidos, e revisado no fim. Cada linha deve apontar para:
- [hh:mm] Nome quando a origem for a transcrição;
- um caminho real, como src/modules/orders/order.service.ts, quando a origem for o código.
A meta é manter pelo menos 80% de cobertura, 70% das linhas com origem na transcrição e cinco ou mais linhas com origem no código.

7. Substituir o README pelo relato do processo
O README final deve registrar o trabalho real realizado:
- ferramentas usadas;
- ordem de produção;
- prompts customizados;
- correções feitas após saídas superficiais ou incorretas;
- número de iterações;
- ordem recomendada de leitura dos documentos.

8. Fazer a revisão final
Antes de considerar o desafio concluído, validar:
- existem todos os arquivos exigidos;
- há entre 5 e 8 ADRs;
- os caminhos citados existem;
- os endpoints e códigos WEBHOOK_* estão no FDD;
- RFC e FDD não estão duplicando conteúdo;
- todas as exclusões vieram da reunião;
- o Tracker cobre os itens principais;
- nenhum arquivo em src/, prisma/, tests/ ou configurações foi alterado.