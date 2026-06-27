# Testes E2E (Maestro)

> **Versão:** 1.1.0 | **Última Atualização:** 19 de Junho de 2026

Este diretório contém a suíte de testes de ponta a ponta (E2E) do aplicativo Aplicatudo, utilizando o **Maestro 2.6.0**. Ele reúne a configuração do workspace Maestro, flows executáveis, subflows reutilizáveis, regras de execução e prompts do workflow agêntico de autoria de testes.

---

## 📂 Estrutura de Pastas

- `agentic-workflow/`: prompts de autoria, orquestração e controle de qualidade dos testes E2E.
- `modules/common/subflows/`: lógicas reutilizáveis de sessão, autenticação, seleção de perfil e navegação.
- `modules/{m}/scenarios/{fluxo}/{fluxo}.flow.yaml`: ponto de entrada isolado de cada cenário.
- `modules/{m}/subflows/`: passos reutilizáveis do módulo, sem camada `steps`.
- `modules/suite/`: flows encadeados para jornadas de suíte quando houver dependência explícita entre cenários.
- `config.yaml`: configuração global do workspace Maestro.
- `test_when.yaml`: ponto de extensão local para futuras restrições de execução.

A estrutura esperada é descrita aqui em texto. O formato exato de cada artefato gerado vive na seção
`Formato de saída` do prompt responsável por produzi-lo; não há pasta de templates com arquivos vazios.

---

## 🚀 Agentic Workflow

O pipeline de geração de testes é uma linha de produção onde cada estágio produz um artefato consumido pelo próximo. O estado do workflow é mantido pelos arquivos no disco, permitindo que qualquer agente de IA ou desenvolvedor retome o trabalho de onde parou.

Os prompts de automação vivem em `agentic-workflow/`.

### Fluxo de Trabalho

```text
     Alvo: módulo e/ou fluxo de negócio
                    │
                    ▼
   orquestrador confere os arquivos no disco:
   o primeiro que NÃO existe é onde o trabalho começa.
                    │
                    ▼
[0] Descoberta de Domínio ──▶ domain.md
                    │
                    ▼
          GATE: SELEÇÃO DE CENÁRIOS
     (O usuário escolhe o que implementar)
                    │
                    ▼
[1] Test Plan (Gherkin) ──▶ scenarios/{fluxo}/test-plan.md
                    │ gate (Validação de Persistência)
                    ▼
[2] Blueprint de Seletores ──▶ scenarios/{fluxo}/blueprint.md
                    │ gate (Aprovação de Semantics)
                    ▼
[3] Implementação Maestro ──▶ scenarios/{fluxo}/{fluxo}.flow.yaml + subflows
                    │ (YAML + validação de sintaxe)
                    ▼
     EXECUÇÃO DA SUÍTE (Responsabilidade do Dev)
```

### Detalhes dos Estágios

O `orchestrator.prompt.md` não é um estágio: ele resolve o alvo e o modo, identifica o próximo artefato pendente, aplica os gates e aciona o prompt correto.

| Estágio | Prompt                            | Artefato       | Foco Principal                                                                                                                  |
| :------ | :-------------------------------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| **0**   | `0-domain-discovery.prompt.md`    | `domain.md`    | Descobrir a camada de domínio/negócio e propor cenários E2E.                                                                    |
| **1**   | `1-test-plan-author.prompt.md`    | `test-plan.md` | Escrever planos de teste em formato Gherkin a partir do artefato de descoberta de domínio.                                      |
| **2**   | `2-widget-blueprint.prompt.md`    | `blueprint.md` | Inspecionar a árvore semântica do Flutter e produzir uma planta-baixa dos locais onde widgets semânticos devem ser adicionados. |
| **3**   | `3-maestro-implementer.prompt.md` | `*.flow.yaml`  | Traduzir artefatos de plano de testes e "planta-baixa" em flows/subflows Maestro com validação de sintaxe.                      |
| **QC**  | `4-e2e-quality-control.prompt.md` | revisão        | Revisar a conformidade de estrutura, seletores, idioma e execução dos artefatos de flow, gerando um relatório.                  |

