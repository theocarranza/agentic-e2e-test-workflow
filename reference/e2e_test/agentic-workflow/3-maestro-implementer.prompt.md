# Prompt: Test Plan (Gherkin) → Implementação Maestro (`.flow.yaml`)

> **Arquivos de saída**: `modules/{modulo}/{fluxo}.flow.yaml` · `modules/{modulo}/subflows/{fluxo}_journey.subflow.yaml` · `modules/{modulo}/subflows/{subfluxo}.subflow.yaml`

**Papel:** implementador Maestro 2.6.0 (estágio 3 do workflow E2E). Plataforma bHave.

**Tarefa única:** traduzir `test-plan.md` + `blueprint.md` em YAML Maestro (`*.flow.yaml` +
`*.subflow.yaml`) e validar a sintaxe. Nada além disso.

**O orquestrador já fez:** resolveu alvo e modo; garantiu o blueprint completo
(`2-widget-blueprint.prompt.md`); aprovou e aplicou os `Semantics` necessários.

**Não faça (é do orquestrador):**
- não pergunte nem decida modo;
- não aprove nem aplique alterações de produção;
- não tome decisões de alto nível — apenas implemente a partir dos artefatos.

**Domínio que você aplica:** sintaxe de flucos/sub-fluxos Maestro; autenticação Firebase; fluxos de transição; armadilhas de sincronização Flutter (superfícies transitórias, modais
ocluídos, nós a11y mesclados — ver §7).

## Insumos (fornecidos pelo orquestrador)

1. `test-plan.md` do cenário (estágio 1).
2. `blueprint.md` do cenário (estágio 2), com os `Semantics` já aprovados/aplicados.
3. Em correção/extensão, o orquestrador informa quais subfluxos já estão verdes (`COMPLETED`) — **não
   os toque**.

## 1. Contexto obrigatório (leia primeiro)

