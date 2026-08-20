# Sakthi Ledger Design System

**Product:** Sri Sakthi Thirumurugan Finance ERP  
**Version:** 1.0 — Design foundation  
**Status:** Required specification before implementation

Sakthi Ledger is the single visual and interaction language for the entire ERP. It is designed for high-frequency financial operations, long working sessions, bilingual English/Tamil content, and audit-sensitive decisions.

The desired character is **quiet authority**: precise, dense, trustworthy, and distinctly financial. The interface must never resemble a generic admin template, a marketing site, or a component-library demonstration.

## Quality benchmark charter

Sakthi Ledger must feel credible beside mature enterprise and fintech products such as Salesforce Financial Services Cloud, Zoho CRM Enterprise, Microsoft Dynamics 365 Finance, Oracle NetSuite, SAP Fiori, Stripe Dashboard, Linear, Ramp, Mercury, Brex, CRED, and Notion.

These products are references for product maturity and execution quality, not templates to reproduce. Sakthi Ledger must remain purpose-built for an Indian NBFC and for Sri Sakthi Thirumurugan Finance.

### Product north star

Sakthi Ledger should feel as though **Apple designed it, Stripe engineered it, Salesforce planned it, CRED branded it, Razorpay organized it, and Notion simplified it**.

This statement has concrete product meaning:

| Influence | Sakthi Ledger interpretation | Evidence required in every relevant screen |
|---|---|---|
| Apple designed it | Restraint, proportion, material quality, typography, spatial continuity, precise motion, and exceptional state finish | Nothing accidental; touch, keyboard, loading, transition, and responsive behaviour feel composed |
| Stripe engineered it | Exact financial language, reliable transactions, explainable states, developer-quality consistency, and trustworthy failure recovery | Amounts, allocations, receipts, exports, web/service states, and audit references are explicit and verifiable |
| Salesforce planned it | Deep CRM relationships, role-aware workflows, approvals, activity history, configuration, and operational scale | Records connect across customers, loans, payments, communications, documents, visits, risk, and approvals |
| CRED branded it | Confident identity, premium tonal contrast, distinctive moments, and memorable module character | Brand appears through controlled material, motion, module identity, and financial moments—not decorative noise |
| Razorpay organized it | Clear payment operations, settlement logic, reconciliation, statuses, reports, and action hierarchy | Collections, cash, receipts, reversals, exports, and exceptions have predictable operational structure |
| Notion simplified it | Calm hierarchy, progressive disclosure, flexible information architecture, and low-friction navigation | Complex data is available without overwhelming the first viewport; context opens when requested |

### Synthesis rules

- Apple-level polish must not create consumer-style empty space that reduces operational information.
- Stripe-level precision must extend beyond appearance into real transactions, files, errors, and auditability.
- Salesforce-level depth must not expose every field at once or turn the interface into a configuration maze.
- CRED-level branding must remain restrained enough for long finance-office sessions and sensitive customer work.
- Razorpay-level organization must use the language and workflows of lending, daily collections, cash handover, arrears, and reconciliation.
- Notion-level simplicity must come from hierarchy and disclosure, not by hiding required controls or financial consequences.
- When influences conflict, financial truth, accessibility, operational speed, privacy, and auditability take priority.

### North-star screen test

Before approval, a screen must satisfy all six questions:

1. **Apple:** Does every proportion, transition, interaction, and responsive state feel intentional?
2. **Stripe:** Are financial values, transaction states, errors, and outputs exact and trustworthy?
3. **Salesforce:** Does the screen fit a complete workflow, relationship model, permission model, and history?
4. **CRED:** Is there a distinctive premium identity without gimmicks or visual fatigue?
5. **Razorpay:** Are actions, statuses, payments, reconciliation, and reports logically organized?
6. **Notion:** Can a new user understand the hierarchy quickly while an expert can reach deeper detail efficiently?

A screen that fails any one question returns to design. Visual beauty cannot compensate for missing workflow depth; feature depth cannot compensate for poor clarity or execution.

### Qualities to achieve

- **Enterprise depth:** complex permissions, audit trails, approvals, exceptions, saved views, configurable policies, and record history must feel native rather than added later.
- **Fintech confidence:** amounts, balances, payment states, reconciliation, risk, and transaction consequences must be exceptionally clear.
- **Operational density:** high information volume must remain calm, legible, sortable, and fast to scan.
- **Interaction polish:** keyboard behaviour, focus, selection, loading, filtering, transitions, and recovery states must feel deliberate.
- **Progressive complexity:** common work is immediate; advanced evidence and controls are available without overwhelming the default view.
- **Record continuity:** customers, applications, loans, payments, approvals, and audit events remain connected through contextual navigation.
- **Professional restraint:** visual distinction comes from typography, alignment, material, data composition, and motion—not gradients, oversized cards, or novelty effects.
- **Local domain fluency:** Indian currency grouping, Aadhaar controls, area-led collections, daily lending, bilingual content, receipts, and cash handover are first-class patterns.

### Reference qualities by category

| Reference category | Quality Sakthi Ledger adopts |
|---|---|
| Salesforce / Zoho | Deep record relationships, configurable workflows, activity history, and saved operational views |
| Dynamics / NetSuite / SAP | Financial seriousness, role-aware workspaces, approvals, traceability, and high-density business data |
| Stripe / Ramp / Mercury / Brex | Precise money presentation, excellent transaction states, calm surfaces, and confident exception handling |
| Linear / Notion | Fast navigation, keyboard fluency, consistent spatial behaviour, and low-friction progressive disclosure |
| CRED | Selective brand confidence and premium finish without allowing decoration to obstruct operations |

### Explicit anti-benchmark

Sakthi Ledger must never resemble AdminLTE, Bootstrap Admin, Material Dashboard, a shadcn component demo, or a generic React dashboard.

The following are automatic design-review failures:

- A page assembled from interchangeable KPI cards, a chart, and a generic table without a defined operational decision.
- A stock sidebar/header/content template with no financial or workflow-specific behaviour.
- Default framework styling that remains visibly recognizable.
- Form controls presented as a component showcase instead of a coherent task flow.
- Identical card containers around every piece of content.
- Decorative gradients, glowing tiles, excessive pill shapes, or arbitrary icon backgrounds used to manufacture “premium” appearance.
- Dashboard widgets with placeholder trends, unexplained percentages, or charts that cannot be acted upon.
- Different component treatments introduced page by page.
- Excessive empty space used to imitate consumer fintech products at the cost of enterprise utility.
- Dense screens made cramped through weak hierarchy, inconsistent alignment, or undersized interaction targets.

### Premium-quality test

Before approval, every page must answer yes to all of the following:

1. Does the page make its primary business decision or task obvious within five seconds?
2. Does every metric identify its meaning, timeframe, comparison, and drill-down path?
3. Can an experienced operator complete the main task without unnecessary navigation?
4. Are money movement, risk, approval, and audit consequences explicit?
5. Does the page remain useful with realistic volumes and long Tamil content?
6. Are loading, empty, error, offline, permission, and success states intentionally designed?
7. Does the page reuse Sakthi Ledger patterns without looking like a component demo?
8. Would the page still feel trustworthy with all decorative colour removed?
9. Is the page recognizably part of the same ERP as every other page?
10. Does it feel purpose-built for this finance business rather than reskinned from an admin template?

## Viewport-first density contract

Sakthi Ledger is designed around the useful first viewport. Users must see the maximum decision-relevant information before scrolling, without reducing legibility or interaction safety.

### First-viewport requirement

At a reference desktop viewport of **1440 × 900**, every primary module page must show:

1. Persistent navigation and command bar
2. Compact page identity and primary actions
3. Operational metric or analytics band
4. Active scope, saved view, and essential filters
5. The beginning of the primary work queue, table, chart, or exception list

The first viewport must never be consumed by a large title, introductory copy, decorative illustration, oversized chart, empty hero area, or open form.

### Vertical budget

| Region | Target height | Maximum |
|---|---:|---:|
| Global command bar | 52px | 56px |
| Context header including breadcrumb/actions | 72px | 88px |
| Analytics/metric band | 104px | 128px |
| Tabs, saved views, and filter bar | 44px | 52px |
| Remaining first viewport | Primary operational content | Must begin above fold |

- Page headings use a single compact row wherever possible.
- Breadcrumb, title, status, record number, and actions share structured horizontal space.
- Explanatory text moves to tooltips, contextual help, or first-use states.
- Filters collapse into active tokens and an advanced-filter panel instead of occupying multiple rows.
- Empty right or left columns are reclaimed by the principal business surface.
- A page must not use stacked metric-card rows.

### Horizontal information use

- Use full-width analytical and table surfaces.
- Use split layouts when simultaneous comparison materially improves the task.
- Use a resizable context panel for record details, evidence, timeline, or quick actions.
- Collapse or dismiss the context panel when not needed; it must not reserve empty space.
- Freeze identity and critical financial columns while allowing secondary columns to scroll.
- Prefer compact summary bands over isolated KPI cards.
- Use small multiples or comparison matrices only when every panel answers part of one business question.

### Information priority

The first viewport follows this order:

1. Critical exceptions and blocking conditions
2. Today’s operational position
3. Portfolio or workflow analytics
4. Primary work queue
5. Supporting history and detail

Low-frequency settings, explanatory content, and secondary evidence move behind contextual disclosure.

### Analytics-first module pages

Every top-level business module opens with compact analytics appropriate to that module. Analytics must be interactive and must filter or navigate the primary work surface.

| Module | First-view analytics |
|---|---|
| Command centre | Exposure, demand, collection efficiency, arrears, cash, exceptions |
| Origination | Pipeline value, stage ageing, approval turnaround, KYC blockers, conversion |
| Portfolio | Principal outstanding, active accounts, scheme mix, yield, maturity, risk migration |
| Collections | Today’s demand, collected, efficiency, collector coverage, cash/digital split, unposted receipts |
| Delinquency | PAR buckets, amount at risk, roll rate, broken promises, recoveries, escalations |
| Finance | Opening cash, inflow, outflow, banked, expected close, variance, unreconciled items |
| Intelligence | Selected report KPIs, period comparison, anomalies, scheduled outputs |
| Control | Pending approvals, SLA breaches, audit exceptions, access events, backup health |

Analytics must not become a decorative dashboard above every page. Detail pages and focused workflows use compact record summaries instead.

## Dashboard command-centre specification

The Dashboard is the operating pulse of Sri Sakthi Thirumurugan Finance. It never starts with a form and never reserves default page space for customer, loan, payment, filter, or configuration entry.

The Dashboard must answer five questions immediately:

1. What happened financially today?
2. Are collections and disbursements on plan?
3. Which areas, collectors, or accounts require attention?
4. What approvals and upcoming repayments need action?
5. How are cash, revenue, profit, outstanding exposure, and risk changing?

### Mandatory dashboard content

The complete Dashboard contains:

- Today’s Collection
- Today’s Disbursement
- Cash Balance
- Collector Performance
- Area Performance
- Recovery Percentage
- Monthly Trend
- Outstanding
- Revenue
- Cash Flow
- Profit
- Risk
- Decision-oriented charts
- Recent Activity
- Quick Actions
- Recent Loans
- Recent Collections
- Notifications
- Calendar
- Upcoming EMIs
- Pending Approvals

These are organized by operational priority and must not be presented as an undifferentiated wall of identical cards.

### Dashboard composition

#### 1. Financial pulse strip

The first analytical band displays:

- Today’s Collection
- Today’s Disbursement
- Cash Balance
- Outstanding
- Recovery Percentage
- Pending Approvals count

Each metric includes amount/value, timeframe, comparison or target, trend direction, and drill-down behaviour. Financial values use Manrope SemiBold. The band uses the Dashboard blue gradient identity with accessible tonal metric partitions rather than separate white cards.

#### 2. Collection and field performance

The primary operational region contains:

- Collection pace versus today’s target
- Collector Performance ranking
- Area Performance comparison
- Recovery Percentage by area and scheme
- Critical collection exceptions

Selecting an area or collector filters all related Dashboard panels and exposes the filtered state in the context bar.

#### 3. Portfolio and business performance

An analytical grid contains:

- Monthly Trend
- Outstanding movement
- Revenue trend
- Cash Flow waterfall
- Profit trend and margin
- Risk distribution and migration

Charts must state the business question, use direct labels, and navigate to the relevant Portfolio, Finance, Collections, or Delinquency workbench.

#### 4. Work and activity rail

A dense action rail combines:

- Pending Approvals
- Notifications
- Upcoming EMIs
- Calendar events
- Recent Activity

Critical and due-today items appear first. Users may switch between agenda, approvals, and notifications without leaving the Dashboard.

#### 5. Recent operations

Two compact, rich work queues display:

- Recent Loans
- Recent Collections

They use the Enterprise Table contract in a reduced column set with identity, amount, status, risk/health, owner, time, and Quick View. “View all” navigates to the corresponding full workbench while preserving the current area/date scope.

#### 6. Quick Actions

Quick Actions are a compact command cluster, not a form container. Approved actions include:

- New Loan
- New Customer
- New Payment
- Record cash handover
- Open approval inbox
- Run day-close checks

