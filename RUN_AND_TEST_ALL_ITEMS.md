# Sri Sakthi Thirumurugan Finance - FINAL build

Files that differ from your original project (everything else is identical):
- server/main.py
- client/src/main.jsx
- client/src/styles.css
- client/index.html (font links)
- server/.env.example and .env.production.example (new OTP/SMS settings only)
To update your real project copy these files over the same paths. NEVER overwrite your real .env or .env.production - only add the new
lines from the .example files to your own .env. Old -> new code for every step is in /patches. See CHANGES.md.

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
(The new fonts load from Google Fonts, so the computer needs internet; offline it falls back to system fonts.)

## Why the OTP did not arrive on the phone - and how to make it arrive
The app can only send a real SMS through an SMS service. With no service configured (the default) it runs in ON-SCREEN mode: the OTP is
shown on the screen after "Send OTP by SMS" and nothing is sent to the phone. That is expected, not a fault.
To get the OTP on the customer's phone you need ONE of these (the app supports both):
A) A free Android-phone SMS gateway (your own phone + SIM sends the SMS): install an SMS-gateway app on an Android phone, create its (free) API
   key, then set in server/.env (or the Render environment settings) the values from that app's documentation:
     SMS_PROVIDER=webhook
     SMS_WEBHOOK_URL=<send-SMS URL from the gateway's documentation>
     SMS_WEBHOOK_HEADERS={"x-api-key":"<your key>"}
     SMS_WEBHOOK_BODY={"recipients":["{mobile_e164}"],"message":"{message}"}
   {message} is replaced by the OTP text and {mobile_e164} by +91 and the number. Use the exact field names your gateway documents.
   The phone must stay switched on with internet and SMS balance. I tested the webhook sender against a local test server, not against any
   specific gateway - test with your own number first.
B) A paid SMS provider such as MSG91: SMS_PROVIDER=msg91, MSG91_AUTH_KEY, MSG91_TEMPLATE_ID.
Restart the backend after changing server/.env. The on-screen OTP switches off automatically once real SMS is configured.
Set SMS_OTP_REQUIRED=false if you want no OTP step at all.

## Test the new registration screen, OTP, speed and font (latest round)
1. Customers page: the registration form is on the left in clean sections (Customer details, Mobile verification, Address and guarantor; Aadhaar mode adds Aadhaar and consent) and
   the customer registry is on the right. The button at the bottom just says "Register". There is no "Consent reference" box.
2. OTP first: type the 10-digit mobile number. A "Send OTP" button appears right beside the number. Press it: a 6-digit code appears in the card under "Mobile verification"
   (no SMS service is connected, so it is shown on screen). Type it and press Verify; "Register" then works. A wrong code shows "Incorrect OTP. 2 attempts remaining"; after 3 the
   OTP locks; Resend waits 30 seconds; the code expires in 5 minutes and works once. "Clear and start over" resets the card.
3. Speed: open Customers, Loans and Customer 360 - they now load their data in parallel, and typing in the customer search only refreshes the list. The server fetches all
   loan balances in a few queries instead of five per loan, so the Loan book, dashboard and search are much faster on a real database.
4. Font: the whole app uses Poppins (refresh with Ctrl+F5; it loads from Google Fonts so the computer needs internet).
5. Real SMS to the customer's phone needs an SMS service (see "Why the OTP did not arrive on the phone" above); the on-screen code works without any account.

## Test the 7 new client requirements
1. Loan closes at 0 - Loans > Loan disbursement: create a Weekly loan, principal 10000, period 7. In Collections pay 1428.57 six times (use the loan list), then on the
   7th payment type 1428.57 again (instead of the full 1428.58): 1 paisa is left. The loan becomes Closed by itself ("Repayment complete (balance below Rs 1 is
   rounding) - closed automatically"); View loan > Servicing history shows a "Rounding" entry and Yet to pay is 0. Paying the exact balance (use "Pay full balance")
   also closes it. Old loans that already show Rs 0 are closed when you open Loans / Collections.
2. Search - Search page: type a customer name. In Loans press the loan ID or "View loan": the Loans page opens with that loan's View loan window. In Customers press the
   name or "Open profile": Customer 360 opens for that customer.
3. Customer 360 - open a customer; in "Complete loan history" press a loan ID or "View loan": the Loans page opens with the View loan window.
4. EMI calculator - EMI Planner: slider and typed rate 1 to 10 (try 1, 1.5, 2.14, 3.2); the numbers change with the rate.
5. Manual rounding - amounts show exact paise (for example Rs 34,781.76). EMI Planner: "Cash in hand: manual round-off" - press Nearest Rs 1 and see "Final cash in hand" change; or
   type your own value. Loans > Loan disbursement: press Preview, then use the round-off box (Nearest 1 / Down 1 / Up 1 / Nearest 10 / typed value). Create the loan:
   View loan shows "Cash handed over (incl. manual round-off)". Nothing is rounded unless you choose it.
6. OTP area - Customers > Register a customer: the box shows Not verified > OTP sent > Verified with one clear next action, and "Clear and start over". It clears after
   registering, when you change the mobile number, and after a wrong/expired/locked code. In Loans, after creating a loan the customer field and any OTP entries are cleared.
7. Loan book filters - Loans > Loan book: Search, Month, Area, Amount from/to, Status, Plan, Collector. The line under the filters shows how many loans match with the
   totals (sanctioned, collected, outstanding). "Clear filters" resets everything.

## Test the interest rate changes
- EMI Planner: "Monthly interest" now has a slider AND a box to type the rate (1% to 10%, starts at 2.14). Try 1, 1.5, 3.2: the interest deducted,
  cash handed over and maximum tenure change with the rate. Typing 0.5 shows "Enter a rate between 1% and 10%".
- Loans > Loan disbursement: "Monthly interest %" accepts 1 to 10 (for example 1, 1.5, 2.14, 3.2); 0.5 or 15 is refused.

## Test steps for items 1-10 (unchanged)
1  Loans > Loan disbursement: rate editable.   2  Pay a loan's full balance in Collections: View loan shows Closed.
3  Collections: "Save payment" opens the "Are you sure?" popup.   4  Loans: type 3+ letters or 4+ digits -> "Existing customer found" list.
5  Customer registry: "Pending approval (n)" filter and one-click Approve.   6  Registry: area filter, Sort/Group by area code.
7  Disbursement has no Tax on fee / Moratorium.   8  Late charge: loan with First due date 45 days ago + Late charge 50 -> View loan shows
   Defaulter + "Apply late charge" (rule LATE_CHARGE_DEFAULTER_DAYS, default 30).   9  No pre-closure field/buttons.
10 View loan > Quick actions: Collect payment, Prepayment, Close account.
