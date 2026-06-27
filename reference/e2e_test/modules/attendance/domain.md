# Módulo: Atendimento

## 1. Visão Geral do Domínio (Foco Clínico ABA)

**Objetivo do Módulo:** O módulo de Atendimento (Attendance) é a sessão de terapia ABA em si — o momento em que o terapeuta aplica programas estruturados (tentativas DTT), registra comportamentos de aquisição (livre operante/naturalístico), ocorrências de comportamentos interferentes e anotações clínicas. Cada atendimento é um artefato temporal com início, dados coletados e encerramento, que alimenta dashboards, relatórios e o registro de evolução diária do estudante.

**Atores/Perfis Clínicos:**

- **Terapeuta (Aplicador):** cria, conduz e encerra o próprio atendimento; pode registrar todos os tipos de dado durante a sessão.
- **Supervisor/Coordenador ABA:** pode criar atendimentos por qualquer terapeuta do grupo; pode excluir atendimentos de terceiros (feature-gated); visualiza o histórico completo e a localização.
- **Sistema:** encerra automaticamente atendimentos por inatividade (finishedBy: 'system').

**Escopo de Negócio:** O módulo gerencia o ciclo de vida de um atendimento — criação (com seleção de folhas estruturadas, comportamentos e GPS), execução (registro de tentativas, comportamentos livres, interferentes e notas), encerramento (finalização ou descarte). O histórico de atendimentos por estudante é exibido e filtrado aqui. O registro de evolução diária (`StudentDailyProgress`) é vinculado ao atendimento, mas gerido por módulo próprio. Programas e comportamentos provêm dos módulos `program` e `behavior`; sua parametrização (datasheets, alvos) está fora do escopo deste módulo.

---

## 2. Modelo de Dados Exaustivo

### Entidade Principal: `Attendance`

[`attendance.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance.model.dart)

| Atributo (Dart)          | Tipo de Dado                   | Campo Firestore                        | Regras de Validação / Nulidade                                                                                          | Significado Clínico ABA                                                | Origem no Código                         |
| ------------------------ | ------------------------------ | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------- |
| `id`                     | `AttendanceId` (Id)            | `attendanceId` (doc ID)                | Gerado com `IdGenerator.newId()` antes da persistência                                                                  | Identificador único do atendimento                                     | `attendance.model.dart`                  |
| `therapist`              | `User`                         | `therapist.*` (parcial)                | Obrigatório; salvo como `User.partialOf(therapist)`                                                                     | Terapeuta que conduz a sessão                                          | `attendance.model.dart`                  |
| `student`                | `Student`                      | `student.*`                            | Obrigatório; studentId validado antes da criação                                                                        | Estudante em atendimento                                               | `create_attendance.usecase.dart`         |
| `status`                 | `AttendanceStatus` (enum)      | `status`                               | Enum: `created` / `ongoing` / `finished`                                                                                | Estado da sessão clínica                                               | `attendance_status.enum.dart`            |
| `observations`           | `List<Note>`                   | `observations` (Map keyed by `noteId`) | Pode ser vazio; upsert: `observations.${note.id}`; delete: `FieldValue.delete()`; ordenado por `createdAt` no ViewModel | Anotações de sessão (texto livre)                                      | `attendance.model.dart`                  |
| `startedAt`              | `DateTime?`                    | `startedAt`                            | Definido em `CreateAttendanceUseCase` via `callContext.calledAt`                                                        | Carimbo de início da sessão                                            | `create_attendance.usecase.dart`         |
| `finishedAt`             | `DateTime?`                    | `finishedAt`                           | Nulo até encerramento; pode ser `lastUpdatedAt()` se timeout                                                            | Carimbo de encerramento da sessão                                      | `finish_attendance.usecase.dart`         |
| `lastActivityDate`       | `DateTime?`                    | `lastActivityDate`                     | Atualizado a cada minuto na tela de atendimento em andamento                                                            | Âncora para detecção de inatividade                                    | `update_last_activity_date_usecase.dart` |
| `finishedBy`             | `String?`                      | `finishedBy`                           | `null` até encerramento; valor: userId ou `'system'`                                                                    | Identifica encerramento manual vs. automático                          | `finish_attendance.usecase.dart`         |
| `programs`               | `List<Program>`                | `programs[]`                           | Pode ser vazio (atendimento apenas comportamental); inclui tentativas e blocos                                          | Programas estruturados aplicados na sessão                             | `attendance.model.dart`                  |
| `behaviorSessionRecords` | `List<BehaviorSessionRecords>` | `behaviorSessionRecords[]`             | Pode ser vazio; inclui registros de aquisição e interferentes                                                           | Histórico de comportamentos da sessão (livre operante + interferentes) | `attendance.model.dart`                  |
| `studentDailyProgressId` | `StudentDailyProgressId?`      | `studentDailyProgressId`               | Nulo até o terapeuta vincular evolução diária                                                                           | Vínculo com o registro de evolução do estudante                        | `attendance.model.dart`                  |
| `calendarEventId`        | `CalendarEventId?`             | `calendarEventId`                      | Nulo para atendimentos não agendados                                                                                    | Vínculo com evento do calendário que originou o atendimento            | `attendance.model.dart`                  |
| `geolocation`            | `Geolocation?`                 | `geolocation.*`                        | Nulo se a feature não estiver ativa ou o dispositivo negou                                                              | Localização GPS do atendimento (trava clínica em algumas contas)       | `attendance.model.dart`                  |
| `metadata`               | `Metadata?`                    | `metadata.*`                           | Contém `createdBy`, `createdAt`, `updatedAt`                                                                            | Rastreabilidade de quem criou e quando                                 | `Entity<AttendanceId>` base              |

### Campos Computados (Entidade)

| Campo                      | Tipo        | Lógica                                                                                                                                         | Significado                                      |
| -------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `lastUpdatedAt()`          | `DateTime?` | `max(lastActivityDate, metadata.updatedAt)`                                                                                                    | Data mais recente de qualquer atividade          |
| `isTimedOut()`             | `bool`      | `elapsedSinceLastActivity >= Duration(hours: AppSettingsService.attendanceInactivityTimeoutHours)` — padrão: **6 horas** (remoto configurável) | Sinaliza encerramento automático por inatividade |
| `elapsedSinceLastActivity` | `Duration`  | `DateTime.now() - lastUpdatedAt()`                                                                                                             | Tempo decorrido desde a última ação              |

Fonte: [`attendance.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance.model.dart), [`system/app_settings.service.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/system/app_settings.service.dart)

### ViewModel: `AttendanceViewModel`

[`attendance.view_model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/view_models/attendance.view_model.dart)