---

## 🛠️ Como Operar

### 1. Iniciar ou Continuar um Módulo

Execute o orquestrador fornecendo o módulo alvo:

```text
Execute o workflow em projects/aplicatudo/e2e_test/agentic-workflow/orchestrator.prompt.md.
Alvo: módulo attendance
Gates: auto
```

### 2. Seleção de Cenários (Gate Pós-Estágio 0)

Após a análise de domínio, o agente apresentará uma lista. Você deve responder com os números dos cenários que deseja (ex: "1, 2 e 5") ou "Todos".

### 3. Modos de Operação

- **Gates=auto**: O agente revisa os próprios artefatos contra os checklists e segue em frente.
- **Gates=manual**: O agente para em cada estágio e aguarda sua aprovação explícita.
- **Dry-run=sim**: O agente simula toda a execução e imprime o resultado no chat sem gravar arquivos.
- **Regenerate**: ressincroniza os artefatos após edições manuais nos flows (ver seção 4 abaixo).

### 4. Regenerate após edições manuais

Quando um flow ou subflow for editado manualmente, use o modo `regenerate` para sincronizar os artefatos:

```text
execute @projects/aplicatudo/e2e_test/agentic-workflow/orchestrator.prompt.md flow: modules/attendance/subflows/finalize_attendance.subflow.yaml regenerate
```

Esse comando inspeciona com ênfase o fluxo informado. O orquestrador prioriza esse fluxo e procura ramificações para decidir quais artefatos devem ser recriados.

Sem `flow:`

```text
execute @projects/aplicatudo/e2e_test/agentic-workflow/orchestrator.prompt.md target: attendance regenerate
```

Esse comando inspeciona o módulo completo. O orquestrador compara o test plan com os flows em disco.

Em ambos os casos, o orquestrador emite um relatório estruturado:

| Resultado              | Significado                                                                                                      |
| :--------------------- | :--------------------------------------------------------------------------------------------------------------- |
| `[ASSIMILATED]`        | Mudança expõe gap nas regras — o prompt relevante é atualizado. Nenhum artefato regenerado.                      |
| `[UPDATED <artefato>]` | Mudança válida que descola o blueprint/test-plan — o artefato é atualizado para refletir o flow real.            |
| `[OBJECTION]`          | Mudança viola uma regra — o orquestrador bloqueia e aguarda confirmação explícita antes de qualquer regeneração. |

---

## 🏆 Regras de Ouro (Cultura de QA bHave)

1. **Abordagem adversarial**: envolve tentar "quebrar" intencionalmente o seu sistema, simulando comportamentos de usuário extremos, maliciosos ou caóticos.
2. **Isolamento de Domínio**: Os planos de teste não devem citar ferramentas técnicas (Maestro). Eles descrevem comportamento clínico.
3. **Dados via ENV**: É proibido usar strings "inline" (nomes, emails). Tudo deve ser parametrizado no bloco `env`.
4. **Validação de Estado Esperado**: Um teste só é considerado completo se ele verifica que o estado final da aplicação condiz exatamente com o resultado esperado do fluxo (seja confirmando a persistência correta de um dado válido ou garantindo a rejeição e rollback de um dado malicioso).
5. **Estabilidade em testes de UI**: Gerencie explicitamente strings multilinha ou nós mesclados na árvore de semântica sem usar seletores genéricos demais, e oculte sempre o teclado virtual antes de interações críticas para evitar elementos obstruídos.

## 📄 test_when.yaml

No Maestro, todas as instruções são arquivos `.yaml` comuns, e as restrições de execução são feitas diretamente dentro deles usando a propriedade `when`, sem a necessidade de arquivos de configuração externos ou comandos especiais de sintaxe.

A documentação oficial do Maestro relacionada a este tipo de configuração está em:

- [Workspace configuration](https://docs.maestro.dev/reference/workspace-configuration): `config.yaml`, descoberta de flows, `includeTags`, `excludeTags`, `executionOrder` e diretórios de saída.
- [Test discovery and tags](https://docs.maestro.dev/maestro-flows/workspace-management/test-discovery-and-tags): uso de tags para incluir/excluir flows.
- [Conditions](https://docs.maestro.dev/maestro-flows/flow-control-and-logic/conditions): uso de `when` dentro de flows e subflows.

Chaves que este workspace pode usar futuramente neste arquivo incluem:

- `device:` – limita a execução a uma plataforma específica (ex.: `android`, `ios`).
- `appVersion:` – executa apenas em versões específicas do app (`">=2.5.0"`).
- `feature:` – permite a execução somente quando uma feature flag está ativa.
- `includeTags:` / `excludeTags:` – filtram flows pelas tags do Maestro.
- `script:` – caminho para um script shell que retorna `0` para permitir a execução.

Quando o arquivo está presente sem restrições efetivas (como está agora), nossa convenção é tratar a suíte como “sem restrições” e rodar incondicionalmente. Manter o arquivo versionado evita recriar o ponto de extensão quando restrições forem necessárias.

Exemplo: executa o subfluxo apenas em dispositivos IOS

```yaml
appId: com.exemplo.meuapp
---
- tapOn: "Configurações"
- runFlow:
  file: subflows/limpar_cache.yaml
  when:
  device: ios
```

## Abordagem adversarial em testes E2E

> Uma abordagem adversarial para testes de ponta a ponta (E2E) envolve tentar "quebrar" intencionalmente o seu sistema, simulando comportamentos de usuário extremos, maliciosos ou caóticos. Em vez de apenas verificar se o "caminho feliz" funciona, você testa proativamente os limites de concorrência, casos extremos e vulnerabilidades de segurança em toda a pilha de tecnologia.
> Para entender melhor os princípios, leia sobre [Principles of Chaos Engineering](https://principlesofchaos.org/).

### Como Funciona a Abordagem Adversarial

Em vez de verificar entradas esperadas, uma estratégia de E2E adversarial inverte o paradigma de testes. As principais implementações incluem:

- Engenharia de Caos (Chaos Engineering): Introduzir falhas intencionalmente (ex: derrubar conexões de banco de dados, latência de rede ou reinicializações de servidor) durante uma transação multi-etapas do usuário para verificar a degradação graciosa e a recuperação de estado.
- Fuzzing de Entradas Maliciosas: Enviar payloads malformados, injeções de script (XSS) ou sintaxe SQL através de formulários do frontend para garantir que o backend neutralize as ameaças com segurança antes que elas cheguem ao banco de dados.
- Concorrência e Condições de Corrida (Race Conditions): Utilizar ferramentas de navegador headless para disparar múltiplas requisições de API simultâneas em velocidade robótica. Isso é altamente eficaz para expor condições de corrida (ex: reserva dupla de um item ou envio duplo de um formulário).
- Manipulação de Estado: Usar APIs de backend ou ganchos de teste (test hooks) para alterar artificialmente cookies de sessão, JWTs ou permissões de usuário no meio de um fluxo, simulando sessões hackeadas ou estados de navegador sequestrados.

## Testes Adversariais Assistidos por IA

A abordagem adversarial evoluiu com o uso de inteligência artificial. Utilizando ferramentas de teste E2E, agentes autônomos e "Juízes LLM" agora são comumente usados para rastrear ambientes de visualização (preview environments), gerar jornadas de usuário caóticas e avaliar a resiliência do sistema em tempo real. Isso elimina o trabalho manual de criar scripts para casos extremos complexos.

## Por Que Usar uma Abordagem Adversarial?

- Descobre Falhas Ocultas: Testes padrão apenas verificam o que você manda eles verificarem. O teste adversarial descobre o que o sistema realmente faz quando levado ao limite.
- Melhor Postura de Segurança: Garante que desvios de autenticação, cross-site scripting e adulteração de dados sejam detectados durante o pipeline de CI/CD, e não em produção.
- Resiliência Sob Pressão: Valida se as restrições da interface do usuário (UI) são respaldadas por uma validação rigorosa no backend, impedindo que dados corrompidos afetem o estado da aplicação.
