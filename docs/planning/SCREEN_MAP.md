# Sakthi Ledger — Complete Screen Map

## 1. Screen composition codes

| Code | Composition |
|---|---|
| CC | Command centre |
| WB | Workbench: analytics + command bar + rich table/queue + Quick View |
| R360 | Record 360 |
| GW | Guided workflow/wizard |
| CR | Control room |
| RP | Report workspace |
| CFG | Configuration workspace |
| OV | Global overlay/drawer/palette |

Every screen inherits the shared shell, design system, states, motion, accessibility, and responsive contracts.

## 2. Global and authentication screens

| ID | Route/state | Screen | Comp. | Primary purpose | Primary action |
|---|---|---|---|---|---|
| G-01 | `/login` | Sign in | GW | Secure authentication | Sign in |
| G-02 | session overlay | Session expiring | OV | Protect work/drafts | Continue session |
| G-03 | `/search?q=` | Global search results | WB | Find business objects | Open result |
| G-04 | command state | Command palette | OV | Navigate/search/launch task | Select command |
| G-05 | create state | Global New menu | OV | Launch permitted create flow | New Customer/Loan/Payment |
| G-06 | `/approvals` | Approval centre | WB | Consolidated decision queue | Review decision |
| G-07 | approval drawer | Approval detail | OV | Evidence and consequence | Approve/return/reject |
| G-08 | `/notifications` | Notification centre | WB | Resolve actionable events | Resolve/open |
| G-09 | `/profile` | Profile and preferences | CFG | Language, density, motion, personal settings | Edit preferences |
| G-10 | global state | Offline/sync centre | OV | Review queued/conflicted actions | Resolve/sync |
| G-11 | global state | Permission denied | state | Explain access boundary | Return/request access |
| G-12 | global state | Not found/removed record | state | Explain missing destination | Return/search |

## 3. Dashboard screens

| ID | Route | Screen | Comp. | Required first-view content | Actions |
|---|---|---|---|---|---|
| D-01 | `/` | Role-composed Dashboard | CC | Financial pulse, collection pace, performance, approvals, recent operations | New actions, drill-down |
| D-02 | `/?view=today` | Today’s operations | CC | Demand, collection, disbursement, cash, collectors, exceptions | Open work queue |
| D-03 | `/?view=areas` | Area performance | CC | Area comparison, outstanding, recovery, risk, trend | Filter/open area |
| D-04 | `/?view=collectors` | Collector performance | CC | Demand, collected, coverage, route, exceptions | Open collector route |

No Dashboard screen contains an embedded record-entry form.

## 4. Customer screens

| ID | Route/state | Screen | Comp. | Analytics/content | Primary action |
|---|---|---|---|---|---|
| C-01 | `/customers` | Customer workbench | WB | Customers, active, KYC pending, risk, follow-ups | New Customer |
| C-02 | `/customers/kyc` | KYC work queue | WB | Pending/failed/ageing/duplicates | Review KYC |
| C-03 | `/customers/follow-ups` | Follow-up work queue | WB | Due, overdue, missed, owner/channel | Complete follow-up |
| C-04 | overlay `/customers/new` | New Customer wizard | GW | Identity through review | Save/submit |
| C-05 | duplicate step | Duplicate resolution | GW | Matches, shared signals, evidence | Open/merge/continue |
| C-06 | `/customers/:id` | Customer 360 Overview | R360 | Identity, exposure, health, risk, due, follow-up, activity | New Loan/Payment |
| C-07 | `/customers/:id/timeline` | Master Timeline | R360 | Financial, communication, field, documents, risk | Filter/open event |
| C-08 | `/customers/:id/loans` | Customer loans | R360 | Active/previous loans, loan timeline, exposure | Open Loan 360 |
| C-09 | `/customers/:id/calendar` | Customer Calendar | R360 | Payment, Collection, Agenda | Add follow-up/reminder |
| C-10 | `/customers/:id/communications` | Communications | R360 | Calls, SMS, WhatsApp, delivery/outcome | Communicate/log |
| C-11 | `/customers/:id/documents` | Document Center | R360 | Document list/preview, verification/version/expiry | Upload document |
| C-12 | `/customers/:id/relationships` | Family and guarantors | R360 | Family Tree, household, guarantors, related exposure | Add relationship |
| C-13 | `/customers/:id/profile` | Profile and capacity | R360 | Employment, business, income, expenses, affordability | Edit section |
| C-14 | `/customers/:id/field` | Field activity | R360 | Map, GPS, visits, notes, attachments | Record visit |
| C-15 | drawer | Customer Quick View | OV | Identity, KYC, risk, exposure, next due, recent activity | Open Customer 360 |
| C-16 | drawer | Follow-up/reminder editor | OV | Purpose, owner, due, channel, outcome | Save/complete |
| C-17 | drawer | Communication composer/logger | OV | Consent, contact, channel, language, template | Send/log |
| C-18 | drawer | Visit recorder | OV | GPS, accuracy, purpose, outcome, notes, attachments | Save/queue |
| C-19 | drawer | Document upload/verification | OV | File, type, related record, expiry, status | Upload/verify |
| C-20 | secure overlay | Aadhaar reveal | OV | Reason, permission, audit warning | Reveal temporarily |

