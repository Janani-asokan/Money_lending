# Sri Sakthi Thirumurugan Finance - FINAL build (all 10 client items)

Only these 3 files differ from your original project (everything else is identical):
- server/main.py
- client/src/main.jsx
- client/src/styles.css
To update your real project, copy just these 3 files over the same paths (do not copy any .env file), then rebuild/redeploy.
Old -> new code for every step is in /patches. Full list of what changed: CHANGES.md

## Run on Windows (demo mode - in-memory data, never touches your real database)
Unzip into a NEW empty folder. Open two PowerShell windows.
Window 1 (backend):
  cd server
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  copy .env.example .env
  uvicorn main:app --reload --port 8000
Window 2 (frontend) - starting from the main money_lending folder:
  cd client
  npm install
  copy .env.example .env
  npm run dev
Open http://localhost:5173   Login: owner / owner123

## Test steps
1  Flexible interest rate - Loans > Loan disbursement: "Monthly interest %" is editable (default 2.14). Change to 3, press
   Preview: note shows "Monthly rate 3%". 0 or 15 shows "Monthly interest rate must be between 0.01% and 10%".
2  Auto-close - pay a loan's full balance in Collections: View loan shows Closed and a "Loan Closed" history entry; it leaves the
   Collections list. Existing zero-balance loans are closed when the server starts.
3  Payment confirmation - Collections: "Save payment" opens "Are you sure you want to record this payment?". Cancel saves nothing.
4  Customer selection in Loans - Loans > Loan disbursement: type 3+ letters of a name or 4+ digits of a mobile; the same
   "Existing customer found" list as Customer onboarding appears; pick one -> "Selected: ...". Nothing is pre-selected.
5  Registry approval - Customers: register a customer in "Manual registration" (stays Pending). In Customer registry press
   "Pending approval (n)" to see only pending ones; press the highlighted Approve on the row - only that row updates
   (it leaves the Pending list). Pending / Fail buttons still work.
6  Area grouping - Customer registry: use "All areas" (pick a code), "Sort by area code", "Group by area code" (header row per area
   with customer count).
7  Tax on fee / Moratorium - Loans > "Optional charges and schedule settings" now shows only Processing fee, First due date and
   Late charge. Press Preview: tax on fee is 0 and there is no moratorium. Old loans still show their saved values.
8  Late charge for defaulters only - create a loan (approved customer) with First due date 45 days in the past and Late charge 50.
   Loans > Loan book > View loan: note "Defaulter - 45 days overdue" and button "Apply late charge for instalment 1".
   Press it: balance rises by 50 and a Penalty entry appears in servicing history; the button moves to instalment 2.
   A loan that is less than 30 days overdue shows the rule message and no button (the server also refuses it).
   Change the 30-day rule in ONE place: LATE_CHARGE_DEFAULTER_DAYS in server/main.py (or the environment variable).
9  Pre-closure removed - no "Pre-closure charge %" field, no "Check closure amount" / "Close loan now" buttons (Loans > Controlled loan
   servicing > Part-payment only has Post part-payment). GET /api/loans/<id>/preclosure-quote now returns 404.
10 View Loan quick actions - Loan book > View loan > "Quick actions":
   - Collect payment: amount is pre-filled with the instalment; Review -> confirm popup -> balance drops, receipt opens, history row Type "Collection".
   - Prepayment: enter an amount below the balance (e.g. 1000); confirm -> balance and "Remaining installments" drop at once, history row Type "Prepayment".
     An amount equal to the full balance is refused ("Use Close account").
   - Close account: enter reason, type the loan ID, tick the box, Confirm -> status Closed, final receipt shown, history shows "Loan Closed".
   (Managers must also enter an owner approval reference to close.)
