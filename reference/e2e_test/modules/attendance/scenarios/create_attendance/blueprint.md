# Blueprint: create_attendance

---

## Tela 1: Student Details page — botão "Iniciar atendimento"

**Arquivo:** `lib/modules/student/presentation/student_page/widgets/start_attendance_button.widget.dart`

| Elemento                    | Widget                                                  | Tipo     | Seletor atual                         | Gap |
| --------------------------- | ------------------------------------------------------- | -------- | ------------------------------------- | --- |
| Botão "Iniciar atendimento" | `ElevatedButton` dentro de `badges.Badge` > `Semantics` | Tappable | `id: student_start_attendance_button` | OK  |

**Estrutura semântica:**

```dart
Semantics(
  identifier: 'student_start_attendance_button',
  // container: não declarado explicitamente
  child: ElevatedButton(...)
)
```

`container` não está declarado no código-fonte. O Flutter eleva automaticamente `container: true` quando `identifier` está presente em `Semantics` (comportamento de merge na árvore semântica). Validado em uso: o seletor `id: student_start_attendance_button` é usado com sucesso nos subflows existentes (`select_student.subflow.yaml`, `start_wizard.subflow.yaml`).

**Armadilha estrutural:**

- Se `scheduledEvents.isNotEmpty`, o botão abre `ScheduledAttendanceDialog` em vez do wizard direto. O cenário `create_attendance` presume ausência de eventos agendados — o seed deve garantir isso. O badge só aparece quando `hasScheduledEventsForUser == true`.

---

## Tela 2: Wizard página 0 — Check Location

**Arquivo:** `lib/modules/attendance/presentation/new_attendance_modal/pages/attendance_check_page_view.widget.dart`

| Elemento                         | Widget                                            | Tipo           | Seletor atual                   | Gap                      |
| -------------------------------- | ------------------------------------------------- | -------------- | ------------------------------- | ------------------------ |
| Botão "Avançar" (p/ Estruturado) | `SubtitledTextButtonWidget` dentro de `Semantics` | Tappable       | `id: new_attendance_check_next` | OK                       |
| Botão "Cancelar"                 | `DismissButtonWidget`                             | Tappable       | `text: "Cancelar"`              | text: seguro             |
| Campo data (disabled)            | `TextField(enabled: false)`                       | Não interativo | n/a                             | fora do fluxo            |
| Campo hora (disabled)            | `TextField(enabled: false)`                       | Não interativo | n/a                             | fora do fluxo            |
| Campo terapeuta (disabled)       | `TextField(enabled: false)`                       | Não interativo | n/a                             | fora do fluxo            |
| `LocationObtainerWidget`         | condicional por `hasAttendanceLocationFeature`    | Variável       | n/a                             | fora do fluxo happy path |

**Estrutura semântica do botão "Avançar":**

```dart
Semantics(
  identifier: 'new_attendance_check_next',
  child: SubtitledTextButtonWidget(...)
)
```

`container` não declarado. Comportamento idêntico ao caso da Tela 1 — validado em uso nos subflows existentes.

**Armadilhas estruturais:**

- A página só é exibida após `ensureInitialized()` completar. Enquanto carrega, `FullscreenLoadingWidget` cobre a tela (Trap B). O implementador deve aguardar `new_attendance_check_next` ser visível antes de interagir.
- `LocationObtainerWidget` aparece apenas se `hasAttendanceLocationFeature == true`. Se presente, pode exibir dialogs de permissão de GPS que bloqueiam o fluxo.

---

## Tela 3: Wizard página 1 — Structured Programs

**Arquivo:** `lib/modules/attendance/presentation/new_attendance_modal/pages/structured_page_view.wigdet.dart`

| Elemento                            | Widget                                            | Tipo               | Seletor atual                        | Gap                      |
| ----------------------------------- | ------------------------------------------------- | ------------------ | ------------------------------------ | ------------------------ |
| Botão "Avançar" (p/ Livre Operante) | `SubtitledTextButtonWidget` dentro de `Semantics` | Tappable           | `id: new_attendance_structured_next` | OK                       |
| Botão "Voltar"                      | `SubtitledTextButtonWidget` (sem Semantics)       | Tappable           | `text: "Voltar"`                     | text: seguro             |
| Seleção de folhas                   | `StructuredDatasheetSelectionWidget`              | Lista selecionável | n/a                                  | fora do fluxo happy path |