## 5. Loan screens

| ID | Route/state | Screen | Comp. | Analytics/content | Primary action |
|---|---|---|---|---|---|
| L-01 | `/loans/pipeline` | Origination pipeline | WB | Pipeline value, stages, blockers, SLA, conversion | New Loan |
| L-02 | `/loans/applications` | Applications workbench | WB | Stage ageing, requested/recommended, risk, deviations | Review application |
| L-03 | `/loans/active` | Active loans | WB | Outstanding, due today, maturity, recovery, health | New Loan/Payment |
| L-04 | `/loans/overdue` | Overdue loans | WB | PAR/DPD buckets, amount at risk, broken promises | Recovery action |
| L-05 | `/loans/closed` | Closed/settled loans | WB | Closure, realized return, duration | Open Loan 360 |
| L-06 | overlay `/loans/new` | New Loan staged drawer | GW/OV | Customer, terms, affordability, verification, recommendation, review | Save/submit |
| L-07 | `/loans/applications/:id` | Application 360 | R360 | Stage, evidence, assessment, deviations, approvals | Submit/review |
| L-08 | `/loans/:id` | Loan 360 Overview | R360 | Principal, paid, outstanding, health, DPD, due | New Payment |
| L-09 | `/loans/:id/schedule` | Repayment schedule | R360 | Instalments/100-day strip, due/paid/missed | Inspect instalment |
| L-10 | `/loans/:id/payments` | Payment ledger | R360 | Payments, allocations, receipts, reversals | New Payment |
| L-11 | `/loans/:id/collections` | Collection history | R360 | Assignments, visits, promises, outcomes | Add follow-up |
| L-12 | `/loans/:id/documents` | Loan documents | R360 | Application, sanction, agreement, evidence | Upload document |
| L-13 | `/loans/:id/approvals` | Loan approvals | R360 | Requests, decisions, conditions, SLA | Open approval |
| L-14 | `/loans/:id/timeline` | Loan Timeline | R360 | Application through closure/recovery | Filter/open event |
| L-15 | drawer | Loan Quick View | OV | Customer, exposure, health, due, risk, actions | Open Loan 360 |
| L-16 | drawer/panel | Schedule calculator | OV | Terms, instalment, completion, total repayment | Apply to draft |
| L-17 | approval drawer | Loan decision | OV | Financial impact, evidence, policy, deviations | Decide |
| L-18 | staged overlay | Documentation checklist | GW | Required documents and conditions | Complete/submit |
| L-19 | staged overlay | Disbursement | GW | Amount, mode, account/reference, maker/checker | Post disbursement |

## 6. Collection and finance-operation screens

