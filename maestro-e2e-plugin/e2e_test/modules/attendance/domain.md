# Module: Attendance

## 1. Domain Overview
### Module Objective
The Attendance module is responsible for recording, tracking, and managing the daily presence, absence, and leave requests of employees within the organization. It ensures accurate timekeeping for payroll and compliance purposes.

### Actors and Profiles
- **Employee**: Can view their own attendance records, clock in/out, and submit leave requests.
- **Manager**: Can view attendance records of their direct reports, approve/reject leave requests, and override attendance entries.
- **HR Admin**: Has global visibility and modification rights across all attendance data and configuration.

### Business Scope
**In Scope:**
- Daily clock in/clock out events.
- Leave request submission and approval workflow.
- Monthly attendance summary generation.
- Offline caching of clock events when network is unavailable.

**Out of Scope:**
- Payroll calculation.
- Performance evaluations based on attendance.

## 2. Exhaustive Data Model
| Attribute (Dart) | Data Type | Database Field | Validation Rules / Nullability | Business Meaning | Source Code (File) |
|---|---|---|---|---|---|
| `id` | `String` | `attendance_id` | Cannot be null | Unique identifier for the attendance record | [attendance_entity.dart](file:///absolute/path/to/attendance_entity.dart) |
| `employeeId` | `String` | `emp_id` | Cannot be null, must be valid UUID | Identifier of the employee | [attendance_entity.dart](file:///absolute/path/to/attendance_entity.dart) |
| `date` | `DateTime` | `record_date` | Cannot be null, past or current date only | Date of the attendance record | [attendance_entity.dart](file:///absolute/path/to/attendance_entity.dart) |
| `clockInTime` | `DateTime?` | `clock_in` | Nullable, must be before clockOutTime | Time the employee clocked in | [attendance_entity.dart](file:///absolute/path/to/attendance_entity.dart) |
| `clockOutTime` | `DateTime?` | `clock_out` | Nullable, must be after clockInTime | Time the employee clocked out | [attendance_entity.dart](file:///absolute/path/to/attendance_entity.dart) |
| `status` | `AttendanceStatus` | `status_enum` | Cannot be null (Present, Absent, Leave) | The daily status of the employee | [attendance_entity.dart](file:///absolute/path/to/attendance_entity.dart) |
| `notes` | `String?` | `notes` | Nullable, max 500 chars | Optional comments provided by the employee or manager | [attendance_entity.dart](file:///absolute/path/to/attendance_entity.dart) |

## 3. Lifecycle and Relevant States
### Entity Lifecycle
- **Created**: A record is initialized when an employee clocks in or is marked absent by default.
- **Updated**: Record is updated when an employee clocks out or a manager overrides the data.
- **Locked**: Record is locked at the end of the pay period, preventing further edits.

### Presentation States
- **Loading**: Showing a spinner while fetching the monthly attendance summary.
- **Empty**: Showing an illustration when there are no records for a newly hired employee.
- **Error**: Displaying a snackbar if the clock-in request fails due to GPS validation.
- **Offline**: A banner indicating that clock events are stored locally and waiting to sync.

### Offline Handling
When the device is offline, clock in/out events are stored locally in the SQLite database via `AttendanceLocalDataSource`. A background task `SyncAttendanceTask` is scheduled to flush these records to the server once connectivity is restored.

## 4. Functional Areas and Business Logic
### Daily Clock In/Out Flow
- **Entry point and route:** `/attendance/daily`
- **Behaviors and validations:**
  - Employee can only clock in once per day.
  - Clock out is only enabled if the employee is currently clocked in.
  - GPS coordinates must be within the designated geofence (if configured).
- **Success UX and Exit navigation:** Shows a success dialog and updates the dashboard status widget.

## 5. Permissions and Profiles
| Profile/Feature | Observed Rule | Source Code/Seed |
|---|---|---|
| `Employee` | Can only fetch records where `emp_id == currentUserId` | [attendance_repository.dart](file:///absolute/path/to/attendance_repository.dart) |
| `Manager` | Can approve leave requests for `reports_to == currentUserId` | [leave_usecase.dart](file:///absolute/path/to/leave_usecase.dart) |

## 6. Failures Catalog and Error Handling
| Failure (Dart Class) | Trigger Condition | UX Presented to User | Source Code |
|---|---|---|---|
| `GeofenceFailure` | User tries to clock in outside the office perimeter | Dialog: "You must be at the office to clock in." | [clock_in_usecase.dart](file:///absolute/path/to/clock_in_usecase.dart) |
| `DuplicateClockInFailure` | User attempts to clock in when already clocked in | Snackbar: "You are already clocked in today." | [clock_in_usecase.dart](file:///absolute/path/to/clock_in_usecase.dart) |
| `OfflineSyncFailure` | Background sync task fails multiple times | Persistent banner: "Some records haven't synced." | [sync_task.dart](file:///absolute/path/to/sync_task.dart) |

## 7. Scenario Seeds (E2E Test Ideas)
- **Robust Happy Path:** Flow: Employee logs in, navigates to attendance, clicks clock in, confirms location, verifies dashboard updates. Test Data: Valid employee account, mocked GPS within bounds. Technical Risk: Low.
- **Offline Resilience:** Flow: Employee goes offline, clocks in, verifies local state update, goes online, verifies sync banner disappears and data appears on remote. Test Data: Valid employee account, network toggling. Technical Risk: High (state reconciliation).
- **Edge Cases:** Flow: Employee attempts to clock out without clocking in. Test Data: Employee with no daily records. Technical Risk: Medium.

## 8. Adaptive Variations by Screen Size
| Breakpoint | Observable Functional Difference | Widgets/Files |
|---|---|---|
| `small <600dp` | Calendar view changes from full month grid to weekly swipeable strip | [attendance_calendar.dart](file:///absolute/path/to/attendance_calendar.dart) |

## 9. Module File Map
### Domain
- `entities/attendance_entity.dart` — [Defines the Attendance data structure]
- `usecases/clock_in_usecase.dart` — [Handles logic for clocking in]
### Data/Infrastructure
- `models/attendance_model.dart` — [DTO for JSON serialization]
- `repositories/attendance_repository_impl.dart` — [Coordinates remote and local data sources]
### Presentation
- `pages/attendance_page.dart` — [Main UI for viewing attendance]
- `widgets/clock_button.dart` — [Reusable widget for clock in/out actions]