**Estrutura semântica do botão "Avançar":**

```dart
Semantics(
  identifier: 'new_attendance_structured_next',
  child: SubtitledTextButtonWidget(...)
)
```

**Armadilhas estruturais:**

- Trap B se aplica: a lista de folhas carrega de forma assíncrona. O botão "Avançar" está sempre visível (não fica disabled enquanto carrega), mas interagir antes do carregamento pode gerar estado inconsistente.
- A aba do AppBar exibe `new_attendance_page.pages.free_operand_tab.title` (anomalia tipográfica no código: o título da página de Estruturado usa a LocaleKey de "free_operand_tab_title" — inofensivo para o teste, mas impede assertVisible por texto do título).

---

## Tela 4: Wizard página 2 — Free Operants

**Arquivo:** `lib/modules/attendance/presentation/new_attendance_modal/pages/free_operand_page_view.wigdet.dart`

| Elemento                           | Widget                                                    | Tipo               | Seletor atual                          | Gap                      |
| ---------------------------------- | --------------------------------------------------------- | ------------------ | -------------------------------------- | ------------------------ |
| Botão "Avançar" (p/ Interferentes) | `SubtitledTextButtonWidget` dentro de `Semantics`         | Tappable           | `id: new_attendance_free_operand_next` | OK                       |
| Botão "Voltar"                     | `SubtitledTextButtonWidget` (sem Semantics)               | Tappable           | `text: "Voltar"`                       | text: seguro             |
| Seleção de comportamentos          | `BehaviorSelectionWidget(isInappropriateBehavior: false)` | Lista selecionável | n/a                                    | fora do fluxo happy path |

**Estrutura semântica do botão "Avançar":**

```dart
Semantics(
  identifier: 'new_attendance_free_operand_next',
  child: SubtitledTextButtonWidget(...)
)
```

**Armadilhas estruturais:**

- Trap B: mesma latência de carregamento de comportamentos via `ensureInitialized()`.
- `BackButton` no `leading` do AppBar faz `previousPage()`, não fecha o modal — não usar para navegação para frente.

---

## Tela 5: Wizard página 3 — Confirmação / Iniciar (Inappropriate Behaviors)

**Arquivo:** `lib/modules/attendance/presentation/new_attendance_modal/pages/inappropriate_behavior_page_view.wigdet.dart`

| Elemento                             | Widget                                          | Tipo     | Seletor atual                     | Gap                                  |
| ------------------------------------ | ----------------------------------------------- | -------- | --------------------------------- | ------------------------------------ |
| Botão "Iniciar atendimento"          | `ButtonWithLoadingWidget` dentro de `Semantics` | Tappable | `text: "Iniciar atendimento"`     | Recomendado como fallback resiliente |
| Container da página (MergeSemantics) | nó pai mesclado                                 | Tappable | `id: new_attendance_start_button` | OK (Validado na execução real)       |
| Botão "Voltar"                       | `SubtitledTextButtonWidget` (sem Semantics)     | Tappable | `text: "Voltar"`                  | text: seguro                         |

**Estrutura semântica — detalhe Trap H:**

```dart
Semantics(
  identifier: 'new_attendance_start_button',
  // container: não declarado — mas SubtitledTextButtonWidget tem MergeSemantics internamente
  child: ButtonWithLoadingWidget(
    onPressed: () => startAttendance(),
    label: Text('Iniciar atendimento'),
  ),
)
```

`new_attendance_start_button` é o identificador do nó `Semantics` que envolve toda a página 3 do wizard via `MergeSemantics`. Embora a fusão semântica ocorra, a execução física confirmou que clicar no ID do container `id: "new_attendance_start_button"` delega corretamente a ação e inicia a sessão de atendimento no emulador. No entanto, o uso de `text: "Iniciar atendimento"` continua sendo documentado como uma alternativa recomendada e resiliente caso a estrutura de layout do widget sofra alterações.

