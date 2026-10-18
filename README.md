
Demo - https://money-lending-app.onrender.com/




# Sri Sakthi Thirumurugan Finance - Money Lending Management System

Money-lending operations platform using React, FastAPI, and MongoDB. It supports a convenient demo mode and a fail-closed production mode.

## Included Features

- JWT login with seeded roles: Owner, Manager, Collector, Accountant
- Aadhaar AES-256-GCM encryption at rest, SHA-256 duplicate lookup, masked UI display
- Customer registration and existing Aadhaar verification acknowledgement flow
- Free customer mobile verification by SMS OTP (sent from your own Android phone)
- Loan disbursement with Daily 100-Day and Monthly EMI schemes
- Server-side timestamped collection entry with payment receipts
- Area-wise dashboard for KUN, SLM, NMK, ERD
- AI-style customer risk scoring
- Overdue alert panel for Day 90, 95, 100, 130+ and monthly EMI grace
- Universal search and filters
- Customer ledger, daily collection, monthly cash flow, and annual report views
- Audit log for login, customer, loan, payment, report, backup, Aadhaar unmask actions
- Manual backup log and new area settings
- Dark/light theme toggle and English/Tamil language toggle
- Seed data: 20 customers, 15 loans, payments, overdue records
- MongoDB support with automatic in-memory fallback for easy demo startup

## Demo Accounts

| Role | Username | Password |
| --- | --- | --- |
| Owner | `owner` | `owner123` |
| Manager | `manager` | `manager123` |
| Collector | `collector` | `collector123` |
| Accountant | `accountant` | `accountant123` |

## Run Locally

Open two terminals from this project folder.

### 1. Backend

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

MongoDB is optional for demo. If MongoDB is running at `mongodb://localhost:27017`, the API uses it. If not, it automatically runs with seeded in-memory data.

### 2. Frontend

```powershell
cd client
npm install
copy .env.example .env
npm run dev
```

Open the Vite URL, usually:

```text
http://localhost:5173
```

## Production Notes

