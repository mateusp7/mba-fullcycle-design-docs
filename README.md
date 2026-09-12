# Design Docs gerados com IA

## Sobre o desafio

O desafio consiste em transformar a transcrição de uma reunião técnica sobre um Sistema de Webhooks de Notificação de Pedidos em um conjunto de documentos de design. A tarefa envolve analisar a transcrição, entender o código existente e registrar requisitos, decisões técnicas, alternativas, questões em aberto e critérios necessários para orientar a implementação.

O trabalho também busca manter a rastreabilidade das informações, conectando cada item documentado à sua fonte na transcrição ou no código. Dessa forma, a IA é usada como apoio à análise e à produção dos documentos, enquanto a consistência e a origem das decisões permanecem verificáveis.

## Ferramentas de IA utilizadas

- **OpenAI Codex**: usado para ler o repositório, analisar a transcrição, identificar decisões técnicas, revisar a consistência dos documentos e criar documentos.
- **Skill Creator**: utilizada para a criação/ajustes das skills de `fdd-writer`, `prd-writer`, `adr-writer` e `rfc-writer`.
- **Skill customizada `fdd-writer`**: usada para conduzir a estruturação do FDD, cobrindo fluxos, contratos, resiliência, observabilidade e critérios de aceite.
- **Skill customizada `prd-writer`**: usada como base para organizar o PRD, seus requisitos, funcionalidades, dependências e critérios de aceitação.
- **Skill customizada `adr-writer`**: usada para registrar as decisões arquiteturais, alternativas, trade-offs e sua rastreabilidade até as fontes do projeto.

## Workflow adotado

### Criação do arquivo mapping

Neste momento, foi adicionada a interação para criação do arquivo [`docs/mapping.md`](docs/mapping.md). O objetivo é apoiar a criação do tracker futuramente e manter um histórico mapeado das evidências, decisões e referências do projeto quando novos chats forem abertos para a geração dos demais documentos.

### Geração da skill de adr-writer

Após a criação do arquivo [`docs/mapping.md`](docs/mapping.md), foi iniciado o processo da criação da skill de geração de um adr, sendo adaptado ao cenário atual do projeto. Para esse caso, solicitei que a IA me gerasse um prompt para criação da skill, com base no meu prompt, para que ela cubra todas as necessidades da seção do documento de ADR.

> Visualizei uma oportunidade de modificação da skill, possibilitando a instancia de 6 subagents para as tarefas, fazendo com que o agente principal seja apenas o orquestrador, evitando, assim, um estouro de janela principal de contexto.

## Prompts customizados

### Levantamento de evidências

```text
Leia TRANSCRICAO.md e o código existente. Crie docs/mapping.md
classificando requisitos funcionais, requisitos não funcionais,
decisões fechadas, alternativas descartadas, questões abertas,
itens fora de escopo e caminhos reais do código.

Toda informação deve ter origem identificável. Não invente
requisitos, decisões, restrições ou arquivos. Diferencie o que
existe no código, o que foi proposto na reunião e o que é apenas
inferência estrutural.
```

### Orquestração dos ADRs

```text
Ajuste a skill adr-writer para que, no modo pacote completo,
o agente principal analise as fontes uma vez, monte pacotes
compactos de evidências por decisão e delegue cada ADR a um
subagent quando houver suporte.

Reserve previamente os números e caminhos dos arquivos, limite
a concorrência, evite enviar TRANSCRICAO.md e docs/mapping.md
completos para cada subagent e faça a validação final no agente
principal. Cada subagent deve escrever apenas seu ADR e retornar
somente o caminho, o status, um resumo curto e eventuais
pendências.
```

## Como navegar a entrega

A ordem sugerida de leitura é:

1. [`README.md`](README.md): contexto do desafio e processo de produção.
2. [`docs/mapping.md`](docs/mapping.md): matriz de evidências da transcrição e do código.
3. [`docs/PRD.md`](docs/PRD.md): problema, público, escopo e objetivos do produto.
4. [`docs/RFC.md`](docs/RFC.md): proposta técnica, alternativas e questões em aberto.
5. [`docs/adrs/`](docs/adrs/): decisões arquiteturais e seus trade-offs.
6. [`docs/FDD.md`](docs/FDD.md): fluxos, contratos e detalhes de implementação.
7. [`docs/TRACKER.md`](docs/TRACKER.md): rastreabilidade dos itens até suas fontes.
