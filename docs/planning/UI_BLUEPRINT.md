# Sakthi Ledger — Complete UI Blueprint

## 1. Experience model

Sakthi Ledger is an analytical operating system for an NBFC. Authenticated pages begin with business position, exceptions, and work—not forms. Creation occurs only through explicit actions and focused task surfaces.

The UI has four permanent layers:

1. **Navigation rail / mobile navigation** — stable module access.
2. **Command bar** — global search, business date, area scope, create actions, notifications, approvals, user context.
3. **Context header** — page identity, status, scope, page actions, saved views, compact analytics.
4. **Workspace** — the module-specific analytical and operational surface.

Optional layers:

- Quick View/context drawer
- Creation or task drawer
- Command palette
- Notification and approval centre
- Floating calculator/allocation panel
- Dialog for a single consequential decision

## 2. Reference viewport blueprint

At 1440 × 900:

- Navigation rail: 248px expanded / 72px collapsed.
- Command bar: 52px.
- Context header: 72–88px.
- Analytics band: 104–128px on module landing pages.
- Table/filter command bar: 44–52px.
- Primary table, chart, queue, timeline, or split workspace begins above the fold.
- Context drawer: 400–640px; New Loan drawer: 720px or up to 55vw.

No authenticated page uses a marketing hero, full-width introduction, decorative illustration, or permanently visible creation form.

## 3. Global shell

### 3.1 Navigation rail

- Brand mark and Sakthi Ledger name.
- Primary modules in stable order.
- Active module uses its identity colour and shared animated marker.
- Collapsed mode retains icons and accessible tooltips.
- Bottom region: help, connection state, language, and user context.

### 3.2 Command bar

Left to right:

1. Global command/search trigger
2. Business date
3. Area scope
4. New action menu
5. Approval inbox
6. Notifications
7. Connectivity/sync state when relevant
8. User/profile menu

The command bar remains stable between pages. Module-specific actions stay in the context header.

### 3.3 Command palette

Groups:

- Search results: customers, loans, receipts, payments, reports.
- Navigation destinations.
- Saved views.
- Quick actions: New Customer, New Loan, New Payment.
- Recent records.

Irreversible actions cannot execute directly from the palette.

### 3.4 Global create menu

- New Customer → onboarding wizard.
- New Loan → staged wide drawer.
- New Payment → focused drawer or allocation wizard.

Availability is role, permission, customer context, and business-state aware.

## 4. Module visual identity

| Module | Identity | Primary composition |
|---|---|---|
| Dashboard | Blue gradient | Command centre |
| Customers | Emerald | CRM workbench / Customer 360 |
| Loans | Royal orange | Pipeline / Loan 360 |
| Collections | Teal | Live control room / reconciliation |
| Reports | Purple | Report catalogue / analytical report |
| Audit | Red | Immutable event workbench |
| Settings | Slate | Configuration index / focused configuration |

Module identity affects the analytical band, active navigation, selected rows, chart highlight, and section marker. Component geometry and semantic status colour remain global.

## 5. Dashboard blueprint

### 5.1 First viewport

```text
┌ Financial pulse: Collection | Disbursement | Cash | Outstanding | Recovery | Approvals ┐
├──────────────────────── Collection pace ───────────────────────┬─ Pending work ──────────┤
│ Target, actual, hourly/route progress, exception markers       │ Approvals / alerts / EMI │
├──────────────── Collector or Area performance ────────────────┼─ Recent collections ────┤
│ Ranking, target, recovery, movement                            │ Rich compact queue        │
└────────────────────────────────────────────────────────────────┴──────────────────────────┘
```

### 5.2 Remaining workspace

- Monthly Trend
- Outstanding movement
- Revenue
- Cash Flow waterfall
- Profit and margin
- Risk distribution/migration
- Area and Collector Performance comparison
- Recent Loans
- Recent Activity
- Calendar
- Notifications
- Upcoming EMIs
- Quick Actions

Dashboard contains no embedded record-entry forms.

