# Design Docs gerados com IA

## Sobre o desafio

O desafio consiste em transformar a transcrição de uma reunião técnica sobre um Sistema de Webhooks de Notificação de Pedidos em um conjunto de documentos de design. A tarefa envolve analisar a transcrição, entender o código existente e registrar requisitos, decisões técnicas, alternativas, questões em aberto e critérios necessários para orientar a implementação.

O trabalho também busca manter a rastreabilidade das informações, conectando cada item documentado à sua fonte na transcrição ou no código. Dessa forma, a IA é usada como apoio à análise e à produção dos documentos, enquanto a consistência e a origem das decisões permanecem verificáveis.

## Ferramentas de IA utilizadas

- **OpenAI Codex**: usado para ler o repositório, analisar a transcrição, identificar decisões técnicas e revisar a consistência dos documentos.
- **Skill Creator**: utilizada para a criação/ajustes das skills de `fdd-writer`, `prd-writer`, `adr-writer` e `rfc-writer`.
- **Skill customizada `fdd-writer`**: usada para conduzir a estruturação do FDD, cobrindo fluxos, contratos, resiliência, observabilidade e critérios de aceite.
- **Skill customizada `prd-writer`**: usada como base para organizar o PRD, seus requisitos, funcionalidades, dependências e critérios de aceitação.

## Workflow adotado

### Criação do arquivo mapping

Neste momento, foi adicionada a interação para criação do arquivo [`docs/mapping.md`](docs/mapping.md). O objetivo é apoiar a criação do tracker futuramente e manter um histórico mapeado das evidências, decisões e referências do projeto quando novos chats forem abertos para a geração dos demais documentos.

### Geração da skill de adr-writer

Após a criação do arquivo [`docs/mapping.md`](docs/mapping.md), foi iniciado o processo da criação da skill de geração de um adr, sendo adaptado ao cenário atual do projeto. Para esse caso, solicitei que a IA me gerasse um prompt para criação da skill, com base no meu prompt, para que ela cubra todas as necessidades da seção do documento de ADR.

> Visualizei uma oportunidade de modificação da skill, possibilitando a instancia de 6 subagents para as tarefas, fazendo com que o agente principal seja o orquestrador.