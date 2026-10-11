# Sakthi Ledger — Complete UX Flows

## 1. UX architecture

All flows follow the same task model:

`Discover → Understand context → Start permitted action → Validate → Review consequence → Confirm → Receive evidence → Return to updated context`

Global rules:

- Forms appear only after explicit action.
- Originating filters, selection, pagination, tab, and scroll are preserved.
- Draft is available for long workflows.
- Financial actions show exact consequence before confirmation.
- Success includes a durable identifier and next actions.
- Failure states explicitly say whether money/data moved.
- Sensitive actions require permission, reason, and audit.
- Mobile/offline flows expose queued, syncing, conflict, and failed states.

## 2. Role journeys

### Owner

Primary journey:

`Dashboard → Portfolio/risk exception → Customer or Loan Quick View → Evidence → Approval decision → Updated Dashboard`

Needs:

- Organization-wide scope
- Cash, revenue, profit, outstanding, risk, and recovery
- Approval queue
- Area/collector comparison
- Audit and export oversight
- Configuration authority

### Manager

Primary journey:

`Today’s operations → Origination/collection exception → Assign/review → Approve or escalate → Monitor completion`

Needs:

- Area/team performance
- Customer verification
- Credit assessment and policy deviation
- Collector route and delinquency work
- Follow-up and approval SLA

### Accountant

Primary journey:

`Finance/collections position → Receipt/payment queue → Reconcile → Resolve variance → Day close → Report/export`

Needs:

- Cash and digital split
- Payment posting/reversal control
- Handover and bank deposit
- Export/report accuracy
- Close evidence and immutable references

### Collector

Primary journey:

`Today’s route → Customer context → Collect/contact/visit → Receipt or follow-up → Cash handover → Sync/close route`

Needs:

- Mobile-first route
- Offline-safe payment/visit capture
- Customer due/risk/contact context
- Receipt delivery
- Promise/follow-up
- Clear handover state

## 3. Authentication and session flow

1. User enters username/password.
2. System validates identity and active status.
3. Success loads role, permission, area scope, business date, saved preferences, and unresolved tasks.
4. User lands on role-composed Dashboard.
5. Expiring session warns without discarding drafts.
6. Reauthentication restores the protected task when policy permits.

Failures:

- Invalid credentials: generic safe error.
- Inactive user: access-disabled state with support path.
- Network unavailable: offline sign-in unavailable unless secure session policy supports it.
- Permission changed during session: current action stops safely and explains scope change.

## 4. New Customer flow

Entry:

- Global New action
- Customers page
- Command palette
- New Loan customer lookup when no match exists

Stages:

1. **Identity:** name, preferred language, DOB/age, gender if required, phone.
2. **Duplicate check:** phone, Aadhaar hash, shared address/reference signals.
3. **Address/area:** registered, residential, business, route/collector.
4. **KYC:** Aadhaar and other identity/address evidence, consent, verification.
5. **Capacity:** employment, business, income, expenses, obligations.
6. **Relationships:** family, household, guarantor, references.
7. **Review:** completeness, duplicate risk, consent, declaration.

Outcomes:

- Save draft
- Submit for verification
- Verified creation when authorized process completes
- Merge/escalate potential duplicate
- Cancel and return to origin

Success returns to Customer 360 with a timeline event and updated Customer analytics.

## 5. KYC verification flow

1. Open KYC work queue or Customer 360.
2. Review identity, masked Aadhaar, evidence, duplicate signals, and consent.
3. Request audited reveal only when required.
4. Choose Verify, Fail, Request correction, or Manual approval according to permission.
5. Capture reason/evidence for non-standard outcome.
6. Confirm customer and consequence.
7. Record verification event and audit entry.
8. Notify owner/collector/customer as configured.

## 6. New Loan flow

Entry:

- Dashboard Quick Action
- Customer 360
- Loans pipeline
- Command palette

The staged wide drawer opens; no loan form is shown before the action.

Stages:

1. **Customer and exposure:** identity, KYC, current/previous loans, risk, existing obligations.
2. **Scheme and terms:** Daily 100-Day or Monthly EMI, principal, rate, tenure, start date, collector.
3. **Affordability:** income, expenses, cash flow, repayment capacity.
4. **Verification:** documents, visits, guarantor, references.
5. **Recommendation:** credit score, risk factors, proposed terms, deviations.
6. **Review:** schedule, total repayment, due pattern, policy, declarations.
7. **Submit:** draft, send for review, or permitted approval.

Branching:

- KYC incomplete → save draft and create KYC blocker.
- Duplicate active application → open/merge rather than create another.
- Policy deviation → mandatory reason and approval route.
- Affordability fails → decline/rework recommendation; no silent override.
- Offline → loan application can draft locally only where policy permits; submission waits for server.

## 7. Loan approval and disbursement flow

1. Approver opens queue item.
2. Review requested/recommended amount, customer exposure, affordability, risk, credit score, KYC, guarantor, documents, visits, and deviations.
3. View prior decisions and policy version.
4. Approve, Approve with conditions, Return, Reject, or Escalate.
5. Capture reason/conditions.
6. Confirm decision and financial impact.
7. Approved application moves to documentation.
8. Documentation checklist completes.
9. Disbursement maker enters mode/account/reference/effective date.
10. Checker verifies and authorizes when policy requires.
11. Server posts disbursement and schedule atomically.
12. Receipt/agreement and timeline events become available.

Failure must state whether the loan was created and whether funds were disbursed.

## 8. New Payment flow

Entry:

- Dashboard Quick Action
- Customer 360
- Loan 360
- Collection route
- Collections workbench

Known account drawer:

1. Confirm customer photograph/name, loan, due, outstanding, and collector.
2. Enter amount and payment mode.
3. Show allocation: principal, interest, charges, advance/excess where applicable.
4. Validate duplicate/time/amount/mode/reference.
5. Confirm exact amount, account, allocation, effective date, and mode.
6. Server posts transaction atomically.
7. Show confirmed receipt number, timestamp, allocation, balance, and delivery actions.
8. Update Customer 360, Loan 360, Collections, Dashboard, report snapshots, timeline, and audit.

Unknown/multiple account:

`Search customer → Select loan(s) → Allocate → Review → Confirm → Receipt`

Failure language:

- “Payment was not posted. No money was recorded.”
- “Payment posted, but receipt delivery failed.”
- “Payment status is uncertain. Do not retry until verification completes.”

## 9. Payment reversal flow

1. Open payment/receipt Quick View.
2. Verify payment status, reconciliation, close period, and downstream impact.
3. Request reversal with reason and evidence.
4. Approval route based on amount, age, and close state.
5. Approver reviews original payment and impact.
6. Server posts reversal as a linked immutable transaction.
7. Balances, schedules, reconciliation, receipt state, timeline, and audit update.
8. Original record remains visible as Reversed; it is never deleted.

## 10. Daily collection flow

1. Manager opens Collection Control Room.
2. System calculates demand and assigns route/account queue.
3. Collector opens mobile route and confirms sync/readiness.
4. For each account: collect, call, message, record promise, record visit, or mark exception.
5. Payments generate receipts and update progress.
6. Collector reviews route completion and cash/digital totals.
7. Collector initiates cash handover.
8. Accountant receives and counts cash, verifies receipts, and records variance.
9. Manager resolves exceptions.
10. Route and day status close with immutable reference.

## 11. Promise, follow-up, and reminder flow

1. From Customer 360, route, or arrears queue, choose Add Follow-up/Promise/Reminder.
2. Set purpose, related loan, owner, channel, due date/time, priority, expected outcome.
3. Save creates timeline, calendar, notification, and work-queue entries.
4. Owner completes, snoozes, reassigns, or marks missed.
5. Completion captures outcome and optional next action.
6. Broken promise updates risk/delinquency signals and escalation.

## 12. Delinquency and recovery flow