| Computed                 | Lógica                                                                                                                                             |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `hasRecords`             | `true` se qualquer `attemptBlock.hasRecords` OU qualquer behavior com records OU qualquer observação não vazia OU `studentDailyProgressId != null` |
| `inappropriateBehaviors` | Filtra `behaviorSessionRecordsList` onde `behavior.isInappropriate == true`                                                                        |
| `aquisitionBehaviors`    | Filtra `behaviorSessionRecordsList` onde `behavior.isInappropriate == false`                                                                       |
| `programsById`           | `Map<String, ProgramViewModel>` para lookup O(1)                                                                                                   |
| `attemptBlocksById`      | `Map<String, AttemptBlockViewModel>` para lookup O(1)                                                                                              |

### Entidade Secundária: `AttendanceSummary`

Projeção leve usada na listagem do histórico. Campos: `attendanceId`, `therapistId`, `therapistName`, `startedAt`, `finishedAt`, `status`, `createdBy`, `studentId`, `studentDailyProgressId`, `calendarEventId`.

Computed: `isExpired()` — `status == ongoing && DateTime.now() - startedAt > 12h`.

Fonte: [`attendance_summary.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance_summary.model.dart)

### Entidade: `Geolocation`

[`geolocation.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/geolocation.model.dart)

| Atributo                                | Tipo           | Significado                                              |
| --------------------------------------- | -------------- | -------------------------------------------------------- |
| `deviceAllowedUsToAsk`                  | `bool`         | O dispositivo permitiu solicitar permissão               |
| `isLocationPermissionAlwaysEnabled`     | `bool`         | Permissão "sempre" concedida                             |
| `userAllowedUsToAsk`                    | `bool`         | Usuário concedeu permissão de localização                |
| `isLocationPermissionPermanentlyDenied` | `bool`         | Permissão negada permanentemente                         |
| `isLocationServiceDisabled`             | `bool`         | Serviço de GPS desativado no dispositivo                 |
| `startingPosition`                      | `Geoposition?` | Coordenadas (latitude, longitude, accuracy, altitude...) |
| `address`                               | `Address?`     | Endereço resolvido via geocodificação reversa            |

Computed: `hasValidCoordinates`, `latitude`, `longitude`, `accuracyInMeters`.

### Cache Local: `AttendanceDataCache`