Actions appear according to role, permission, business state, and current area scope.

### First-viewport Dashboard layout

At 1440 × 900, the first viewport must contain:

1. Compact Dashboard context header and business-date/area controls
2. Full financial pulse strip
3. Collection pace chart
4. Collector or Area Performance panel
5. Pending Approvals / critical work rail
6. Visible beginning of Recent Collections or Upcoming EMIs

Revenue, Cash Flow, Profit, Risk, monthly analysis, recent loans, calendar, and full activity remain immediately below in a tightly composed analytical grid. The first viewport must never contain introductory copy, a form, decorative hero artwork, or empty placeholder space.

### Dashboard interactions

- Global date, business date, scheme, and area scope update all applicable panels.
- Cross-filtering is visible and reversible.
- Metric click opens the responsible workbench with the same filter context.
- Chart selection updates related rankings and recent-operation queues.
- Quick View uses the standard drawer without resetting Dashboard state.
- Dashboard configuration allows users to reorder approved regions and collapse lower-priority panels, but cannot insert unapproved widget types.
- Refresh retains current data until replacement data arrives and shows a slim progress indicator.
- Real-time or near-real-time timestamps display the freshness of collection, cash, and approval data.

### Dashboard responsive behaviour

- **Mobile:** financial pulse, critical approvals, Today’s Collection, Upcoming EMIs, collector route/performance, recent collections, and Quick Actions receive priority.
- **Tablet:** financial pulse plus two-column collection/performance and work-rail regions.
- **Laptop:** financial pulse plus collection chart, performance comparison, approvals, and recent operations above the fold.
- **Large desktop:** adds simultaneous area and collector comparison; it does not enlarge cards or create unused margins.
- Mobile charts transform to ranked bars, compact trends, or agenda rows where necessary.
- All Dashboard actions remain available without hover.

### Dashboard state requirements

- Loading preserves the final analytical composition using structural skeletons.
- No-activity states distinguish “business day not opened”, “no transactions yet”, and “no matching filtered results”.
- Partial API failure preserves successful panels and identifies stale or unavailable regions.
- Offline state shows last-synced financial pulse and disables actions that cannot be safely queued.
- Permission-limited users see an intentionally recomposed Dashboard, not blank restricted panels.
- Success after a new loan, customer, payment, or approval refreshes relevant metrics and recent activity without resetting the page.

### Absolute form prohibition

- No input form appears in the Dashboard’s default, loading, empty, error, or responsive layouts.
- No “quick add” fields are embedded inside cards, charts, tables, or the activity rail.
- Search and analytical filters are controls, not record-entry forms.
- Record creation begins only after an explicit Quick Action or command.
- Closing a creation flow returns to the same Dashboard filters, position, and panel state.

## Reporting functional and export contract

Every visible report action must work end to end. Fake buttons, placeholder downloads, renamed file formats, browser-only mock exports, JSON previews, and mailto-based delivery are prohibited.

This is a functional acceptance contract as well as a design rule. A report is incomplete until Preview, PDF, Excel, CSV, Print, Share, and Email are implemented, validated, permission-controlled, and audited for that report type.

### Mandatory actions for every report

Every report provides:

1. **Generate**
2. **Preview**
3. **Download PDF**
4. **Download Excel**
5. **Download CSV**
6. **Print**
7. **Share**
8. **Email**

An action appears only when its real service is available. An unavailable integration must be shown as an explicit configuration state for authorized administrators, not as a clickable control that does nothing.

### One report snapshot

All actions operate from one immutable generated report snapshot containing:

- Report type and version
- Effective filters and saved-view parameters
- Area and permission scope
- Business date/time range
- Time zone and locale
- Requested/generated timestamps
- Requesting user
- Source-data watermark or snapshot identifier
- Row count and totals
- Masking and confidentiality policy

Preview, PDF, Excel, CSV, Print, Share, and Email must agree on the same rows, totals, filters, ordering, date scope, and generation timestamp. If data changes after generation, the user explicitly regenerates a new snapshot.

### Generate

- Generate validates required parameters and permissions before starting.
- Small reports may generate synchronously; large reports create a background export job.
- Progress states: Validating → Querying → Calculating → Formatting → Ready.
- Generation failure states the failed stage, confirms whether an artifact exists, and offers retry.
- Regeneration creates a new version; it never silently replaces a previously shared file.

### Preview

- Preview renders a designed report surface with title, scope, generated time, summaries, charts, tables, totals, notes, and pagination where relevant.
- Raw JSON or a generic `<pre>` block is prohibited.
- Preview supports page mode for printable reports and responsive continuous mode for exploration.
- Row counts, totals, and filters are visible.
- Large previews use server pagination or virtualization without changing the underlying snapshot.
- Preview identifies masked columns and omitted data caused by permission policy.

### Download PDF

- Produces a valid `.pdf` document with MIME type `application/pdf` and a valid PDF file signature.
- PDF is generated from the report snapshot, not from a screenshot of the web page.
- Supports proper pagination, repeating table headers, page numbers, report header/footer, generated timestamp, filter summary, and confidentiality marking.
- Embeds fonts required for Plus Jakarta Sans/Inter/Manrope and Tamil-script output.
- Currency, Indian grouping, negative signs, Tamil text, and long customer names must render correctly.
- Wide tables use approved landscape pages or continued column groups; content is never silently clipped.
- Charts render as print-quality vector or high-resolution assets with accessible labels.
- A PDF export must open successfully in standard PDF readers and contain all expected pages.

### Download Excel

- Produces a real Office Open XML `.xlsx` workbook with MIME type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
- HTML renamed as `.xls` or `.xlsx` is prohibited.
- Workbook opens without a format-warning dialog in Microsoft Excel and compatible readers.
- Uses typed cells for dates, currency, percentages, and numbers; amounts are not exported as formatted text.
- Includes a Summary sheet and one or more clearly named Data sheets where appropriate.
- Header row is frozen, filters are enabled, column widths are usable, and financial formats use Indian grouping.
- Formula cells are used only when required and must not expose unsafe external links or executable content.
- Sensitive values remain masked according to the report snapshot policy.
- Row limits are handled through additional sheets or a documented large-export strategy.

### Download CSV

- Produces an actual RFC-compatible `.csv` text file using UTF-8 with BOM for reliable Excel/Tamil compatibility.
- Uses correct quoting for commas, double quotes, newlines, and empty values.
- Contains a stable documented column order and one header row.
- Dates use an unambiguous export format; numeric cells remain machine-readable.
- CSV formula-injection values beginning with `=`, `+`, `-`, or `@` are safely neutralized when content is user-controlled.
- A multi-table report produces separate named CSV files inside a real `.zip` artifact or requires selection of a specific dataset; unrelated tables are never flattened ambiguously.

### Print

- Print opens a dedicated print representation of the generated report snapshot.
- Navigation, buttons, filters, drawers, notifications, and application chrome are excluded.
- Print output uses the same pagination, repeating headers, totals, and masking rules as PDF.
- The browser print dialog opens only after the print document is ready.
- Canceling print returns to the unchanged report workspace.
- Printing the entire application window is prohibited.

### Share

- Share first creates or selects an actual report artifact from the immutable snapshot.
- Internal share creates a permission-checked link with recipient scope, expiry, download policy, and optional password/OTP according to configuration.
- External/native share sends the selected real PDF, Excel, CSV/ZIP artifact when device support permits.
- A share link never grants broader area or Aadhaar access than the recipient is authorized to receive.
- Revocation, expiry, download count, and access history are visible.
- Copying a generic current-page URL is not considered report sharing.

### Email

- Email uses a configured server-side email delivery service; `mailto:` is not an implementation.
- Composer includes permitted recipients, subject, message, attachment format, expiry/link option, and confidentiality notice.
- The selected real artifact is attached or delivered through a secured download link.
- Large files use secure links instead of silently dropping attachments.
- Delivery states: Queued, Sending, Delivered, Bounced, Failed, or Partially delivered.
- Email action records sender, recipients, report snapshot, format, message metadata, delivery provider reference, and outcome.
- Retry never creates accidental duplicate delivery without warning.

### Export action design

- Generate is the primary action until a snapshot is ready.
- Once ready, Preview is the primary viewing state; download actions live in a clear Export menu or action group.
- PDF, Excel, and CSV use distinct labelled icons; icon-only download controls are prohibited.
- Print, Share, and Email remain separate labelled actions.
- Each action shows Queued/Generating/Ready/Failed state and never uses an indefinite spinner after a known failure.
- Successful file generation shows file name, format, size, generated time, and Download/Open action.
- Background jobs notify the user when ready and appear in Export History.
- Repeated clicks reuse a ready artifact or explicitly create a new snapshot; they do not spawn invisible duplicate jobs.

### Actual-file requirements

Every downloadable, shared, or emailed artifact must exist as a real generated file with:

- Unique artifact identifier
- Correct filename extension
- Correct MIME type
- Valid format signature/magic bytes
- Non-zero file size
- Cryptographic checksum
- Report snapshot relationship
- Creator and created timestamp
- Expiry/retention policy
- Permission and masking metadata
- Generation status and failure details

Files must be streamed or delivered from an authorized endpoint. Client-generated filename tricks are not accepted as report generation.

### Naming convention

`SSTF_<ReportName>_<Scope>_<FromDate>_<ToDate>_<GeneratedTimestamp>.<extension>`

Example: `SSTF_DailyCollections_ERD_2026-07-16_2026-07-16_20260716-184530.xlsx`

Filenames use safe characters, remain deterministic enough to identify the report, and never expose Aadhaar or sensitive customer data.

### Export history

Every report has an Export History context panel containing:

- Format
- File name and size
- Snapshot and report version
- Generated by and generated time
- Filters/scope
- Status
- Download count
- Share/email activity
- Expiry
- Regenerate, download, revoke, or retry actions as permitted

### Security and audit

- Generation, preview, download, print, share, email, recipient access, revocation, and failure are audited.
- Export permission is evaluated separately from report-view permission where policy requires it.
- Sensitive data remains masked unless the report type and user permission explicitly authorize export.
- Aadhaar reveal is never inferred from a prior UI reveal.
- Signed download URLs expire and cannot be guessed.
- Email addresses and share recipients are validated before delivery.
- Rate limits and large-export quotas prevent accidental system overload.

### Validation and acceptance tests

Every report/format combination must pass automated and visual checks:

1. Generate report with known fixture data.
2. Confirm Preview row count, totals, filters, and scope.
3. Generate PDF, Excel, and CSV artifacts.
4. Verify correct extension, MIME type, magic bytes, non-zero size, and checksum.
5. Parse each output with an independent format reader.
6. Compare exported row counts and totals with the report snapshot.
7. Verify Tamil, currency, dates, negative values, long names, and page boundaries.
8. Verify Print uses report-only layout.
9. Share artifact, enforce recipient permission/expiry, and test revocation.
10. Email artifact/link through the configured delivery service and verify delivery outcome.
11. Verify every action creates the correct audit event.
12. Verify failure, retry, timeout, cancellation, and expired-link states.

No report is marked complete when only its button exists. The report is complete only when all supported actions pass this acceptance suite.

### Current implementation replacement requirement

The existing report implementation is explicitly non-compliant and must be replaced during the reporting implementation phase because it currently:

- Renders raw JSON as Preview
- Saves HTML with an `.xls` extension instead of generating `.xlsx`
- Constructs a limited ASCII-only PDF that truncates report content
- Prints the surrounding application rather than a dedicated report document
- Shares only a client-created CSV
- Uses `mailto:` with a shortened text summary instead of email delivery

None of these behaviours may survive the redesign.

## Customer 360 CRM specification

Customer 360 is the authoritative relationship, lending, communication, field-service, and risk workspace for one customer. It is not a profile card with loan and document sections. It must allow a manager, collector, accountant, or owner to understand the complete relationship and take the next permitted action without searching across modules.

### Customer 360 purpose

The workspace must answer:

1. Who is this customer and how can they be verified or contacted?
2. What is the complete current and historical financial relationship?
3. What is due, overdue, promised, or scheduled next?
4. What risk, credit, family, guarantor, employment, business, and income context affects the relationship?
5. What communication, field visit, location, and collector history exists?
6. What documents, attachments, approvals, and audit-sensitive events support decisions?

### Mandatory CRM capability set

Customer 360 includes:

- Master Timeline
- Payment Calendar
- Collection Calendar
- Loan Timeline
- Document Center
- Call Logs
- SMS history
- WhatsApp history
- Follow-ups
- Reminders
- Risk Meter
- Credit Score
- Family Tree
- Guarantor relationships
- Employment profile
- Business profile
- Income and affordability
- Previous Loans
- Collector Notes
- Attachments
- GPS data
- Customer Map
- Visit History
- Communication Timeline

### Customer identity header

The fixed Customer 360 header contains:

- Customer photograph or verified initials avatar
- Full name in preferred language
- Customer ID
- Primary phone and area
- KYC status
- Relationship status
- Risk badge
- Current collector and route
- Last interaction and next scheduled action
- Permission-aware quick actions

Approved quick actions:

- New Loan
- New Payment
- Call
- Send SMS
- Open WhatsApp
- Add Follow-up
- Add Reminder
- Record Visit
- Upload Document
- More actions

Sensitive identity reveal, loan approval, payment reversal, write-off, and document deletion never execute directly from the quick-action row.

### First-viewport CRM cockpit

At 1440 × 900, Customer 360 must show without page scrolling:

1. Compact identity header and relationship status
2. Exposure and repayment summary band
3. Risk Meter and Credit Score
4. Next EMI / collection obligation
5. Current follow-up or promise-to-pay
6. Recent Communication Timeline entries
7. Upcoming calendar items
8. Customer Map or last-known visit/location summary when permission allows
9. Visible tab navigation for the complete CRM workspace

The first viewport must not begin with a large photograph, giant customer card, document thumbnails, or edit form.

### Workspace architecture

Customer 360 uses a persistent summary band, stable tab set, and optional right context rail.

Primary tabs remain within the seven-tab system limit:

1. Overview
2. Timeline
3. Loans
4. Calendar
5. Communications
6. Documents
7. More

“More” opens stable secondary destinations for Relationships, Profile & Capacity, and Field Activity. On mobile collector workflows, Field Activity may be promoted into the visible tab set while preserving the same destination and deep link. This is role-aware navigation, not a separate page design.

#### Overview

- Total and current exposure
- Principal outstanding
- Paid amount and payment percentage
- Next due and days-past-due
- Loan Health
- Risk Meter and Credit Score
- Active loans and recent payments
- Follow-ups, reminders, and promises
- Recent communication and field activity
- Family/guarantor summary
- Employment/business/income summary

Overview is a CRM cockpit. It does not duplicate the full content of every tab.

#### Timeline

The Master Timeline merges:

- Customer creation and KYC events
- Loan applications, sanctions, disbursements, and closures
- Payments, reversals, waivers, and receipts
- Calls, SMS, WhatsApp, follow-ups, and reminders
- Visits, GPS captures, route events, and collector notes
- Document uploads, verification, expiry, and access
- Risk or credit-score changes
- Approval and audit-sensitive actions

Events are filterable by financial, communication, field, document, risk, and system categories. Related reversals or corrections link to the original event.

#### Loans

- Active Loans
- Previous Loans
- Loan Timeline
- Repayment schedules
- Payment progress
- Arrears and recovery history
- Sanction and approval evidence
- Scheme, rate, tenure, collector, and area history

Selecting a loan opens Quick View in the context rail; the full Loan 360 remains one click away.

#### Calendar

The Calendar tab combines three switchable views:

- **Payment Calendar:** contractual instalments, paid dates, missed dates, adjustments, and future dues.
- **Collection Calendar:** planned visits, actual collections, collector assignments, promises, and missed collection activity.
- **Relationship Agenda:** calls, follow-ups, reminders, document expiries, visits, and approval commitments.

Month, week, and agenda presentations share the global Calendar component. Selecting an event opens contextual detail rather than navigating away unnecessarily.

#### Communications

The Communications workspace contains:

- Communication Timeline
- Call Logs
- SMS history
- WhatsApp history
- Follow-ups
- Reminders
- Contact preferences and consent
- Delivery/read status where available
- Outcome and next-action tracking

Each communication event includes channel, direction, actor, recipient, timestamp, outcome, related loan, and next step. Message content and recordings follow permission, retention, and masking policies.

#### Documents

The Document Center contains:

- KYC and identity documents
- Address and employment evidence
- Business and income evidence
- Loan agreements and sanction documents
- Receipts and statements
- Guarantor documents
- Visit photographs and Attachments
- Expired, rejected, replaced, and verified versions

Document list and preview use a split layout. Metadata includes type, owner, related record, verification status, expiry, version, upload source, timestamp, and audit history. Aadhaar and other sensitive records remain masked and permission-controlled.

#### Relationships

The Relationships workspace contains:

- Family Tree
- Household members
- Guarantor relationships
- Shared address, phone, business, and exposure signals
- Related customers
- Dependency and income contribution
- Relationship verification status

Family Tree uses an accessible node-link visualization with an equivalent structured list. Selecting a person opens a context panel. It must not imply legal or financial responsibility without an explicit relationship type and verification state.

#### Profile and capacity

The Profile workspace includes:

- Employment history and current Employment
- Business profile, ownership, sector, and operating history
- Income sources, frequency, reliability, and verified evidence
- Household expenses and disposable income
- Existing obligations
- Affordability calculations
- Address and residency history
- References and Guarantor details

Editing opens focused drawers or staged workflows. The tab itself remains an analytical record view.

#### Field activity

The Field Activity workspace contains:

- Customer Map
- Permissioned GPS captures
- Visit History
- Collector Notes
- Visit outcomes
- Photographs and Attachments
- Route and location context
- Next field action

GPS entries show collector/device source, accuracy, captured time, consent/policy context, and whether the location is customer-provided, verified, or visit-derived. The system never presents approximate coordinates as verified residence.

### Risk Meter

The Risk Meter is an explainable composite, not a decorative gauge.

- Scale: Low, Moderate, High, Critical, or Unscored.
- Shows current level, previous level, direction, last evaluation time, and model/policy version.
- Primary contributing factors are listed alongside the meter.
- Positive and adverse factors are separated.
- Users can open evidence and calculation details according to permission.
- Risk changes create Timeline events.
- Colour is accompanied by label, score range, and explanation.

### Credit Score

- Shows score, scale, source, retrieved date, expiry/freshness, and change from prior score.
- Internal score and external bureau score are never merged without clear labels.
- Unavailable or insufficient-data state is explicit.
- Access, refresh, and reveal actions are audited.
- Score alone never determines approval presentation; policy, affordability, and human decision remain visible.

### Follow-up and reminder model

- A Follow-up records business purpose, owner, due date/time, channel, related loan, priority, and expected outcome.
- A Reminder is a personal or assigned prompt linked to a customer event or follow-up.
- States: Scheduled, Due, Completed, Snoozed, Cancelled, Missed.
- Completion captures outcome and next action.
- Overdue follow-ups appear in Customer 360, Dashboard, Notifications, and the owner’s work queue.
- Creation uses a compact drawer; it never inserts a permanent form into Customer 360.

### Collector Notes

- Notes include author, role, timestamp, related loan/visit, visibility, and optional attachments.
- Notes are chronological and immutable after the permitted correction window.
- Corrections preserve original text and audit history.
- Sensitive, abusive, discriminatory, or unsupported risk language is prohibited through content policy and review controls.
- Notes never replace structured visit outcomes, promises, or payment records.

### Customer Map and GPS privacy

- Map and GPS access is permission-controlled and logged.
- Exact coordinates are shown only when operationally required.
- Location source, accuracy radius, and capture time are always visible.
- Users can distinguish registered address, business location, collection point, and last visit.
- Map markers use shared semantic and module tokens; they do not expose sensitive state through colour alone.
- Exports and screenshots follow data-protection policy.

### Context rail

The optional right rail displays the most relevant secondary context for the selected tab:

- Current loan Quick View
- Next due and payment allocation
- Follow-up/reminder detail
- Communication detail
- Document preview metadata
- Relationship node detail
- Visit or GPS detail

The rail is resizable on desktop, overlay/full-screen on smaller devices, and collapses completely when unused.

### Responsive Customer 360

- **Mobile:** identity, due status, Loan Health, risk, quick actions, agenda, communications, and field activity receive priority.
- **Tablet portrait:** summary band becomes a two-column matrix; context rail becomes a sheet.
- **Tablet landscape/laptop:** master-detail split supports timeline, documents, relationships, and visits.
- **Desktop:** persistent summary band, tab workspace, and optional context rail coexist.
- Tabs may horizontally scroll on mobile but retain stable order and deep links.
- Family Tree transforms to a structured relationship list on compact screens.
- Customer Map becomes a bounded map with an accompanying visit list; it never consumes the entire mobile page by default.
- Calendars default to agenda mode on compact screens.
- Communication and field actions use touch targets and never depend on hover.

### Customer 360 states

- No active loan still shows Previous Loans, relationship, communications, documents, risk, and servicing opportunities.
- Missing KYC, score, employment, income, guarantor, GPS, or consent data uses specific completion states and permitted next actions.
- Partial service failure preserves unaffected CRM data and labels stale regions.
- Offline mode shows last-synced relationship data and safe queued actions.
- Restricted users see masked or omitted sensitive data with an access explanation, not broken blank sections.
- Loading skeletons reproduce identity, summary band, tabs, timeline, and context rail.

### Customer 360 form prohibition

- No large form is embedded in Overview or any tab.
- Profile edits, communication logging, reminders, visits, document uploads, and relationship changes open focused drawers.
- New Loan opens the prescribed staged wide drawer.
- New Payment opens the prescribed payment drawer or allocation wizard.
- Complex KYC or capacity changes open a save-and-resume step workflow.
- Completing or cancelling a task returns to the same tab, selected record, timeline position, and context state.

### Scroll policy

- The application shell never scrolls with page content.
- Tables, timelines, and long panels scroll within clearly bounded work regions.
- Sticky headers and totals preserve decision context.
- Avoid nested scrolling unless a persistent inspector must coexist with a primary table.
- A workflow may scroll vertically, but the stage indicator and action footer remain visible.
- Important totals and primary actions never require scrolling to the bottom of an unbounded form.

### Density quality guardrails

- Maximum useful information does not mean smallest possible text.
- Default body text remains 16px; only dense tables, filters, and metadata use the approved 14px compact or 13px caption roles. Interactive targets remain at least 40px desktop.
- Use grouping, alignment, frozen columns, hierarchy, and progressive disclosure before reducing size.
- Every visible metric, column, label, or chart must support a current decision.
- If a region is empty, expand the adjacent useful region rather than preserving symmetry.
- Decorative whitespace is prohibited; functional breathing room follows the spacing scale.

## Responsive portability contract — release blocker

Sakthi Ledger must be fully usable on mobile phones, tablets, laptops, and large desktop displays. Responsive behaviour is designed with each page, not added after desktop implementation. A page cannot pass design review without approved layouts and states for all device classes.

### Supported device classes

| Class | Reference widths | Primary posture | Product priority |
|---|---:|---|---|
| Compact mobile | 360–479px | One-handed field use | Critical for collectors and approvals |
| Mobile | 480–767px | Field and quick office tasks | Critical |
| Tablet | 768–1023px | Touch operations and review | Critical |
| Laptop | 1024–1439px | Primary office workspace | Critical |
| Desktop | 1440–1919px | Dense multi-panel operations | Critical |
| Large desktop | 1920px+ | Command centre and comparison | Supported without uncontrolled stretching |

Both portrait and landscape orientations must be tested for mobile and tablet. No supported layout may require browser zoom to complete a core task.

### Adaptive shell

#### Mobile

- Top bar: 48px with module identity, global search, notifications, and profile.
- Bottom navigation: up to five role-priority destinations; “More” opens the complete domain menu.
- Global create button opens New customer, New loan, and New payment according to permission.
- Context header uses a compact title/status row and horizontally scrollable tabs where necessary.
- Drawers and inspectors become full-screen sheets with clear back navigation.
- Command palette becomes full-screen search/command mode.

#### Tablet

- Collapsible 64px navigation rail in landscape; bottom navigation or overlay menu in portrait.
- Master-detail split layout is allowed in landscape.
- Context panels use 40–45% width and may collapse.
- Touch-sized table controls and sticky primary actions are mandatory.

#### Laptop and desktop

- Expanded or collapsed navigation rail based on available width and user preference.
- Full metric/analytics band and primary work surface appear in the first viewport.
- Resizable inspectors and frozen table columns are available.
- Large desktop adds useful comparison/context panels; it does not inflate spacing or card sizes.

### Responsive information priority

The same business meaning is preserved at every size, but presentation adapts:

1. Critical status and monetary consequence
2. Primary identity and next action
3. Today’s or current-period analytics
4. Primary work queue
5. Supporting detail, evidence, and history

Mobile does not simply hide important desktop columns. Secondary attributes move into expandable row detail, a context sheet, or a record view. Permissions and audit information remain accessible.

### Responsive analytics

- Desktop metric strips may show 5–7 metrics in one row.
- Tablet shows 3–4 with horizontal paging only when comparisons remain understandable.
- Mobile uses a compact two-column metric matrix or one horizontally scrollable snap row with a visible position cue.
- The primary metric and critical exception count are never pushed below an introductory block.
- Charts change representation when necessary: grouped bars may become ranked bars; wide timelines may become agenda lists; heatmaps may become summarized bands.
- Chart tooltips become tap details and must never require hover.
- Every chart retains a table or accessible summary on mobile.

### Responsive tables and work queues

- Laptop and desktop use full operational tables with user-controlled columns and density.
- Tablet freezes the primary identity and exposes secondary columns through horizontal scroll or row detail.
- Mobile converts broad tables to compact work-queue rows designed per domain; it must not render a squeezed desktop table.
- Mobile rows show identity, critical amount, status, due context, and one primary action.
- Bulk selection is supported on tablet/desktop and only on mobile workflows where field operators genuinely need it.
- Filters open in a full-height sheet on mobile and show active-filter tokens above results.
- Sort, filter, selection, and pagination state survive rotation and task completion.