## 6. Customers blueprint

### 6.1 Customer workbench

First viewport:

- Emerald analytics band: total customers, active relationships, KYC pending, at-risk customers, follow-ups due, new this period.
- Saved views and filter command bar.
- Enterprise customer table with identity avatar, collector, verification, risk, exposure, loan health, next due, payment progress, quick actions.
- Quick View drawer.

Views:

- All customers
- Active relationships
- KYC pending/failed
- High/Critical risk
- Follow-ups due
- No active loan
- Recently added

### 6.2 Customer 360

Persistent identity header + exposure summary band + seven-tab navigation + optional context rail.

Tabs:

- Overview
- Timeline
- Loans
- Calendar
- Communications
- Documents
- More: Relationships, Profile & Capacity, Field Activity

First viewport contains identity, KYC, collector, exposure, loan health, risk meter, credit score, next due, current follow-up, recent communication, upcoming agenda, and location/visit summary.

### 6.3 Customer onboarding

Save-and-resume wizard:

1. Identity and duplicate check
2. Address and area
3. KYC
4. Household, employment, business, income
5. Family, guarantor, references
6. Consent and review

No table is shown beside the wizard. A compact summary rail shows validation, duplicate risk, and completion.

## 7. Loans blueprint

### 7.1 Origination pipeline

Analytics:

- Pipeline value
- Applications by stage
- KYC blockers
- Approval SLA
- Sanction rate
- Today’s disbursement

Pipeline stages:

`Draft → KYC → Credit assessment → Manager review → Approval → Documentation → Disbursement`

Users switch between board and enterprise-table views. Stage ageing, owner, risk, requested amount, recommended amount, policy deviations, and next action are visible.

### 7.2 Active loans workbench

Royal-orange summary band: principal outstanding, active accounts, due today, overdue, recovery %, maturity next 30 days.

Enterprise table:

- Customer and collector identity
- Scheme
- Principal/outstanding
- Payment progress
- Loan Health
- Due days/DPD
- Risk
- Status
- Quick actions and Quick View

### 7.3 New Loan drawer

Full-height staged drawer:

1. Customer and exposure
2. Scheme and terms
3. Affordability
4. Verification
5. Recommendation/deviations
6. Review and submit

Floating schedule preview and calculator are available without expanding the drawer.

### 7.4 Loan 360

Header: loan ID, customer, scheme, status, risk, collector, next due, primary action.

Tabs:

- Overview
- Schedule
- Payments
- Collections
- Documents
- Approvals
- Timeline

Summary: sanctioned, disbursed, paid, outstanding, next due, DPD, repayment %, loan health, expected completion.

Daily loans use the 100-segment collection strip. Monthly loans use instalment/amortization schedule.

## 8. Collections blueprint

### 8.1 Collection control room

Teal live band:

- Today’s demand
- Collected
- Recovery %
- Remaining
- Active collectors
- Unposted receipts
- Cash/digital split
- Variance

Main split:

- Left: area/collector hierarchy and ranking.
- Centre: demand/collection work queue.
- Right: exceptions, handover, upcoming route/commitments.

### 8.2 Collector route

- Route sequence and map/list switch.
- Customer identity, due, risk, promise, last contact, GPS/visit context.
- Record Payment, Call, WhatsApp, Promise, Visit actions.
- Offline queue and sync status.

### 8.3 New Payment

Known account: focused drawer.

1. Confirm customer/loan
2. Amount and mode
3. Allocation preview
4. Confirmation
5. Receipt

Unknown/multiple account: short allocation wizard.

### 8.4 Reconciliation and day close

Summary: opening cash, expected cash, collector handovers, digital collections, deposits, expenses, physical cash, variance.

Split layout:

- Transaction/receipt queue
- Selected evidence and resolution context

Day close remains blocked until required exceptions are resolved or approved.

## 9. Reports blueprint

### 9.1 Report catalogue

Purple analytical header + searchable report catalogue grouped by:

- Portfolio
- Collections
- Delinquency
- Finance
- Customer
- Compliance/Audit

Each entry identifies purpose, freshness, required parameters, permission, last generated, scheduled state, and output formats.

### 9.2 Report workspace

- Compact parameter strip or parameter drawer.
- Generate action.
- Designed preview using the immutable report snapshot.
- Summary, charts, tables, totals, filter/scope definition.
- PDF, Excel, CSV, Print, Share, Email actions.
- Export History context rail.

Raw JSON preview and fake file buttons are prohibited.

## 10. Audit blueprint

### 10.1 Audit workbench

Red identity marker without turning every event into an error.

- Event volume, sensitive access, failed operations, configuration changes, export/share activity.
- Actor/source/entity/date filters.
- Immutable timeline/table switch.
- Actor avatar, action badge, object identity, source/IP/device, timestamp, result, sensitivity.
- Quick View exposes before/after, reason, related event, correlation ID, and evidence.

### 10.2 Sensitive-access review

- Aadhaar reveal
- Export of sensitive data
- Permission changes
- Payment reversal
- Write-off/waiver
- Share/email access

No edit/delete action exists in the audit interface.

## 11. Settings blueprint

### 11.1 Settings index

Slate grouped navigation with health and dependency summary:

- Organization
- Areas and routes
- Users, roles, permissions
- Loan products and policies
- Collection and arrears rules
- Payment modes and receipt numbering
- Notifications and communication channels
- Reports, exports, email, share policy
- Security, privacy, data retention
- Backup and recovery
- Language, business date, financial year
- Integrations

### 11.2 Configuration page

- Configuration summary and effective state.
- Dependency/impact panel.
- Current and scheduled values.
- Change history.
- Edit opens drawer or staged workflow.
- Consequential changes require reason, preview, approval, effective date, and audit.

## 12. Global overlays

### 12.1 Approval centre

- Consolidated queue for loan, deviation, reversal, variance, write-off, sensitive access, configuration, and report-share approvals.
- Decision drawer shows financial impact, evidence, policy, prior decisions, and audit context.

### 12.2 Notification centre

- Critical, High, Normal, Informational.
- Group by Today, Earlier, Resolved.
- Resolution state matters more than read state.

### 12.3 Universal Quick View

Right-side drawer for customer, loan, payment, receipt, report artifact, approval, audit event, or configuration object.

## 13. State blueprint

Every screen designs:

- Initial loading
- Refreshing/stale
- Empty first use
- Empty filtered result
- Completed/no work
- Partial failure
- Full failure
- Offline/queued
- Permission restricted
- Success/confirmation
- Validation warning
- Conflict/concurrent update
- Reduced motion
- Tamil text expansion

## 14. Responsive blueprint

### Mobile

- Bottom navigation + full menu.
- Two-column metric matrix or snap strip.
- Domain-specific work-queue rows instead of squeezed tables.
- Drawers become full-screen sheets.
- Agenda replaces wide calendars.
- Field collection, payment, visit, communication, approvals, and due work prioritized.

### Tablet

- Collapsed rail or bottom navigation by posture.
- Master-detail split in landscape.
- Context panels become 40–45% sheets.
- Touch targets ≥44px.

### Laptop

- Primary operational workspace.
- Dense analytics and tables above fold.
- Frozen identity/actions and optional Quick View.

### Large desktop

- Additional comparison and context panels.
- No inflated cards, uncontrolled line lengths, or unused margins.

## 15. UI acceptance standard

A page is ready for high-fidelity design only when:

- Its primary decision is clear in five seconds.
- First viewport contains useful business information.
- Module identity is recognizable but not overpowering.
- No default form consumes analytical space.
- Every action has a service and state contract.
- All component use comes from the Component Library.
- Responsive layouts exist for mobile, tablet, laptop, and desktop.
- Financial data, risk, permissions, privacy, and audit consequences are explicit.
- Motion choreography and reduced-motion equivalent are annotated.