**Armadilha estrutural:**

- Trap C: após o tap, `startAttendance()` chama `CreateAttendanceUseCase` + `BeginOrResumeAttendanceUseCase`. A transição `created → ongoing` pode levar até 60 s. O implementador deve aguardar `ongoing_attendance_finalize_button` com timeout mínimo de 60 s antes de prosseguir.

---

## Tela 6: Ongoing Attendance page — AppBar + TabBar + aba Anotações

**Arquivo:** `lib/modules/attendance/presentation/ongoing_attendance_page/ongoing_attendance.page.dart`

| Elemento                          | Widget                                                  | Tipo           | Seletor atual                            | Gap           |
| --------------------------------- | ------------------------------------------------------- | -------------- | ---------------------------------------- | ------------- |
| Botão "Finalizar" (AppBar action) | `OutlinedButton` dentro de `Semantics(container: true)` | Tappable       | `id: ongoing_attendance_finalize_button` | OK            |
| Aba "Anotações" (índice 3)        | `Tab` dentro de `Semantics(container: true)`            | Tappable       | `id: ongoing_attendance_tab_3`           | OK            |
| Aba "Estruturado" (índice 0)      | `Tab` dentro de `Semantics(container: true)`            | Tappable       | `id: ongoing_attendance_tab_0`           | OK            |
| Aba "Naturalístico" (índice 1)    | `Tab` dentro de `Semantics(container: true)`            | Tappable       | `id: ongoing_attendance_tab_1`           | OK            |
| Aba "Interferentes" (índice 2)    | `Tab` dentro de `Semantics(container: true)`            | Tappable       | `id: ongoing_attendance_tab_2`           | OK            |
| Tag "Em atendimento"              | `TagWidget` (sem Semantics próprio)                     | Não interativo | `text: "Em atendimento"`                 | text: seguro  |
| Timer                             | `SimpleTimerWidget`                                     | Não interativo | n/a                                      | fora do fluxo |

**Estrutura semântica confirmada — botão "Finalizar":**

```dart
Semantics(
  identifier: 'ongoing_attendance_finalize_button',
  container: true,
  child: OutlinedButton(...)
)
```

`container: true` explícito — seletor seguro.

**Estrutura semântica confirmada — abas:**

```dart
Semantics(
  identifier: 'ongoing_attendance_tab_$i',
  container: true,
  child: Tab(text: tr(tabNames[i])),
)
```

`container: true` explícito em todos os tabs. A TabBar também tem `isScrollable: true`, mas a aba "Anotações" (índice 3) em tela `<600dp` pode já estar visível sem scroll, dependendo do número de tabs e do espaço disponível. O implementador deve `assertVisible: id: ongoing_attendance_tab_3` antes de `tapOn` para verificar visibilidade antes de decidir entre tap direto e swipe.

**Armadilha estrutural:**

- TabBar `isScrollable: true`: se a aba 3 estiver fora da viewport, `tapOn id: ongoing_attendance_tab_3` falha silenciosamente (a árvore a11y não expõe nós cortados). Verificar visibilidade com `assertVisible` primeiro.

---

## Tela 7: Observation Input — campo de texto + botão enviar

**Arquivo:** `lib/modules/attendance/presentation/ongoing_attendance_page/widgets/tabs/attendances_notes_tab/observation_input.widget.dart`

| Elemento               | Widget                                                            | Tipo     | Seletor atual               | Gap |
| ---------------------- | ----------------------------------------------------------------- | -------- | --------------------------- | --- |
| Campo de texto da nota | `TextField` dentro de `Semantics(container: true)`                | Input    | `id: attendance_note_input` | OK  |
| Botão enviar           | `IconButtonWidget` dentro de `Semantics(container: true)` > `Ink` | Tappable | `id: attendance_note_send`  | OK  |

**Estrutura semântica confirmada — campo:**

```dart
Semantics(
  identifier: 'attendance_note_input',
  container: true,
  child: TextField(...)
)
```

**Estrutura semântica confirmada — botão enviar:**