### Responsive forms and task surfaces

- Forms use one column on mobile, two or more only when field relationships and width permit.
- Wizard stage labels collapse to current stage plus progress on mobile; the full stage list opens on demand.
- Primary action footer remains sticky above system navigation and safe-area insets.
- Numeric keyboard is requested for amount and phone inputs.
- Camera capture and file upload are first-class KYC actions on mobile.
- Floating calculators and previews become bottom sheets on mobile.
- Payment confirmation never places the final amount or account identity below the fold.
- Draft saving protects workflows across connectivity loss, orientation change, and app/background transitions.

### Touch, pointer, and keyboard parity

- Minimum target: 44×44px touch; visually compact controls may use expanded hit areas.
- Hover is enhancement only; every hover interaction has tap and keyboard equivalents.
- Swipe gestures may accelerate navigation but never provide the only route to an action.
- Desktop workflows remain fully keyboard navigable.
- Tablet keyboard and trackpad use must be supported without switching UI modes.

### Device-specific module behaviour

| Module | Mobile priority | Tablet/laptop priority |
|---|---|---|
| Dashboard | Critical exceptions, today’s numbers, approvals | Comparative analytics and area performance |
| Customers | Search, identity, KYC capture, contact, next action | Customer 360 and linked records |
| Loans | Exposure, due state, schedule, application progress | Assessment, schedule comparison, approval evidence |
| Collections | Route, payment, receipt, promise, handover | Collector control room and reconciliation |
| Reports | Saved report summary and export status | Full parameters, charts, tables, comparisons |
| Audit | Recent sensitive events and filters | Full timeline, actor/source analysis, evidence |
| Settings | Essential profile/device preferences | Full configuration and dependency management |

### Performance and resilience budgets

- Mobile design assumes variable field connectivity and mid-range Android hardware.
- The initial authenticated shell and current-work summary must remain lightweight.
- Large tables use server pagination or virtualization; the interface never renders entire datasets unnecessarily.
- Charts load after essential metrics and primary work queues.
- Images and documents use responsive previews and explicit full-resolution access.
- Offline and queued states are visible, durable, and conflict-aware.
- Layout shifts after data load are prohibited; skeletons reserve final component dimensions.

### Responsive QA gate

Every page must be verified at minimum at 360×800, 390×844, 768×1024, 1024×768, 1366×768, 1440×900, and 1920×1080.

Approval requires:

- No clipped Tamil or English labels
- No hidden monetary consequence or critical status
- No inaccessible action caused by viewport height
- No accidental nested horizontal scrolling
- No dependence on hover
- No overlapping keyboard, bottom navigation, toast, or sticky action footer
- Correct safe-area handling
- Stable state after orientation change
- Usable loading, empty, error, offline, success, and permission states
- First-viewport information priority preserved for the device class

---

## 1. Non-negotiable principles

1. **One product, one language.** All pages use the same shell, grid, type scale, spacing, controls, data presentation, states, and motion.
2. **Operations before decoration.** Every visible element must support comprehension, decision-making, navigation, or action.
3. **Dense, not cramped.** Use alignment, grouping, separators, and typography to carry information. Do not solve density with oversized cards or empty whitespace.
4. **Financial clarity.** Monetary values use Indian grouping, tabular numerals, consistent signs, right alignment, and explicit meaning.
5. **Risk is never colour-only.** Every status combines text with colour and, where valuable, an icon.
6. **Actions follow consequence.** Routine actions are easy; financial, identity, and irreversible actions require explicit review.
7. **Progressive disclosure.** Show essential operational information first and reveal evidence, history, or advanced controls when requested.
8. **Bilingual by construction.** Components must accommodate Tamil labels without clipping, abbreviation, or layout breakage.
9. **No forms beside tables.** Create and edit flows use a focused page, dialog, or drawer according to the rules below.
10. **No dead ends.** Empty, error, permission, and success states always explain what happened and what can happen next.

---

## 2. Brand signature

### 2.1 Name usage

- Full name in sign-in, official reports, receipts, and legal documents: **Sri Sakthi Thirumurugan Finance**.
- Product name in the application shell and internal references: **Sakthi Ledger**.
- Never reduce the identity to an unexplained acronym in customer-facing documents.

### 2.2 Visual character

- Midnight navy provides institutional authority.
- Deep teal identifies the primary operational path.
- Antique gold is a restrained brand accent, never a generic button colour.
- Warm ledger neutrals create a calmer workspace than cold blue-grey dashboards.
- Semantic colours are reserved for state and risk.

### 2.3 Logo safe area

- Minimum clear space: the height of the logo mark on every side.
- Minimum digital height: 28px shell, 40px authentication, 56px formal documents.
- Never place the logo inside a coloured gradient, pill, generic card, or decorative container.

### 2.4 Module identity system

Every primary module has a recognizable identity, but no module creates a separate component library. Module colour influences the context header, active navigation marker, analytical emphasis, chart highlight, selected row tint, and section marker. It does not change typography, spacing, component anatomy, interaction behaviour, semantic status colours, or financial conventions.

| Module | Identity | Primary | Deep | Soft surface | Header treatment |
|---|---|---:|---:|---:|---|
| Dashboard | Blue gradient | `#2F6FED` | `#173E8F` | `#E8F0FF` | Midnight-to-blue analytical gradient |
| Customers | Emerald | `#138A61` | `#0B5D42` | `#E5F5EE` | Emerald identity line and soft customer summary field |
| Loans | Royal orange | `#D96518` | `#9D3F0C` | `#FFF0E5` | Royal-orange sanction/exposure emphasis |
| Collections | Teal | `#07827D` | `#075B58` | `#E3F5F3` | Teal live-operations marker |
| Reports | Purple | `#7453C6` | `#4B328D` | `#F0EBFC` | Purple analysis and export context |
| Audit | Red | `#B6433C` | `#7D2925` | `#FBE9E7` | Restrained red traceability marker |
| Settings | Slate | `#5B6B7A` | `#344351` | `#EBEFF2` | Slate configuration context |

Dashboard gradient token: `linear-gradient(118deg, #142E57 0%, #1F55A5 52%, #2F6FED 100%)`. It is reserved for the dashboard analytical band and must not be repeated as a generic card background.

#### Module identity application

- The module accent appears in no more than 15% of a normal workspace.
- Module identity is strongest in the compact context/analytics band and becomes quieter in dense work regions.
- Navigation uses the active module colour as a 3px indicator plus a soft selected surface.
- Charts use the module accent for the selected or primary series; supporting series use shared neutral/categorical tokens.
- Tabs use the module colour for the active indicator.
- Selected table rows use the module soft surface with a stronger identity edge.
- Module icons remain part of the shared outline family; colour supplies identity without changing drawing style.
- Focus rings remain global teal for accessibility and predictable keyboard navigation.
- Success, warning, critical, information, and lifecycle states always use semantic tokens. A red audit module does not turn neutral audit events into errors.

#### Module surface families

To avoid repetitive white-card layouts, each module combines approved surfaces according to its purpose:

- **Dashboard:** gradient analytical band, dark comparison panels, neutral metric strips, and full-width intelligence surfaces.
- **Customers:** warm record canvas, emerald identity bands, connected profile sections, and a persistent activity/context rail.
- **Loans:** exposure summary band, royal-orange stage markers, repayment schedule surfaces, and policy/evidence panels.
- **Collections:** teal live-status band, route/collector split workspace, compact cash tiles, and exception queues.
- **Reports:** purple parameter strip, edge-to-edge visualization panels, comparison matrices, and export history rail.
- **Audit:** restrained red trace markers, chronological surfaces, actor/source filters, and immutable event detail panels.
- **Settings:** slate navigation index, grouped configuration sections, dependency summaries, and change-impact panels.

Cards are only one available container. Pages should also use summary bands, bordered sections, tonal fields, split workspaces, inline metrics, tables, timelines, and edge-to-edge analytical panels. A grid of identical white cards is prohibited.

#### Consistency boundary

Module identity may change colour emphasis and composition appropriate to the work. It may not change:

- Type scale or font family
- Spacing scale or density modes
- Button hierarchy or control dimensions
- Table anatomy and financial alignment
- Form structure and validation
- Dialog, drawer, toast, or notification behaviour
- Status meanings
- Border-radius system
- Accessibility and responsive rules

This creates recognizable modules without making the ERP feel like unrelated websites.

---

## 3. Foundations

### 3.1 Colour system

All tokens are semantic. Components consume semantic tokens, never arbitrary hex values.

#### Brand and action

| Token | Light | Dark | Use |
|---|---:|---:|---|
| `brand-midnight-950` | `#101D2D` | `#101D2D` | Navigation, formal headers |
| `brand-midnight-900` | `#17283B` | `#17283B` | Elevated navigation |
| `brand-teal-700` | `#086C68` | `#36B5AC` | Primary action, active focus |
| `brand-teal-800` | `#075B58` | `#69CEC6` | Primary hover / dark text accent |
| `brand-gold-500` | `#B88A35` | `#D5AD62` | Brand detail, selected premium metric |
| `brand-gold-100` | `#F4E9D3` | `#3B3122` | Restrained gold highlight |

#### Neutral surfaces

| Token | Light | Dark | Use |
|---|---:|---:|---|
| `canvas` | `#F3F1EC` | `#0D141C` | Application background |
| `surface-1` | `#FBFAF7` | `#131D27` | Primary workspace |
| `surface-2` | `#F7F5F0` | `#192530` | Grouped content |
| `surface-3` | `#EEEAE2` | `#22313E` | Hover and selected neutral |
| `surface-inverse` | `#17283B` | `#E7EDF1` | Inverse surfaces |
| `border-subtle` | `#DEDAD1` | `#2A3A47` | Component boundaries |
| `border-strong` | `#C7C1B6` | `#405260` | Strong separation |
| `text-primary` | `#17222E` | `#F1F4F5` | Main content |
| `text-secondary` | `#52606C` | `#AEBBC4` | Supporting content |
| `text-tertiary` | `#7C858C` | `#82919B` | Metadata and placeholders |
| `text-disabled` | `#A7A7A1` | `#65727B` | Disabled content |

#### Semantic

| Meaning | Strong | Soft background | Border | Typical use |
|---|---:|---:|---:|---|
| Success | `#16734B` | `#E4F3EB` | `#9ECDB3` | Paid, reconciled, approved |
| Warning | `#A35C00` | `#FFF0D5` | `#E6BD75` | Due soon, variance, review |
| Critical | `#B83A32` | `#FBE7E4` | `#E3A19B` | Overdue, failed, blocked |
| Information | `#2B629B` | `#E7F0FA` | `#A7C4E1` | Guidance, processing |
| Neutral | `#596671` | `#ECEFF1` | `#C8CFD4` | Draft, inactive, unknown |

#### Financial conventions

- Positive movement uses success only when it is operationally beneficial.
- Negative movement uses critical only when it is adverse; accounting credits/debits must not be blindly colour-coded.
- Zero and unavailable values use neutral text.
- Arrears ageing uses a fixed ordered scale: Current → 1–30 → 31–60 → 61–90 → 91–120 → 120+.
- Charts, badges, tables, and filters must use the same semantic mapping.
- Text contrast must meet WCAG AA; interactive focus and critical state boundaries must remain distinguishable at 200% zoom.

### 3.2 Typography

Typography is a primary part of the product identity. Default browser or operating-system fonts are not an acceptable product state.

#### Font roles

| Family | Role | Approved usage |
|---|---|---|
| **Plus Jakarta Sans** | Brand and hierarchy | Display heading, page title, section title, card/panel title, major navigation identity |
| **Inter** | Interface and reading | Body copy, controls, labels, tables, filters, tabs, validation, notifications, long-form content |
| **Manrope** | Financial and numerical emphasis | Currency, balances, exposure, repayment values, KPIs, percentages, ratios, totals, chart values |
| **Noto Sans Tamil** | Tamil script companion | Tamil translations, paired by role and weight with the Latin typography system |

- Plus Jakarta Sans, Inter, Manrope, and Noto Sans Tamil must be explicitly loaded and bundled or served as controlled product assets.
- No component may declare `Arial`, `Helvetica`, `Segoe UI`, `Roboto`, `system-ui`, or a browser-default font as its intended face.
- Font loading is part of the application shell and must be preloaded to avoid a visible default-font interface.
- Tamil text uses Noto Sans Tamil because the three Latin families do not provide complete Tamil-script coverage; its size, weight, and line-height must visually match the assigned role.

#### Authoritative type scale

