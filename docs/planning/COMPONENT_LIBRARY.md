# Sakthi Ledger — Component Library

This library is the implementation inventory for the [Sakthi Ledger Design System](../DESIGN_SYSTEM.md). No page may create a visually or behaviorally independent version of a listed component.

## 1. Library architecture

### Foundation layer

- Colour tokens
- Typography tokens
- Spacing and grid
- Radius, border, elevation
- Module identity tokens
- Motion tokens and Framer Motion variants
- Responsive breakpoints
- Icon registry
- Localization and number/date/currency formatting

### Primitive layer

- Text
- Icon
- Divider
- Surface
- Stack / Inline / Grid
- VisuallyHidden
- FocusRing
- Portal

### Control layer

- Button
- IconButton
- LinkButton
- Input
- Textarea
- Select
- Combobox
- Checkbox
- Radio
- Switch
- DatePicker
- DateRangePicker
- FileUpload
- OTP/secure input where required

### Composite layer

- StatusBadge
- RiskBadge
- LoanHealth
- Tag
- Avatar
- IdentityCell
- Money
- Metric
- ProgressBar
- CollectionStrip
- FilterBar
- SavedViewPicker
- TableCommandBar
- DataTable
- Timeline
- Calendar
- ChartFrame
- Notification
- Toast
- Empty/Error/Success state

### Pattern layer

- ApplicationShell
- ContextHeader
- AnalyticsBand
- Workbench
- Record360
- GuidedWizard
- ControlRoom
- ReportWorkspace
- QuickViewDrawer
- ApprovalDrawer
- Receipt

## 2. Foundations API

| Foundation | Required outputs |
|---|---|
| Colour | Global semantic tokens, seven module identity sets, light/dark/print mappings |
| Typography | Plus Jakarta Sans hierarchy, Inter interface, Manrope financial, Noto Sans Tamil |
| Spacing | 4px base / 8px rhythm |
| Motion | Framer Motion duration/easing/spring variants and reduced-motion variants |
| Formatting | Indian currency, compact lakh/crore, percentage, DPD, dates, Tamil locale |
| Icons | One outline family, stable semantic mapping |
| Responsive | Mobile, tablet, laptop, desktop, large desktop helpers |

## 3. Layout components

### ApplicationShell

Slots:

- Navigation
- CommandBar
- ContextHeader
- Main
- ContextRail
- Overlays

States: expanded/collapsed navigation, mobile, offline, session warning, permission-recomposed.

### PageGrid

Variants: 4, 8, 12-column responsive grid; full-bleed operational region; readable narrative region.

### SplitLayout

Variants:

- 40/60
- 50/50
- 60/40
- primary + resizable context rail

Must collapse to stacked/sheet behavior on narrow widths.

### StickyRegion

Uses: command bar, context header, table header, action footer, record summary.

Must calculate offsets centrally; pages cannot invent sticky z-indexes.

## 4. Navigation components

### NavigationRail

- Expanded/collapsed
- Module groups
- Module identity marker
- Permission-aware visibility
- Framer Motion shared active indicator

### MobileNavigation

- Up to five role-priority destinations
- More menu
- Global create trigger
- Safe-area support

### CommandBar

- Search/command palette trigger
- Business date
- Area scope
- Quick create
- Approvals
- Notifications
- Sync status
- User menu

### Breadcrumb

Hierarchy only; stable deep links; compact collapse on mobile.

### Tabs

Variants: record, workspace, report. Maximum seven visible before stable grouping/overflow.

### CommandPalette

Groups: search, navigation, saved views, commands, recent. Keyboard and mobile full-screen modes.

## 5. Typography and financial display

### Heading

Roles: 56 Heading, 42 PageTitle, 28 SectionTitle, 20 CardTitle with responsive scaling.

### Body and Caption

Inter 16 Body; Inter 13 Caption; compact UI 14.

### Money

Props/concepts:

- value
- currency INR
- size: standard/metric/hero
- sign policy
- privacy mask
- semantic tone
- compact lakh/crore mode

Always Manrope SemiBold, tabular figures, Indian grouping.

### FinancialDelta

Shows value, direction, period, and semantic meaning. Positive is not automatically green.

### DPD

Formats future due, due today, and days past due. Uses arrears policy tokens.

## 6. Buttons and actions

### Button

Variants: primary, secondary, tertiary, destructive, quiet-destructive.

Sizes: compact 32, standard 40, large 48.