| ID | Route/state | Screen | Comp. | Analytics/content | Primary action |
|---|---|---|---|---|---|
| O-01 | `/collections` | Collection Control Room | CR | Demand, collected, recovery, collectors, cash/digital, exceptions | New Payment |
| O-02 | `/collections/routes` | Route overview | WB | Route demand, coverage, completion, variance | Open route |
| O-03 | `/collections/routes/:id` | Collector route | CR | Sequence/map, customers, due, risk, outcomes, sync | Collect/contact/visit |
| O-04 | `/collections/demand` | Demand queue | WB | Due/overdue demand, owner, health, promises | New Payment/follow-up |
| O-05 | `/collections/payments` | Payments and receipts | WB | Posted/pending/reversed, mode, collector, reconciliation | New Payment |
| O-06 | overlay `/collections/payments/new` | New Payment drawer | GW/OV | Account, amount, allocation, confirmation, receipt | Post payment |
| O-07 | drawer | Payment Quick View | OV | Payment, allocation, receipt, reconciliation, audit | Open receipt/request reversal |
| O-08 | confirmation | Confirmed Receipt | OV | Amount, allocation, reference, balance, delivery | Print/share/send |
| O-09 | approval flow | Payment reversal | GW | Original, reason, evidence, impact, decision | Request/post reversal |
| O-10 | `/collections/promises` | Promises/follow-ups | WB | Due/broken/owner/amount/risk | Complete/contact |
| O-11 | `/collections/handover` | Cash handover | CR | Collector expected/physical/variance/status | Receive handover |
| O-12 | drawer | Handover detail | OV | Receipt list, expected, physical, evidence, variance | Accept/escalate |
| O-13 | `/collections/reconciliation` | Reconciliation | CR | Unmatched, duplicates, variance, digital/cash | Resolve item |
| O-14 | drawer | Reconciliation resolution | OV | Expected/actual, evidence, source, outcome | Resolve/request approval |
| O-15 | `/collections/day-close` | Day close | CR | Opening, flows, expected, physical, variance, checks | Close business day |
| O-16 | confirmation | Day-close summary | OV | Totals, exceptions, approvals, close reference | Confirm close |
| O-17 | `/collections/delinquency` | Delinquency workbench | WB | PAR/DPD, roll rates, promises, recoveries, escalations | Assign/recovery action |
| O-18 | drawer | Delinquency Quick View | OV | Loan, risk, DPD, contact, promises, strategy | Record action |
| O-19 | overlay | Offline sync/conflict | OV | Queued payments/visits, server state, resolution | Verify/retry |

## 7. Report screens

| ID | Route/state | Screen | Comp. | Content | Primary action |
|---|---|---|---|---|---|
| R-01 | `/reports` | Report catalogue | WB | Categories, purpose, permission, freshness | Open report |
| R-02 | `/reports/saved` | Saved reports | WB | Owner, parameters, last run, sharing | Run/edit |
| R-03 | `/reports/scheduled` | Scheduled reports | WB | Schedule, delivery, last/next result | Edit schedule |
| R-04 | `/reports/:type` | Report parameters | RP | Required scope/period/filters | Generate |
| R-05 | `/reports/runs/:runId` | Report Preview | RP | Immutable snapshot, summary, charts, tables, totals | Export/share |
| R-06 | drawer | Export menu/status | OV | PDF/XLSX/CSV/Print generation states | Generate artifact |
| R-07 | drawer | Share report | OV | Artifact, recipients/scope, expiry, policy | Create share |
| R-08 | drawer | Email report | OV | Recipient, message, artifact/link, delivery | Send |
| R-09 | `/reports/exports` | Export History | WB | Artifact, file, checksum/status, share/email, expiry | Download/revoke/retry |
| R-10 | print document | Report print view | RP | Report-only paginated content | Print |

Every report type supports Preview, PDF, Excel, CSV, Print, Share, and Email through real services/artifacts.

## 8. Audit screens

| ID | Route/state | Screen | Comp. | Content | Primary action |
|---|---|---|---|---|---|
| A-01 | `/audit` | Audit workbench | WB | Events, actor, entity, action, result, source, correlation | Open event |
| A-02 | `/audit?sensitive=true` | Sensitive access review | WB | Aadhaar, exports, shares, permission, reversal | Investigate |
| A-03 | `/audit?category=financial` | Financial action audit | WB | Payment, reversal, disbursement, close | Investigate |
| A-04 | `/audit?category=config` | Configuration audit | WB | Before/after, reason, approval, effective time | Investigate |
| A-05 | `/audit?category=exports` | Export/share/email audit | WB | Artifact, actor, recipient, access/outcome | Investigate/revoke where allowed |
| A-06 | drawer | Audit event Quick View | OV | Immutable detail, before/after, linked events | Open related object |