```dart
Semantics(
  identifier: 'attendance_note_send',
  container: true,
  child: Ink(
    child: IconButtonWidget(onPressed: onClick, icon: Icon(Icons.send)),
  ),
)
```

Ambos com `container: true` explícito — seletores seguros.

**Armadilha estrutural:**

- `ObservationEditorWidget` substitui `ObservationInputWidget` quando `isEditingText == true` (modo de edição de nota existente). Se o flow chegar à aba Anotações no modo de edição, `attendance_note_input` e `attendance_note_send` não estarão presentes. O fluxo happy path não edita notas, então o modo de edição não deve estar ativo.
- O `Row` raiz de `ObservationInputWidget` recebe a `GlobalKey inputKey` que é usada em `onTapOutside` para detectar cliques fora do campo. Não impacta a seleção pelo Maestro.

---

## Tela 8: Finalization dialog — "Todos os registros estão salvos"

**Arquivo:** `lib/modules/attendance/presentation/attendance.flow.dart` (método `showFinishOrDiscardAttendanceDialog`) + `lib/shared-widgets/dialogs/confirmation_dialog.widget.dart`

| Elemento                                       | Widget                                                           | Tipo           | Seletor atual                              | Gap          |
| ---------------------------------------------- | ---------------------------------------------------------------- | -------------- | ------------------------------------------ | ------------ |
| Botão de confirmação ("Finalizar atendimento") | `ButtonWithLoadingWidget` dentro de `Semantics(container: true)` | Tappable       | `id: attendance_finalize_confirm`          | OK           |
| Botão "Cancelar"                               | `DismissButtonWidget` (sem Semantics próprio)                    | Tappable       | `text: "Cancelar"`                         | text: seguro |
| Mensagem do dialog                             | `Text("Todos os registros estão salvos.")`                       | Não interativo | `text: "Todos os registros estão salvos."` | text: seguro |

**Estrutura semântica confirmada — botão de confirmação:**

```dart
// Em ConfirmationDialogWidget._wrapWithIdentifier():
Semantics(
  identifier: 'attendance_finalize_confirm',
  container: true,
  child: ButtonWithLoadingWidget(...)
)
```

`container: true` explícito — seletor seguro.

**Armadilha estrutural:**

- Se `hasRecords == false` no momento do tap em "Finalizar", o `OngoingAttendanceController` exibe `showDiscardAttendanceConfirmationDialog` em vez de `showFinishOrDiscardAttendanceDialog`. O dialog de descarte não tem `attendance_finalize_confirm` — o Maestro travaria aguardando o seletor. A nota deve ser enviada e confirmada na lista **antes** de acionar "Finalizar".
- O `FullscreenLoadingDialogWidget` é exibido durante a execução de `FinishAttendanceUseCase` (via `FullscreenLoadingDialogWidget.wait`). O Maestro deve aguardar o desaparecimento do dialog de loading antes de assertar `attendance_details_page_title`.

---

## Tela 9: Attendance Details page — AppBar + TabBar + aba Anotações

**Arquivo:** `lib/modules/attendance/presentation/attendance_detail_page/attendance_details_page.widget.dart`

| Elemento                                  | Widget                                        | Tipo           | Seletor atual                       | Gap                           |
| ----------------------------------------- | --------------------------------------------- | -------------- | ----------------------------------- | ----------------------------- |
| Título "Detalhes do atendimento" (AppBar) | `Text` dentro de `Semantics(container: true)` | Não interativo | `id: attendance_details_page_title` | OK                            |
| Aba "Resumo" (índice 0)                   | `Tab` dentro de `Semantics(container: true)`  | Tappable       | `id: attendance_details_tab_0`      | OK                            |
| Aba "Estruturado" (índice 1)              | `Tab` dentro de `Semantics(container: true)`  | Tappable       | `id: attendance_details_tab_1`      | OK                            |
| Aba "Naturalístico" (índice 2)            | `Tab` dentro de `Semantics(container: true)`  | Tappable       | `id: attendance_details_tab_2`      | OK                            |
| Aba "Interferentes" (índice 3)            | `Tab` dentro de `Semantics(container: true)`  | Tappable       | `id: attendance_details_tab_3`      | OK                            |
| Aba "Anotações" (índice 4)                | `Tab` dentro de `Semantics(container: true)`  | Tappable       | `id: attendance_details_tab_4`      | **Trap I — fora da viewport** |