States: default, hover, focus, pressed, disabled-with-reason, loading, success acknowledgement.

### IconButton

Requires accessible label and tooltip. Only for universal actions.

### QuickActionCluster

Shows context-valid high-frequency actions; never a full site menu.

### OverflowMenu

Groups routine, review, and sensitive/destructive actions.

## 7. Form components

### Field

Composes label, requirement, control, help, warning, error, and audit/sensitivity hint.

### TextInput / Textarea

Variants: standard, masked, read-only, secure reveal, prefix/suffix.

### MoneyInput

Indian grouping after blur; raw numeric semantics; allocation/limit context.

### PhoneInput

India default; normalized storage; duplicate/contact-consent signals.

### AadhaarInput

Masked entry; checksum/length policy; hash duplicate lookup; encrypted persistence; reveal separate from edit.

### Select / Combobox

Searchable for large lists; selected item remains visible; keyboard/touch support.

### DatePicker / DateRangePicker

Business date, blocked dates, financial-year presets, Tamil localization.

### FileUpload

Camera/file source; progress; preview; validation; virus-scan/processing state; retry.

### FormSection

One coherent purpose; responsive field grid; no nested card decoration.

### Wizard

Step rail, draft status, validation summary, sticky footer, review stage, save/resume.

### StepForm

Used inside New Loan drawer and other staged tasks.

## 8. Badges, tags, identity

### StatusBadge

Required mapped statuses include Verified, Pending, Overdue, Closed, Premium, VIP, Active, Inactive plus domain lifecycle states.

Always background + border + icon + label + hover/focus detail + Framer Motion.

### RiskBadge

Low, Moderate, High, Critical, Unscored. Separate from lifecycle status.

### LoanHealth

Healthy, Watch, Stressed, Delinquent, Critical plus explanation trigger and trend.

### Tag

Classification/filter only; removable when appropriate; not a lifecycle status.

### Avatar

Customer photo/initials, collector/user initials, object icon. Size variants 24/28/32/36/40/48.

### IdentityCell

Avatar + primary identity + ID + area/route metadata + optional verification marker.

## 9. Data table system

### TableCommandBar

Search → saved view → filters → active tokens/count → result count → density → columns → export → overflow.

### DataTable

Features:

- Rich identity cells
- Customer/collector avatars where relevant
- Status/Risk/LoanHealth cells
- Money and percentage alignment
- Progress bars
- Due days
- Quick actions
- Expandable row
- Sticky header
- Frozen columns
- Column settings
- Pagination
- Selection/bulk actions
- Quick View drawer
- Loading/refresh/empty/error/offline states
- Compact/standard/comfortable density
- Framer Motion row/update/expand transitions

### ColumnSettings

Show/hide, reorder, freeze, reset; persisted per user/saved view.

### Pagination

Range, total, page size, direct page, previous/next; restores row position.

### MobileWorkQueue

Domain-specific alternative to a squeezed table. Shows identity, critical amount, state, due context, and primary action.

## 10. Analytics and charts

### AnalyticsBand

Module-identity surface with 4–7 metrics desktop and adaptive mobile presentation.

### KPI

Label, Manrope value, period, comparison/target, trend, drill-down. Animated only from confirmed data.

### ChartFrame

Title, business question, scope, controls, chart, direct labels, tooltip, accessible summary, data table, empty/error/loading states.

Chart variants:

- Line
- Area
- Grouped/stacked/ranked bar
- Bullet
- Waterfall
- Ageing band
- Heatmap
- Donut limited to 2–5 parts
- Sparkline

### RiskMeter

Explainable level, score/range, prior state, direction, evaluated time, factors, evidence.

### CreditScore

Score, source, scale, freshness, history, access audit.

### ProgressBar

Exact label, actual/target, over-target behavior, semantic meaning.

### CollectionStrip

100 segments for daily loans: paid, due, upcoming, missed, waived, adjusted.

## 11. Cards and information surfaces

### MetricTile

Used inside structured band, not repeated generic white-card grid.

### SummaryBand

Horizontally aligned financial values and statuses.

### AnalyticalPanel

Chart/table/annotation with module-aware tonal treatment.

### RecordCard

Compact identity, state, essential metadata, next action.

### ExceptionCard

Severity, business impact, reason, owner, due action.

### TonalField / BorderedSection

Alternative to white cards for coherent page regions.

## 12. Overlays

### Dialog

Small 400, medium 560, large 720; focused decision only; no nested dialogs.