[`attendance_data_cache.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance_data_cache.model.dart)

Persistido localmente via `ILocalStorageService` (Hive) sob a chave `'AttendancesOnGoing'` (JSON indexado por `userId`). Campos: `attendanceId`, `userId`, `studentId`, `accountId`, `institutionName?`, `attendance?`. Apenas um atendimento por `userId` é armazenado no cache simultaneamente — tentativa de cachear um atendimento com mesmo `attendanceId` substitui a entrada anterior.

---

## 3. Ciclo de Vida da Entidade e Estados da UI

### Diagrama ASCII do Ciclo de Vida

```text
[CRIADO (created)]
      │
      │ BeginOrResumeAttendanceUseCase
      │ (markAsOngoing + stream aguarda status==ongoing, timeout 10s)
      ▼
[EM ANDAMENTO (ongoing)] ◀─── BeginOrResumeAttendanceUseCase (resume)
      │         │
      │         │ isTimedOut() == true
      │         ▼
      │    [TIMEOUT → FinishAttendanceUseCase(finishedBy:'system')]
      │
      │ FinishAttendanceUseCase (manual, useLastActivityDate: false)
      ▼
[ENCERRADO (finished)]
      │
      │ DeleteAttendanceUseCase (sempre disponível no histórico)
      ▼
    [∅ — removido do Firestore e do cache]

Caminho alternativo:
[CRIADO] → hasRecords == false → DiscardAttendance → DeleteAttendanceUseCase → [∅]
```

### Estados da Apresentação

**Nova tela de atendimento (modal):**

- Carregando: `FullscreenLoadingWidget` enquanto `ensureInitialized()` busca programas e comportamentos
- Página 0: revisão de dados (estudante, terapeuta, data, GPS)
- Página 1: seleção de folhas estruturadas (pode ser vazia)
- Página 2: seleção de comportamentos de aquisição
- Página 3: seleção de interferentes → botão "Iniciar atendimento"
- Erro de criação: toast "Não foi possível iniciar o atendimento, verifique sua conexão e tente novamente."

**Ongoing Attendance Page:**

- Carregando: stream do Firestore aguarda `status == ongoing`
- Em andamento: 4 abas (Estruturado / Naturalístico / Interferentes / Anotações)
- Diálogo discard (hasRecords == false): "Atendimento sem registros" — botões "Descartar" / "Continuar"
- Diálogo finalizar (hasRecords == true): confirmação — todos os registros estão salvos
- Modal de timeout: "Atendimento encerrado automaticamente pelo sistema" (OK → navega para detalhes)
- Modal de atendimento excluído: "Não é possível continuar, este atendimento foi excluído." (OK)

**Histório de Atendimentos:**

- Carregando: SkeletonScaffold
- Lista vazia: "Nenhum atendimento para exibir ainda"
- Lista preenchida: agrupada por data, com cabeçalho "Hoje / [dia da semana] (dd/mm/aaaa)"
- Filtro por terapeuta: toolbar chip selector (multi-select)
- Busca: por data formatada ou nome do terapeuta

### Tratamento Offline

- **Criação:** requer conexão. `CouldNotStartAttendanceFailure` ou `MustBeOnlineToStartAttendanceFailure` (mapeado de `RepositoryFailure.isServiceUnavailable()`) → toast de erro.
- **Execução (após criado):** atualizações otimistas — UI atualiza antes da confirmação do Firestore. `SaveRecordUseCase` e `AddBehaviorRecordUseCase` são fire-and-forget.
- **Cache local:** `AttendanceDataCache` (Hive) persiste o `attendanceId` em andamento; ao reabrir o app, `LoadUserOngoingAttendanceDataCacheUseCase` detecta e oferece retomada.
- **Sincronização:** a stream do Firestore é a fonte de verdade; reconexão sincroniza automaticamente.
- **Programas (AddProgramsToAttendanceUseCase):** fire-and-forget; se falhar, erro de conexão é exibido (localização: `attendance_page.add_programs_modal.messages.failures.connection_error`: "Não foi possível adicionar a(s) folha(s). Verifique sua conexão.").

**Rota Firestore:** `students/{studentId}/attendances/{attendanceId}` (subcoleção sob o documento do estudante). Coleção de summaries por mês: `students/{studentId}/attendances-by-month/{yyyy-MM}`.

Fonte: [`create_attendance.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/create_attendance.usecase.dart), [`attendance_firebase.repository.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/infrastructure/attendance_firebase.repository.dart)

---

## 4. Áreas Funcionais e Lógica de Negócio

### 4.1 Iniciar Atendimento (Modal)

**Ponto de Entrada:** Botão `student_start_attendance_button` (`ElevatedButton` com `Semantics(identifier: 'student_start_attendance_button')`) na `StudentDetailPage` → `NewAttendanceModalWidget`. Se houver eventos agendados não finalizados para o estudante, o botão exibe um badge de contagem e abre `ScheduledAttendanceDialog` em vez do modal direto. Pode ser disparado também via `ScheduledAttendanceDialog` (evento agendado do calendário).

**Rota:** modal sem rota de GoRouter própria; push de `NewAttendanceModalWidget` via `AppRouter`.

**Fluxo do modal (PageView — 4 páginas):**

| Página             | Conteúdo                                                            | Ação                |
| ------------------ | ------------------------------------------------------------------- | ------------------- |
| 0 — Confirmar      | Estudante, terapeuta, data/hora atual, botão "Permitir uso do GPS?" | `nextPage()`        |
| 1 — Folhas         | `StructuredDatasheetSelectionWidget` (folhas ativas dos programas)  | `nextPage()`        |
| 2 — Livre Operante | `BehaviorSelectionWidget` (naturalistic behaviors)                  | `nextPage()`        |
| 3 — Interferentes  | `BehaviorSelectionWidget` (inappropriate behaviors)                 | `startAttendance()` |

**GPS:** `LocationObtainerWidget` obtém a localização antes de confirmar. Se negado/desativado, `Geolocation` é criado com `userAllowedUsToAsk: false` — o atendimento prossegue sem coordenadas.

**`startAttendance()`:** chama `IAttendanceFlow.startAttendance()` → `CreateAttendanceUseCase` + `BeginOrResumeAttendanceUseCase`. Navega para `OngoingAttendancePage`.

**Rota de saída:** `OngoingAttendancePageRoute` (parâmetros: `accountId`, `studentId`, `attendanceId`). Se somente comportamentos foram selecionados (sem folhas), abre diretamente na aba de comportamentos (`pageName + '_1'`).

**Risco técnico:** entre a abertura do modal e o `startAttendance()`, o Firestore pode estar indisponível (offline) → `MustBeOnlineToStartAttendanceFailure` → toast "Não foi possível iniciar o atendimento, verifique sua conexão e tente novamente."

### 4.2 Atendimento em Andamento (Ongoing Attendance Page)

**Rota:** `OngoingAttendancePageRoute` com `accountId`, `studentId`, `attendanceId`.

**AppBar:** tag "Em atendimento" + nome do estudante + timer + botão "Finalizar".

**4 Abas (StatefulNavigationShell + TabController):**

| Aba           | LocaleKey                           | Conteúdo                                                  |
| ------------- | ----------------------------------- | --------------------------------------------------------- |
| Estruturado   | `aba_terms.structured.singular`     | Blocos de tentativas DTT por programa/folha               |
| Naturalístico | `aba_terms.naturalistic.singular`   | Registros de comportamentos de aquisição (livre operante) |
| Interferentes | `aba_terms.problem_behavior.plural` | Registros de comportamentos interferentes                 |
| Anotações     | `aba_terms.note.plural`             | Notas de sessão (texto livre)                             |

**Timer de inatividade:** `Timer.periodic(1 minuto)` chama `UpdateLastActivityDateUseCase`.

**Finalizar (hasRecords == true):**

1. Dialog: "Todos os registros estão salvos." → confirmar → `FinishAttendanceUseCase(useLastActivityDate: false)` → navega para `AttendanceDetailsPage`.
2. Se `isTimedOut()`: `finishedBy = 'system'`, `finishedAt = lastUpdatedAt()`.

**Descartar (hasRecords == false):**

1. Dialog "Atendimento sem registros" → "Descartar" → `DeleteAttendanceUseCase` → navega para `StudentAttendancesPage`.
2. "Continuar" → fecha o dialog, permanece na tela.

**Aba Estruturado — Lógica de Tentativas:**

- `SaveRecordUseCase`: otimista, fire-and-forget.
- `AddAttemptBlock`: conclui bloco atual (`FinishAttemptBlockUseCase`) + cria novo bloco.
- `ReplaceAttemptBlock`: substitui bloco existente por nova configuração de folha.
- `RandomizeAttemptsUseCase` / `UndoRandomizationUseCase`: embaralha/desfaz a ordem dos alvos no bloco.
- `AddProgramsToAttendanceUseCase`: adiciona folhas/programas durante a sessão (fire-and-forget; erro de conexão exibido via toast).

**Aba Anotações:**

- Adicionar: `AddObservationUseCase`.
- Editar in-line: `UpdateObservationUseCase`.
- Excluir: `DeleteObservationUseCase`.
- Permissão: qualquer participante da conta pode anotar.

### 4.3 Histórico de Atendimentos (Student Attendances Page)

**Rota:** `StudentAttendancesPageRoute` (parâmetros: `accountId`, `studentId`).

**Data source:** stream real-time do Firestore via `StreamAttendancesUseCase` → agrupado por data local via `foundation.compute` (isolate).

**AppBar secundário (toolbar):** contador de atendimentos, seletor de terapeuta (multi-select chips), botão de busca.

**Busca:** por data formatada (`getHeaderDate`) OU por `AttendanceSummary.searchHasMatch(text)` (nome do terapeuta).

**Web:** filtro de terapeuta sincronizado com query param `?therapistId=...` na URL.

**Delete:** `canDeleteAttendance(attendance, student)` → popup menu com "Excluir" → `DeleteAttendanceConfirmationDialogWidget` (requer digitar "EXCLUIR ATENDIMENTO") → `DeleteAttendanceUseCase`.

**Navegação para detalhes:** tap em qualquer item → `AttendanceDetailsPageRoute`.

### 4.4 Detalhes do Atendimento (Attendance Details Page)

**Rota:** `AttendanceDetailsPageRoute` (parâmetros: `accountId`, `studentId`, `attendanceId`).

**Dados:** stream real-time via `StreamAttendanceUseCase`.

**5 Abas:**

| Aba           | LocaleKey                                          | Conteúdo                                                     |
| ------------- | -------------------------------------------------- | ------------------------------------------------------------ |
| Resumo        | `attendance_details_page.tabs.attendance_summary`  | Métricas gerais: acertos, aproveitamento, duração, registros |
| Estruturado   | `aba_terms.structured.singular`                    | Blocos de tentativas (somente leitura)                       |
| Naturalístico | `aba_terms.naturalistic.singular`                  | Comportamentos de aquisição                                  |
| Interferentes | `aba_terms.problem_behavior.plural`                | Comportamentos interferentes                                 |
| Anotações     | `attendance_details_page.tabs.observation_summary` | Notas de sessão                                              |

**Localização:** botão de localização na AppBar → `AttendanceLocationDialog` (mostra mapa estático + endereço; estados: "Obtendo localização", "Localização não obtida" com motivo específico, mapa disponível).

**Evolução diária:** aba de evolução víncula `StudentDailyProgressId` ao atendimento via `canAddDailyProgressToAttendance`.

### 4.5 Atendimento Agendado (Scheduled Attendance Dialog)

**Ponto de Entrada:** FAB badge na `StudentDetailPage` mostra contagem de eventos agendados; tap → `ScheduledAttendanceDialog`.

**Conteúdo:** lista de atendimentos agendados para hoje com status (em andamento, finalizado, pendente).

**Ações por item:**

- "Iniciar" → flow padrão de novo atendimento.
- "Antecipar" → dialog de confirmação com horário previsto → inicia imediatamente.
- "Atrasado" → dialog mostrando o atraso → inicia imediatamente.
- "Atendimento não agendado" → abre modal padrão sem `calendarEventId`.

---

## 5. Matriz de Permissões

| Permissão                         | Método                                                 | Condição                                                                                                | UX para acesso negado                                        |
| --------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Criar atendimento                 | `canCreateAttendance(student)`                         | `canEditStudent(student)` AND `Feature.students_atendances_create`                                      | FAB não exibido                                              |
| Excluir próprio atendimento       | `canDeleteAttendance(attendance, student)`             | `canEditStudent(student)` AND `createdBy == userId`                                                     | Popup menu ausente                                           |
| Excluir atendimento de terceiro   | `canDeleteAttendance(attendance, student)`             | `canEditStudent(student)` AND `Feature.students_atendances_delete` AND (não `ongoing` OU `isExpired()`) | Popup menu ausente                                           |
| Coletar localização               | `canCollectAttendanceLocation()`                       | Feature de billing habilitada OU plano trial                                                            | GPS não solicitado; `Geolocation(userAllowedUsToAsk: false)` |
| Adicionar evolução ao atendimento | `canAddDailyProgressToAttendance(attendance, student)` | Terapeuta: apenas próprio atendimento; Supervisor: `Feature.students_daily_progress_create`             | Aba de evolução não exibida                                  |
| Vincular evolução diária          | `canBindDailyProgressToAttendance(summary, student)`   | `canEditStudent(student)` e atendimento próprio (terapeuta)                                             | Campo de vínculo não exibido                                 |

Fonte: [`permissions.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/user/core/permissions.dart)

