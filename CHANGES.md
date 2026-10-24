# Change log (cumulative) - Sri Sakthi Thirumurugan Finance

Files changed so far: `server/main.py`, `client/src/main.jsx`
Originals are kept untouched in `original/`. One `.patch` per step is in `patches/`.

## Step 1 - Flexible interest rate (at loan creation only) - DONE
- server/main.py: new constants DEFAULT/MIN/MAX_MONTHLY_INTEREST_RATE (min 0.01, max 10, env-overridable) and
  `validate_new_loan_rate()`; replaced the hard "must be 2.14%" check in `loan_quote` and `create_loan`.
- client/src/main.jsx (Loans form): "Monthly interest %" is editable (default 2.14); quote note shows the entered rate.
- Not changed: existing loans, EMI Planner screen (still fixed 2.14), legacy-loan migration.

## Step 2 - Zero-balance loans auto-marked "Closed" - DONE
- server/main.py only (no frontend change).
- New `sync_loan_status()` : if a loan's balance is 0 its stored status becomes "Closed" (closed_at, closed_by "System",
  closure_reason), plus a "Loan Closed" event in loan history and an audit entry. "Written Off" loans are never touched.
- Called automatically after: payment saved (`create_payment`), adjustment posted (`loan_adjustment`),
  approved reversal (`decide_reversal`, which can also reopen a Closed loan to Active when the balance is outstanding again).
- New `auto_close_zero_balance_loans()` runs at every server start (both memory and MongoDB) and closes existing loans that
  already have balance 0. It only closes (never reopens), is idempotent, and never blocks startup. No money, ledger or
  schedule rows are changed.

## Step 3 - Confirmation before recording a payment ("Are you sure?" popup) - DONE
- client/src/main.jsx only (no backend change).
- Collections screen: pressing "Save payment and print receipt" no longer saves. It opens a popup (`PaymentConfirmModal`)
  showing customer, loan, amount, mode, UPI reference and the balance after payment. The payment is sent to the
  server only when the user presses "Confirm and save payment"; Cancel / clicking outside saves nothing.
- The old save code moved into `confirmAndSave()`. The idempotency request id is now created when the popup opens, so a
  retry from the same popup can never create a duplicate payment.
- `PaymentConfirmModal` is reusable; Step 10 (instant collection on View Loan) will use it too.

## Step 4 - Customer selection in Loan works like Customer Onboarding - DONE
- client/src/main.jsx and client/src/styles.css (1 new CSS rule: `.customer-picker`). No backend change.
- New shared code: `findCustomerMatches()` (same rule as onboarding: name 3+ letters or mobile 4+ digits, top 4),
  `CustomerSuggestions` (the "Existing customer found" list, markup identical to before) and `CustomerPicker`.
- Customer Onboarding now uses the shared `findCustomerMatches` + `CustomerSuggestions` (behaviour unchanged).
- Loan disbursement: the ID-only dropdown is replaced by `CustomerPicker` (Name + Mobile fields, suggestion list, a
  "Selected: name - ID - mobile - status" line). The first customer is no longer auto-selected; "Create loan",
  "Preview" and "Send Aadhaar-linked OTP" stay disabled until a customer is chosen.

## Hotfix to Step 2 - sweep now runs in the background
- server/main.py: the zero-balance sweep is started with `schedule_auto_close_sweep()` (asyncio background task) instead of
  being awaited during start-up, so a slow or failing sweep can never delay the API from coming up.

# Items 5 to 10 (your list: registry approval, area grouping, remove tax/moratorium, late charge, pre-closure, View Loan quick actions)
Files changed in this round: server/main.py, client/src/main.jsx, client/src/styles.css (patch: patches/step-05-to-10-combined.patch)

## Item 5 - Easier customer approval (Customers > Customer registry) - DONE
- main.jsx: "All (n) / Pending approval (n)" filter; Approve is now the highlighted one-click button on pending/failed rows
  (disabled for already approved or Aadhaar-verified customers); approving updates only that row instead of reloading
  4 endpoints. Pending / Fail buttons unchanged. No backend change.

## Item 6 - Area code grouping in the customer search - DONE
- main.jsx: area filter dropdown, "Sort by area code" and "Group by area code" (group header rows with counts). Uses the
  existing customer area code (KUN/SLM/NMK/ERD); no new field. styles.css: registry-controls + group-row styles.

## Item 7 - Tax on fee and Moratorium removed from loan disbursement - DONE
- main.jsx: both inputs removed from the disbursement form (form sends 0).
- main.py: new loans always get tax_rate 0, moratorium 0 (forced in loan_quote and create_loan; LoanIn default tax 0), so the
  calculation has no tax or moratorium. Old loans/data are untouched and still display their stored values.

## Item 8 - Late charge only for defaulters - DONE
- main.py: ONE configurable rule `LATE_CHARGE_DEFAULTER_DAYS` (default 30, env-overridable): a defaulter is a loan whose oldest
  unpaid instalment is at least that many days past due. `late_charge_status()` decides; the late-fee endpoint now refuses
  non-defaulters. Loan details return the status.
- main.jsx (View Loan): shows "Defaulter - N days overdue" and an owner/manager button "Apply late charge for instalment n"
  (only for defaulters); non-defaulters see the rule. The "Late charge" amount field at disbursement is kept.

## Item 9 - Pre-closure removed - DONE
- main.jsx: "Pre-closure charge %" field, "Check closure amount" and "Close loan now" buttons removed from the UI.
- main.py: route GET /api/loans/{id}/preclosure-quote removed; closing a loan no longer adds a pre-closure charge.
  Historical data and old closure receipts are untouched.