**Estrutura semântica confirmada — título:**

```dart
Semantics(
  identifier: 'attendance_details_page_title',
  container: true,
  child: Text(tr(LocaleKeys.attendance_details_page_title)),
)
```

`container: true` explícito. Presente em dois locais no código: no builder de erro e no builder de sucesso — garante que o seletor funciona mesmo no estado de loading inicial.

**Estrutura semântica confirmada — abas:**

```dart
Semantics(
  identifier: 'attendance_details_tab_$i',
  container: true,
  child: Tab(text: tr(tabNames[i])),
)
```

`container: true` explícito em todos os tabs.

**Armadilha estrutural — Trap I (TabBar `isScrollable: true`):**
A `TabBar` tem `isScrollable: true`. Em dispositivo `<600dp` com 5 abas, a aba "Anotações" (índice 4) está fora da viewport inicial. Nós de acessibilidade de widgets clippados por `isScrollable: true` **não são expostos** na árvore a11y do Maestro — `tapOn id: attendance_details_tab_4` falha. A navegação correta e mais resiliente é via swipes horizontais condicionados à visibilidade do elemento até que a nota esteja visível, com limite de 4 iterações:

```yaml
- repeat:
    times: 4
    while:
      notVisible:
        text: ${NOTE_TEXT}
    commands:
      - swipe:
          start: "80%, 50%"
          end: "20%, 50%"
          duration: 300
```

Implementação confirmada em `verify_finalized_attendance_note.subflow.yaml`.

---

## Semantics a adicionar (consolidado)

Após inspeção completa de todos os widgets do fluxo, **nenhuma alteração de produção é necessária**. Todos os elementos interativos do caminho feliz já possuem `Semantics` com `identifier` e `container: true` (onde necessário):

| Seletor                              | Arquivo                                        | `container: true`?                       | Status                                           |
| ------------------------------------ | ---------------------------------------------- | ---------------------------------------- | ------------------------------------------------ |
| `student_start_attendance_button`    | `start_attendance_button.widget.dart`          | implícito (sem declaração, mas funciona) | OK em uso                                        |
| `new_attendance_check_next`          | `attendance_check_page_view.widget.dart`       | implícito                                | OK em uso                                        |
| `new_attendance_structured_next`     | `structured_page_view.wigdet.dart`             | implícito                                | OK em uso                                        |
| `new_attendance_free_operand_next`   | `free_operand_page_view.wigdet.dart`           | implícito                                | OK em uso                                        |
| `new_attendance_start_button`        | `inappropriate_behavior_page_view.wigdet.dart` | implícito — Trap H                       | usar `text: "Iniciar atendimento"`, nunca `id:`  |
| `ongoing_attendance_finalize_button` | `ongoing_attendance.page.dart`                 | **explícito**                            | OK                                               |
| `ongoing_attendance_tab_3`           | `ongoing_attendance.page.dart`                 | **explícito**                            | OK — verificar visibilidade antes de tap         |
| `attendance_note_input`              | `observation_input.widget.dart`                | **explícito**                            | OK                                               |
| `attendance_note_send`               | `observation_input.widget.dart`                | **explícito**                            | OK                                               |
| `attendance_finalize_confirm`        | `confirmation_dialog.widget.dart`              | **explícito**                            | OK                                               |
| `attendance_details_page_title`      | `attendance_details_page.widget.dart`          | **explícito**                            | OK                                               |
| `attendance_details_tab_4`           | `attendance_details_page.widget.dart`          | **explícito**                            | Trap I — inacessível via `tapOn id`; usar swipes |

**Único risco residual não coberto por código:** a Trap I (`attendance_details_tab_4`) e a Trap H (`new_attendance_start_button`) são armadilhas de layout/semântica, não de falta de `identifier`. A solução para ambas está nos subflows já implementados e não requer modificação do código de produção.