| Role | Family | Size / line | Weight | Use |
|---|---|---:|---:|---|
| Heading | Plus Jakarta Sans | 56 / 64px | 700 | Authentication, executive statement, or formal high-emphasis moment only |
| Page title | Plus Jakarta Sans | 42 / 50px | 700 | One primary title per page |
| Section | Plus Jakarta Sans | 28 / 36px | 650 | Major workspace region |
| Card | Plus Jakarta Sans | 20 / 28px | 650 | Card, panel, drawer, dialog, or table title |
| Body | Inter | 16 / 24px | 400 | Default interface and readable content |
| Body strong | Inter | 16 / 24px | 600 | Important labels, actions, and explanatory emphasis |
| Compact UI | Inter | 14 / 20px | 500 | Dense tables, filters, navigation metadata, and control labels |
| Caption | Inter | 13 / 18px | 500 | Helper text, timestamps, annotations, and secondary metadata |
| Micro label | Inter | 12 / 16px | 650 | Short codes, overlines, and chart annotations only |
| Financial standard | Manrope | 16 / 22px | 600 | Money and numerical values inside tables, forms, and detail views |
| Financial metric | Manrope | 24 / 30px | 600 | Analytics-band values and significant totals |
| Financial hero | Manrope | 36 / 42px | 650 | One dominant balance or amount in a focused financial workspace |

#### Responsive type scale

The authoritative sizes apply at desktop widths. Hierarchy remains intact on smaller viewports without clipping or consuming the operational viewport.

| Role | Desktop ≥1440 | Laptop 1024–1439 | Tablet 768–1023 | Mobile <768 |
|---|---:|---:|---:|---:|
| Heading | 56px | 48px | 42px | 36px |
| Page title | 42px | 36px | 32px | 28px |
| Section | 28px | 26px | 24px | 22px |
| Card | 20px | 20px | 18px | 18px |
| Body | 16px | 16px | 16px | 16px |
| Caption | 13px | 13px | 13px | 13px |

#### Financial-number treatment

- All financial values use **Manrope SemiBold** at weight 600 or 650.
- Use `font-variant-numeric: tabular-nums lining-nums` for currency, balances, counts, dates, percentages, loan numbers, and receipt numbers.
- Financial values must be at least as prominent as their surrounding body text and may never use tertiary text colour.
- Monetary values are right aligned in tables and vertically aligned by baseline in summary bands.
- Labels remain visually subordinate to values through size, weight, and colour—not through excessive spacing.
- Primary amounts use `text-primary`; adverse, positive, warning, or overdue colour is added only when the meaning is semantically valid.
- Totals use a strong top rule or tonal summary field plus SemiBold numbers. Do not rely on bold weight alone.
- Concealed amounts preserve layout width to prevent columns and totals from shifting.
- Charts use Manrope SemiBold for direct values, axes with financial units, targets, and tooltips.
- Use Indian grouping: `₹1,24,500`, `₹25L`, `₹1.2Cr`, `−₹8,250`, and `12.6%`.
- Do not use a space after the rupee symbol or western grouping such as `₹124,500`.
- Zero is displayed as `₹0`; an em dash means unavailable, not zero.

#### Hierarchy and density rules

- Sentence case everywhere. Never use title case for every word.
- Uppercase is limited to short codes and micro labels; Tamil is never forced uppercase.
- Heading 56px is never used as a routine page title or repeated inside authenticated workspaces.
- Page titles occupy one line at desktop whenever possible and never exceed two lines.
- A 42px page title shares its row with record status and page actions; it does not create a separate hero region.
- Section titles are used only for true page regions. Subsections use card-title or body-strong styles.
- Card titles remain concise; supporting counts and metadata use Inter Caption.
- Typography creates hierarchy before boxes, shadows, or extra whitespace are introduced.

### 3.3 Spacing

Base unit: **4px**. Primary rhythm: **8px**.

| Token | Value | Typical use |
|---|---:|---|
| `space-0` | 0 | Flush relationships |
| `space-1` | 4px | Icon-label refinement |
| `space-2` | 8px | Inline gaps, compact stacks |
| `space-3` | 12px | Control groups |
| `space-4` | 16px | Standard component padding |
| `space-5` | 20px | Dense panel padding |
| `space-6` | 24px | Page and section gap |
| `space-8` | 32px | Major separation |
| `space-10` | 40px | Focused workflow section |
| `space-12` | 48px | Rare, top-level separation |

Layout rules:

- Desktop page inset: 24px; compact desktop: 20px; tablet: 16px; mobile: 12px.
- Standard component gap: 12px.
- Standard section gap: 24px.
- Do not stack multiple empty padding layers.
- Cards within cards are prohibited unless the inner object is an interactive record or a materially separate financial summary.

### 3.4 Grid and responsive layout

- Desktop: 12 columns, 20px gutters, fluid width.
- Tablet: 8 columns, 16px gutters.
- Mobile/collector: 4 columns, 12px gutters.
- Application canvas uses the full available width; there is no arbitrary marketing-site max-width.
- Readable narrative content may cap at 760px, but operational tables and workbenches do not.
- Breakpoints: 480, 768, 1024, 1280, 1536.
- Navigation rail: 248px expanded, 72px collapsed.
- Context rail or inspector: 360–440px, resizable where records are data-heavy.

### 3.5 Border radius

| Token | Value | Use |
|---|---:|---|
| `radius-0` | 0 | Tables, formal document edges |
| `radius-1` | 4px | Tags, compact controls |
| `radius-2` | 6px | Inputs, buttons, badges |
| `radius-3` | 8px | Cards, menus, popovers |
| `radius-4` | 10px | Dialogs and drawers |
| `radius-pill` | 999px | Status dots, avatars, true pills only |

Do not mix radii within a component family. Large 16–24px “friendly SaaS” rounding is prohibited.

### 3.6 Borders, elevation, and focus

- Default border: 1px `border-subtle`.
- Strong boundary: 1px `border-strong`.
- Selected control: teal border plus 2px soft focus ring.
- Cards rely on borders and surface change; they do not float by default.
- Elevation 1: menus and sticky headers.
- Elevation 2: drawers and dialogs.
- Elevation 3: urgent confirmations only.
- Keyboard focus: 2px teal ring with 2px offset; it is never removed.

### 3.7 Iconography

- Use one outline icon family throughout the product.
- Standard stroke: 1.75px.
- Sizes: 16px compact, 18px controls, 20px navigation, 24px state illustrations.
- Icons do not replace ambiguous labels for primary business actions.
- Use established meanings consistently: search, filter, download, print, approve, reject, warning, lock, history, receipt.
- Rupee, payment, loan, customer, and compliance icons must not change between modules.
- Do not use multicolour icons, emojis, filled icon mixtures, or decorative icon circles.

### 3.8 Motion and animation

Motion is a required part of every Sakthi Ledger screen. It communicates hierarchy, state, continuity, completion, urgency, and spatial relationship while preserving the seriousness of financial operations.

**Framer Motion is the mandatory motion engine for the React interface.** Page transitions, shared layout changes, presence, drawers, notifications, charts, numbers, timelines, progress, tables, cards, KPIs, skeletons, and receipts must use the same motion tokens and orchestration rules. Isolated CSS animation is allowed only for simple low-level states that do not need orchestration, such as a native focus colour transition.

Motion must never delay an operator, hide an exact financial result, create a false sense of processing, or make a payment appear posted before server confirmation.

#### Motion tokens

| Token | Duration | Use |
|---|---:|---|
| `motion-instant` | 80ms | Press and focus feedback |
| `motion-fast` | 140ms | Hover, tooltip, menu |
| `motion-standard` | 200ms | Expand, tab, popover |
| `motion-enter` | 240ms | Page region, dialog, drawer, notification entry |
| `motion-exit` | 180ms | Dialog or drawer exit |
| `motion-data` | 360ms | Chart, KPI, progress, and table-data update |
| `motion-emphasis` | 480ms | Confirmed receipt, completed workflow, important state change |
| `motion-skeleton` | 1200ms | Skeleton luminance cycle |

#### Easing and spring profiles

- Product ease: `cubic-bezier(0.2, 0, 0, 1)`.
- Exit ease: `cubic-bezier(0.4, 0, 1, 1)`.
- Data ease: `cubic-bezier(0.22, 1, 0.36, 1)`.
- Drawer spring: stiffness 420, damping 38, mass 0.85.
- Notification spring: stiffness 500, damping 42, mass 0.8.
- No elastic, rubber-band, overshoot-heavy, or playful bounce animation in financial workflows.

#### Screen choreography

Every screen contains at least three coordinated motion layers:

1. **Shell continuity:** navigation and command bar remain spatially stable while module identity transitions.
2. **Page entrance:** context header fades and moves up no more than 6px over 200ms.
3. **Content reveal:** analytics, work queue, and context rail enter in priority order with a maximum 30ms stagger and a maximum total choreography of 360ms.

- Route transitions crossfade the workspace without sliding the entire application horizontally.
- Module accent and analytical-band colour transition over 240ms.
- Returning to a prior screen restores scroll and selection without replaying the full entrance sequence.
- Background data refresh never replays page-entry animation.

#### Animated numbers

- KPIs and financial totals animate from their previous confirmed value to the new confirmed value over 360–600ms.
- Initial analytical load may animate from zero only when zero cannot be mistaken for a real reported state.
- Currency symbols, negative signs, decimal precision, Indian grouping, and units remain stable while digits change.
- Large changes use a restrained digit roll or value interpolation; routine refresh uses a short crossfade/interpolation.
- The exact final value is present in accessible text throughout; assistive technology announces only the final confirmed value.
- Payment, approval, and reconciliation values do not animate until the server confirms success.
- User-entered amount fields never animate while typing.

#### Animated charts

- Lines draw from left to right; bars grow from the zero baseline; areas fade and reveal along the time axis.
- Initial chart entrance: 360–480ms. Filter update: 280–360ms.
- Axis, labels, targets, and grid remain stable while data marks transition.
- Cross-filtering emphasizes selected marks and dims supporting marks without removing context.
- Tooltips fade/scale from 98% over 140ms and track pointer/touch changes without lag.
- Charts never animate through meaningless intermediate categories or reorder rankings so slowly that comparison becomes difficult.
- Reduced-motion mode shows the final chart immediately with a short opacity change.

#### Animated sidebar and navigation

- Expanded/collapsed width transitions over 220ms using shared layout animation.
- Labels fade after expansion begins and before collapse completes, preventing clipped text.
- Active module indicator moves using a shared layout marker.
- Navigation groups expand/collapse over 180–200ms with height and opacity choreography.
- Mobile bottom navigation does not move; active identity and selection states animate within fixed positions.
- Permission changes do not make navigation items fly across the screen; affected items fade and the remaining structure settles quickly.

#### Animated search and command palette

- Global search expands from its command-bar anchor over 180ms.
- Command palette enters with backdrop fade, 6px rise, and 98%→100% scale over 200ms.
- Result groups reveal with a maximum 20ms stagger.
- Keyboard selection uses a shared highlight that moves between results.
- Search-result updates crossfade while the input and group headings remain stable.
- No-results, loading, and recent-search states transition in the same container to prevent layout jumps.

#### Animated drawers, dialogs, and floating panels

- Drawers enter from their attached edge using the drawer spring and exit over 180ms.
- The backdrop fades to its prescribed opacity over 180ms.
- Drawer header and sticky footer remain stable while step content crossfades and moves no more than 8px.
- New Loan stage transitions show forward/back direction without sliding the entire 720px drawer across the screen.
- Dialogs fade with a maximum 8px rise and 98%→100% scale.
- Floating panels originate visually from their trigger when possible and never cover the confirmed amount or primary action.
- Focus moves only after the entry animation has established the destination and returns immediately on close.

#### Animated notifications and toasts

- Notifications enter from the top-right on desktop or below the top bar on mobile using the notification spring.
- New critical notifications receive one restrained border/indicator pulse; continuous pulsing is prohibited.
- Read, resolved, snoozed, and removed items collapse smoothly while preserving nearby focus.
- Notification-centre groups use shared layout animation when items change category.
- Toasts enter with 12px translation and opacity, remain stable for reading, and exit in 180ms.
- Queued toasts reposition with shared layout animation rather than jumping.

#### Animated timeline

- Initial timeline events reveal in chronological groups with a maximum 24ms stagger.
- Newly created events enter at the correct position and briefly emphasize their event marker.
- Expanding an event animates height and opacity without moving the timeline axis.
- Date-group navigation scrolls smoothly only when reduced motion is not requested.
- Communication, payment, visit, risk, and document event markers transition using their stable semantic styles.
- Long timelines virtualize; animation applies only to visible events.

#### Animated progress

- Progress bars animate from the previous confirmed percentage to the current value over 360ms.
- The numerical label changes in synchronization with the bar.
- Segmented 100-day loan strips animate only changed segments, not all 100 segments on every refresh.
- Workflow steppers move the active indicator between stages and reveal completion state over 200ms.
- Indeterminate progress is used only when progress cannot be measured and never for a completed server transaction.

#### Animated tables

- Table body fades in after the structural skeleton resolves; headers and command bar remain fixed.
- Newly inserted rows fade and receive a 480ms soft module-tint highlight.
- Updated financial cells crossfade/interpolate while the row stays in place.
- Expanded rows animate height and opacity over 200ms.
- Column visibility/reordering uses fast shared layout transitions without stretching text.
- Sorting changes row position quickly with restrained layout animation only for small visible datasets; large datasets crossfade to the sorted result.
- Pagination crossfades the body while preserving table dimensions, header, and focus context.
- Hover transitions background, row-edge marker, and quick-action opacity over 140ms. Rows never lift, scale, or shift.

#### Animated cards and KPI surfaces