---

## 6. Catálogo de Failures e Tratamento de Erros

| Failure (Classe Dart)                           | Condição de Disparo                                                   | UX Apresentada ao Usuário                                                                                                                                                   | Origem no Código                                                                                                                                                                                                 |
| ----------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MustBeOnlineToStartAttendanceFailure`          | `RepositoryFailure.isServiceUnavailable()` durante `createAttendance` | Toast: "Não foi possível iniciar o atendimento, verifique sua conexão e tente novamente."                                                                                   | [`create_attendance.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/create_attendance.usecase.dart)                   |
| `CouldNotStartAttendanceFailure`                | Qualquer outro erro durante `createAttendance`                        | Toast: "Não foi possível iniciar o atendimento, verifique sua conexão e tente novamente."                                                                                   | [`create_attendance.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/create_attendance.usecase.dart)                   |
| `InvalidStatusToBeginOrResumeAttendanceFailure` | `BeginOrResumeAttendance` recebe status `finished`                    | Toast: "Erro. O Atendimento solicitado não pode ser aplicado"                                                                                                               | [`begin_or_resume_attendance.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/begin_or_resume_attendance.usecase.dart) |
| `InvalidStatusToFinishAttendanceFailure`        | `FinishAttendance` recebe status inválido                             | Toast: "Erro: o Atendimento não foi finalizado corretamente"                                                                                                                | [`finish_attendance.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/finish_attendance.usecase.dart)                   |
| `AttendanceNotFoundFailure`                     | Firestore não encontra o documento do atendimento                     | Toast genérico de erro + widget de erro de carregamento                                                                                                                     | [`attendance_not_found.failure.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/failures/attendance_not_found.failure.dart)              |
| `AttendanceDataCacheFailure`                    | Erro ao ler/escrever o cache local Hive                               | Toast genérico de erro; retomada do atendimento pode falhar                                                                                                                 | [`attendance_data_cache_failure.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/failures/attendance_data_cache_failure.dart)            |
| `TimeoutFailure` (interno)                      | Stream aguarda `status == ongoing` por > 10 segundos                  | Propaga como `CouldNotStartAttendanceFailure`                                                                                                                               | [`begin_or_resume_attendance.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/begin_or_resume_attendance.usecase.dart) |
| `LocationPermissionPermanentlyDeniedFailure`    | GPS permanentemente negado                                            | Toast na tela de localização: "A permissão de localização está desativada. Se desejar registrar a localização, você precisará habilitá-la nas configurações do aplicativo." | [`get_user_geo_location.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/get_user_geo_location.usecase.dart)           |
| `LocationServiceDisabledFailure`                | Serviço de GPS desativado no dispositivo                              | Dialog de localização: "Serviço de localização indisponível" + botão "Ativar localização"                                                                                   | [`get_user_geo_location.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/get_user_geo_location.usecase.dart)           |
| `Failure('finished at cannot be null')`         | `FinishAttendance` sem data de encerramento calculável                | Toast: "Erro: o Atendimento não foi finalizado corretamente"                                                                                                                | [`finish_attendance.usecase.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/finish_attendance.usecase.dart)                   |

---

## 7. Sementes de Cenário

### Caminho Feliz Robusto

- **iniciar_e_finalizar_atendimento:** terapeuta navega para estudante com programas ativos → abre modal → seleciona folha estruturada + 1 comportamento de aquisição + 1 interferente → inicia → registra 3 tentativas no bloco DTT → registra 1 ocorrência de comportamento → adiciona 1 anotação → finaliza → verifica que na página de detalhes os dados persistiram (acertos, comportamentos, anotações). **Dados de teste:** `<estudante_com_programas>`, `<folha_ativa>`, `<comportamento_aquisicao>`, `<interferente>`. **Risco técnico:** corrida entre o `unawaited(markAsOngoing)` e a stream aguardando `status == ongoing` (timeout de 10s).

- **descartar_atendimento_sem_registros:** terapeuta inicia atendimento sem selecionar nada → tela de andamento → toca "Finalizar" → dialog "Atendimento sem registros" aparece → confirma descarte → atendimento removido do Firestore → retorna para histórico de atendimentos. **Risco técnico:** verificar que o atendimento não aparece mais na lista após o descarte (latência Firestore).

### Resiliência Offline

- **criacao_offline:** dispositivo sem conexão → terapeuta tenta iniciar atendimento → toast "Não foi possível iniciar o atendimento, verifique sua conexão e tente novamente." → modal permanece aberto → restaura conexão → tenta novamente → sucesso. **Risco técnico:** `MustBeOnlineToStartAttendanceFailure` vs. `CouldNotStartAttendanceFailure` — verificar qual failure é mapeado.

- **retomada_apos_fechamento_app:** terapeuta inicia atendimento → fecha o app forçadamente → reabre → sistema detecta `AttendanceDataCache` → oferece retomada → `BeginOrResumeAttendanceUseCase` com status `ongoing` → sessão retomada com dados preservados. **Risco técnico:** `AttendanceDataCacheFailure` se o Hive corrompeu; sincronização do `lastActivityDate` após retomada.

- **registro_durante_instabilidade:** atendimento em andamento → conexão cai → terapeuta registra 5 tentativas → conexão restaura → verifica persistência no Firestore e nos detalhes do atendimento. **Risco técnico:** tentativas fire-and-forget podem ser perdidas sem retry; verificar se o ViewModel local ficou dessincronizado do Firestore.

### Casos de Borda Clínicos

- **timeout_por_inatividade:** atendimento com dados registrados → dispositivo inativo por tempo superior a `attendanceInactivityTimeoutHours` → ao reabrir: modal "Atendimento encerrado automaticamente pelo sistema" → toca OK → navega para detalhes → `finishedBy == 'system'` e `finishedAt == lastUpdatedAt()`. **Risco técnico:** `isTimedOut()` calculado com `DateTime.now()` local — verificar se a diferença de fuso horário do emulador afeta o cálculo.

- **atendimento_agendado_antecipado:** evento agendado para horário futuro → terapeuta aciona "Antecipar" → dialog de confirmação com horário previsto → confirma → atendimento iniciado com `calendarEventId` vinculado → verificar `AttendanceSummary.calendarEventId` persistido. **Risco técnico:** race condition entre o início antecipado e a atualização do evento no calendário.

- **cancelamento_no_modal_em_etapas:** terapeuta avança até a página 3 do modal (interferentes) → volta para página 0 → fecha o modal sem iniciar → verificar que nenhum atendimento foi criado no Firestore. **Risco técnico:** o `CreateAttendanceUseCase` é chamado somente no `startAttendance()` — confirmar que não há chamada prematura.

### Concorrência e Estado

- **dois_terapeutas_mesmo_estudante:** terapeuta A inicia atendimento para o estudante → terapeuta B (supervisor) inicia outro atendimento para o mesmo estudante → ambos estão em andamento simultaneamente → verificar que cada `AttendanceId` é independente e ambos aparecem no histórico. **Risco técnico:** `BeginOrResumeAttendanceUseCase.saveAttendanceInCache` sobrescreve o cache — apenas um atendimento por usuário por vez no cache local.

- **rapida_sequencia_de_tentativas:** terapeuta registra tentativas em velocidade máxima (tapping rápido) no bloco DTT → verificar que todas as tentativas foram persistidas sem duplicação ou perda. **Risco técnico:** operações otimistas concorrentes no mesmo `attemptBlock`; ausência de debounce no `SaveRecordUseCase`.

- **adicionar_programa_durante_sessao:** atendimento em andamento sem folhas estruturadas → terapeuta adiciona programa via modal "Adicionar programas" → verifica que o programa aparece na aba Estruturado. **Risco técnico:** `AddProgramsToAttendanceUseCase` é fire-and-forget; o ViewModel é atualizado otimisticamente antes da confirmação do Firestore.

### Validação e Permissão

- **terapeuta_sem_permissao_delete:** terapeuta visualiza histórico de atendimento de outro terapeuta → popup menu não deve exibir "Excluir" (sem `Feature.students_atendances_delete`). **Risco técnico:** `canDeleteAttendance` depende de `attendance.createdBy` — verificar que o campo está presente no `AttendanceSummary` do seed.

- **excluir_atendimento_em_andamento_expirado:** atendimento com status `ongoing` e `isExpired() == true` (iniciado há > 12h) → supervisor pode excluir → dialog de confirmação → "EXCLUIR ATENDIMENTO" digitado → exclusão bem-sucedida. **Risco técnico:** a verificação de `isExpired()` usa `DateTime.now()` — no emulador, manipular o relógio pode ser necessário para simular este cenário.

- **gps_permanentemente_negado:** permissão de localização permanentemente negada no dispositivo → modal de novo atendimento mostra tela de GPS com texto "A permissão de localização está desativada..." + botão "Abrir configurações" → atendimento pode ser iniciado mesmo sem localização → `geolocation.userAllowedUsToAsk == false` persistido. **Risco técnico:** o emulador Android pode não ter GPS habilitado por padrão.

---

## 8. Variações Adaptativas por Tamanho de Tela

Com base na análise do código da camada de apresentação do módulo `attendance`:

A maioria das telas não usa `AppWindowBreakpoints` (`NewAttendanceModalWidget`, `StudentAttendancesPageWidget`, `AttendanceDetailsPageWidget`). A exceção é a **aba Estruturado da tela de atendimento em andamento**.

### Aba Estruturado (`AttendanceStructuredTabWidget`)

[`attendance_structured_tab.widget.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/ongoing_attendance_page/widgets/tabs/attendance_structured_tab/attendance_structured_tab.widget.dart) usa `AdaptiveLayout` com dois slots distintos:

| Breakpoint           | Widget de layout                                              | Comportamento                                                                                                                                                      |
| -------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `small <600dp`       | `AttendanceProgramsScrollableSheetView`                       | Lista de blocos na tela principal; tap num `AttemptBlockTileWidget` abre um `DraggableScrollableSheet` cobrindo a lista para exibir `AttemptBlockDatasheetWidget`. |
| `mediumAndUp ≥600dp` | `AttendanceProgramListWidget` + `AttemptBlockDatasheetWidget` | Painel lateral fixo: lista de blocos à esquerda, folha de registro à direita (side-by-side).                                                                       |

**Implicação para os testes E2E:** emuladores Android de telefone rodam a `<600dp` → variante `small` é o caminho padrão. No `small`, a folha de registro só fica acessível após abrir o `DraggableScrollableSheet` (superfície ocluída enquanto fechada).

Referência: [`app_breakpoints.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/theme/app_breakpoints.dart) — `small <600dp`, `medium 600–839dp`, `large >839dp` (via `flutter_adaptive_scaffold`).

---

## 9. Mapa de Arquivos do Módulo

### Domínio

- **Entidade principal:** [`core/attendance.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance.model.dart)
- **Entidade summary:** [`core/attendance_summary.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance_summary.model.dart)
- **Entidade status:** [`core/attendance_status.enum.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance_status.enum.dart)
- **Entidade geolocalização:** [`core/geolocation.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/geolocation.model.dart)
- **Entidade cache:** [`core/attendance_data_cache.model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/attendance_data_cache.model.dart)
- **Interface repositório:** [`core/i_attendance_repository.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/i_attendance_repository.dart)
- **Failures:** [`core/failures/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/failures/)
- **Use Cases (22):** [`core/use_cases/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/use_cases/) + [`core/usecases/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/core/usecases/)

