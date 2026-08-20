# Sri Sakthi Thirumurugan Finance - Money Lending Management System

Money-lending operations platform using React, FastAPI, and MongoDB. It supports a convenient demo mode and a fail-closed production mode.

## Included Features

- JWT login with seeded roles: Owner, Manager, Collector, Accountant
- Aadhaar AES-256-GCM encryption at rest, SHA-256 duplicate lookup, masked UI display
- Customer registration and existing Aadhaar verification acknowledgement flow
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