- Cards enter by priority with opacity and a maximum 6px rise; they do not float upward continuously.
- Hoverable cards transition border, tonal surface, and optional directional icon over 140ms.
- KPI surfaces animate value, comparison, sparkline, and trend marker as one coordinated unit.
- Cross-filtered cards use a shared selected-state marker.
- Collapsing analytical regions animates height while preserving the page’s logical focus target.
- Cards never rotate, tilt, glow, or use parallax.

#### Animated skeletons

- Skeletons reproduce final structure and use a 1200ms low-contrast luminance sweep.
- Table, Customer 360, Dashboard, chart, and drawer skeletons each match their final anatomy.
- Skeleton-to-content transition crossfades over 160ms without layout shift.
- Partial refresh retains data and uses a slim animated progress line rather than replacing content with skeletons.
- Skeleton animation pauses when the page is not visible and becomes static in reduced-motion mode.

#### Animated receipts and confirmations

- A receipt animates only after confirmed posting.
- Confirmation sequence: status marker resolves → confirmed amount emphasizes → allocation rows reveal → receipt reference and actions appear.
- Total sequence duration: no more than 480ms.
- The animation may use a restrained check draw and soft success-surface transition; confetti, coins, fireworks, and celebratory bursts are prohibited.
- Printing/exporting uses the static final receipt and never captures transitional frames.
- Reversed or failed payments use state-specific transitions and never reuse success motion.

#### Animated hover and press states

- Buttons compress no more than 1% or shift by no more than 1px on press.
- Links, icons, rows, cards, chart marks, calendar events, and map markers use the shared 140ms hover token.
- Hover never reveals the only way to complete an action.
- Touch receives immediate pressed-state feedback without waiting for hover logic.

#### Performance contract

- Animate `transform`, `opacity`, and composited properties whenever possible.
- Avoid animating large blur, box-shadow, layout-intensive dimensions, or entire map/chart canvases continuously.
- Keep no more than the visible region’s required animations active.
- Virtualized tables and timelines animate only mounted content.
- Motion must remain smooth on mid-range Android devices and ordinary office laptops.
- Page interaction becomes available immediately; choreography never blocks input.
- Loading animation is not used to disguise slow data or network behaviour.

#### Reduced-motion and accessibility

- Respect `prefers-reduced-motion` and provide a product-level reduced-motion preference.
- Reduced mode removes translation, scale, digit roll, chart drawing, stagger, and smooth scrolling.
- Essential state change remains visible through an 80–140ms opacity or colour transition, or appears instantly.
- Focus indicators never animate away or become delayed.
- Screen readers receive final state and confirmed values, not every animation frame.
- Motion never becomes the sole signifier of success, failure, risk, selection, or progress.

#### Motion review failures

- Different timings or easing invented by individual pages
- Bouncy finance actions
- Replaying full-page animation on filter or pagination change
- Count-up animation that temporarily shows false financial values
- Continuous pulsing, floating, glowing, or parallax
- Animated rows that cause users to lose selection or focus
- Skeletons that do not match final layout
- Success animation before server confirmation
- Motion that remains active offscreen
- Missing reduced-motion behaviour

---

## 4. Application composition

### 4.1 Persistent shell

Every authenticated page uses the same shell:

1. Navigation rail
2. Top command bar
3. Context header
4. Main workspace
5. Optional inspector rail

The top command bar includes global search, business date, area scope, notifications, approvals, and user context. Page-specific actions never migrate into the global command bar.

### 4.2 Context header

Order:

1. Breadcrumb
2. Page title and optional record identifier
3. Status and critical metadata
4. Primary page action and overflow actions
5. Optional metric strip
6. Tabs or saved views

Page titles, action locations, and tab treatment remain identical across modules.

### 4.3 Workspace patterns

Use one of six approved compositions:

- **Command centre:** metric strip + analytical grid + exception queue.
- **Workbench:** saved views + filter bar + data table + optional inspector.
- **Record 360:** identity header + summary band + tabs + activity rail.
- **Guided workflow:** progress stepper + focused form sections + review stage.
- **Control room:** live metrics + hierarchy/queue + contextual detail.
- **Report:** parameter header + result summary + visualization/table + export actions.

No page invents a seventh composition without design-system review.

### 4.4 On-demand task surfaces

Default module pages contain analytics, work queues, records, and exceptions. Creation forms are never rendered in the default page layout.

The only global creation entry points are:

- **New customer**
- **New loan**
- **New payment**

These actions may be launched from the page action, global quick actions, command palette, or a valid record context. Permission and context determine which actions are available.

#### Interaction selection

| Pattern | Use | Must not be used for |
|---|---|---|
| Drawer | Short contextual task, quick edit, evidence review, or the staged New Loan workflow | Unstructured giant forms |
| Wizard | Multi-stage, policy-sensitive creation with dependencies | One-field or one-decision actions |
| Step form | Structured task with 3–7 visible stages and save/resume | Unrelated settings collected together |
| Floating panel | Calculator, lookup, allocation preview, or temporary reference | Primary record creation or audit-critical confirmation |
| Split layout | Table-to-record inspection, side-by-side comparison, reconciliation | Permanent creation form beside a table |
| Command palette | Navigation, search, and launching permitted quick actions | Direct execution of irreversible financial actions |
| Quick actions | High-frequency, context-valid actions | Long menus of low-frequency operations |
| Context panel | Record summary, history, risk, evidence, or next actions | Duplicate copy of the main page |

#### New customer

- Opens a save-and-resume wizard.
- Stages: identity → address/area → KYC → livelihood/household → references → review.
- Duplicate lookup occurs as early as identity permits.
- A compact persistent summary shows completion, validation, duplicate risk, and draft status.
- Completion returns to Customer 360 and refreshes customer analytics.

#### New loan

- Requires a customer context or begins with customer search.
- Always opens a full-height wide drawer; the Dashboard or originating workspace remains visible behind it.
- The drawer contains a staged step form: customer/exposure → scheme/terms → affordability → verification → recommendation → review.
- Desktop width: 720px or up to 55vw, whichever preserves a useful view of the originating workspace.
- Tablet and mobile: the drawer becomes a full-screen sheet while retaining the same staged workflow.
- Calculations and schedules use a floating preview panel rather than widening the form.
- Policy deviations appear in context and feed the approval workflow.
- Completion returns to the application or loan workspace and refreshes origination analytics.
- When launched from the Dashboard, completion closes the drawer, refreshes Today’s Disbursement, Outstanding, Risk, Pending Approvals, Recent Loans, and Recent Activity, and retains the Dashboard’s prior scope and position.

#### New payment

- Opens a focused drawer for routine posting when customer and loan context are known.
- Opens a short wizard when allocation, multiple loans, or exception handling is required.
- Flow: identify account → amount/mode → allocation preview → confirmation → receipt.
- The final confirmation names the customer, loan, amount, allocation, effective date, and payment mode.
- Completion returns to the collection workspace, updates analytics immediately, and offers the receipt.

#### Context preservation

- The originating page retains filters, sort, selection, pagination, and scroll position.
- Successful completion updates affected metrics and rows without resetting the workspace.
- Cancel returns exactly to the prior state.
- Draft workflows can be resumed from the appropriate work queue.
- No task surface creates a second navigation system.

### 4.5 Quick actions and command palette

- The global quick-action trigger exposes only New customer, New loan, New payment, and role-specific high-frequency actions.
- Contextual quick actions appear beside the record identity or in the inspector footer.
- The command palette supports natural object search, destination navigation, saved views, and launching permitted creation flows.
- Commands show scope and consequence before launch.
- Keyboard shortcuts must not bypass confirmation, permission, or audit requirements.
- Quick-action lists are ranked by frequency and context; they are not a complete site map.

---

## 5. Core components

### 5.1 Buttons

#### Variants

- **Primary:** teal fill; one principal action per region.
- **Secondary:** neutral surface with strong border.
- **Tertiary:** text/icon action without persistent container.
- **Destructive:** critical fill; only in confirmation context.
- **Quiet destructive:** critical text for reversible or low-frequency actions.
- **Icon button:** only for universally understood actions; tooltip required.

#### Sizes

| Size | Height | Horizontal padding | Icon |
|---|---:|---:|---:|
| Compact | 32px | 10px | 16px |
| Standard | 40px | 14px | 18px |
| Large | 48px | 18px | 20px |

Rules:

- Labels begin with a verb: “Record payment”, “Approve loan”, “Export report”.
- Loading retains button width and replaces the leading icon with a spinner.
- Disabled buttons explain why through adjacent help or a tooltip.
- Button groups order actions: secondary/tertiary first, primary last.
- Never show two visually equal primary actions in one action cluster.

### 5.2 Forms

#### Anatomy

Label → optional requirement marker → control → helper text → validation message.

- Labels remain above controls.
- Standard control height: 40px; compact table filters: 32px; multiline minimum: 88px.
- Form sections use a title, one-sentence purpose when necessary, and a responsive 12-column field grid.
- Short related fields may share a row; unrelated fields do not.
- Currency inputs show `₹` inside the leading boundary and Indian digit grouping after blur.
- Dates use `DD MMM YYYY` for display and an explicit date picker for entry.
- Aadhaar displays `XXXX XXXX 1234`; reveal requires permission, reason, and audit capture.
- Phone entry defaults to India and displays `+91` clearly.

#### Validation

- Validate on blur and on submit; avoid aggressive error messages during typing.
- Errors appear beneath the field and in a submit summary for long workflows.
- Warnings permit continuation only when policy allows it.
- Saved drafts display last-saved time and sync state.
- Required fields are identified in text; colour alone is insufficient.

#### Approved form containers

- On-demand wizard or step form for customer onboarding, loan applications, sanctions, and configuration.
- Dialog for one decision or up to four small fields.
- Drawer for payment posting, contextual edits, and short tasks that do not require comparing a broad table.
- Floating panel for calculators, lookup, allocation preview, and temporary supporting tools; never for the primary form.
- Sticky workflow footer for Back, Save draft, Continue, and final submit actions.
- Never place a creation form permanently beside a list or table.
- Never render New customer, New loan, or New payment fields before the user explicitly launches that action.
- Break large forms into coherent stages; do not shrink or compress a giant form into one screen.

### 5.3 Tables

Tables are financial operations workspaces, not spreadsheets. They must communicate identity, ownership, state, risk, progress, urgency, and available action without forcing users to open every record.

The visual result must never look like Excel: avoid boxed cell grids, uniform text-only columns, spreadsheet-style row/column coordinates, and borders around every cell. Use strong column alignment, subtle horizontal separators, tonal states, grouped information, and rich record cells.

#### Enterprise table contract

Every customer, loan, and collection table includes or supports:

1. Customer avatar and identity
2. Collector avatar and ownership
3. Lifecycle status badge
4. Risk badge
5. Repayment progress bar
6. Loan health indicator
7. Due days / days-past-due context
8. Payment percentage
9. Quick actions
10. Expandable row detail
11. Hover animation
12. Column settings
13. Sticky header
14. Pagination
15. Search
16. Filters
17. Density toggle
18. Export
19. Quick View drawer

For tables where a customer, collector, loan, payment percentage, or due state does not logically exist—such as configuration, report catalogue, or system audit tables—the same structural role must be represented by the relevant business object, actor, completion state, or event health. Irrelevant fake columns are prohibited.

#### Rich identity cells

**Customer identity** is a compound cell:

- 32px customer avatar or verified initials avatar
- Customer name as the primary row link
- Customer ID and locality/area as compact metadata
- Optional verification marker
- No customer photograph is displayed outside permitted identity contexts

**Collector identity** is a compound ownership cell:

- 28px collector avatar or initials
- Collector name
- Route/area code as caption
- Availability or handover exception only when operationally relevant

Non-person tables use the same pattern with an object icon or actor avatar, primary identifier, and relevant metadata.

#### Status and risk

- Lifecycle status uses the global Status Badge component.
- Risk uses a separate compact Risk Badge: Low, Moderate, High, Critical, or Unscored.
- Status and risk must never be merged into a single ambiguous colour.
- Badge label and colour mappings remain identical in tables, filters, record pages, charts, and drawers.
- Critical status or risk may add a 3px row-edge marker but must not tint the entire row aggressively.

#### Loan health

Loan Health is a compound financial signal, not an unexplained score. It combines:

- Health label: Healthy, Watch, Stressed, Delinquent, or Critical
- Repayment progress
- Due-days context
- Payment percentage
- Optional trend marker showing improvement or deterioration

The visible health label is always accompanied by an accessible explanation in the expandable row or Quick View drawer.

#### Due days

- Future due dates display `Due in 6 days`.
- Due today displays `Due today`.
- Past due displays `12 DPD` plus overdue amount where space permits.
- Closed or fully paid records display `Completed`, not a meaningless zero.
- DPD colour follows configured arrears policy and is never derived from module identity colour.

#### Payment percentage and progress

- Payment percentage uses Manrope SemiBold.
- A compact 72–104px progress bar appears with an exact percentage label.
- Progress represents `amount paid ÷ total contracted amount` unless the column explicitly names another calculation.
- Hover/focus reveals amount paid, total amount, remaining amount, and schedule position.
- Progress colour communicates loan health, not arbitrary completion percentage.
- Values over 100% expose adjustment or excess-payment context and are never silently capped.