### Infraestrutura / Dados

- **Data model + mapper:** [`infrastructure/attendance.data_model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/infrastructure/attendance.data_model.dart), [`attendance_model.mapper.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/infrastructure/attendance_model.mapper.dart)
- **Repositório Firebase:** [`infrastructure/attendance_firebase.repository.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/infrastructure/attendance_firebase.repository.dart)
- **Summary data model:** [`infrastructure/attendance_summary.model.data_model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/infrastructure/attendance_summary.model.data_model.dart)
- **Geolocation data model:** [`infrastructure/geolocation.data_model.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/infrastructure/geolocation.data_model.dart)

### Apresentação

- **Modal de novo atendimento:** [`presentation/new_attendance_modal/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/new_attendance_modal/)
- **Tela de atendimento em andamento:** [`presentation/ongoing_attendance_page/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/ongoing_attendance_page/)
- **Histórico de atendimentos:** [`presentation/student_attendances_page/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/student_attendances_page/)
- **Detalhes do atendimento:** [`presentation/attendance_detail_page/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/attendance_detail_page/)
- **Dialog de atendimento agendado:** [`presentation/dialogs/scheduled_attendance_dialog.widget.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/dialogs/scheduled_attendance_dialog.widget.dart)
- **Dialog de localização:** [`presentation/dialogs/attendance_location_dialog/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/dialogs/attendance_location_dialog/)
- **ViewModels:** [`presentation/view_models/`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/view_models/)
- **Flow (orquestração de UI):** [`presentation/attendance.flow.dart`](file:///home/corporaterick/Documents/Projects/aplicatudo-monorepo/projects/aplicatudo/lib/modules/attendance/presentation/attendance.flow.dart)

---

## 10. Relacionados e Interfaces de Integração

- **`student`:** O atendimento é sempre vinculado a um `Student`. A `StudentDetailPage` é o ponto de entrada para criar atendimentos. O histórico (`StudentAttendancesPage`) é acessado via menu "Atendimentos" na `StudentDetailPage`.
- **`program`:** Os programas e suas folhas de registro (datasheets) são carregados via `IStudentProgramFlow.listStudentPrograms()` durante a inicialização do modal. Não há importação direta — comunicação via Flow pattern.
- **`behavior`:** Comportamentos de aquisição e interferentes são carregados via `IBehaviorFlow` durante a inicialização do modal.
- **`student_daily_progress`:** O atendimento pode ser vinculado a um registro de evolução diária. O vínculo é gerido pelo módulo `student_daily_progress`; o atendimento apenas armazena o `studentDailyProgressId`.
- **`calendar_event`:** Atendimentos originados de eventos agendados carregam `calendarEventId`. O módulo de calendário gerencia os eventos; o atendimento apenas referencia o ID.
- **`record`:** Tentativas individuais (`Record`) são persistidas via `SaveRecordUseCase` dentro do contexto do atendimento.
- **`attempt-block`:** Blocos de tentativas são geridos dentro do atendimento; `AddAttemptBlockUseCase`, `FinishAttemptBlockUseCase` e `ReplaceAttemptBlockUseCase` operam sobre eles.
- **Firebase Functions:** O repositório chama duas Cloud Functions via `FirebaseFunctions`: `signStaticMapUrlOnCall` (assina URL do mapa estático para exibição segura) e `getAddressFromCoordinatesOnCall` (geocodificação reversa de latitude/longitude → `Address`). Ambas são invocadas no `AttendanceLocationDialog` para exibir a localização do atendimento.
- **`collection_names.dart` / `collection_names.ts`:** O nome da coleção Firestore de atendimentos deve estar sincronizado entre `projects/aplicatudo/lib/configurations/firestore/collection_names.dart` e `projects/functions/src/repository/collection_names.ts`.