### Drawer

400 compact, 480 standard, 640 evidence; full-screen sheet mobile.

### NewLoanDrawer

720px/up to 55vw, staged workflow, sticky header/footer, floating schedule preview.

### QuickViewDrawer

Identity, status, risk, health, financial summary, timeline, actions, previous/next.

### ContextPanel

Resizable desktop rail; sheet mobile; selected evidence/detail only.

### FloatingPanel

Calculator, schedule, allocation, lookup. Never primary creation form.

### Popover / Tooltip / Menu

Shared positioning, collision, focus, dismissal, motion.

## 13. CRM components

### MasterTimeline

Financial, communication, field, document, risk, approval, and system events.

### CommunicationTimeline

Call, SMS, WhatsApp, direction, delivery/read, actor, outcome, next action.

### LoanTimeline

Application, approval, disbursement, instalments, payments, arrears, restructure, closure.

### FamilyTree

Accessible node-link visualization + equivalent structured list.

### DocumentCenter

List/preview split, verification, version, expiry, related record, sensitivity.

### VisitHistory

Collector, purpose, outcome, GPS source/accuracy, attachments, next action.

### CustomerMap

Registered/business/visit/collection locations with source and accuracy.

### FollowUp / Reminder

Owner, due time, channel, purpose, priority, state, outcome.

## 14. Calendars

### OperationsCalendar

Demand, collection, holiday, day close, scheduled report.

### PaymentCalendar

Contractual due, paid, missed, adjusted, upcoming.

### CollectionCalendar

Planned/actual visit, collector, promise, missed action.

### Agenda

Compact/mobile canonical presentation.

## 15. Notifications and feedback

### NotificationCentre

Priority, category, business impact, action, resolution state, grouping.

### NotificationItem

Icon, category, message, impact, timestamp, action, resolution.

### Toast

Success, info, warning, error; queue; optional action; transaction reference.

### Banner

Page/panel warning or critical; title, consequence, action.

### Skeleton

Page, table, chart, record, drawer, timeline, metric variants matching final anatomy.

### EmptyState

First use, no results, completed. One primary and optional secondary action.

### ErrorState

Field, section, page, transaction, partial failure, uncertain outcome.

### SuccessState

Routine, created record, payment, approval, day close, report artifact.

## 16. Financial operations

### PaymentAllocation

Principal, interest, charges, advance/excess; before/after balance.

### Receipt

Confirmed amount, transaction/receipt ID, server time, customer/loan, allocation, mode, collector, verification, delivery actions.

### CashSummary

Opening, inflow, digital, deposits, expense, expected, physical, variance.

### ReconciliationItem

Expected/actual, source, evidence, mismatch, resolution, approval.

### ApprovalSummary

Decision, financial impact, evidence, policy, deviations, prior actions.

## 17. Report components

### ReportCatalogueItem

Purpose, category, parameters, permission, freshness, last generated, schedule.

### ReportParameterBar

Compact essential parameters; advanced parameter drawer.

### ReportPreview

Immutable snapshot, summaries, charts, tables, totals, filters, pagination.

### ExportActionGroup

PDF, Excel, CSV, Print, Share, Email with queued/generating/ready/failed states.

### ExportHistory

Artifact identity, format, file size, checksum metadata, generation/share/email history, expiry.

## 18. Motion variants

Central variants:

- screenEnter/screenExit
- contentStagger
- drawerEnter/drawerExit
- dialogEnter/dialogExit
- notificationEnter/exit
- tableRowEnter/update/expand
- timelineEventEnter
- chartUpdate
- numberUpdate
- progressUpdate
- skeletonPulse
- receiptConfirmed
- reducedMotion equivalents

Pages cannot define ad hoc timing/easing.

## 19. Required component states

Every interactive component supports, where applicable:

- Default
- Hover
- Focus
- Pressed/active
- Selected
- Disabled with reason
- Read-only
- Loading
- Empty
- Warning
- Error
- Success
- Offline/queued/syncing/conflict
- Permission denied
- Reduced motion
- Tamil/long content
- Touch and keyboard

## 20. Library acceptance

- Visual parity in light/dark/print where applicable.
- Accessibility names, keyboard behavior, focus restoration, screen-reader state.
- Responsive stories at 360, 768, 1024, 1440.
- Realistic financial data; no lorem ipsum or demo cards.
- Snapshot and interaction tests.
- No page-specific copy of an existing component.
- No component marked complete without all required states.