#### Quick actions

- One high-frequency action may appear directly in the row, such as Record payment or View receipt.
- Up to two icon actions may accompany it when universally understood.
- Remaining actions use an overflow menu grouped by routine, review, and sensitive actions.
- Quick actions appear on row hover, keyboard focus, and touch selection; essential actions cannot be hover-only.
- Permissions and record state determine availability.
- Destructive, approval, reversal, and Aadhaar-reveal actions require their prescribed confirmation and audit flow.

#### Expandable rows

- A dedicated chevron control expands the row without navigating away.
- Expanded content spans the row and uses a tonal surface rather than a nested card grid.
- Approved expanded content: repayment snapshot, next instalments, contact details, promises, last payment, risk reasons, and recent activity.
- Expansion never contains the full record page or a giant edit form.
- Only one row expands by default within dense tables; multi-expand can be enabled for explicit comparison workflows.
- Expanded state is keyboard accessible and announced.

#### Quick View drawer

- Clicking the identity link opens the full record workspace; clicking Quick View opens a right-side drawer.
- Quick View preserves table filters, sorting, pagination, selection, and scroll position.
- Drawer includes identity, status, risk, loan health, due position, financial summary, recent timeline, and context-valid quick actions.
- Previous/next controls navigate the current filtered result set.
- Complex editing or underwriting leaves Quick View for the focused record/workflow.
- On mobile, Quick View becomes a full-screen context sheet.

#### Table command bar

Every enterprise table has one compact command bar with a consistent order:

1. Search
2. Saved view
3. Essential filters
4. Active-filter count/tokens
5. Result count
6. Density toggle
7. Column settings
8. Export
9. Table overflow

- Search operates on clearly named fields and displays its scope.
- Filters open in a popover/drawer and retain active tokens in the command bar.
- Column settings support show/hide, reorder, freeze, and reset to system default.
- Density toggle supports Compact, Standard, and Comfortable; the selected mode persists per user and view.
- Export respects filters, sorting, area permissions, and masked-data policy.
- Large exports run as background jobs and appear in notifications/export history.

#### Non-Excel visual treatment

- Table surface may use the module soft tint in the header or selection layer; it is not always a white card.
- Column headers use Inter 13px SemiBold with strong text contrast.
- Body identity uses Inter 14–16px; financial values use Manrope SemiBold.
- Vertical cell borders are absent by default.
- Horizontal separators use `border-subtle` and become stronger only at groups or totals.
- Header and total rows may use tonal surfaces.
- Zebra striping is not used unless a long read-only report demonstrably benefits from it.
- Row content aligns by baseline and intentional column rhythm, not by wrapping every value in a pill.

#### Anatomy

Title/summary → table command bar → column header → rich record rows → optional totals → pagination.

#### Dimensions

- Compact row: 40px with 28px avatars.
- Standard operational row: 48px with 32px avatars.
- Comfortable row: 56px with 36px avatars.
- Header: 44px.
- Financial and numeric columns: right aligned.
- Status, date, text, and identity columns: left aligned.
- Selection column and primary identity column may freeze.

#### Behaviour

- Sticky header for scrolling datasets.
- Sort state is explicit in label and icon.
- Filters display as removable tokens and are included in the result count.
- Column visibility and density persist per user and saved view.
- Row hover is subtle; selected rows use a teal-tinted surface and left indicator.
- Clicking the primary identity opens the record; row menus contain secondary actions.
- Bulk actions appear in a selection toolbar, not permanently above the table.
- Totals distinguish visible-page totals from all-result totals.
- Pagination displays range, total, and page size.
- Horizontal scrolling keeps identity and critical status visible.

#### Sticky behaviour

- Command bar may remain sticky beneath the page/context header when the table is the primary workspace.
- Column header remains sticky beneath the command bar with correct offset.
- Primary identity and selection columns freeze horizontally on desktop/tablet.
- Quick actions may freeze at the right edge when horizontal scrolling is necessary.
- Sticky layers use borders and subtle elevation to show separation without heavy shadows.

#### Hover and interaction animation

- Hover transition: 140ms background-colour and row-edge emphasis.
- Row content never moves, scales, lifts, or changes height on hover.
- Quick actions fade in without shifting existing columns.
- Keyboard focus produces the same discoverability as hover.
- Reduced-motion mode removes fades and changes state instantly.

#### Financial cells

- Use tabular numerals and Indian grouping.
- Amount cells may show a secondary label such as principal, interest, or penalty.
- Negative values use a true minus sign.
- Do not replace zero with a dash; dash means unavailable.
- Overdue values include DPD or ageing context where decision-relevant.

#### Table states

- Initial load: structural row skeletons.
- Refresh: retain existing data with a subtle progress line.
- No results: filtered empty state with “Clear filters”.
- No records: domain-specific empty state.
- Partial failure: inline warning above retained data.

#### Pagination

- Pagination is always visible for paged datasets, including a single page when page-size context is valuable.
- Display format: `1–50 of 1,284` with previous, next, direct page navigation, and page-size selection.
- Default page size: 50 desktop/laptop, 25 tablet, 20 mobile work queue.
- Changing pages preserves filters, sorting, selected columns, and density.
- Returning from a record or Quick View restores the prior page and row position.

### 5.4 Cards and panels

Cards group one coherent subject. They are not default wrappers for all content.

#### Types

- **Metric tile:** label, value, comparison, optional sparkline.
- **Analytical panel:** title, controls, visualization, annotation.
- **Record card:** identity, status, essential metadata, next action.
- **Exception card:** severity, impact, reason, owner, due action.
- **Summary band:** horizontally aligned values within a record workspace.

Rules:

- Default padding: 16px or 20px; never mixed within a row.
- A metric tile has one dominant value, not several competing KPIs.
- Interactive cards have a consistent hover boundary and clear focus state.
- Avoid nested decorative cards, gradient fills, glass effects, and oversized icons.
- Use full-width panels when a table or chart benefits from horizontal space.

### 5.5 Status badges

Status is never displayed as plain text. Every lifecycle, verification, account, repayment, approval, and relationship-tier state uses the Sakthi Ledger Badge component.

Badges combine colour, background, border, icon, label, hover detail, and motion. They remain compact enough for dense tables while feeling deliberate and premium.

#### Anatomy

Icon + concise label inside a tonal background and 1px semantic border.

- Height: 26px standard, 22px compact.
- Radius: 6px; VIP may use the same radius and must not become a pill.
- Horizontal padding: 8px standard, 6px compact.
- Internal gap: 5px.
- Icon: mandatory, 14px standard or 12px compact, 1.75px stroke.
- Label: Inter 13px SemiBold standard or 12px SemiBold compact.
- Border: 1px with sufficient contrast against both badge background and surrounding surface.
- Status label never truncates in a primary record header; table cells may use an approved short label with full accessible name.

#### Required badge styles

| Status | Text/Icon | Background | Border | Icon | Meaning |
|---|---:|---:|---:|---|---|
| Verified | `#126B45` | `#E5F5EC` | `#94CBAE` | Shield-check | Identity or evidence verified |
| Pending | `#925100` | `#FFF1D6` | `#E5BC70` | Clock | Waiting for action or confirmation |
| Overdue | `#A8322C` | `#FBE7E5` | `#E19A94` | Alert-circle | Contractual obligation is past due |
| Closed | `#596168` | `#EEF0F1` | `#C9CED1` | Circle-check | Lifecycle completed and closed |
| Premium | `#6740AD` | `#F0E9FC` | `#C2ABE8` | Gem | Premium relationship tier |
| VIP | `#7A5815` | `#F8EDCF` | `#D8B85E` | Crown | VIP relationship tier |
| Active | `#245EA8` | `#E7F0FC` | `#A2C0E5` | Activity | Account or relationship currently active |
| Inactive | `#526170` | `#E9EDF0` | `#B8C2CA` | Pause-circle | Account or relationship inactive |

Dark-theme equivalents use the same hue identity with darker tonal backgrounds, stronger borders, and WCAG AA label contrast. Colours may not be substituted by module accents.

#### Badge icon contract

- One status uses one icon throughout the ERP.
- Icons are part of the shared outline icon family.
- Verified never uses the same icon as Closed.
- Pending never uses an error or warning-triangle icon unless the state is also blocked.
- Overdue uses an alert icon and must not use a decorative flame.
- Premium and VIP are relationship-tier badges; their gem/crown icons do not imply approval, creditworthiness, or lower risk.
- Icon and text are always present together in operational contexts. Icon-only badges are prohibited.

#### Hover and focus

- Hover transitions background, border, and icon emphasis over 140ms.
- Badge translates no more than −1px on hover; table badges remain stationary to protect row alignment.
- Tooltip appears after 400ms and explains the status definition, effective date, and owner/source when available.
- Keyboard focus uses the global focus ring and exposes the same tooltip/detail.
- Interactive badges use a pointer cursor and open filtered detail, history, or explanation.
- Non-interactive badges retain hover polish but do not impersonate a button.

#### Framer Motion behaviour

- Entry: 160ms opacity plus 96%→100% scale.
- Status change: old badge exits over 120ms; new badge enters over 180ms using shared layout position.
- Verified may draw its shield-check once after confirmed verification.
- Pending may show one restrained clock-hand transition when first created; it never pulses continuously.
- Overdue may receive one 480ms border emphasis when newly becoming overdue; continuous red flashing is prohibited.
- Premium and VIP use one subtle highlight sweep on first reveal only; no looping shimmer.
- Hover/focus animation uses the global `motion-fast` token.
- Reduced-motion mode switches states instantly or with an 80ms opacity change.
- Badge animation begins only after the underlying status is confirmed.

#### Status placement

- Record headers show the primary lifecycle badge beside the identifier/title.
- Tables use a dedicated status column; plain status words are prohibited.
- Quick View drawers repeat the primary badge in the identity summary.
- Timelines render the event outcome badge where status changed.
- Calendars, notifications, and approval queues use the same component and token mapping.
- Charts may use status colours, but legends and tooltips must render the label and icon-equivalent meaning.
- Printed receipts and reports use bordered monochrome-compatible badge treatment so meaning survives grayscale output.

Approved groups:

- Loan: Draft, Under review, Approved, Active, Overdue, Closed, Written off.
- Payment: Posted, Pending, Reversed, Failed, Reconciled.
- KYC: Not started, In progress, Verified, Expired, Rejected.
- Approval: Pending, Approved, Rejected, Returned.
- System: Online, Syncing, Offline, Degraded.

Rules:

- One status always maps to one semantic token across the entire ERP.
- Use no more than one primary lifecycle badge and one secondary risk badge together.
- Category labels use tags, not status badges.
- Premium and VIP are relationship tiers, not substitutes for Active, Verified, Risk, or Loan Health.
- If a new status is required, its label, colour, background, border, icon, hover detail, motion, and dark/print treatment must be added here before product use.
- Raw status strings from the API must be mapped to an approved badge; they may never appear directly in the interface.

### 5.6 Tags

Tags represent classification, filters, ownership, or user-entered labels.

- Height: 24px standard, 20px compact.
- Neutral by default; colour only for stable taxonomy.
- Removable tags include a labelled remove target.
- Overflow collapses to “+3” with an accessible popover.
- Tags wrap in detail views but truncate in table cells.
- Statuses must not be represented as removable tags.

### 5.7 Progress bars and steppers

#### Linear progress

- Height: 6px standard; 10px when segmented.
- Show label, numeric value, target, and unit outside the bar.
- Values over target continue visually through an explicit over-target marker; never cap silently.
- Semantic colour depends on performance meaning, not percentage alone.

#### Workflow stepper

- Used for onboarding, application, sanction, and day close.
- States: not started, current, complete, warning, blocked.
- Desktop: vertical rail for long workflows; horizontal only for five or fewer short stages.
- Users can revisit completed steps; blocked future steps explain prerequisites.

#### Collection strip

- A purpose-built 100-segment repayment visualization for daily loans.
- Paid, due today, upcoming, missed, waived, and adjusted states have fixed styles.
- Each segment exposes date and amount on hover/focus.

### 5.8 Charts and data visualization

Charts answer a stated business question. Decorative charts are prohibited.

#### Approved chart set

- Line: trend over time.
- Area: cumulative or volume trend.
- Grouped bar: area/collector comparison.
- Stacked bar: composition over time.
- Bullet chart: actual versus target.
- Waterfall: cash or balance movement.
- Ageing band: portfolio distribution.
- Heatmap: collection performance by date/area.
- Donut: only for 2–5 parts when total composition is the message.
- Sparkline: compact trend paired with a value.

#### Visual rules

- Use the same categorical palette in every module.
- Axes begin at zero for bars unless a clearly annotated exception is required.
- Currency axis labels use compact Indian notation: `₹2L`, `₹25L`, `₹1Cr`.
- Full values appear in tooltip and data table.
- Direct labels are preferred to distant legends.
- Grid lines are subtle; chart borders are absent.
- Tooltips show period, exact value, comparison, and definition when needed.
- Every chart includes an accessible summary and tabular alternative.
- Loading charts use structural skeletons, not spinners.
- Empty charts explain why data is absent.
- Animation is limited to a 320ms transition after filter changes.
- 3D charts, gauges, radar charts, rainbow palettes, and unlabelled pies are prohibited.