Audit events have no edit/delete action.

## 9. Settings screens

| ID | Route | Screen | Comp. | Content | Primary action |
|---|---|---|---|---|---|
| S-01 | `/settings` | Settings index | CFG | Sections, health, pending changes, dependencies | Open section |
| S-02 | `/settings/organization` | Organization | CFG | Legal/display identity, timezone, currency, business date | Propose edit |
| S-03 | `/settings/areas-routes` | Areas and routes | CFG | Area/route hierarchy, assignment, active state | Add/edit |
| S-04 | `/settings/users` | Users | WB/CFG | Identity, role, scope, status, last login | Add/edit user |
| S-05 | `/settings/roles` | Roles and permissions | CFG | Capabilities, sensitivity, scope | Propose role change |
| S-06 | `/settings/loan-products` | Loan products | CFG | Daily/Monthly products, limits, rates, term, versions | New version |
| S-07 | `/settings/arrears` | Collection and arrears policy | CFG | DPD buckets, grace, alerts, strategy | New version |
| S-08 | `/settings/payments` | Payment and receipt policy | CFG | Modes, allocation, idempotency, numbering | Propose edit |
| S-09 | `/settings/communications` | Communication channels | CFG | SMS, WhatsApp, email providers/templates/consent | Configure/test |
| S-10 | `/settings/reporting` | Reporting and delivery | CFG | Definitions, exports, sharing, email, retention | Configure |
| S-11 | `/settings/security` | Security and privacy | CFG | Session, encryption, masking, access, retention | Propose edit |
| S-12 | `/settings/backups` | Backup and recovery | CFG | Jobs, status, retention, restore evidence | Run backup/test restore |
| S-13 | `/settings/localization` | Language/date/financial year | CFG | English/Tamil, formats, business calendar | Propose edit |
| S-14 | `/settings/integrations` | Integrations | CFG | Provider state, credentials reference, webhooks/jobs | Configure/test |
| S-15 | drawer/workflow | Configuration change | GW/OV | Value, dependency impact, effective date, reason, approval | Submit/schedule |
| S-16 | drawer | Configuration history | OV | Versions, before/after, approvals, effective state | Inspect |

## 10. Report type inventory

Each type uses R-04/R-05 with its own real parameter, calculation, and output contract.

- Customer Ledger
- Daily Collection
- Monthly Cash Flow
- Annual Business Report
- Loan Summary
- Defaulters/Delinquency
- Area Performance
- Collector Performance
- Profit and Interest
- Recovery Rate
- Business Growth
- Outstanding/Maturity
- Payment and Receipt Register
- Cash Handover
- Reconciliation and Variance
- Day Close
- KYC/Verification
- Approval SLA
- Audit/Sensitive Access
- Export/Share/Email Activity

## 11. State coverage matrix

Every screen ID must document/test:

| State | Required |
|---|---|
| Loading skeleton | Yes |
| Refresh/stale | Yes for data screens |
| Empty first-use | Where domain can be empty |
| Empty filtered | All workbenches |
| Partial failure | Multi-panel screens |
| Full error | All routes |
| Offline/queued | All field/mutation screens |
| Permission restricted | All protected routes/actions |
| Validation | All task surfaces |
| Success | All mutations |
| Conflict | All mutable/versioned records |
| Reduced motion | All animated screens |
| Tamil/long content | All user-facing screens |
| Mobile/tablet/laptop/desktop | All screens |

## 12. Placeholder prohibition

- No screen uses generic KPI values without period, definition, comparison, and drill-down.
- No chart exists without a business question and real calculation.
- No action exists without a service contract.
- No empty card is added to balance a grid.
- No page is a generic table plus permanent form.
- No screen is implemented before its ID, route, data, actions, states, permissions, and responsive behavior are approved here.
