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

# Step 11 - SMS OTP for customer registration (own OTP service + MSG91 gateway) - DONE
Files changed in this round: server/main.py, client/src/main.jsx, client/src/styles.css, server/.env.example, .env.production.example
(patch: patches/step-11-sms-otp-registration.patch)

- main.py: OTP service (6-digit OTP, 5-minute expiry, 3 wrong tries then locked, 3 resends, 30-second gap, 8 SMS per number per hour,
  a newer OTP cancels the older one). The OTP is stored only as a keyed hash tied to the OTP id and mobile number and never
  appears in the audit log. New collection `sms_otps` (number, sent/verified time, who did it, gateway message ids, status).
  Routes: GET /api/otp/sms/status, POST /api/otp/sms/send, /resend, /verify (owner and manager only).
  POST /api/customers now requires a verified, unused OTP for that exact mobile number (single use, used within 15 minutes);
  it is consumed in the same transaction that creates the customer. The customer record keeps mobile_verified_at, mobile_otp_id.
  MSG91 sending lives in one function (_msg91_send_blocking). With no gateway configured, development mode prints the OTP in the
  API window and shows it on screen; production refuses development mode.
- main.jsx (Customers > Register a customer, both Manual and Aadhaar modes): "Mobile verification by SMS OTP" box:
  Send OTP by SMS, enter code, Verify, Resend with countdown. "Create pending profile / Register" is blocked until verified.
  Changing the mobile number clears the verification.
- Settings: SMS_OTP_REQUIRED, SMS_PROVIDER, MSG91_AUTH_KEY, MSG91_TEMPLATE_ID, SMS_OTP_HMAC_KEY (see server/.env.example).
- Not included (not requested): OTP at loan disbursement. A verified OTP only proves the customer received the code on that
  number; customers stay "Pending Verification" until approved, exactly as before.

## Step 11 update - works WITHOUT a paid SMS account
- When no gateway is configured (SMS_PROVIDER empty, no MSG91 key/template) the app uses ON-SCREEN mode: after "Send OTP by SMS" the 6-digit
  OTP is shown on screen to the staff member (and printed in the API log). All limits, single use, hashing and the "must verify before
  registering" rule still apply. This does not prove the customer's phone, because staff see the code. A banner says so.
- Real SMS is optional: set SMS_PROVIDER=msg91 + MSG91_AUTH_KEY + MSG91_TEMPLATE_ID. SMS_OTP_REQUIRED=false turns the OTP step off.

# Step 12 - OTP to the customer's phone without MSG91, adjustable EMI planner rate, new fonts
Files changed in this round: server/main.py, client/src/main.jsx, client/src/styles.css, client/index.html, server/.env.example, .env.production.example
(patch: patches/step-12-webhook-sms-emi-rate-fonts.patch)
- main.py: new generic SMS provider `SMS_PROVIDER=webhook` (SMS_WEBHOOK_URL / HEADERS / BODY / SMS_MESSAGE_TEMPLATE). The OTP SMS is sent by
  any HTTP SMS service, including a free Android-phone SMS gateway. Tested here against a real local HTTP server (request body, headers,
  message id, HTTP errors, bad settings). No provider = on-screen OTP, as before.
- Interest rate: allowed range for new loans is now 1% to 10% (was 0.01-10). MIN_MONTHLY_INTEREST_RATE in server/main.py.
- main.jsx: EMI Planner interest is adjustable (slider + typed value, 1% to 10%, default 2.14); the explanation and maximum tenure follow the rate.
  Loan disbursement rate field uses the same 1-10 range.
- Fonts: Plus Jakarta Sans (text) and Sora (titles) loaded from Google Fonts in client/index.html, applied in styles.css. System fonts are the fallback.

# Step 13 - Client round 2 (7 requirements)
Files changed in this round: server/main.py, client/src/main.jsx, client/src/styles.css (patch: patches/step-13-client-round-2.patch)

1. Loan auto-closes when the repayment reaches 0 - FIXED PROPERLY. Cause found: money was shown without paise, so a balance of Rs 0.01-0.49 appeared as "Rs 0"
   but was not 0 (example: Rs 10,000 weekly over 7 weeks has a last instalment of 1,428.58 while the regular instalment is 1,428.57).
   main.py: a balance below Rs 1 (AUTO_CLOSE_RESIDUAL_PAISE=99) is settled as a rounding entry (journal: Waiver and Correction Expense / Loans,
   recorded in the loan history as a "Rounding" write-off, fully balanced and audited) and the loan is closed. The loan list and details also self-heal
   any loan whose stored status is still Active, and the start-up sweep covers old loans. Collections: "Pay full balance" button and exact outstanding.
2. Search: loan IDs, customer names, "View loan" and "Open profile" now navigate to the Loans screen (View loan opens) or Customer 360.
3. Customer 360: every loan has View loan / clickable loan ID that opens the loan.
4. EMI calculator rate is flexible (slider + typed, 1% to 10%) - from the previous round, kept.
5. Cash-in-hand rounding is manual: amounts now show paise exactly (no hidden rounding). Loan disbursement and the EMI planner have a "Manual round-off"
   box (type an amount from -100 to +100, or press Nearest 1 / Down 1 / Up 1 / Nearest 10). Final cash in hand = exact amount + your round-off.
   main.py: LoanIn.round_off adjusts the cash handed over; the difference is booked to "Waiver and Correction Expense" so the journal stays balanced;
   stored on the loan as round_off and shown on View loan.
6. OTP area is clear: registration shows a step-by-step box (Not verified / OTP sent / Verified), shows only the next action, and "Clear and start over".
   It clears itself after registration, when the mobile number changes, and after wrong/expired/locked codes. In Loan disbursement the Aadhaar OTP area and
   the customer field clear after a loan is created or when another customer is chosen.
7. Loan book filters: Search, Month (disbursed), Area, Amount from/to, Status, Plan, Collector, Clear filters, plus live totals (loans, sanctioned, collected, outstanding).

# Step 14 - Registration screen redesign, speed, font, OTP priority
Files changed in this round: server/main.py, client/src/main.jsx, client/src/styles.css, client/index.html (patch: patches/step-14-registration-ui-speed-font.patch)
- Registration form rebuilt as clean, aligned sections (Customer details, Mobile verification, Aadhaar and consent, Address and guarantor) with one footer
  (pending-approval note + Register). No more scattered boxes; checkbox row fixed; stacks to one column on phones.
- OTP first: a "Send OTP" button sits right beside the Mobile number box; the code card is directly below it (code, Verify, Resend, Clear). Real SMS needs an SMS
  service (see guide); until then the code is shown on screen after Send OTP.
- Button reads just "Register" (both Aadhaar and Manual). "Consent reference" field removed; the consent tick-box and purpose stay (server records an automatic
  reference CONSENT-<customer id>).
- Page gap fixed: on wide screens the Customers page is now: editor (full width when editing), registration form on the left and the customer registry on the right.
- Speed: (1) Customers page no longer reloads four endpoints on every key typed in search and no longer loads everything twice when opened; screens now load their data
  in parallel (Customers, Customer 360, Loans). (2) Server: loan list, dashboard, search and reports fetch payments/adjustments/write-offs/schedules in one batch instead
  of five queries per loan (tested: 160 queries for 40 loans became 5, identical balances).
- Font: Poppins (bold, open letter spacing like the reference picture) for the whole app; negative letter-spacing removed. Loaded from Google Fonts in index.html.