### 5.9 Dialogs

Dialogs interrupt the workflow only for focused decisions.

#### Sizes

- Small: 400px confirmation.
- Medium: 560px focused task.
- Large: 720px evidence-heavy decision.
- Anything larger becomes a full-page workflow.

#### Anatomy

Title → concise consequence/context → content → optional validation summary → actions.

- Primary action is last; destructive action uses explicit verb and object.
- Financial confirmation shows amount, account, customer, allocation, and effective date.
- Close via button and Escape unless the action is processing or legally requires a decision.
- Unsaved changes trigger a discard confirmation.
- Nested dialogs are prohibited.

### 5.10 Drawers and inspectors

Use drawers to preserve context while reviewing details or making a contained edit.

- Width: 400px compact, 480px standard, 640px evidence-heavy.
- New Loan workflow drawer: 720px or up to 55vw on desktop, with internal staged navigation rather than a single giant form.
- Opens from the right in desktop; becomes a full-screen sheet on small screens.
- Header and footer remain sticky; content scrolls independently.
- Drawers contain one task or record context.
- A table may open a read-only inspector drawer; complex editing moves to a focused workflow.
- Drawers do not stack. A deeper record replaces the drawer content with visible back navigation.

### 5.11 Timeline

The timeline is the canonical history component for customers, loans, approvals, and audit-sensitive actions.

- Reverse chronological by default.
- Each event includes actor, action, object, timestamp, source, and optional reason.
- Date separators group events by day.
- Event icons represent stable event types, not decoration.
- Corrections and reversals link to the original event.
- Sensitive reveals and approval decisions use strong semantic markers.
- Filters include activity type, actor, and date.
- System-generated events are visually quieter but never hidden by default.
- Audit timelines are immutable in the UI.

### 5.12 Calendar components

#### Date picker

- Locale-aware, Monday-first, keyboard navigable.
- Displays `DD MMM YYYY`; Tamil locale receives translated month/day labels.
- Today, selected date, business date, blocked date, and due date are visually distinct.
- Date constraints explain why a date is unavailable.

#### Date range

- Two-month desktop view; one-month mobile view.
- Presets: Today, Yesterday, This week, This month, Previous month, Financial year, Custom.
- Financial-year range follows configured business policy.

#### Operations calendar

- Used for demand, collection, holidays, day close, and scheduled reports.
- Month, week, and agenda modes share consistent event colours.
- Dense days show top priorities and an explicit overflow count.
- Business holidays and non-collection days use pattern plus label, not colour alone.

### 5.13 Notification system

Notifications are actionable operational events, not a feed of every system change.

#### Priority

- Critical: blocks money movement, compliance, security, or day closing.
- High: requires action today.
- Normal: requires review.
- Informational: no immediate action.

#### Notification centre

- Group by Today, Earlier, and resolved.
- Each notification includes category, concise event, business impact, timestamp, and action.
- Read/unread is secondary to resolved/unresolved.
- Users can filter by area, category, and priority.
- Critical items cannot be silently dismissed; resolution requires an action or reason.
- Deduplicate repeated events and summarize bursts.
- Notification count represents actionable unread items, not historical total.

### 5.14 Toast messages

Toasts acknowledge lightweight results and never contain essential evidence.

- Position: bottom-right desktop, bottom-centre mobile.
- Width: 360px maximum.
- Success: 4 seconds.
- Information: 6 seconds.
- Warning: persistent up to 10 seconds when action is available.
- Error: persists until dismissed or resolved.
- Maximum three visible; additional messages queue.
- Include one optional action such as Undo or View receipt.
- Financial posting success includes transaction reference and a route to the receipt.
- Do not use a toast as the only confirmation for destructive or irreversible actions.

### 5.15 Loading skeletons

Skeletons reproduce the structure of the destination.

- Use neutral pulse from `surface-2` to `surface-3` over 1.2 seconds.
- Tables show header and 6–10 row structures.
- Metric strips preserve label/value hierarchy.
- Record pages preserve identity header, summary band, and tab content.
- Charts preserve title, plot, and axis silhouettes.
- After initial load, refreshes retain current data and use a slim progress indicator.
- Do not mix full-page skeletons and central spinners.
- Respect reduced motion with a static skeleton.

---

## 6. State language

### 6.1 Empty states

There are three types:

- **First-use:** explains the capability and offers the permitted starting action.
- **No results:** names the active query/filter and offers reset.
- **Completed:** confirms there is currently no work, such as “All receipts reconciled”.

An empty state contains a concise title, one sentence, and at most one primary plus one secondary action. Illustrations, if used, are small monochrome line graphics. Never place a large cartoon in an operational workspace.

### 6.2 Error states

#### Field error

Placed directly below the relevant input with correction guidance.

#### Section error

Inline banner within the affected panel; unaffected content remains available.

#### Page error

Explains what failed, whether data is safe, a retry action, and a support/reference code.

#### Transaction error

Must state:

1. Whether the transaction was posted
2. Whether money moved
3. What the user should do next
4. A trace/reference identifier

Never show raw stack traces, database messages, or ambiguous “Something went wrong” alone.

### 6.3 Success states

- Routine save: toast plus updated inline state.
- Created record: focused success summary with identifier and next actions.
- Payment: amount, allocation, transaction number, timestamp, collector, and receipt action.
- Approval: decision, approver, effective state, and next workflow stage.
- Day close: reconciliation summary, exceptions count, and immutable close reference.
- Never use confetti or celebratory animation for normal financial operations.

### 6.4 Warning and critical banners

- Warning banners explain risk and continuation conditions.
- Critical banners identify blocking impact and required resolution.
- Banners use icon, title, description, and optional action.
- Page-level banners sit below the context header; panel-level banners remain within the panel.
- Dismissal is allowed only when the information is non-blocking and recoverable from the notification centre.

### 6.5 Offline and degraded states

- The shell displays connectivity state persistently.
- Read-only cached data is labelled with last-sync time.
- Queued collection entries show local reference and sync status.
- Conflicts require explicit review; the system never silently overwrites a financial record.

---

## 7. Menus, navigation, and discovery

### 7.1 Navigation

- Domain groups and order remain stable for all users; permissions remove unavailable destinations without rearranging the rest.
- Active destination uses teal indicator, stronger text, and subtle selected surface.
- Icons support labels; collapsed navigation includes tooltips.
- Breadcrumbs show hierarchy, not browser history.

### 7.2 Tabs

- Used for sibling views within one record or workspace.
- Underline/indicator treatment; tabs are not pill buttons.
- Counts may appear after labels.
- Tab order is stable and deep-linkable.
- More than seven tabs require grouping or an overflow menu.

### 7.3 Search and command palette

- Global search finds customer, phone, masked Aadhaar suffix, loan, receipt, and transaction.
- Results group by object type and show enough context to distinguish duplicates.
- Command palette supports navigation and safe routine commands.
- Destructive and high-consequence approvals cannot execute directly from search.

### 7.4 Filters and saved views

- Common filters appear in a compact bar; advanced filters open a popover or drawer.
- Active filters become removable tokens.
- Saved views retain filters, sorting, columns, density, and area scope.
- System views and personal views are visibly distinguished.
- Filter changes update result count and shareable URL state.

---

## 8. Supporting components

### 8.1 Tooltips

- Explain icons, abbreviations, truncated values, and calculation definitions.
- Appear after 400ms hover or immediately on keyboard focus.
- Never contain essential actions or long-form business rules.

### 8.2 Popovers

- Used for lightweight selection, definitions, and compact filters.
- Close on outside interaction and Escape.
- Must not contain long forms or nested navigation.

### 8.3 Menus

- Group actions by purpose and separate destructive actions.
- Each menu item uses icon, verb label, and shortcut where relevant.
- Unavailable actions are hidden when unauthorized and disabled with explanation when temporarily unavailable.

### 8.4 Pagination

- Shows `1–50 of 1,284`, page size, next/previous, and direct page access for large result sets.
- Cursor-based datasets use “Load next” with retained scroll context.
- Page changes move focus to the table caption, not the browser top.

### 8.5 Avatars and identity

- Initials-based neutral avatars are standard.
- Customer photographs appear only where identity verification benefits from them.
- Role, area, or status is expressed in adjacent text/badge, never by avatar colour alone.

### 8.6 Dividers

- Use spacing first, subtle divider second, strong divider only for financial totals or fixed regions.
- Vertical dividers are limited to toolbars and summary bands.

### 8.7 Receipts and printable documents

- Formal white document surface independent of light/dark application theme.
- Full business identity, receipt number, server timestamp, loan/customer reference, allocation, mode, and verification mark.
- Monetary total is visually dominant but not decorative.
- Print layouts use black text and reliable borders; meaning cannot depend on colour.

---

## 9. Accessibility and localization

- Minimum target size: 40×40px desktop; 44×44px touch workflows.
- All workflows work by keyboard with logical focus order.
- Dialogs and drawers trap focus and restore it to the opener.
- Tables have captions, scoped headers, and announced sort state.
- Charts include accessible summaries and data tables.
- Errors are associated with fields programmatically and summarized on submit.
- English and Tamil strings are never hard-coded inside layout components.
- Allow at least 35% label expansion and test Tamil at every supported breakpoint.
- Do not truncate customer names, critical statuses, amounts, or decision consequences.
- Dates, numbers, and currency follow product locale rules consistently.

---

## 10. Content language

- Use direct operational language: “Record payment”, not “Add collection”.
- Use domain nouns consistently: customer, application, loan account, instalment, payment, receipt, arrears, collector, area, sanction, disbursement.
- Avoid generic labels such as item, entry, data, submit, OK, and process.
- Confirmations name the action and consequence.
- Error messages state what happened and how to recover.
- Status labels describe current state; button labels describe the next action.

Examples:

- Good: “Approve ₹75,000 loan”
- Bad: “Confirm”
- Good: “Payment was not posted. No money was recorded.”
- Bad: “Transaction failed”
- Good: “3 receipts require reconciliation”
- Bad: “You have notifications”

---

## 11. Component state matrix

Every interactive component must be designed and implemented in these states where applicable:

| State | Required treatment |
|---|---|
| Default | Resting appearance and accessible name |
| Hover | Subtle affordance, no layout shift |
| Focus | Visible teal focus ring |
| Active | Immediate pressed/selected feedback |
| Disabled | Reduced emphasis plus explanation |
| Loading | Preserved dimensions and progress feedback |
| Empty | Domain-specific explanation and next action |
| Error | Clear cause, impact, and recovery |
| Warning | Risk plus continuation condition |
| Success | Confirmed new state and reference where relevant |
| Read-only | Clearly distinct from editable but fully legible |
| Offline | Sync state, local reference, and constraints |
| Permission denied | Reason and permitted escalation path |

No component is complete if only its default state exists.

---

## 12. Consistency governance

### 12.1 Rules for new pages

Before a page is approved, it must identify:

1. User and operational decision
2. Approved workspace composition
3. Primary object and status model
4. Primary and secondary actions
5. Data density and responsive behaviour
6. Empty, loading, error, warning, success, and permission states
7. Audit and approval implications
8. English and Tamil validation
9. Keyboard and accessibility behaviour
10. Reused design-system components
11. Framer Motion entrance, update, interaction, and exit choreography
12. Reduced-motion equivalent and animation performance budget

### 12.2 Prohibited patterns

- Generic four-card dashboard followed by unrelated widgets
- Permanent forms beside tables
- Large blank hero regions inside authenticated pages
- Gradient statistic cards
- Floating glass panels
- Multiple radius systems
- Page-specific button colours
- Page-specific status colours
- Icons from mixed families
- Unexplained icon-only business actions
- Modals containing entire pages
- Nested cards used only to create visual interest
- Decorative charts without a decision or comparison
- Toast-only financial confirmation
- Tables that hide identity or critical status while scrolling
- Different navigation or header structures between modules

### 12.3 Design review gate

No page moves to implementation until it passes:

- Foundation compliance
- Component reuse review
- State completeness review
- Financial-format review
- Responsive-density review
- Tamil layout review
- Accessibility review
- Workflow and permission review
- Motion choreography and reduced-motion review

Any new visual pattern must be added to this system before it appears in a product page. One-off page styling is not permitted.

---

## 13. Definition of design-system complete

The system is ready for product-page design only when the following exist and agree with this specification:

- Token inventory for both themes
- Typography and icon assets
- Layout grid and shell templates
- Component anatomy for every component in this document
- All component state variants
- Table and chart examples using real lending data
- Form validation and financial confirmation examples
- Record 360, workbench, workflow, command centre, control room, and report templates
- Responsive collector patterns
- English/Tamil stress tests
- Accessibility annotations
- Framer Motion variants/tokens, screen choreography, and reduced-motion specifications
- Content and terminology dictionary
- Design QA checklist

This document is the governing contract. Product screens may combine approved patterns, but they may not invent a different visual language.