1. System evaluates schedule, DPD, promises, payments, and policy.
2. Account enters configured ageing bucket and arrears queue.
3. Manager assigns owner/strategy.
4. Collector contacts or visits customer.
5. Record outcome: Paid, Promise, No contact, Dispute, Hardship, Escalate.
6. Promise due date creates reminders.
7. Broken promise increases priority and records a timeline event.
8. Restructure, waiver, legal escalation, or write-off follows approval policy.
9. Recovery payment updates DPD, health, risk, and work queue.

## 13. Communication flow

1. Choose Call, SMS, or WhatsApp from customer context.
2. Confirm contact, consent, preferred language, and permitted template/channel.
3. Send/initiate communication through configured service.
4. Capture direction, provider reference, delivery/read state, outcome, and related loan.
5. Optionally create follow-up/reminder.
6. Communication Timeline and Master Timeline update.

Failed delivery is shown as failed, not as sent. Direct device handoff and server messaging are explicitly distinguished.

## 14. Field visit and GPS flow

1. Collector opens scheduled visit/customer.
2. App requests location permission with purpose.
3. Capture source, coordinates, accuracy, timestamp, and device identity.
4. Record visit purpose, customer/contact result, notes, photographs/attachments, and next action.
5. User reviews location accuracy and evidence.
6. Save locally if offline; sync later with conflict protection.
7. Customer Map, Visit History, Timeline, and route status update.

## 15. Cash reconciliation and day-close flow

1. System establishes opening balance.
2. Aggregate collector cash, digital payments, deposits, expenses, and adjustments.
3. Accountant records physical cash and bank/deposit references.
4. System calculates expected close and variance.
5. Resolve matching issues, duplicates, unposted receipts, and handover differences.
6. Variance above policy threshold requires reason and approval.
7. Run close checks.
8. Confirm close summary and effective business date.
9. Server locks the period and creates close reference/report.
10. Reopening requires separate high-authority approval and audit.

## 16. Report flow

1. Select report from catalogue/saved view.
2. Set parameters and scope.
3. Generate immutable report snapshot.
4. Review designed Preview.
5. Generate actual PDF, Excel, or CSV artifact; or Print dedicated layout.
6. Share secured artifact or Email via configured service.
7. Track generation/delivery in Export History.
8. Revoke share or regenerate a new snapshot when needed.

No button is visible as functional until its service is available.

## 17. Audit investigation flow

1. Search/filter actor, entity, action, date, source, result, or correlation ID.
2. Open Quick View.
3. Review immutable event, before/after, reason, source/IP/device, and linked events.
4. Navigate to related object according to permission.
5. Export/share only through sensitive audit-report policy.
6. Audit investigation itself is logged when policy requires.

## 18. Settings change flow

1. Open configuration page and review current value/dependencies.
2. Choose Edit.
3. Enter proposed change and effective date.
4. System previews affected products, schedules, users, or reports.
5. Capture reason.
6. Submit directly or to approval based on consequence.
7. On effective date, configuration version activates.
8. Prior version remains in history and audit.

## 19. Global search flow

1. Open command palette.
2. Type customer, phone, Aadhaar suffix, loan, receipt, payment, report, or destination.
3. Results group by object with disambiguating context.
4. Select result to open full record; use Quick View when invoked explicitly.
5. Search respects area and field-level permissions.
6. Sensitive search/reveal events are audited where required.

## 20. Cross-cutting recovery flow

For every mutation:

1. Assign client request/correlation ID.
2. Prevent accidental double submit.
3. Distinguish validation, permission, conflict, network, server, and uncertain-outcome errors.
4. Preserve user input when safe.
5. Offer retry only when idempotent/safe.
6. Provide durable reference for support.
7. Update UI only from confirmed state.
8. Record audit event for success and security-relevant failure.

## 21. UX acceptance checklist

- Entry point is explicit and permission-aware.
- User understands context before acting.
- Long tasks save/resume.
- Consequence is reviewed before financial confirmation.
- Success produces evidence/reference.
- Failure states whether data/money moved.
- Originating context is restored.
- Related modules update consistently.
- Mobile, offline, Tamil, accessibility, reduced-motion, and conflict paths are covered.