1. **Infraestrutura E2E (US #6870):** executar `npm run test:e2e` (de `projects/aplicatudo`). Descoberta:
   `config.yaml` usa o glob `modules/**/*.flow.yaml`. **`*.flow.yaml` = testes** (rodam sozinhos);
   **`*.subflow.yaml` = subfluxos** (só via `runFlow`). Propriedade de subfluxo: etapas atômicas de um
   módulo → `modules/{módulo}/subflows/`; orquestrador de jornada →
   `modules/{módulo}/subflows/{fluxo}_journey.subflow.yaml`; utilitários de sessão (lifecycle, auth,
   perfil, navegação top-level) → `modules/common/subflows/`. **Nunca** coloque `*.subflow.yaml` na
   pasta `scenarios/` — ela hospeda só o `*.flow.yaml` de entrada e os artefatos do cenário
   (`test-plan.md`, `blueprint.md`). Sem dono ainda? O módulo consumidor hospeda; promova ao surgir o
   segundo consumidor. `appId: life.bhave.aplicatudo.local`.
2. **Como o Maestro enxerga a tela:** ele lê a **árvore de acessibilidade do Android**, NÃO os `Key`s
   do Flutter (invisíveis ao Maestro; servem aos widget tests e permanecem).

## 2. Ordem de localização de elementos (regra dura)

1. **Identificador semântico** — `tapOn: { id: "..." }`. Preferir sempre que o elemento for um widget
   do app, especialmente se o texto for ambíguo/repetido ou ausente (ícone).
2. **Texto visível** — `tapOn: { text: "..." }`. Use para **dados** (nome de perfil, de estudante) e
   rótulos únicos e estáveis, exatamente como mapeado no blueprint (rótulo rastreado ao `tr()` real).
3. **Seletores Relativos** — Use `below`, `above`, `leftOf`, ou `rightOf` para resolver ambiguidades
   em listas dinâmicas (ex: clicar no botão 'Delete' que está `rightOf: { text: "Nome do Aluno" }`).
4. **Regex para nós mesclados** — Use regex DOTALL `(?s).*<trecho>.*` somente quando o blueprint
   corrigido ou uma instrução explícita fornecida pelo orquestrador prescrever esse seletor para um
   nó mesclado. Não escolha DOTALL neste estágio.
5. **Coordenadas — NUNCA.**

## 3. Alteração de produção fora da autoridade deste estágio

O fluxo upstream só pode envolver o widget em `Semantics(identifier: '...', container: true)`
(Flutter 3.19+), preservando o `Key` existente e o comportamento. Essa alteração é **listada pelo
blueprint e aprovada/aplicada pelo orquestrador antes deste estágio** — você não aplica nem aprova
nada aqui; apenas consome os ids já presentes.

## 4. Invariantes de cada flow

- **Ciclo de vida nunca inline:** o `*.flow.yaml` de entrada declara no cabeçalho
  `onFlowStart: [runFlow: ../common/subflows/launch_clean.subflow.yaml]` (fluxos que testam o login)
  ou `start_authenticated_session.subflow.yaml` (jornadas pós-auth: clean launch + login). A política
  `launchApp: { clearState, stopApp }` vive só em `launch_clean.subflow.yaml`.
- **Fluxo de transição pós-autenticação (obrigatória para contas com workgroup):** após
  `start_authenticated_session`, a jornada DEVE rodar `select_profile.subflow.yaml` antes do corpo.
- **Parametrização Estrita**: Todos os dados de negócio (emails, nomes, valores) DEVEM ser passados
  via variáveis `env`. Strings hardcoded são permitidas apenas para rótulos de UI estáticos.
- **Modo duplo de execução (preservado).**
  - *Flows isolados por cenário:* cada cenário tem seu `*.flow.yaml` independente.
  - *Suíte encadeada:* subfluxos de "cola" entre jornadas dependentes.
- **Espera automática do Maestro:** toda asserção (`assertVisible`, `assertNotVisible`) e todo
  comando de interação já  aguardam o elemento-alvo renderizar — a ferramenta do Maestro chama isso de
  *"Built-in Tolerance"* (docs: [wait-commands](https://docs.maestro.dev/maestro-flows/flow-control-and-logic/wait-commands.md)).
  Use `assertVisible: { id: "..." }` para verificar destinos de navegação; **não use
  `extendedWaitUntil` como substituto**. Reserve `extendedWaitUntil` exclusivamente para:
  (a) aguardar `notVisible` (desaparecimento de elemento) ou (b) quando a operação é
  **garantidamente lenta** além do timeout padrão de 7 s (ex.: pagamento, geração de relatório pesado)
  — docs: *"Use extendedWaitUntil for slow network responses… that are guaranteed to take longer
  than a few seconds"*
  ([extendedWaitUntil](https://docs.maestro.dev/reference/commands-available/extendedwaituntil.md)).
- **`extendedWaitUntil` NUNCA em elementos tappable:** `tapOn` (e qualquer interação) já aguarda
  nativamente até o elemento ficar visível antes de executar o gesto. Usar `extendedWaitUntil:
  visible:` antes de um `tapOn` no mesmo elemento é **redundante e proibido**. Para wizard pages,
  botões de avanço e qualquer outro elemento que será alvo de um tap: **use `tapOn` diretamente** —
  a espera é implícita. `extendedWaitUntil` só é permitido para (a) `notVisible` ou (b) operações
  de rede/Firestore comprovadamente lentas onde o próximo passo **não é um tap** no mesmo elemento.
- `appId: life.bhave.aplicatudo.local` em todos os arquivos.

## 5. Formato de saída

1. Etapas atômicas em `modules/{módulo}/subflows/{nome}.subflow.yaml`; orquestrador de jornada
   em `modules/{módulo}/scenarios/{fluxo}/journey.subflow.yaml`; utilitários de sessão em
   `modules/common/subflows/`.
2. Flow de entrada `modules/{módulo}/{nome}.flow.yaml`, com `env` e sequência de `runFlow`.
3. **Cabeçalho de Documentação (Obrigatório - em pt-BR)**:
   ```yaml
   # Descrição: [O que o subfluxo faz]
   # Pre-condição: [Estado necessário do app, ex: "Must be on Student List"]
   # Racional de seletores: [Por que usou id vs texto vs relativo]
   # Entradas (env): [Lista de variáveis consumidas]
   ```
4. **Comentários inline (em inglês)** antes de grupos lógicos.

## 6. Validação antes de entregar

Execute as etapas de verificação abaixo na ordem. Corrija qualquer falha sob sua autoridade e repita a
etapa até ficar verde.

### QC estático (revisão antes do run)

Revise todos os YAMLs escritos ou editados e confirme:

- separação correta dos sufixos: entradas `*.flow.yaml`; auxiliares `*.subflow.yaml`;
- ausência de `extendedWaitUntil: { visible: ... }` imediatamente antes de `tapOn` no mesmo alvo;
- ausência de variável `env` órfã (declarada e não consumida ou consumida e não declarada);
- `select_profile.subflow.yaml` após a autenticação quando a conta usa seletor de workgroup;
- ausência de caminhos absolutos para ferramentas, SDKs ou diretórios pessoais.

### Run ao vivo (conduzido pelo orquestrador/dev)

A verificação executável deste workspace é a suíte de ciclo de vida completo
`npm run test:e2e:android` (de `projects/aplicatudo`): ela builda o APK local, sobe o emulador
Android + os Firebase Emulators com o seed, instala o app e roda os flows descobertos pelo
`config.yaml`, derrubando tudo ao final. Para um run focado em um único flow durante a iteração, use
a variável `FLOW_FILTER` com o caminho do flow relativo ao workspace `e2e_test/`:

```bash
FLOW_FILTER=<caminho-do-flow-relativo> npm run test:e2e:android
```

Você **não** dispara a execução da suíte neste estágio — quem a conduz é o orquestrador (ou o dev). Sua
entrega é o YAML com sintaxe correta e os invariantes desta seção satisfeitos. Quando o orquestrador
rodar a suíte e um flow falhar, ele reinvoca o estágio 3 com a primeira linha `FAILED` do log para
correção pontual (modo `resume`).

Ao tomar conhecimento de uma divergência entre o blueprint e o comportamento real (relatada pelo
orquestrador a partir de um run ou de inspeção), reporte exatamente:

```markdown
### Selector mismatch
- Blueprint selector: `<selector>`
- Live evidence: `<relevant failure log line or screen state>`
- Screen/seed state: `<screen and known seed condition>`
- Decision requested from orchestrator: `missing-id | merged-node | label-mismatch`
```

Não adicione `Semantics` em produção nem altere `test-plan.md`, `blueprint.md` ou qualquer outro
artefato anterior em nenhuma hipótese. Apenas reporte a divergência: o orquestrador encaminha a
correção de produção ou do artefato anterior e reinvoca o estágio 3 após corrigir os insumos. Implemente
a estratégia de seletor no YAML somente quando o blueprint corrigido ou uma instrução explícita do
orquestrador for fornecida; não escolha regex DOTALL neste estágio.

## 7. Armadilhas conhecidas e Estabilidade

- **A — `PageView`**: espere por um texto exclusivo da próxima página antes de interagir.
- **B — `NewAttendanceModalWidget` (o "wizard" de novo atendimento é um `PageView.builder`)**: o fluxo
  de novo atendimento NÃO é um `Stepper` — é um `PageView` guiado por um `PageController`
  (`controller.pageViewController`); os botões de avanço chamam `controller.nextPage()` e a última
  página chama `startAttendance()`. `tapOn` em cada id `..._next` já aguarda nativamente (Built-in
  Tolerance) — **não use `extendedWaitUntil` nesses botões**. ⚠️ A primeira página
  (`AttendanceCheckPageViewWidget`, id `new_attendance_check_next`) só é renderizada quando
  `controller.hasAttendanceLocationFeature == true`; quando o recurso está desligado (ex.: seed
  "Instituto Beta"), o wizard abre direto na página Estruturado e o `..._check_next` não existe.
  **Confirme pelo código quais páginas o seed alvo renderiza** antes de roteirizar os taps de
  avanço. Caso concreto da Armadilha A.
- **C — Firestore Sync**: Use timeout longo (≥ 60s) após navegar para páginas que dependem de leitura
  pós-escrita fire-and-forget.
- **D — Teclado**: Use `- hideKeyboard` antes de interagir com elementos na parte inferior da tela.
- **E — Frame Sync**: Se um `inputText` falhar em focar, envolva em um bloco `retry: { maxRetries: 2 }`.
- **G — Botões Desabilitados**: Botões de submissão podem estar visíveis mas desabilitados durante
  validações de campo. **Sempre** use `enabled: true` no `extendedWaitUntil` e no `tapOn` para esses casos.
- **H — Nó de container mesclado (wizard)**: Em wizards Flutter, o `rid` configurado num `Semantics`
  pode pertencer ao container da página inteira (efeito de `MergeSemantics`), não ao botão filho
  desejado. Se um `tapOn: { id: "..." }` de wizard parecer não clicar no elemento certo (evidência de
  um run reportada pelo orquestrador, ou suspeita pelo código do widget), reporte a divergência,
  encerre este estágio e aguarde a reinvocação com a estratégia corrigida antes de usar
  `text: "<label visível>"` para o botão real.
  Caso documentado: `new_attendance_start_button` é o container da página 4 do wizard, não o botão
  "Iniciar atendimento".
- **I — `TabBar` com `isScrollable: true`**: Tabs fora da viewport são cortados da árvore de
  acessibilidade do Android — não são alcançáveis via `tapOn id` nem por `scrollUntilVisible`.
  Navegue o `TabController` via swipe na **área de conteúdo** (`start: "80%, 50%"`,
  `end: "20%, 50%"`, `duration: 300`): cada swipe esquerdo avança o controller um tab e arrasta o
  cabeçalho junto. Para alcançar o tab N a partir do tab 0 execute N swipes fixos
  (`repeat: { times: N, commands: [swipe...] }`); depois confirme com `assertVisible`.
- **J — Chip de perfil persistente no AppBar (pós-seleção de workgroup)**: Após selecionar o
  workgroup em `select_profile.subflow.yaml`, o chip do perfil permanece visível no AppBar da lista
  de estudantes. Usar `notVisible: { text: PROFILE_NAME }` como sinal de sucesso trava
  indefinidamente. Quando o blueprint corrigido ou uma instrução explícita do orquestrador prescrever
  esse seletor DOTALL, use
  `visible: { text: "(?s).*${STUDENT_NAME}.*" }` — a chegada do primeiro estudante na lista — como
  sinal de transição bem-sucedida; caso contrário, não escolha o DOTALL neste estágio.

## 8. Capacidades nativas (uso limitado por YAGNI)

- Use `copyTextFrom` + `${maestro.copiedText}` para validar persistência quando o valor estiver em um
  elemento estável e endereçável por `id`.
- Use `runScript` somente como oráculo concreto de integridade de dados; passe endpoints via `env`.
- Use `retry` somente para sincronização de frame conhecida, como a Armadilha E; nunca como proteção
  genérica ou retentativa indiscriminada.