## Item 10 - View Loan quick actions - DONE
- main.jsx (View Loan > Quick actions): Collect payment, Prepayment, Close account.
  Collection and Prepayment use the "Are you sure?" popup from Step 3, then POST /api/payments (balance updates at once,
  receipt shown, row added to Repayment history with a new Type column). Close account opens the final-settlement form
  (reason, typed loan ID, owner approval reference for managers), sets status Closed and refreshes the loan.
- main.py: PaymentIn.payment_type (Collection or Prepayment). A prepayment must be less than the outstanding balance
  (full settlement uses Close account). Prepayment = extra payment ahead of schedule: balance drops immediately and the
  remaining instalments are cleared in order (earliest first); instalment amounts do not change.

## Round 3 - client feedback items + full application audit - DONE
Files: server/main.py, client/src/main.jsx, client/src/styles.css

### Requested items
1. **Loans close at zero** - loans already closed automatically when the balance reached 0, but older (pre-versioned)
   loans had no stored schedule, so they showed "0 instalments remaining / Completed" while money was still due. Their
   schedule is now derived from the contract terms (`repayment_rows()`), so remaining instalments and next due date are
   correct, and a loan only shows 0 remaining when its balance is actually 0 (and is then Closed).
2. **Search opens the record** - customer names open Customer 360; a loan ID (or the whole row) opens the full loan
   record in place with Collect / Prepayment / Close account. Search runs as you type and shows counts.
3. **Customer 360** - its loans open the same loan record in place (shared `useLoanViewer`). The Dashboard's pending
   dues, area drill-down and "Needs attention" alerts open loans the same way.
4. **EMI planner** - interest rate is adjustable (slider + typed value, limits from the server: 0.01%-10%, default
   2.14%), loan amount and tenure can be typed, and Daily / Weekly / Monthly plans use the same formula as loan creation.
5. **Manual rounding of cash in hand** - nothing is rounded automatically any more (amounts show paise when present).
   At disbursement the owner can type the cash actually handed over (within +/- MAX_CASH_ROUNDING_RUPEES, default 100);
   the difference is absorbed in the upfront interest, the ledger stays balanced, and the loan record shows
   "Cash rounded by hand from Rs X". Daily cash closing shows the exact ledger cash and the live difference.
6. **OTP areas clear** - the Aadhaar and mobile OTP boxes close once verified and have a close (X) button; choosing a
   different customer on the loan form clears any OTP proof that belonged to the previous customer.
7. **Loan book filters** - month, area, plan, status, collector, min/max amount, text search and sorting, with live
   totals (sanctioned / paid / outstanding) and paging (25 rows, "Show more").

### Faults found and fixed during the audit
- Live (MongoDB) crashes: editing a customer, renaming an area, posting a penalty/waiver and previewing an interest
  rebate all returned "Internal Server Error".
- Demo (in-memory) crashes: part-payment, restructure and write-off only worked with MongoDB (new `atomic()` helper).
- Dashboard "Areas requiring collection" matched customers by area name instead of code; older loans were missing from
  "Pending dues"; reversed payments were counted in collection totals.
- Speed: list screens made several database queries per loan; they now bulk-load once per request
  (dashboard 185 ms -> 40 ms, loans 130 ms -> 25 ms on a local MongoDB; the gap grows with the loan book).
- Demo data: payments were dated in the future, overpaid loans, and duplicate receipt numbers crashed a fresh MongoDB start.
- Layout: full-width panels did not span the page (customer registry was squeezed into a narrow column with very tall
  rows); loan tables hid Status / View off-screen; loan-record quick-action buttons were nearly invisible; "Paid today"
  badges were unreadable; KPI tiles overflowed; messages never disappeared; consent checkbox and OTP boxes were cramped;
  loan tables become cards on phones; reports show Rs amounts and readable dates.


## Round 4 - Loan date, existing loans and OTP borrower acknowledgement - DONE
- **Loan date**: every loan has a date. New loans: today or up to NEW_LOAN_BACKDATE_DAYS (7) back; never in the future.
- **Existing loans** (money given before the app): tick "Existing loan", choose the original date (up to 5 years back),
  enter the amount already repaid and the date up to which it was repaid. The schedule starts from the original date,
  the balance is principal minus repaid, and the loan auto-closes if fully repaid. Accounting: no cash moves today -
  the outstanding amount is posted Dr Loan Principal Receivable / Cr Opening Balance Equity; the earlier repayments are
  stored as one "Opening balance" record (receipt OPN-<loan>) that is excluded from today's/monthly collection totals
  and cannot be reversed as a receipt.
- **Borrower acknowledgement by OTP**: "Send acknowledgement OTP" SMSes the loan's key facts (loan amount, cash given,
  instalment x count, first due date) and an OTP to the customer's registered mobile. Entering the OTP creates an
  acknowledgement number ACK-YYYYMMDD-NNNNNN tied to those exact terms; changing any amount needs a new OTP. The number
  is stored on the loan, shown on the loan record, the KFS and a printable acknowledgement, and can be used only once.
  LOAN_ACK_OTP=auto (default: required whenever SMS works), required, or off (typed reference instead).
- Customer picker: typing a new name/mobile clears the previous selection (prevented loans going to the wrong customer).

## Round 5 - Forgot password and show-password eye icon - DONE

- Eye icon on every password field (sign-in, change password, reset password).
- "Forgot password?" on the sign-in page: SMS OTP to the account's recovery mobile, then set a new password. Old sessions are revoked.
- Settings -> Password recovery mobile (verified by OTP). `OWNER_RECOVERY_MOBILE` env var as a fallback for the owner.
- Same reply for unknown usernames so accounts cannot be discovered; OTP 10 min, 5 attempts, single use; per-device and per-account rate limits.