The complete production stack includes React, FastAPI, MongoDB and an Nginx gateway with health checks, restart policies and friendly maintenance responses. Follow [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for production, staging, monitoring and restart-drill instructions.

Set strong values in `server/.env` before real deployment. Production startup intentionally fails with demo secrets, memory fallback, wildcard CORS, or a weak initial password:

```text
APP_ENV=production
APP_SECRET_KEY=use-a-long-cryptographically-random-secret
AADHAAR_AES_KEY=change-this-32-byte-key-12345678
MONGO_URL=mongodb://app_user:password@database:27017/?authSource=admin
MONGO_DB=money_lending_production
MONGO_ENABLED=true
ALLOW_MEMORY_FALLBACK=false
CORS_ORIGINS=https://finance.example.com
INITIAL_ADMIN_USERNAME=owner
INITIAL_ADMIN_PASSWORD=use-a-unique-password-of-12-or-more-characters
```

Remove `INITIAL_ADMIN_PASSWORD` after the first startup. Use HTTPS, encrypted storage, least-privilege database credentials, and automated off-site backups with a tested restore procedure.

## Free SMS OTP (customer mobile verification)

Owners and Managers can verify a customer's mobile number with a 6-digit SMS OTP from **Customer 360** or right after registering a new customer. Verified customers show "Mobile verified"; editing the mobile number clears the verification.

Paid SMS APIs (MSG91, Twilio, Fast2SMS, ...) charge per message and need DLT registration in India. To keep this **free**, the app sends SMS through your own Android phone using the open-source [SMS Gateway for Android](https://sms-gate.app) app — each OTP is a normal SMS from your SIM, covered by your plan's free SMS (most Indian prepaid plans include 100 SMS/day).

**Quickest setup:** after step 2 below, double-click `setup-sms.bat` (or run `python scripts/setup_sms.py`). It checks your gateway login, confirms the phone is online, sends you a test OTP and saves the settings into `server/.env` for you.

1. Install **SMS Gateway for Android** on a spare Android phone with an active SIM (Play Store or [GitHub releases](https://github.com/capcom6/android-sms-gateway/releases)) and allow SMS permission.
2. Open the app, enable **Cloud server**, tap **Online**, and note the username and password it shows.
   (Or enable **Local server** if the phone and backend are on the same Wi-Fi; the URL is then `http://<phone-ip>:8080/message`.)
3. In `server/.env` set:

```text
SMS_PROVIDER=android_gateway
SMS_GATEWAY_URL=https://api.sms-gate.app/3rdparty/v1/message
SMS_GATEWAY_USERNAME=<from the app>
SMS_GATEWAY_PASSWORD=<from the app>
```

4. Restart the backend. Keep the phone charged and connected.

### Live server (Render or any host)

`server/.env` is **never uploaded** with your code (git ignores it because it holds secrets). That is why SMS can work on your PC but not on the live site. Add the same values in your hosting dashboard (Render: backend service → **Environment**):

```text
SMS_PROVIDER=android_gateway
SMS_GATEWAY_URL=https://api.sms-gate.app/3rdparty/v1/message
SMS_GATEWAY_USERNAME=<Cloud server username from the app>
SMS_GATEWAY_PASSWORD=<Cloud server password from the app>
```

- Use the app's **Cloud server** credentials and the `api.sms-gate.app` URL. A **Local server** address such as `http://192.168.x.x:8080` only works from your own Wi-Fi; an online server can never reach it.
- With Docker (`compose.production.yml`) put these in `server/.env` on the server; do not add them to the compose `environment:` list (that replaces them with blanks).
- Then open **Settings → SMS OTP setup** on the live site. It checks every setting, logs in to the gateway, shows whether your phone is online, and has a **Send test SMS** button with delivery status.
- On the live (production) server OTPs are never shown on screen. If SMS is not set up, sending an OTP shows what is missing instead. To deliberately allow on-screen demo OTPs there, set `SMS_ALLOW_DEMO_OTP=true`.

For local testing without any phone, leave `SMS_PROVIDER=console` (the default outside production): the OTP is printed in the server log and shown on screen as "Demo mode OTP". Console mode is refused in production.

Security: OTPs are random 6-digit codes stored only as HMAC hashes, expire after 5 minutes, lock after 3 wrong attempts, can be resent after 30 seconds, and are limited to 10 per customer per day. Every send/verify is written to the audit log. Set `REQUIRE_MOBILE_VERIFIED_DISBURSAL=true` to block loan disbursal until the mobile is verified.

API: `GET /api/sms/status`, `POST /api/customers/{customer_id}/mobile-otp/send`, `POST /api/customers/{customer_id}/mobile-otp/verify` (`{"otp_id": "...", "otp": "123456"}`).

## Go-live gate

- Deploy the frontend and API behind HTTPS, preferably on one trusted domain.
- Set `APP_ENV=production`; never enable memory fallback for live records.
- Change the initial owner password and create named accounts for every staff member.
- Configure daily encrypted MongoDB backups to separate storage and perform a restore drill.
- Verify opening balances and interest calculations with the business owner before importing records.
- Test onboarding, approval, disbursement, payment retry, receipts, reports, and every role on staging.
- Establish retention, consent, Aadhaar access, and incident procedures with a qualified Indian compliance adviser.
- Monitor `/api/health`, database capacity, errors, TLS certificate expiry, and backup completion.

The in-app **Manual backup** action is an audit acknowledgement, not a database dump. It must not be treated as the production backup system.

## Persistent production database

The production database definition is in `compose.production.yml`. It provides an authenticated MongoDB 7 instance, a durable named data volume, a least-privilege application user, health checks, and a single-node replica set. A single-node replica supports transaction development but is **not high availability**; a live deployment should use a managed multi-node MongoDB replica set across failure zones.

1. Install and start Docker Desktop.
2. Copy `.env.production.example` to `.env.production`.
3. Replace every `CHANGE_ME` value with independently generated secrets.
4. Run `powershell -ExecutionPolicy Bypass -File .\scripts\start-production-db.ps1`.
5. Copy the backend settings from `.env.production` into `server/.env` and set a strong `INITIAL_ADMIN_PASSWORD` for the first startup.
6. Start the API and verify `/api/health` reports `"database":"mongodb"` and `"environment":"production"`.

The MongoDB port is bound only to `127.0.0.1`. The application account has `readWrite` access only to the lending database; the root account must never be placed in `server/.env`. Keep the Docker data directory on an encrypted disk. For stronger at-rest encryption, use a managed MongoDB service with encryption and customer-managed keys.

Live writes use MongoDB majority acknowledgement, journaling, and retryable writes. The application creates no TTL indexes and exposes no delete endpoint for customers, loans, payments, or audit records, so records are not automatically expired or removable by normal staff workflows. Any future deletion workflow must be owner-only, require a reason and confirmation, and retain an auditable soft-deleted record.
