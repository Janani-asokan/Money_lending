from __future__ import annotations

import base64
import asyncio
import gzip
import hashlib
import hmac
import json
import os
import random
import secrets
import shutil
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen
from collections import defaultdict, deque
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from bson import json_util
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

load_dotenv()

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-change-me")
APP_ENV = os.getenv("APP_ENV", "development").lower()
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true" if APP_ENV == "production" else "false").lower() == "true"
ACCESS_COOKIE = "stf_access"
REFRESH_COOKIE = "stf_refresh"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "money_lending_demo")
ALLOW_MEMORY_FALLBACK = os.getenv("ALLOW_MEMORY_FALLBACK", "true").lower() == "true"
MONGO_ENABLED = os.getenv("MONGO_ENABLED", "true" if APP_ENV == "production" else "false").lower() == "true"
AADHAAR_KEY_RAW = os.getenv("AADHAAR_AES_KEY", "0123456789abcdef0123456789abcdef")
AADHAAR_AES_KEY = AADHAAR_KEY_RAW.encode()
AADHAAR_KEY_VERSION = os.getenv("AADHAAR_KEY_VERSION", "v1")
AADHAAR_KEY_PROVIDER = os.getenv("AADHAAR_KEY_PROVIDER", "environment")
AADHAAR_KEYRING: dict[str, bytes] = {AADHAAR_KEY_VERSION: AADHAAR_AES_KEY}
for key_item in [x for x in os.getenv("AADHAAR_AES_KEYS", "").split(",") if x.strip()]:
    version, separator, raw_key = key_item.partition(":")
    if separator: AADHAAR_KEYRING[version.strip()] = raw_key.encode()
AUDIT_HMAC_KEY = hashlib.sha256((os.getenv("AUDIT_HMAC_KEY") or APP_SECRET_KEY + ":audit-chain").encode()).digest()
AUDIT_ARCHIVE_DIR_RAW = os.getenv("AUDIT_ARCHIVE_DIR", "").strip()
AUDIT_ARCHIVE_DIR = Path(AUDIT_ARCHIVE_DIR_RAW).resolve() if AUDIT_ARCHIVE_DIR_RAW else None
STRICT_COMPLIANCE_MODE = os.getenv("STRICT_COMPLIANCE_MODE", "false").lower() == "true"
AADHAAR_AUTH_PROVIDER_URL = os.getenv("AADHAAR_AUTH_PROVIDER_URL", "").rstrip("/")
AADHAAR_AUTH_PROVIDER_KEY = os.getenv("AADHAAR_AUTH_PROVIDER_KEY", "")
AADHAAR_AUTH_PROVIDER_NAME = os.getenv("AADHAAR_AUTH_PROVIDER_NAME", "Authorized AUA/KUA provider")
REQUIRE_VERIFIED_DISBURSAL = os.getenv("REQUIRE_VERIFIED_DISBURSAL", "false").lower() == "true"
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()]
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(Path(__file__).resolve().parent.parent / "backups"))).resolve()
BACKUP_KEY_RAW = os.getenv("BACKUP_ENCRYPTION_KEY", "")
BACKUP_ENCRYPTION_KEY = BACKUP_KEY_RAW.encode()
OFFSITE_BACKUP_DIR_RAW = os.getenv("OFFSITE_BACKUP_DIR", "").strip()
OFFSITE_BACKUP_DIR = Path(OFFSITE_BACKUP_DIR_RAW).resolve() if OFFSITE_BACKUP_DIR_RAW else None
LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(title="Sri Sakthi Thirumurugan Finance API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PASSWORD_SCHEMES = ["bcrypt", "pbkdf2_sha256"] if APP_ENV == "production" else ["pbkdf2_sha256", "bcrypt"]
pwd_context = CryptContext(schemes=PASSWORD_SCHEMES, deprecated="auto", pbkdf2_sha256__rounds=29000)
mongo_client: Optional[AsyncIOMotorClient] = None
db = None
USE_MEMORY = True
STORE: dict[str, list[dict[str, Any]]] = {}
MEMORY_SEQUENCE_LOCK = asyncio.Lock()
SEQUENCE_RECONCILED: set[str] = set()

ROLES = {"owner": 4, "manager": 3, "accountant": 2, "collector": 1}
AREAS = [
    {"code": "KUN", "name": "Kundi"},
    {"code": "SLM", "name": "Salem"},
    {"code": "NMK", "name": "Namakkal"},
    {"code": "ERD", "name": "Erode"},
]
PAYMENT_MODES = ["Cash", "UPI", "Bank Transfer"]
ACCOUNT_MAP = {
    "1000": ("Cash on Hand", "Asset"),
    "1010": ("UPI Clearing", "Asset"),
    "1020": ("Bank Account", "Asset"),
    "1030": ("Cash with Collectors", "Asset"),
    "1100": ("Loan Principal Receivable", "Asset"),
    "1200": ("Interest Receivable", "Asset"),
    "1300": ("Penalty Receivable", "Asset"),
    "2100": ("Indirect Tax Payable", "Liability"),
    "3000": ("Opening Balance Equity", "Equity"),
    "4000": ("Interest Income", "Income"),
    "4100": ("Penalty Income", "Income"),
    "4200": ("Processing Fee Income", "Income"),
    "5000": ("Operating Expenses", "Expense"),
    "5100": ("Waiver and Correction Expense", "Expense"),
    "5200": ("Credit Write-off Expense", "Expense"),
}
LOAN_TYPES = ["Daily 100-Day", "Weekly", "Monthly EMI"]
VERIFICATION_STATUSES = {
    "Verified",
    "Pending Verification",
    "Verification Failed",
    "Manual Verification Approved",
}


@app.middleware("http")
async def production_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))[:100]
    started = time.perf_counter()
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path not in {"/api/auth/login", "/api/auth/refresh"}:
        origin = request.headers.get("Origin")
        if origin and origin not in CORS_ORIGINS:
            return Response(content='{"detail":"Untrusted request origin"}', status_code=403, media_type="application/json")
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        if access_token:
            try:
                token_payload = jwt.decode(access_token, APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                auth_session = await find_one("auth_sessions", {"session_id": token_payload.get("sid")})
                supplied_csrf = request.headers.get("X-CSRF-Token", "")
                expected_hash = auth_session.get("csrf_hash", "") if auth_session else ""
                if not supplied_csrf or not expected_hash or not hmac.compare_digest(hashlib.sha256(supplied_csrf.encode()).hexdigest(), expected_hash):
                    return Response(content='{"detail":"Invalid or missing CSRF token"}', status_code=403, media_type="application/json")
            except JWTError:
                pass
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
    response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
    return response


def validate_production_config() -> None:
    if APP_ENV != "production":
        return
    problems = []
    if APP_SECRET_KEY in {"dev-secret-change-me", "change-this-demo-secret"} or len(APP_SECRET_KEY) < 32:
        problems.append("APP_SECRET_KEY must be a random value of at least 32 characters")
    if AADHAAR_AES_KEY == b"0123456789abcdef0123456789abcdef":
        problems.append("AADHAAR_AES_KEY must not use the demo key")
    if len(AADHAAR_AES_KEY) != 32:
        problems.append("AADHAAR_AES_KEY must be exactly 32 UTF-8 bytes")
    if STRICT_COMPLIANCE_MODE and AADHAAR_KEY_PROVIDER not in {"aws-kms", "azure-key-vault", "gcp-kms", "hsm"}:
        problems.append("AADHAAR_KEY_PROVIDER must identify an HSM or managed KMS in production")
    if STRICT_COMPLIANCE_MODE and not os.getenv("AUDIT_HMAC_KEY"):
        problems.append("AUDIT_HMAC_KEY must be stored separately from the database")
    if ALLOW_MEMORY_FALLBACK:
        problems.append("ALLOW_MEMORY_FALLBACK must be false")
    if not MONGO_ENABLED:
        problems.append("MONGO_ENABLED must be true")
    mongo_srv = MONGO_URL.startswith("mongodb+srv://")
    if "@" not in MONGO_URL:
        problems.append("MONGO_URL must use an authenticated database user")
    if not mongo_srv and "authSource=" not in MONGO_URL:
        problems.append("non-SRV MONGO_URL must specify authSource")
    # mongodb+srv discovers the Atlas replica set through DNS. A standard
    # mongodb:// URL must identify the replica set explicitly.
    if not mongo_srv and "replicaSet=" not in MONGO_URL:
        problems.append("non-SRV MONGO_URL must specify replicaSet")
    if "w=majority" not in MONGO_URL or "journal=true" not in MONGO_URL:
        problems.append("MONGO_URL must require majority and journaled writes")
    if any(origin == "*" for origin in CORS_ORIGINS):
        problems.append("CORS_ORIGINS must list trusted origins")
    if not COOKIE_SECURE:
        problems.append("COOKIE_SECURE must be true")
    if len(BACKUP_ENCRYPTION_KEY) != 32:
        problems.append("BACKUP_ENCRYPTION_KEY must be exactly 32 UTF-8 bytes")
    if problems:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))


class LoginIn(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=6, max_length=200)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=6, max_length=200)
    new_password: str = Field(min_length=12, max_length=200)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not all((any(c.islower() for c in value), any(c.isupper() for c in value), any(c.isdigit() for c in value), any(not c.isalnum() for c in value))):
            raise ValueError("New password must include uppercase, lowercase, number, and symbol")
        return value


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    father_name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(min_length=10, max_length=15)
    aadhaar: str = Field(default="", max_length=12)
    address: str = Field(min_length=5, max_length=500)
    area: str = Field(min_length=2, max_length=3)
    guarantor: str = Field(default="", max_length=120)
    status: str = "Pending Verification"
    aadhaar_consent_given: bool = False
    aadhaar_consent_purpose: str = Field(default="", max_length=300)
    aadhaar_consent_reference: str = Field(default="", max_length=120)

    def model_post_init(self, __context: Any) -> None:
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError("Invalid verification status")
        if self.aadhaar and (not self.aadhaar_consent_given or len(self.aadhaar_consent_purpose.strip()) < 5 or len(self.aadhaar_consent_reference.strip()) < 3):
            raise ValueError("Recorded customer consent, disclosed purpose, and consent reference are required for Aadhaar")

    @field_validator("name", "father_name", "address", "guarantor")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("mobile")
    @classmethod
    def valid_mobile(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 10 or digits[0] not in "6789":
            raise ValueError("Mobile must be a valid 10-digit Indian number")
        return digits

    @field_validator("area")
    @classmethod
    def uppercase_area(cls, value: str) -> str:
        return value.strip().upper()


class LoanIn(BaseModel):
    customer_id: str
    principal: float = Field(gt=0, le=100000000)
    interest_rate: float = Field(default=2.14, ge=0, le=100)
    loan_type: str
    repayment_period: int = Field(default=100, ge=1, le=600)
    collector_id: str
    borrow_date: Optional[str] = None
    disbursement_mode: str = "Cash"
    interest_method: str = "Reducing"
    processing_fee: float = Field(default=0, ge=0, le=10000000)
    tax_rate: float = Field(default=18, ge=0, le=100)
    first_due_date: Optional[str] = None
    moratorium_periods: int = Field(default=0, ge=0, le=24)
    moratorium_interest_capitalized: bool = True
    preclosure_charge_rate: float = Field(default=0, ge=0, le=10)
    late_fee: float = Field(default=0, ge=0, le=1000000)
    kfs_acknowledgement_reference: str = Field(min_length=3, max_length=120)
    identity_verification_id: Optional[str] = Field(default=None, max_length=120)

    @field_validator("disbursement_mode")
    @classmethod
    def valid_disbursement_mode(cls, value: str) -> str:
        if value not in PAYMENT_MODES:
            raise ValueError("Invalid disbursement mode")
        return value

    @field_validator("interest_method")
    @classmethod
    def valid_interest_method(cls, value: str) -> str:
        if value not in {"Reducing", "Flat"}:
            raise ValueError("Interest method must be Reducing or Flat")
        return value


class PartPaymentIn(BaseModel):
    amount: float = Field(gt=0, le=100000000)
    strategy: str = "Reduce EMI"
    effective_date: str
    borrower_consent_reference: str = Field(min_length=3, max_length=120)
    mode: str = "Bank Transfer"

    @field_validator("mode")
    @classmethod
    def valid_part_payment_mode(cls, value: str) -> str:
        if value not in PAYMENT_MODES:
            raise ValueError("Invalid payment mode")
        return value

    @field_validator("strategy")
    @classmethod
    def valid_strategy(cls, value: str) -> str:
        if value not in {"Reduce EMI", "Reduce Tenor"}:
            raise ValueError("Invalid recalculation strategy")
        return value


class RestructureIn(BaseModel):
    annual_rate: float = Field(ge=0, le=100)
    remaining_periods: int = Field(ge=1, le=600)
    moratorium_periods: int = Field(default=0, ge=0, le=24)
    effective_date: str
    approval_reference: str = Field(min_length=3, max_length=120)
    borrower_consent_reference: str = Field(min_length=3, max_length=120)


class WriteOffIn(BaseModel):
    amount: float = Field(gt=0, le=100000000)
    reason: str = Field(min_length=5, max_length=300)
    approval_reference: str = Field(min_length=3, max_length=120)


class PaymentIn(BaseModel):
    loan_id: str
    amount: float = Field(gt=0, le=100000000)
    mode: str
    collector_id: Optional[str] = None
    request_id: Optional[str] = Field(default=None, min_length=8, max_length=100)

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, value: str) -> str:
        if value not in PAYMENT_MODES:
            raise ValueError("Invalid payment mode")
        return value


class ExpenseIn(BaseModel):
    amount: float = Field(gt=0, le=100000000)
    description: str = Field(min_length=3, max_length=300)
    paid_from: str = "Cash"
    expense_category: str = Field(default="General", min_length=2, max_length=80)
    request_id: str = Field(min_length=8, max_length=100)


class CollectorDepositIn(BaseModel):
    collector_id: str
    amount: float = Field(gt=0, le=100000000)
    destination: str = "Cash"
    reference: str = Field(min_length=3, max_length=120)
    request_id: str = Field(min_length=8, max_length=100)


class SettlementIn(BaseModel):
    amount: float = Field(gt=0, le=100000000)
    reference: str = Field(min_length=3, max_length=120)
    request_id: str = Field(min_length=8, max_length=100)


class OpeningBalanceIn(BaseModel):
    account: str
    amount: float = Field(gt=0, le=1000000000)
    as_of_date: str
    reference: str = Field(min_length=3, max_length=120)
    request_id: str = Field(min_length=8, max_length=100)


class DailyCloseIn(BaseModel):
    business_date: str
    actual_cash: float = Field(ge=0, le=1000000000)
    notes: str = Field(default="", max_length=500)


class ReversalIn(BaseModel):
    reason: str = Field(min_length=5, max_length=300)


class ReversalDecisionIn(BaseModel):
    decision: str
    approval_reference: str = Field(min_length=3, max_length=120)
    comments: str = Field(default="", max_length=300)

    @field_validator("decision")
    @classmethod
    def valid_decision(cls, value: str) -> str:
        normalized = value.strip().title()
        if normalized not in {"Approve", "Reject"}:
            raise ValueError("Decision must be Approve or Reject")
        return normalized


class AadhaarAccessRequestIn(BaseModel):
    purpose: str = Field(min_length=5, max_length=300)
    case_reference: str = Field(min_length=3, max_length=120)


class AadhaarAccessDecisionIn(BaseModel):
    decision: str
    comments: str = Field(default="", max_length=300)
    @field_validator("decision")
    @classmethod
    def valid_access_decision(cls, value: str) -> str:
        result = value.strip().title()
        if result not in {"Approve", "Reject"}: raise ValueError("Decision must be Approve or Reject")
        return result


class ConsentWithdrawalIn(BaseModel):
    customer_request_reference: str = Field(min_length=3, max_length=120)
    reason: str = Field(min_length=5, max_length=300)


class AadhaarDeletionRequestIn(BaseModel):
    reason: str = Field(min_length=5, max_length=300)
    customer_request_reference: str = Field(min_length=3, max_length=120)


class AuditResealIn(BaseModel):
    incident_reference: str = Field(min_length=3, max_length=120)
    reason: str = Field(min_length=10, max_length=500)


class AadhaarOtpStartIn(BaseModel):
    customer_id: str
    purpose: str = Field(min_length=5, max_length=300)
    consent_reference: str = Field(min_length=3, max_length=120)
    proposed_disbursal_amount: float = Field(default=0, ge=0, le=100000000)
    owner_notes: str = Field(default="", max_length=500)


class AadhaarOtpVerifyIn(BaseModel):
    verification_id: str
    otp: str = Field(pattern=r"^(?:\d{4}|\d{6})$")


class AadhaarOtpResendIn(BaseModel):
    verification_id: str


class LoanAdjustmentIn(BaseModel):
    kind: str
    amount: float = Field(gt=0, le=100000000)
    reason: str = Field(min_length=5, max_length=300)
    request_id: str = Field(min_length=8, max_length=100)

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, value: str) -> str:
        allowed = {"Penalty", "Interest Waiver", "Penalty Waiver"}
        if value not in allowed:
            raise ValueError("Invalid adjustment type")
        return value


class VerificationIn(BaseModel):
    status: str
    reason: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError("Invalid verification status")


class CustomerDeleteIn(BaseModel):
    confirmation: str = Field(min_length=3, max_length=40)
    reason: str = Field(min_length=5, max_length=300)


class AreaIn(BaseModel):
    code: str
    name: str


class ReportRequest(BaseModel):
    report_type: str
    customer_id: Optional[str] = None
    date: Optional[str] = None
    month: Optional[str] = None
    year: Optional[int] = None


def now() -> datetime:
    return datetime.now(timezone.utc)


BUSINESS_TIMEZONE = ZoneInfo(os.getenv("BUSINESS_TIMEZONE", "Asia/Kolkata"))


def business_now() -> datetime:
    return now().astimezone(BUSINESS_TIMEZONE)


def business_date_key(value: str) -> str:
    return parse_date(value).astimezone(BUSINESS_TIMEZONE).date().isoformat()


def business_month_key(value: str) -> str:
    return parse_date(value).astimezone(BUSINESS_TIMEZONE).strftime("%Y-%m")


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def to_paise(value: Any) -> int:
    return int((Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100))


def from_paise(value: int) -> float:
    return float((Decimal(value) / 100).quantize(Decimal("0.01")))


def receipt_debit_account(mode: str, collector_id: str, user_id: str) -> str:
    if mode == "UPI":
        return "1010"
    if mode == "Bank Transfer":
        return "1020"
    return "1030" if collector_id and collector_id != "SYSTEM" else "1000"


def cash_account(mode: str) -> str:
    mapping = {"Cash": "1000", "UPI": "1010", "Bank Transfer": "1020", "Bank": "1020"}
    if mode not in mapping:
        raise HTTPException(422, "Invalid cash or settlement account")
    return mapping[mode]


def ledger_line(account_code: str, debit_paise: int = 0, credit_paise: int = 0, **dimensions: Any) -> dict[str, Any]:
    if account_code not in ACCOUNT_MAP or debit_paise < 0 or credit_paise < 0 or (debit_paise and credit_paise):
        raise ValueError("Invalid journal line")
    name, account_type = ACCOUNT_MAP[account_code]
    return {
        "account_code": account_code, "account_name": name, "account_type": account_type,
        "debit_paise": int(debit_paise), "credit_paise": int(credit_paise), "dimensions": dimensions,
    }


async def post_journal(
    entry_id: str, source_type: str, source_id: str, description: str,
    lines: list[dict[str, Any]], user: dict[str, Any], session: Any = None,
    reversal_of: Optional[str] = None,
) -> dict[str, Any]:
    debit = sum(line["debit_paise"] for line in lines)
    credit = sum(line["credit_paise"] for line in lines)
    if debit <= 0 or debit != credit:
        raise HTTPException(500, "Unbalanced journal entry was blocked")
    entry = {
        "entry_id": entry_id, "source_type": source_type, "source_id": source_id,
        "description": description, "timestamp": iso(now()), "status": "Posted",
        "debit_paise": debit, "credit_paise": credit, "lines": lines,
        "posted_by": user.get("name", "System"), "posted_by_id": user.get("id", "SYSTEM"),
    }
    if reversal_of:
        entry["reversal_of"] = reversal_of
    if USE_MEMORY:
        await insert_one("journal_entries", entry)
    else:
        await db.journal_entries.insert_one(deepcopy(entry), session=session)
    return entry


def parse_date(value: Optional[str]) -> datetime:
    if not value:
        return now()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    month_days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return value.replace(year=year, month=month, day=min(value.day, month_days[month - 1]))


def periodic_irr(cashflows: list[Decimal]) -> Decimal:
    if not cashflows or cashflows[0] >= 0 or not any(flow > 0 for flow in cashflows[1:]):
        return Decimal("0")
    low, high = Decimal("-0.9999"), Decimal("10")
    for _ in range(160):
        rate = (low + high) / 2
        npv = sum(flow / ((Decimal(1) + rate) ** index) for index, flow in enumerate(cashflows))
        if npv > 0:
            low = rate
        else:
            high = rate
    return (low + high) / 2


def build_amortization(payload: LoanIn, borrow: datetime) -> dict[str, Any]:
    principal = Decimal(str(payload.principal)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    annual_rate = Decimal(str(payload.interest_rate)) / 100
    periods = payload.repayment_period
    periods_per_year = Decimal(365 if payload.loan_type == "Daily 100-Day" else 52 if payload.loan_type == "Weekly" else 12)
    period_rate = annual_rate / periods_per_year
    first_due = parse_date(payload.first_due_date) if payload.first_due_date else (borrow + timedelta(days=1) if payload.loan_type == "Daily 100-Day" else borrow + timedelta(days=7) if payload.loan_type == "Weekly" else add_months(borrow, 1))
    def due_for(number: int) -> datetime:
        if payload.loan_type == "Daily 100-Day": return first_due + timedelta(days=number - 1)
        if payload.loan_type == "Weekly": return first_due + timedelta(days=7 * (number - 1))
        return add_months(first_due, number - 1)
    balance = principal
    rows: list[dict[str, Any]] = []
    for index in range(1, payload.moratorium_periods + 1):
        due = due_for(index)
        interest = (balance * period_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if payload.moratorium_interest_capitalized:
            balance += interest
        rows.append({"number": index, "due_date": iso(due), "opening": float(balance - interest if payload.moratorium_interest_capitalized else balance), "payment": 0.0, "principal": 0.0, "interest": float(interest), "closing": float(balance), "moratorium": True})
    repayment_periods = max(periods - payload.moratorium_periods, 1)
    if payload.interest_method == "Flat":
        tenure_years = Decimal(periods) / periods_per_year
        total_interest = (principal * annual_rate * tenure_years).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        payment = ((principal + total_interest) / repayment_periods).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        flat_interest = (total_interest / repayment_periods).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        payment = (balance / repayment_periods if period_rate == 0 else balance * period_rate * ((Decimal(1) + period_rate) ** repayment_periods) / (((Decimal(1) + period_rate) ** repayment_periods) - 1)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        flat_interest = Decimal("0")
    previous_due = borrow
    for offset in range(repayment_periods):
        number = payload.moratorium_periods + offset + 1
        due = due_for(number)
        opening = balance
        if payload.interest_method == "Flat":
            interest = flat_interest
            principal_part = min(payment - interest, balance)
        else:
            day_count = max((due - previous_due).days, 1)
            interest = (balance * annual_rate * Decimal(day_count) / 365).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if offset == 0 else (balance * period_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            principal_part = min(max(payment - interest, Decimal("0")), balance)
        actual_payment = principal_part + interest
        balance = (balance - principal_part).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if offset == repayment_periods - 1 and balance:
            principal_part += balance; actual_payment += balance; balance = Decimal("0")
        rows.append({"number": number, "due_date": iso(due), "opening": float(opening), "payment": float(actual_payment), "principal": float(principal_part), "interest": float(interest), "closing": float(balance), "moratorium": False})
        previous_due = due
    fee = Decimal(str(payload.processing_fee)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax = (fee * Decimal(str(payload.tax_rate)) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    net_disbursed = principal - fee - tax
    cashflows = [-net_disbursed] + [Decimal(str(row["payment"])) for row in rows if row["payment"] > 0]
    irr = periodic_irr(cashflows)
    annual_apr = ((Decimal(1) + irr) ** int(periods_per_year) - 1) * 100
    interest_total = sum(Decimal(str(row["interest"])) for row in rows)
    return {
        "rows": rows, "emi": float(payment), "principal": float(principal),
        "interest_total": float(interest_total), "processing_fee": float(fee), "tax": float(tax),
        "net_disbursed": float(net_disbursed), "apr": float(annual_apr.quantize(Decimal("0.0001"))),
        "first_due_date": iso(first_due), "maturity_date": rows[-1]["due_date"],
        "total_repayment": float(sum(Decimal(str(row["payment"])) for row in rows)),
    }


def clean_aadhaar(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) != 12:
        raise HTTPException(status_code=422, detail="Aadhaar must contain exactly 12 digits")
    return digits


def mask_aadhaar(value: str) -> str:
    digits = clean_aadhaar(value)
    return f"XXXX XXXX {digits[-4:]}"


def aadhaar_hash(value: str) -> str:
    return hashlib.sha256(clean_aadhaar(value).encode()).hexdigest()


def encrypt_aadhaar(value: str) -> dict[str, str]:
    aesgcm = AESGCM(AADHAAR_KEYRING[AADHAAR_KEY_VERSION])
    nonce = secrets.token_bytes(12)
    cipher = aesgcm.encrypt(nonce, clean_aadhaar(value).encode(), None)
    return {
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(cipher).decode(), "key_version": AADHAAR_KEY_VERSION,
    }


def decrypt_aadhaar(payload: dict[str, str]) -> str:
    version = payload.get("key_version", "v1")
    key = AADHAAR_KEYRING.get(version)
    if not key: raise HTTPException(503, f"Aadhaar key version {version} is unavailable")
    aesgcm = AESGCM(key)
    nonce = base64.b64decode(payload["nonce"])
    cipher = base64.b64decode(payload["ciphertext"])
    return aesgcm.decrypt(nonce, cipher, None).decode()


def create_token(user: dict[str, Any], session_id: str) -> str:
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "user_id": user["id"],
        "sid": session_id,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "exp": now() + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, APP_SECRET_KEY, algorithm=JWT_ALGORITHM)


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in user.items() if k not in {"password_hash", "initial_password_fingerprint"}}


async def find_many(collection: str, query: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    query = query or {}
    if USE_MEMORY:
        return [deepcopy(x) for x in STORE.get(collection, []) if matches(x, query)]
    rows = await db[collection].find(query, {"_id": 0}).to_list(length=10000)
    return rows


async def find_one(collection: str, query: dict[str, Any]) -> Optional[dict[str, Any]]:
    if USE_MEMORY:
        for row in STORE.get(collection, []):
            if matches(row, query):
                return deepcopy(row)
        return None
    return await db[collection].find_one(query, {"_id": 0})


async def insert_one(collection: str, doc: dict[str, Any]) -> dict[str, Any]:
    doc = deepcopy(doc)
    if USE_MEMORY:
        STORE.setdefault(collection, []).append(doc)
    else:
        await db[collection].insert_one(doc)
    return deepcopy(doc)


async def replace_one(collection: str, key: dict[str, Any], doc: dict[str, Any]) -> None:
    if USE_MEMORY:
        rows = STORE.setdefault(collection, [])
        for i, row in enumerate(rows):
            if matches(row, key):
                rows[i] = deepcopy(doc)
                return
        rows.append(deepcopy(doc))
    else:
        await db[collection].replace_one(key, doc, upsert=True)


async def ensure_indexes() -> None:
    if USE_MEMORY:
        return
    await db.customers.create_index("customer_id", name="idx_customers_customer_id", unique=True)
    indexes = await db.customers.index_information()
    mobile_index = indexes.get("idx_customers_mobile")
    if mobile_index and not mobile_index.get("unique", False):
        duplicates = await db.customers.aggregate([
            {"$match": {"profile_deleted_at": {"$exists": False}, "mobile": {"$type": "string"}}},
            {"$group": {"_id": "$mobile", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$limit": 10},
        ]).to_list(length=10)
        if duplicates:
            raise RuntimeError("Duplicate customer mobiles must be resolved before enabling uniqueness: " + ", ".join(str(item["_id"]) for item in duplicates))
        await db.customers.drop_index("idx_customers_mobile")
    await db.customers.create_index("mobile", name="idx_customers_mobile", unique=True)
    aadhaar_index = indexes.get("idx_customers_aadhaar_hash")
    expected_partial = {"aadhaar_hash": {"$type": "string"}}
    if aadhaar_index and aadhaar_index.get("partialFilterExpression") != expected_partial:
        await db.customers.drop_index("idx_customers_aadhaar_hash")
    await db.customers.create_index(
        "aadhaar_hash", name="idx_customers_aadhaar_hash", unique=True,
        partialFilterExpression=expected_partial,
    )
    await db.loans.create_index("loan_id", name="idx_loans_loan_id", unique=True)
    await db.users.create_index("username", name="idx_users_username", unique=True)
    await db.auth_sessions.create_index("session_id", name="idx_auth_session_id", unique=True)
    await db.auth_sessions.create_index("expires_at", name="idx_auth_session_expiry", expireAfterSeconds=0)
    await db.payments.create_index("receipt_no", name="idx_payments_receipt_no", unique=True)
    await db.payments.create_index("request_id", name="idx_payments_request_id", unique=True, sparse=True)
    await db.audit_logs.create_index("id", name="idx_audit_id", unique=True)
    await db.audit_logs.create_index("chain_sequence", name="idx_audit_chain_sequence", unique=True, sparse=True)
    await db.verification_events.create_index("id", name="idx_verification_event_id", unique=True)
    await db.journal_entries.create_index("entry_id", name="idx_journal_entry_id", unique=True)
    await db.journal_entries.create_index(
        [("source_type", 1), ("source_id", 1)], name="idx_journal_source", unique=True,
    )
    await db.journal_entries.create_index("timestamp", name="idx_journal_timestamp")
    await db.expenses.create_index("request_id", name="idx_expense_request", unique=True)
    await db.collector_deposits.create_index("request_id", name="idx_deposit_request", unique=True)
    await db.settlements.create_index("request_id", name="idx_settlement_request", unique=True)
    await db.opening_balances.create_index("request_id", name="idx_opening_request", unique=True)
    await db.opening_balances.create_index("account_code", name="idx_opening_account", unique=True)
    await db.loan_adjustments.create_index("request_id", name="idx_adjustment_request", unique=True)
    await db.daily_closings.create_index(
        [("business_date", 1), ("area", 1)], name="idx_daily_close_date_area", unique=True,
    )
    await db.loan_schedules.create_index([("loan_id", 1), ("version", 1)], name="idx_loan_schedule_version", unique=True)
    await db.part_payments.create_index("part_payment_id", name="idx_part_payment_id", unique=True)
    await db.writeoffs.create_index("writeoff_id", name="idx_writeoff_id", unique=True)
    await db.loan_events.create_index("event_id", name="idx_loan_event_id", unique=True)
    await db.reversal_requests.create_index("request_id", name="idx_reversal_request_id", unique=True)
    await db.reversal_requests.create_index(
        [("original_entry_id", 1), ("status", 1)], name="idx_reversal_original_status"
    )
    await db.auth_sessions.create_index("session_id", name="idx_auth_session_id", unique=True)
    await db.auth_sessions.create_index("refresh_hash", name="idx_auth_refresh_hash", unique=True)
    await db.auth_sessions.create_index("expires_at", name="idx_auth_session_expiry", expireAfterSeconds=0)
    await db.aadhaar_consents.create_index("consent_id", name="idx_aadhaar_consent_id", unique=True)
    await db.aadhaar_access_requests.create_index("request_id", name="idx_aadhaar_access_request_id", unique=True)
    await db.aadhaar_deletion_requests.create_index("request_id", name="idx_aadhaar_deletion_request_id", unique=True)
    await db.identity_verifications.create_index("verification_id", name="idx_identity_verification_id", unique=True)
    await db.identity_verifications.create_index("provider_transaction_id", name="idx_identity_provider_txn", unique=True, sparse=True)
    if not await db.audit_chain_state.find_one({"_id": "primary"}):
        latest = await db.audit_logs.find_one({"chain_sequence": {"$exists": True}}, sort=[("chain_sequence", -1)])
        await db.audit_chain_state.update_one({"_id": "primary"}, {"$setOnInsert": {"sequence": int(latest.get("chain_sequence", 0)) if latest else 0, "head_hash": latest.get("entry_hash", "GENESIS") if latest else "GENESIS", "epoch": 1}}, upsert=True)
    else:
        await db.audit_chain_state.update_one({"_id": "primary", "epoch": {"$exists": False}}, {"$set": {"epoch": 1}})
    await db.customers.create_index("name", name="idx_customers_name")
    await db.customers.create_index(
        [("name", "text"), ("customer_id", "text"), ("mobile", "text")],
        name="txt_customers_name_code_mobile",
        default_language="none",
    )


def matches(row: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        if isinstance(expected, dict) and "$in" in expected:
            if row.get(key) not in expected["$in"]:
                return False
        elif row.get(key) != expected:
            return False
    return True


def customer_matches_search(row: dict[str, Any], query: str) -> bool:
    ql = query.lower().strip()
    if not ql:
        return True
    haystack = " ".join([
        str(row.get("customer_id", "")),
        str(row.get("name", "")),
        str(row.get("mobile", "")),
        str(row.get("aadhaar_masked", "")),
        str(row.get("area", "")),
    ]).lower()
    return ql in haystack


async def audit(user: Optional[dict[str, Any]], action: str, entity: str, entity_id: str, data: Any = None, request: Optional[Request] = None, session: Any = None) -> None:
    async def append(active_session: Any = None) -> None:
        state = await db.audit_chain_state.find_one({"_id": "primary"}, session=active_session) if not USE_MEMORY else None
        sequence = int(state.get("sequence", 0)) + 1 if state else len(STORE.get("audit_logs", [])) + 1
        previous_hash = state.get("head_hash", "GENESIS") if state else (STORE.get("audit_logs", [{}])[-1].get("entry_hash", "GENESIS") if STORE.get("audit_logs") else "GENESIS")
        entry = {
            "id": f"AUD-{sequence:010d}", "chain_sequence": sequence, "chain_epoch": int(state.get("epoch", 1)) if state else 1, "previous_hash": previous_hash,
            "action": action, "entity": entity, "entity_id": entity_id,
            "user": user["name"] if user else "System", "user_id": user.get("id", "SYSTEM") if user else "SYSTEM",
            "role": user["role"] if user else "system", "timestamp": iso(now()),
            "ip": request.client.host if request and request.client else "local", "details": data or {},
        }
        canonical = json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str).encode()
        entry["entry_hash"] = hmac.new(AUDIT_HMAC_KEY, canonical, hashlib.sha256).hexdigest()
        if USE_MEMORY:
            await insert_one("audit_logs", entry)
        else:
            result = await db.audit_chain_state.update_one({"_id": "primary", "sequence": sequence - 1, "head_hash": previous_hash}, {"$set": {"sequence": sequence, "head_hash": entry["entry_hash"], "updated_at": entry["timestamp"]}}, session=active_session)
            if result.modified_count != 1: raise HTTPException(503, "Concurrent audit append conflict; retry the operation")
            await db.audit_logs.insert_one(deepcopy(entry), session=active_session)
    if USE_MEMORY:
        async with MEMORY_SEQUENCE_LOCK:
            await append()
    elif session is not None:
        await append(session)
    else:
        async with await mongo_client.start_session() as own_session:
            await own_session.with_transaction(append)


async def current_user(request: Request) -> dict[str, Any]:
    header = request.headers.get("Authorization", "")
    token = header.removeprefix("Bearer ") if header.startswith("Bearer ") else request.cookies.get(ACCESS_COOKIE, "")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(token, APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if payload.get("type") != "access" or not payload.get("sid"):
        raise HTTPException(status_code=401, detail="Invalid session token")
    auth_session = await find_one("auth_sessions", {"session_id": payload["sid"]})
    if not auth_session or auth_session.get("revoked_at"):
        raise HTTPException(status_code=401, detail="Session has been revoked")
    user = await find_one("users", {"id": payload["user_id"]})
    if not user or not user.get("active", True):
        raise HTTPException(status_code=401, detail="Inactive user")
    return user


def require(*roles: str):
    async def checker(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Not allowed for this role")
        return user
    return checker


def require_min(role: str):
    async def checker(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if ROLES[user["role"]] < ROLES[role]:
            raise HTTPException(status_code=403, detail="Not enough permission")
        return user
    return checker


async def aadhaar_provider_call(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not AADHAAR_AUTH_PROVIDER_URL or not AADHAAR_AUTH_PROVIDER_KEY:
        raise HTTPException(503, "Automatic Aadhaar verification is not configured. Connect an authorized AUA/KUA provider first.")
    def send() -> dict[str, Any]:
        request = UrlRequest(
            f"{AADHAAR_AUTH_PROVIDER_URL}{path}", data=json.dumps(payload).encode(), method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {AADHAAR_AUTH_PROVIDER_KEY}"},
        )
        try:
            with urlopen(request, timeout=20) as response: return json.loads(response.read())
        except HTTPError as exc:
            raise HTTPException(502, f"Aadhaar provider rejected the request with status {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise HTTPException(502, "Aadhaar provider is temporarily unreachable") from exc
    return await asyncio.to_thread(send)


async def next_sequence(prefix: str, field: str, collection: str) -> int:
    if not USE_MEMORY:
        counter_id = f"{collection}:{prefix}"
        if counter_id not in SEQUENCE_RECONCILED:
            rows = await db[collection].find({}, {field: 1}).to_list(length=None)
            max_seen = 0
            for row in rows:
                value = str(row.get(field, ""))
                if value.startswith(prefix):
                    digits = "".join(ch for ch in value[len(prefix):] if ch.isdigit())
                    if digits:
                        max_seen = max(max_seen, int(digits))
            await db.counters.update_one(
                {"_id": counter_id},
                {"$max": {"value": max_seen}, "$setOnInsert": {"created_at": iso(now())}},
                upsert=True,
            )
            SEQUENCE_RECONCILED.add(counter_id)
        counter = await db.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"value": 1}, "$setOnInsert": {"created_at": iso(now())}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(counter["value"])
    async with MEMORY_SEQUENCE_LOCK:
        rows = await find_many(collection)
        max_seen = 0
        for row in rows:
            value = str(row.get(field, ""))
            if value.startswith(prefix):
                digits = "".join(ch for ch in value[len(prefix):] if ch.isdigit())
                if digits:
                    max_seen = max(max_seen, int(digits))
        return max_seen + 1


def loan_schedule(loan: dict[str, Any]) -> dict[str, Any]:
    if loan.get("contract_version", 1) >= 2:
        return {
            "installment": loan.get("emi", 0), "total_payable": loan.get("total_repayment", 0),
            "expected_completion": loan.get("maturity_date"),
        }
    borrow = parse_date(loan["borrow_date"])
    total_payable = round(float(loan.get("total_repayment", float(loan["principal"]) + float(loan.get("contract_interest", 0)))), 2)
    if loan["loan_type"] == "Daily 100-Day":
        installment = round(total_payable / 100, 2)
        expected = borrow + timedelta(days=100)
    elif loan["loan_type"] == "Weekly":
        weeks = max(loan.get("repayment_period", 52), 1)
        installment = round(total_payable / weeks, 2)
        expected = borrow + timedelta(days=7 * weeks)
    else:
        months = max(loan.get("repayment_period", 12), 1)
        installment = round(total_payable / months, 2)
        expected = borrow + timedelta(days=30 * months)
    return {"installment": installment, "total_payable": total_payable, "expected_completion": iso(expected)}


async def enrich_loan(loan: dict[str, Any]) -> dict[str, Any]:
    balances = await loan_component_balances(loan)
    paid = from_paise(balances["paid_paise"])
    total_payable = from_paise(balances["total_payable_paise"])
    balance = from_paise(balances["balance_paise"])
    borrow = parse_date(loan["borrow_date"])
    elapsed = max((now() - borrow).days, 0)
    schedule = loan_schedule(loan)
    schedule_doc = await find_one("loan_schedules", {"loan_id": loan["loan_id"], "version": int(loan.get("schedule_version", 1))})
    repayment_rows = [row for row in (schedule_doc or {}).get("rows", []) if not row.get("moratorium") and float(row.get("payment", 0)) > 0]
    paid_remaining = Decimal(str(paid))
    installments_paid = 0
    next_due_date = None
    for row in repayment_rows:
        due = Decimal(str(row.get("payment", 0)))
        if paid_remaining >= due:
            installments_paid += 1; paid_remaining -= due
        elif next_due_date is None:
            next_due_date = row.get("due_date")
    remaining_installments = max(len(repayment_rows) - installments_paid, 0)
    frequency = "Daily" if loan["loan_type"] == "Daily 100-Day" else "Weekly" if loan["loan_type"] == "Weekly" else "Monthly"
    status_value = loan.get("status", "Active")
    if balance <= 0:
        status_value = "Closed"
    elif loan["loan_type"] == "Daily 100-Day" and elapsed > 130:
        status_value = "Overdue"
    elif loan["loan_type"] == "Weekly" and now() > parse_date(schedule["expected_completion"]) + timedelta(days=2):
        status_value = "Overdue"
    elif loan["loan_type"] == "Monthly EMI" and now() > parse_date(schedule["expected_completion"]) + timedelta(days=5):
        status_value = "Overdue"
    return {
        **loan, **schedule, "total_payable": total_payable, "paid": paid, "balance": balance,
        "principal_balance": from_paise(balances["principal_balance_paise"]),
        "interest_balance": from_paise(balances["interest_balance_paise"]),
        "penalty_balance": from_paise(balances["penalty_balance_paise"]),
        "frequency": frequency, "installments_paid": installments_paid,
        "remaining_installments": remaining_installments, "next_due_date": next_due_date,
        "days_elapsed": elapsed, "status": status_value,
    }


async def loan_component_balances(loan: dict[str, Any], session: Any = None) -> dict[str, int]:
    if USE_MEMORY:
        payments = [p for p in await find_many("payments", {"loan_id": loan["loan_id"]}) if p.get("status", "Posted") != "Reversed"]
        adjustments = [a for a in await find_many("loan_adjustments", {"loan_id": loan["loan_id"]}) if a.get("status", "Posted") != "Reversed"]
    else:
        payments = await db.payments.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).sort("timestamp", 1).to_list(length=None)
        adjustments = await db.loan_adjustments.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).to_list(length=None)
    if USE_MEMORY:
        part_payments = [p for p in await find_many("part_payments", {"loan_id": loan["loan_id"]}) if p.get("status", "Posted") != "Reversed"]
        writeoffs = [p for p in await find_many("writeoffs", {"loan_id": loan["loan_id"]}) if p.get("status", "Posted") != "Reversed"]
    else:
        part_payments = await db.part_payments.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).to_list(length=None)
        writeoffs = await db.writeoffs.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).to_list(length=None)
    principal = to_paise(loan["principal"])
    interest = to_paise(loan.get("contract_interest", Decimal(str(loan["principal"])) * Decimal(str(loan.get("interest_rate", 0))) / 100))
    penalty = sum(to_paise(a["amount"]) for a in adjustments if a["kind"] == "Penalty")
    interest = max(interest - sum(to_paise(a["amount"]) for a in adjustments if a["kind"] == "Interest Waiver"), 0)
    penalty = max(penalty - sum(to_paise(a["amount"]) for a in adjustments if a["kind"] == "Penalty Waiver"), 0)
    original_total = principal + interest + penalty
    paid_total = 0
    for payment in payments:
        amount = to_paise(payment["amount"])
        paid_total += amount
        allocation = payment.get("allocation")
        if allocation:
            penalty = max(penalty - int(allocation.get("penalty_paise", 0)), 0)
            interest = max(interest - int(allocation.get("interest_paise", 0)), 0)
            principal = max(principal - int(allocation.get("principal_paise", 0)), 0)
        else:
            part = min(amount, penalty); penalty -= part; amount -= part
            part = min(amount, interest); interest -= part; amount -= part
            principal = max(principal - amount, 0)
    for part_payment in part_payments:
        amount = to_paise(part_payment["amount"])
        principal = max(principal - amount, 0)
        paid_total += amount
    for writeoff in writeoffs:
        allocation = writeoff.get("allocation", {})
        penalty = max(penalty - int(allocation.get("penalty_paise", 0)), 0)
        interest = max(interest - int(allocation.get("interest_paise", 0)), 0)
        principal = max(principal - int(allocation.get("principal_paise", 0)), 0)
    return {
        "principal_balance_paise": principal, "interest_balance_paise": interest,
        "penalty_balance_paise": penalty, "balance_paise": principal + interest + penalty,
        "paid_paise": paid_total, "total_payable_paise": original_total,
    }


async def customer_view(customer: dict[str, Any]) -> dict[str, Any]:
    visible = {k: v for k, v in customer.items() if k not in {"aadhaar_encrypted", "aadhaar_hash"}}
    visible["aadhaar_masked"] = f"XXXX XXXX {customer['aadhaar_last4']}" if customer.get("aadhaar_last4") else ("Stored securely" if customer.get("aadhaar_encrypted") else "Not provided")
    visible["has_aadhaar"] = bool(customer.get("aadhaar_encrypted"))
    return visible


async def seed_data() -> None:
    global STORE
    existing = await find_many("users")
    if existing:
        # Keep the production owner aligned with the password managed by the
        # hosting platform. The keyed fingerprint avoids storing the password
        # itself and prevents re-hashing it on every restart.
        if APP_ENV == "production":
            admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
            admin_username = os.getenv("INITIAL_ADMIN_USERNAME", "owner")
            if len(admin_password) < 12:
                raise RuntimeError("INITIAL_ADMIN_PASSWORD (12+ characters) is required for production startup")
            if USE_MEMORY:
                raise RuntimeError("Production owner synchronization requires MongoDB")
            owner = await db.users.find_one({"username": admin_username, "role": "owner"})
            if not owner:
                raise RuntimeError(f"Owner account '{admin_username}' was not found")
            password_fingerprint = hmac.new(
                APP_SECRET_KEY.encode(), admin_password.encode(), hashlib.sha256
            ).hexdigest()
            managed_fingerprint = owner.get("initial_password_fingerprint", "")
            if managed_fingerprint != "user-managed" and not hmac.compare_digest(managed_fingerprint, password_fingerprint):
                await db.users.update_one(
                    {"_id": owner["_id"]},
                    {"$set": {
                        "password_hash": pwd_context.hash(admin_password),
                        "initial_password_fingerprint": password_fingerprint,
                        "active": True,
                        "must_change_password": True,
                        "password_synced_at": iso(now()),
                    }},
                )
                # Existing sessions should not survive an administrative password reset.
                await db.auth_sessions.delete_many({"user_id": owner["id"]})
        return
    STORE = {name: [] for name in [
        "users", "auth_sessions", "areas", "customers", "loans", "payments", "audit_logs", "overdue_alerts", "backups",
        "notifications", "verification_events", "verification_logs", "identity_verifications", "identity_verification_events", "journal_entries", "reversal_requests", "aadhaar_consents", "aadhaar_access_requests", "aadhaar_deletion_requests", "expenses", "collector_deposits",
        "settlements", "loan_adjustments", "daily_closings", "opening_balances", "loan_schedules", "loan_events", "part_payments", "writeoffs",
    ]}
    if not USE_MEMORY and APP_ENV != "production":
        for name in STORE:
            await db[name].delete_many({})
    if APP_ENV == "production":
        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
        if len(admin_password) < 12:
            raise RuntimeError("INITIAL_ADMIN_PASSWORD (12+ characters) is required for first production startup")
        for area in AREAS:
            await insert_one("areas", {**area, "counter": 0, "active": True})
        await insert_one("users", {
            "id": "USR-001", "username": os.getenv("INITIAL_ADMIN_USERNAME", "owner"),
            "name": os.getenv("INITIAL_ADMIN_NAME", "Owner"), "email": os.getenv("INITIAL_ADMIN_EMAIL", ""),
            "role": "owner", "area": AREAS[0]["code"], "active": True,
            "password_hash": pwd_context.hash(admin_password),
            "initial_password_fingerprint": hmac.new(
                APP_SECRET_KEY.encode(), admin_password.encode(), hashlib.sha256
            ).hexdigest(),
            "must_change_password": True,
        })
        return
    for area in AREAS:
        await insert_one("areas", {**area, "counter": 0, "active": True})
    users = [
        ("USR-001", "owner", "Owner", "owner@stf.local", "owner123", "owner", "KUN"),
        ("USR-002", "manager", "Manager", "manager@stf.local", "manager123", "manager", "SLM"),
        ("USR-003", "collector", "Collector", "collector@stf.local", "collector123", "collector", "NMK"),
        ("USR-004", "accountant", "Accountant", "accountant@stf.local", "accountant123", "accountant", "ERD"),
        ("USR-005", "collector2", "Collector Arun", "arun@stf.local", "collector123", "collector", "KUN"),
    ]
    for uid, username, name, email, password, role, area in users:
        await insert_one("users", {
            "id": uid, "username": username, "name": name, "email": email, "role": role,
            "area": area, "active": True, "password_hash": pwd_context.hash(password),
        })
    names = [
        ("Muthu Kumar", "Rangasamy"), ("Selvi Priya", "Murugan"), ("Karthik Raj", "Sundaram"),
        ("Lakshmi Devi", "Paramasivan"), ("Arun Kumar", "Ganesan"), ("Revathi S", "Shanmugam"),
        ("Suresh Babu", "Balakrishnan"), ("Meena K", "Krishnan"), ("Naveen Raj", "Ravi"),
        ("Gayathri P", "Palani"), ("Rajesh M", "Mahendran"), ("Deepa L", "Loganathan"),
        ("Vignesh R", "Raman"), ("Kalaivani T", "Thangavel"), ("Prakash S", "Subramani"),
        ("Jayanthi N", "Natarajan"), ("Saravanan V", "Velu"), ("Anitha D", "Durai"),
        ("Balamurugan C", "Chinnasamy"), ("Hema R", "Rajendran"),
    ]
    collectors = ["USR-003", "USR-005"]
    for i, (name, father) in enumerate(names, start=1):
        area = AREAS[(i - 1) % len(AREAS)]["code"]
        seq = await next_sequence(area, "_customer_seq", "customers")
        customer_id = f"{area}{seq:03d}"
        aadhaar = f"43001234{i:04d}"
        await insert_one("customers", {
            "id": customer_id,
            "_customer_seq": f"{area}{seq}",
            "customer_id": customer_id,
            "name": name,
            "father_name": father,
            "mobile": f"9{random.randint(100000000, 999999999)}",
            "address": f"{10+i}, Main Road, {area}, Tamil Nadu - 6{i:05d}",
            "area": area,
            "guarantor": f"Guarantor {i}",
            "status": "Verified" if i % 7 else "Pending Verification",
            "created_at": iso(now() - timedelta(days=150 - i)),
            "operator": "Manager",
            "aadhaar_encrypted": encrypt_aadhaar(aadhaar),
            "aadhaar_hash": aadhaar_hash(aadhaar),
            "risk_score": max(24, min(96, 78 - (i % 6) * 7 + random.randint(-4, 8))),
        })
    customers = await find_many("customers")
    for i, customer in enumerate(customers[:15], start=1):
        borrow = now() - timedelta(days=random.choice([12, 35, 68, 91, 101, 132, 155]))
        loan_type = "Daily 100-Day" if i % 3 else "Monthly EMI"
        period = 100 if loan_type == "Daily 100-Day" else random.choice([6, 10, 12])
        principal = random.choice([25000, 40000, 50000, 75000, 100000, 125000])
        loan_id = f"{customer['customer_id']}-{borrow.strftime('%Y%m%d')}"
        loan = {
            "loan_id": loan_id,
            "customer_id": customer["customer_id"],
            "principal": float(principal),
            "interest_rate": random.choice([10, 12, 14, 18]),
            "loan_type": loan_type,
            "repayment_period": period,
            "collector_id": collectors[i % len(collectors)],
            "borrow_date": iso(borrow),
            "status": "Active",
            "created_at": iso(borrow),
        }
        await insert_one("loans", loan)
        installment = loan_schedule(loan)["installment"]
        paid_count = random.randint(4, min(80, max(6, (now() - borrow).days)))
        for p in range(1, paid_count + 1):
            if random.random() < 0.18:
                continue
            pay_dt = borrow + timedelta(days=p if loan_type == "Daily 100-Day" else p * 30)
            await insert_one("payments", {
                "receipt_no": f"RCP-{pay_dt.strftime('%Y%m%d')}-{p:03d}",
                "loan_id": loan_id,
                "customer_id": customer["customer_id"],
                "amount": installment,
                "mode": random.choice(PAYMENT_MODES),
                "collector_id": loan["collector_id"],
                "timestamp": iso(pay_dt),
            })
    await refresh_overdue_alerts()
    await insert_one("backups", {"id": "BKP-001", "timestamp": iso(now() - timedelta(hours=8)), "status": "Completed", "retention_days": 90})


async def refresh_overdue_alerts() -> None:
    if USE_MEMORY:
        STORE["overdue_alerts"] = []
        STORE["notifications"] = []
    loans = [await enrich_loan(x) for x in await find_many("loans")]
    for loan in loans:
        if loan["status"] == "Closed":
            continue
        urgency = None
        if loan["loan_type"] == "Daily 100-Day":
            if loan["days_elapsed"] >= 130:
                urgency = "Day 130+ Overdue"
            elif loan["days_elapsed"] >= 100:
                urgency = "Day 100 Final Alert"
            elif loan["days_elapsed"] >= 95:
                urgency = "Day 95 Warning"
            elif loan["days_elapsed"] >= 90:
                urgency = "Day 90 Watch"
        else:
            expected = parse_date(loan["expected_completion"])
            if now() > expected + timedelta(days=5):
                urgency = "EMI Grace Breached"
        if urgency:
            customer = await find_one("customers", {"customer_id": loan["customer_id"]})
            alert = {
                "id": f"ALT-{loan['loan_id']}",
                "loan_id": loan["loan_id"],
                "customer_id": loan["customer_id"],
                "customer_name": customer["name"] if customer else "",
                "area": customer["area"] if customer else "",
                "urgency": urgency,
                "balance": loan["balance"],
                "days_elapsed": loan["days_elapsed"],
                "message": f"{urgency}: {loan['loan_id']} has INR {loan['balance']:,.0f} outstanding.",
                "created_at": iso(now()),
            }
            await insert_one("overdue_alerts", alert)
            await insert_one("notifications", {**alert, "channel": "In-app WhatsApp/SMS", "sent": False})


@app.on_event("startup")
async def startup() -> None:
    global mongo_client, db, USE_MEMORY
    validate_production_config()
    if not MONGO_ENABLED:
        USE_MEMORY = True
        await seed_data()
        return
    try:
        mongo_client = AsyncIOMotorClient(
            MONGO_URL,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
        )
        await mongo_client.admin.command("ping")
        db = mongo_client[MONGO_DB]
        USE_MEMORY = False
    except Exception:
        if not ALLOW_MEMORY_FALLBACK:
            raise
        USE_MEMORY = True
    await ensure_indexes()
    await seed_data()
    if APP_ENV == "production":
        hello = await db.command("hello")
        if not hello.get("setName"):
            raise RuntimeError("Production MongoDB must be configured as a replica set")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    database_status = "memory-demo" if USE_MEMORY else "mongodb"
    if not USE_MEMORY:
        try:
            await db.command("ping")
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    backup_status: dict[str, Any] = {"configured": len(BACKUP_ENCRYPTION_KEY) == 32, "offsite_configured": OFFSITE_BACKUP_DIR is not None}
    if not USE_MEMORY:
        latest = await db.backups.find_one({"status": "Completed"}, sort=[("timestamp", -1)])
        if latest:
            backup_status.update({
                "last_completed_at": latest.get("timestamp"),
                "last_backup_present": (BACKUP_DIR / latest.get("filename", "")).is_file(),
            })
    production_gaps = []
    if APP_ENV == "production" and OFFSITE_BACKUP_DIR is None: production_gaps.append("offsite_backup_not_configured")
    if APP_ENV == "production" and not os.getenv("AUDIT_ARCHIVE_DIR", "").strip(): production_gaps.append("external_audit_archive_not_configured")
    if APP_ENV == "production" and not (AADHAAR_AUTH_PROVIDER_URL and AADHAAR_AUTH_PROVIDER_KEY): production_gaps.append("aadhaar_provider_not_configured")
    return {
        "ok": True,
        "ready": True,
        "production_ready": not production_gaps,
        "production_gaps": production_gaps,
        "database": database_status,
        "environment": APP_ENV,
        "release": os.getenv("RENDER_GIT_COMMIT", "local")[:8],
        "durability": "memory-demo" if USE_MEMORY else "majority-journaled",
        "backup": backup_status,
        "time": iso(now()),
    }


@app.on_event("shutdown")
async def shutdown() -> None:
    if mongo_client is not None:
        mongo_client.close()


def set_auth_cookies(response: Response, request: Request, access_token: str, refresh_token: str) -> None:
    loopback = request.url.hostname in {"127.0.0.1", "localhost", "::1"}
    secure_cookie = COOKIE_SECURE and not loopback
    # Render hosts the static frontend and API on separate HTTPS origins.
    # Cross-origin credentialed requests require SameSite=None + Secure.
    common = {
        "httponly": True,
        "secure": secure_cookie,
        "samesite": "none" if secure_cookie else "lax",
        "path": "/",
    }
    response.set_cookie(ACCESS_COOKIE, access_token, max_age=ACCESS_TOKEN_MINUTES * 60, **common)
    response.set_cookie(REFRESH_COOKIE, refresh_token, max_age=REFRESH_TOKEN_DAYS * 86400, **common)


@app.post("/api/auth/login")
async def login(payload: LoginIn, request: Request, response: Response) -> dict[str, Any]:
    client_key = request.client.host if request.client else "unknown"
    attempts = LOGIN_ATTEMPTS[client_key]
    cutoff = time.time() - 900
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    if len(attempts) >= 10:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 15 minutes.", headers={"Retry-After": "900"})
    user = await find_one("users", {"username": payload.username})
    if not user or not pwd_context.verify(payload.password, user["password_hash"]):
        attempts.append(time.time())
        raise HTTPException(status_code=401, detail="Invalid credentials")
    attempts.clear()
    session_id = str(uuid.uuid4())
    refresh_token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    session_record = {
        "session_id": session_id, "user_id": user["id"],
        "refresh_hash": hashlib.sha256(refresh_token.encode()).hexdigest(),
        "csrf_hash": hashlib.sha256(csrf_token.encode()).hexdigest(),
        "created_at": iso(now()), "last_rotated_at": iso(now()),
        "expires_at": now() + timedelta(days=REFRESH_TOKEN_DAYS), "revoked_at": None,
        "ip": request.client.host if request.client else "local",
        "user_agent": request.headers.get("user-agent", "")[:300],
    }
    await insert_one("auth_sessions", session_record)
    token = create_token(user, session_id)
    set_auth_cookies(response, request, token, refresh_token)
    await audit(user, "login", "user", user["id"], {"session_id": session_id, "user_agent": session_record["user_agent"]}, request)
    return {"user": public_user(user), "csrf_token": csrf_token, "session_expires_in_seconds": ACCESS_TOKEN_MINUTES * 60}


@app.post("/api/auth/refresh")
async def refresh_session(request: Request, response: Response) -> dict[str, Any]:
    supplied = request.cookies.get(REFRESH_COOKIE, "")
    if not supplied:
        raise HTTPException(401, "Missing refresh session")
    digest = hashlib.sha256(supplied.encode()).hexdigest()
    auth_session = await find_one("auth_sessions", {"refresh_hash": digest})
    expiry = auth_session.get("expires_at") if auth_session else None
    if isinstance(expiry, str): expiry = parse_date(expiry)
    if isinstance(expiry, datetime) and expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc)
    if not auth_session or auth_session.get("revoked_at") or not expiry or expiry <= now():
        raise HTTPException(401, "Refresh session is invalid or expired")
    user = await find_one("users", {"id": auth_session["user_id"]})
    if not user or not user.get("active", True):
        raise HTTPException(401, "Inactive user")
    replacement = secrets.token_urlsafe(48)
    replacement_hash = hashlib.sha256(replacement.encode()).hexdigest()
    if USE_MEMORY:
        auth_session.update({"refresh_hash": replacement_hash, "last_rotated_at": iso(now())})
        await replace_one("auth_sessions", {"session_id": auth_session["session_id"]}, auth_session)
    else:
        result = await db.auth_sessions.update_one({"session_id": auth_session["session_id"], "refresh_hash": digest, "revoked_at": None}, {"$set": {"refresh_hash": replacement_hash, "last_rotated_at": iso(now())}})
        if result.modified_count != 1:
            raise HTTPException(401, "Refresh token reuse was blocked")
    set_auth_cookies(response, request, create_token(user, auth_session["session_id"]), replacement)
    await audit(user, "session_refresh_rotated", "auth_session", auth_session["session_id"], {}, request)
    return {"user": public_user(user), "session_expires_in_seconds": ACCESS_TOKEN_MINUTES * 60}


@app.get("/api/auth/csrf")
async def issue_csrf(request: Request, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    token = request.cookies.get(ACCESS_COOKIE, "")
    payload = jwt.decode(token, APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    csrf_token = secrets.token_urlsafe(32)
    csrf_hash = hashlib.sha256(csrf_token.encode()).hexdigest()
    if USE_MEMORY:
        session = await find_one("auth_sessions", {"session_id": payload["sid"]})
        session["csrf_hash"] = csrf_hash
        await replace_one("auth_sessions", {"session_id": payload["sid"]}, session)
    else:
        await db.auth_sessions.update_one({"session_id": payload["sid"], "user_id": user["id"]}, {"$set": {"csrf_hash": csrf_hash}})
    return {"csrf_token": csrf_token}


@app.post("/api/auth/change-password")
async def change_password(payload: PasswordChangeIn, request: Request, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    if not pwd_context.verify(payload.current_password, user["password_hash"]):
        raise HTTPException(422, "Current password is incorrect")
    if pwd_context.verify(payload.new_password, user["password_hash"]):
        raise HTTPException(422, "New password must be different")
    access = request.cookies.get(ACCESS_COOKIE, "")
    token_payload = jwt.decode(access, APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    updates = {"password_hash": pwd_context.hash(payload.new_password), "must_change_password": False, "password_changed_at": iso(now()), "initial_password_fingerprint": "user-managed"}
    if USE_MEMORY:
        user.update(updates); await replace_one("users", {"id": user["id"]}, user)
        for session in await find_many("auth_sessions", {"user_id": user["id"]}):
            if session["session_id"] != token_payload["sid"]: session["revoked_at"] = iso(now()); await replace_one("auth_sessions", {"session_id": session["session_id"]}, session)
    else:
        await db.users.update_one({"id": user["id"]}, {"$set": updates})
        await db.auth_sessions.update_many({"user_id": user["id"], "session_id": {"$ne": token_payload["sid"]}}, {"$set": {"revoked_at": iso(now())}})
    await audit(user, "password_changed", "user", user["id"], {"other_sessions_revoked": True}, request)
    return {"status": "Password changed; other sessions revoked"}


@app.post("/api/auth/logout")
async def logout(request: Request, response: Response, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    token = request.cookies.get(ACCESS_COOKIE) or request.headers.get("Authorization", "").removeprefix("Bearer ")
    payload = jwt.decode(token, APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    if USE_MEMORY:
        auth_session = await find_one("auth_sessions", {"session_id": payload["sid"]})
        if auth_session: auth_session["revoked_at"] = iso(now()); await replace_one("auth_sessions", {"session_id": payload["sid"]}, auth_session)
    else:
        await db.auth_sessions.update_one({"session_id": payload["sid"]}, {"$set": {"revoked_at": iso(now())}})
    response.delete_cookie(ACCESS_COOKIE, path="/"); response.delete_cookie(REFRESH_COOKIE, path="/")
    await audit(user, "logout", "auth_session", payload["sid"], {}, request)
    return {"status": "Logged out"}


@app.get("/api/auth/sessions")
async def list_sessions(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    rows = await find_many("auth_sessions", {"user_id": user["id"]})
    return [{k: v for k, v in row.items() if k not in {"refresh_hash", "csrf_hash"}} for row in sorted(rows, key=lambda x: x["created_at"], reverse=True)]


@app.delete("/api/auth/sessions/{session_id}")
async def revoke_session(session_id: str, request: Request, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    target = await find_one("auth_sessions", {"session_id": session_id, "user_id": user["id"]})
    if not target: raise HTTPException(404, "Session not found")
    if USE_MEMORY:
        target["revoked_at"] = iso(now()); await replace_one("auth_sessions", {"session_id": session_id}, target)
    else:
        await db.auth_sessions.update_one({"session_id": session_id}, {"$set": {"revoked_at": iso(now())}})
    await audit(user, "session_revoked", "auth_session", session_id, {}, request)
    return {"status": "Revoked"}


@app.get("/api/me")
async def me(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return public_user(user)


@app.get("/api/bootstrap")
async def bootstrap(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    collectors = [public_user(x) for x in await find_many("users", {"role": "collector", "active": True})]
    if not collectors and user.get("role") in {"owner", "manager"}:
        self_managed = public_user(user)
        self_managed["name"] = f"{self_managed['name']} (self-managed)"
        collectors = [self_managed]
    return {
        "user": public_user(user),
        "areas": await find_many("areas"),
        "collectors": collectors,
        "payment_modes": PAYMENT_MODES,
        "loan_types": LOAN_TYPES,
    }


@app.get("/api/dashboard")
async def dashboard(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    customers = [await customer_view(x) for x in await find_many("customers") if not x.get("profile_deleted_at")]
    loans = [await enrich_loan(x) for x in await find_many("loans")]
    payments = await find_many("payments")
    today_key = business_now().date().isoformat()
    month_key = business_now().strftime("%Y-%m")
    today_payments = [p for p in payments if business_date_key(p["timestamp"]) == today_key]
    month_payments = [p for p in payments if business_month_key(p["timestamp"]) == month_key]
    area_summary = []
    for area in await find_many("areas"):
        code = area["code"]
        area_customers = [c for c in customers if c["area"] == code]
        area_loans = [l for l in loans if l["customer_id"] in {c["customer_id"] for c in area_customers}]
        area_today = [p for p in today_payments if p["customer_id"] in {c["customer_id"] for c in area_customers}]
        area_month = [p for p in month_payments if p["customer_id"] in {c["customer_id"] for c in area_customers}]
        customers_with_dues = {l["customer_id"] for l in area_loans if l["status"] not in {"Closed", "Written Off"} and l["balance"] > 0}
        paid_customer_ids_today = {p["customer_id"] for p in area_today}
        area_summary.append({
            "area": code,
            "name": area["name"],
            "customers": len(area_customers),
            "active_loans": len([l for l in area_loans if l["status"] == "Active"]),
            "outstanding": round(sum(l["balance"] for l in area_loans), 2),
            "today_collection": round(sum(p["amount"] for p in area_today), 2),
            "monthly_collection": round(sum(p["amount"] for p in area_month), 2),
            "paid_customers_today": len(paid_customer_ids_today),
            "customers_yet_to_pay": len(customers_with_dues - paid_customer_ids_today),
            "customers_with_dues": len(customers_with_dues),
            "total_disbursed": round(sum(l["principal"] for l in area_loans), 2),
            "daily_loans": len([l for l in area_loans if l["loan_type"] == "Daily 100-Day"]),
            "weekly_loans": len([l for l in area_loans if l["loan_type"] == "Weekly"]),
            "monthly_loans": len([l for l in area_loans if l["loan_type"] == "Monthly EMI"]),
            "customer_dues": [{
                "customer_id": loan["customer_id"], "customer_name": next((c["name"] for c in area_customers if c["customer_id"] == loan["customer_id"]), loan["customer_id"]),
                "loan_id": loan["loan_id"], "frequency": loan["frequency"], "paid": loan["paid"], "outstanding": loan["balance"],
                "installment": loan["installment"], "remaining_installments": loan["remaining_installments"], "next_due_date": loan.get("next_due_date"), "status": loan["status"],
            } for loan in area_loans if loan["status"] not in {"Closed", "Written Off"} and loan["balance"] > 0],
        })
    collector_breakdown = []
    for collector in await find_many("users", {"role": "collector"}):
        cp = [p for p in payments if p["collector_id"] == collector["id"]]
        collector_breakdown.append({"name": collector["name"], "total": round(sum(p["amount"] for p in cp), 2), "count": len(cp)})
    alerts = await find_many("overdue_alerts")
    customer_by_id = {customer["customer_id"]: customer for customer in customers}
    pending_dues = []
    for loan in loans:
        if loan["status"] in {"Closed", "Written Off"} or loan["balance"] <= 0: continue
        schedule_doc = await find_one("loan_schedules", {"loan_id": loan["loan_id"], "version": int(loan.get("schedule_version", 1))})
        paid_remaining = Decimal(str(loan.get("paid", 0)))
        next_row = None
        for installment_row in (schedule_doc or {}).get("rows", []):
            installment_due = Decimal(str(installment_row.get("payment", 0)))
            applied = min(paid_remaining, installment_due); paid_remaining -= applied
            remaining_due = installment_due - applied
            if remaining_due > 0 and not installment_row.get("moratorium"):
                next_row = {**installment_row, "remaining_due": float(remaining_due)}; break
        if not next_row: continue
        due_at = parse_date(next_row["due_date"]); client = customer_by_id.get(loan["customer_id"], {})
        pending_dues.append({
            "loan_id": loan["loan_id"], "customer_id": loan["customer_id"], "customer_name": client.get("name", loan["customer_id"]),
            "mobile": client.get("mobile", ""), "frequency": "Daily" if loan["loan_type"] == "Daily 100-Day" else "Weekly" if loan["loan_type"] == "Weekly" else "Monthly",
            "installment_number": next_row["number"], "amount_due": next_row["remaining_due"], "next_due_date": next_row["due_date"],
            "overdue": due_at < now(), "days_overdue": max((now() - due_at).days, 0), "plan_balance": loan["balance"],
        })
    pending_dues.sort(key=lambda item: item["next_due_date"])
    return {
        "totals": {
            "customers": len(customers),
            "pending_verification": len([c for c in customers if c["status"] == "Pending Verification"]),
            "active_loans": len([l for l in loans if l["status"] == "Active"]),
            "overdue_loans": len([l for l in loans if l["status"] == "Overdue"]),
            "today_collection": round(sum(p["amount"] for p in today_payments), 2),
            "monthly_collection": round(sum(p["amount"] for p in month_payments), 2),
            "outstanding": round(sum(l["balance"] for l in loans if l["status"] != "Closed"), 2),
        },
        "split": {
            "daily": len([l for l in loans if l["loan_type"] == "Daily 100-Day"]),
            "weekly": len([l for l in loans if l["loan_type"] == "Weekly"]),
            "monthly": len([l for l in loans if l["loan_type"] == "Monthly EMI"]),
        },
        "area_summary": area_summary,
        "collector_breakdown": collector_breakdown,
        "alerts": alerts,
        "pending_dues": pending_dues,
        "cashflow": build_cashflow(payments),
    }


def build_cashflow(payments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, float] = {}
    for payment in payments:
        key = payment["timestamp"][:7]
        buckets[key] = buckets.get(key, 0) + float(payment["amount"])
    return [{"month": key, "collection": round(value, 2)} for key, value in sorted(buckets.items())[-8:]]


@app.get("/api/customers")
async def customers(q: str = "", area: str = "", status_filter: str = "", user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    customer_records = [x for x in await find_many("customers") if not x.get("profile_deleted_at")]
    rows = [await customer_view(x) for x in customer_records]
    loan_rows = await find_many("loans")
    loans_by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for loan in loan_rows:
        loans_by_customer[loan["customer_id"]].append(loan)
    for row in rows:
        customer_loans = loans_by_customer.get(row["customer_id"], [])
        row["loan_count"] = len(customer_loans)
        row["can_delete_profile"] = not customer_loans or all(loan.get("status") in {"Closed", "Written Off"} for loan in customer_loans)
    if q.strip():
        rows = [r for r in rows if customer_matches_search(r, q)]
    if area:
        rows = [r for r in rows if r["area"] == area]
    if status_filter:
        rows = [r for r in rows if r["status"] == status_filter]
    return rows


@app.delete("/api/customers/{customer_id}")
async def delete_completed_customer(customer_id: str, payload: CustomerDeleteIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer or customer.get("profile_deleted_at"):
        raise HTTPException(404, "Active customer profile not found")
    if payload.confirmation.strip().upper() != customer_id.upper():
        raise HTTPException(422, f"Type customer ID {customer_id} exactly to confirm deletion")
    customer_loans = await find_many("loans", {"customer_id": customer_id})
    incomplete = []
    for loan in customer_loans:
        enriched = await enrich_loan(loan)
        if enriched.get("status") not in {"Closed", "Written Off"} or float(enriched.get("balance", 0)) > 0:
            incomplete.append(f"{loan['loan_id']} ({enriched.get('status')}, balance {enriched.get('balance', 0):.2f})")
    if incomplete:
        raise HTTPException(409, "Complete every loan before deleting this profile: " + ", ".join(incomplete))
    receipts = {p.get("receipt_no") for p in await find_many("payments", {"customer_id": customer_id})}
    pending_reversals = [r for r in await find_many("reversal_requests", {"status": "Pending"}) if r.get("original_source_id") in receipts]
    if pending_reversals:
        raise HTTPException(409, "Resolve pending payment reversals before deleting this customer profile")
    stamp = iso(now())
    redacted = deepcopy(customer)
    for field in ["aadhaar_encrypted", "aadhaar_hash", "aadhaar_last4", "aadhaar_key_version"]:
        redacted.pop(field, None)
    redacted.update({
        "name": "Deleted customer", "father_name": "", "mobile": f"deleted-{customer_id}",
        "address": "", "guarantor": "", "status": "Profile Deleted",
        "profile_deleted_at": stamp, "profile_deleted_by": user["name"],
        "profile_deletion_reason": payload.reason.strip(), "aadhaar_consent_status": "Deleted",
    })
    audit_details = {
        "reason": payload.reason.strip(), "loan_ids": [loan["loan_id"] for loan in customer_loans],
        "loan_count": len(customer_loans), "identity_fields_removed": True, "financial_history_retained": True,
    }
    if USE_MEMORY:
        await replace_one("customers", {"customer_id": customer_id}, redacted)
        await audit(user, "completed_customer_profile_deleted", "customer", customer_id, audit_details, request)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                result = await db.customers.replace_one({"customer_id": customer_id, "profile_deleted_at": {"$exists": False}}, redacted, session=session)
                if result.modified_count != 1:
                    raise HTTPException(409, "Customer profile changed concurrently; reload and retry")
                await audit(user, "completed_customer_profile_deleted", "customer", customer_id, audit_details, request, session=session)
    return {"customer_id": customer_id, "status": "Profile Deleted", "deleted_at": stamp, "financial_history_retained": True}


@app.post("/api/customers")
async def create_customer(payload: CustomerIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    if payload.aadhaar and len(payload.aadhaar) != 12:
        raise HTTPException(422, "Aadhaar must contain exactly 12 digits when provided")
    area = await find_one("areas", {"code": payload.area})
    if not area or not area.get("active", True):
        raise HTTPException(422, "Select an active operating area")
    existing = await find_one("customers", {"aadhaar_hash": aadhaar_hash(payload.aadhaar)}) if payload.aadhaar else None
    if existing:
        view = await customer_view(existing)
        await audit(user, "aadhaar_duplicate_check", "customer", view["customer_id"], {"result": "existing"}, request)
        ack_seq = await next_sequence("VER", "id", "acknowledgements")
        return {"duplicate": True, "customer": view, "ack_no": f"VER-{now().strftime('%Y%m%d')}-{ack_seq:06d}"}
    existing_mobile = await find_one("customers", {"mobile": payload.mobile})
    if existing_mobile:
        view = await customer_view(existing_mobile)
        await audit(user, "mobile_duplicate_check", "customer", view["customer_id"], {"result": "existing"}, request)
        ack_seq = await next_sequence("MOB", "id", "acknowledgements")
        return {"duplicate": True, "customer": view, "ack_no": f"MOB-{now().strftime('%Y%m%d')}-{ack_seq:06d}"}
    seq = await next_sequence(payload.area, "_customer_seq", "customers")
    customer_id = f"{payload.area}{seq:03d}"
    customer = {
        "id": customer_id,
        "_customer_seq": f"{payload.area}{seq}",
        "customer_id": customer_id,
        "name": payload.name,
        "father_name": payload.father_name,
        "mobile": payload.mobile,
        "address": payload.address,
        "area": payload.area,
        "guarantor": payload.guarantor,
        "status": "Pending Verification",
        "verification_updated_at": iso(now()),
        "verification_updated_by": user["name"],
        "created_at": iso(now()),
        "operator": user["name"],
        "risk_score": risk_score(payload.model_dump()),
    }
    if payload.aadhaar:
        customer["aadhaar_encrypted"] = encrypt_aadhaar(payload.aadhaar)
        customer["aadhaar_hash"] = aadhaar_hash(payload.aadhaar)
        customer["aadhaar_last4"] = clean_aadhaar(payload.aadhaar)[-4:]
        customer["aadhaar_consent_status"] = "Active"
        customer["aadhaar_key_version"] = AADHAAR_KEY_VERSION
    verification_seq = await next_sequence("VEF", "id", "verification_events")
    verification_event = {
        "id": f"VEF-{verification_seq:08d}", "customer_id": customer_id,
        "from_status": None, "to_status": "Pending Verification",
        "reason": "Registered before Aadhaar/manual verification", "user": user["name"], "timestamp": iso(now()),
    }
    consent = None
    if payload.aadhaar:
        consent_seq = await next_sequence("CNS", "consent_id", "aadhaar_consents")
        consent = {"consent_id": f"CNS-{consent_seq:09d}", "customer_id": customer_id, "status": "Active", "purpose_disclosed": payload.aadhaar_consent_purpose.strip(), "customer_consent_reference": payload.aadhaar_consent_reference.strip(), "captured_at": iso(now()), "captured_by": user["name"], "captured_by_id": user["id"]}
    audit_details = {"masked_aadhaar": mask_aadhaar(payload.aadhaar) if payload.aadhaar else "Not provided", "method": "aadhaar" if payload.aadhaar else "manual", "status": "Pending Verification"}
    try:
        if USE_MEMORY:
            await insert_one("customers", customer)
            await insert_one("verification_events", verification_event)
            if consent: await insert_one("aadhaar_consents", consent)
            await audit(user, "customer_registration", "customer", customer_id, audit_details, request)
        else:
            async with await mongo_client.start_session() as session:
                async with session.start_transaction():
                    await db.customers.insert_one(deepcopy(customer), session=session)
                    await db.verification_events.insert_one(deepcopy(verification_event), session=session)
                    if consent: await db.aadhaar_consents.insert_one(deepcopy(consent), session=session)
                    await audit(user, "customer_registration", "customer", customer_id, audit_details, request, session=session)
    except DuplicateKeyError as exc:
        duplicate = await find_one("customers", {"mobile": payload.mobile})
        if not duplicate and payload.aadhaar:
            duplicate = await find_one("customers", {"aadhaar_hash": aadhaar_hash(payload.aadhaar)})
        if duplicate:
            raise HTTPException(409, f"Customer already exists as {duplicate['customer_id']}") from exc
        raise HTTPException(409, "Customer registration conflicts with an existing record") from exc
    return {"duplicate": False, "customer": await customer_view(customer), "ack_no": f"REG-{now().strftime('%Y%m%d')}-{seq:03d}"}


@app.patch("/api/customers/{customer_id}/verification")
async def update_customer_verification(customer_id: str, payload: VerificationIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer:
        raise HTTPException(404, "Customer not found")
    previous = customer.get("status", "Pending Verification")
    customer["status"] = payload.status
    customer["verification_updated_at"] = iso(now())
    customer["verification_updated_by"] = user["name"]
    await replace_one("customers", {"customer_id": customer_id}, customer)
    verification_seq = await next_sequence("VEF", "id", "verification_events")
    event = {
        "id": f"VEF-{verification_seq:08d}",
        "customer_id": customer_id,
        "from_status": previous,
        "to_status": payload.status,
        "reason": payload.reason or "Manual verification workflow",
        "user": user["name"],
        "timestamp": iso(now()),
    }
    await insert_one("verification_events", event)
    await audit(user, "verification_status_update", "customer", customer_id, event, request)
    return {"customer": await customer_view(customer), "event": event}


@app.post("/api/customers/{customer_id}/aadhaar-access-requests")
async def request_aadhaar_access(customer_id: str, payload: AadhaarAccessRequestIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer:
        raise HTTPException(404, "Customer not found")
    if not customer.get("aadhaar_encrypted"):
        raise HTTPException(404, "Aadhaar was not provided for this customer")
    if customer.get("aadhaar_consent_status") != "Active": raise HTTPException(409, "Active customer consent is required")
    request_seq = await next_sequence("AAR", "request_id", "aadhaar_access_requests")
    record = {"request_id": f"AAR-{request_seq:09d}", "customer_id": customer_id, "purpose": payload.purpose, "case_reference": payload.case_reference, "status": "Pending", "requested_at": iso(now()), "requested_by": user["name"], "requested_by_id": user["id"]}
    await insert_one("aadhaar_access_requests", record)
    await audit(user, "aadhaar_access_requested", "aadhaar_access_request", record["request_id"], {"customer_id": customer_id, "purpose": payload.purpose, "case_reference": payload.case_reference}, request)
    return record


@app.get("/api/aadhaar/provider-status")
async def aadhaar_provider_status(user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    configured = bool(AADHAAR_AUTH_PROVIDER_URL and AADHAAR_AUTH_PROVIDER_KEY)
    return {"configured": configured, "provider": AADHAAR_AUTH_PROVIDER_NAME if configured else None, "verified_disbursal_required": REQUIRE_VERIFIED_DISBURSAL, "mode": "UIDAI-authorized-provider" if configured else "disabled"}


@app.post("/api/aadhaar/otp/start")
async def start_aadhaar_otp(payload: AadhaarOtpStartIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": payload.customer_id})
    if not customer or not customer.get("aadhaar_encrypted"): raise HTTPException(404, "Customer Aadhaar record not found")
    if customer.get("aadhaar_consent_status") != "Active": raise HTTPException(409, "Active Aadhaar consent is required")
    provider = await aadhaar_provider_call("/otp/start", {"aadhaar_number": decrypt_aadhaar(customer["aadhaar_encrypted"]), "purpose": payload.purpose, "consent_reference": payload.consent_reference})
    provider_transaction_id = provider.get("transaction_id") or provider.get("txn_id")
    if not provider_transaction_id: raise HTTPException(502, "Aadhaar provider returned no transaction reference")
    seq = await next_sequence("IDV", "verification_id", "identity_verifications")
    verification_id = f"IDV-{seq:09d}"
    requested_at = now()
    expires_in = max(60, min(int(provider.get("expires_in_seconds", 180)), 600))
    record = {"verification_id": verification_id, "customer_id": payload.customer_id, "provider": AADHAAR_AUTH_PROVIDER_NAME, "provider_transaction_id": provider_transaction_id, "purpose": payload.purpose, "consent_reference": payload.consent_reference, "proposed_disbursal_amount": payload.proposed_disbursal_amount, "owner_notes": payload.owner_notes, "mobile_number": customer["mobile"], "aadhaar_masked": customer.get("aadhaar_masked") or (f"XXXX XXXX {customer.get('aadhaar_last4')}" if customer.get("aadhaar_last4") else "Stored securely"), "status": "OTP Sent", "requested_at": iso(requested_at), "expires_at": iso(requested_at + timedelta(seconds=expires_in)), "attempt_count": 0, "max_attempts": 3, "resend_count": 0, "max_resends": 3, "resend_available_at": iso(requested_at + timedelta(seconds=30)), "requested_by": user["name"], "requested_by_id": user["id"]}
    await insert_one("identity_verifications", record)
    await audit(user, "aadhaar_otp_requested", "identity_verification", verification_id, {k: v for k, v in record.items() if k not in {"provider_transaction_id"}}, request)
    return {"verification_id": verification_id, "status": "OTP Sent", "masked_destination": provider.get("masked_mobile", "Aadhaar-linked mobile"), "expires_in_seconds": expires_in, "expires_at": record["expires_at"], "attempts_remaining": record["max_attempts"], "resends_remaining": record["max_resends"], "resend_available_at": record["resend_available_at"]}


@app.post("/api/aadhaar/otp/verify")
async def verify_aadhaar_otp(payload: AadhaarOtpVerifyIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    attempt = await find_one("identity_verifications", {"verification_id": payload.verification_id})
    if not attempt: raise HTTPException(404, "Verification request not found")
    if attempt["status"] != "OTP Sent": raise HTTPException(409, "Verification request is no longer pending")
    if parse_date(attempt["expires_at"]) <= now():
        await db.identity_verifications.update_one({"verification_id": payload.verification_id, "status": "OTP Sent"}, {"$set": {"status": "Expired", "completed_at": iso(now())}})
        raise HTTPException(410, "OTP expired. Request a new OTP.")
    provider = await aadhaar_provider_call("/otp/verify", {"transaction_id": attempt["provider_transaction_id"], "otp": payload.otp})
    verified = provider.get("verified") is True or str(provider.get("status", "")).lower() in {"verified", "success", "y"}
    stamp = iso(now()); final_status = "Verified" if verified else "OTP Sent"
    if not verified:
        new_attempt_count = int(attempt.get("attempt_count", 0)) + 1
        max_attempts = int(attempt.get("max_attempts", 3))
        remaining = max(max_attempts - new_attempt_count, 0)
        next_status = "Locked" if remaining == 0 else "OTP Sent"
        result = await db.identity_verifications.update_one(
            {"verification_id": payload.verification_id, "status": "OTP Sent", "attempt_count": int(attempt.get("attempt_count", 0))},
            {"$set": {"status": next_status, "last_failed_at": stamp}, "$inc": {"attempt_count": 1}},
        )
        if result.modified_count != 1: raise HTTPException(409, "OTP state changed. Please refresh and try again.")
        event = {"verification_id": payload.verification_id, "event": "OTP verification failed", "attempt_number": new_attempt_count, "attempts_remaining": remaining, "timestamp": stamp, "actor_id": user["id"]}
        await insert_one("identity_verification_events", event)
        await audit(user, "aadhaar_otp_verification_failed", "identity_verification", payload.verification_id, event, request)
        if remaining == 0: raise HTTPException(423, "OTP locked after 3 incorrect attempts. Request a new OTP.")
        raise HTTPException(422, f"Incorrect OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
    public_log = {"verification_id": attempt["verification_id"], "client_id": attempt["customer_id"], "aadhaar_reference": attempt["aadhaar_masked"], "mobile_number": attempt["mobile_number"], "otp_status": final_status, "verified_at": stamp if verified else None, "attempted_at": stamp, "disbursed_amount": attempt["proposed_disbursal_amount"], "owner_notes": attempt["owner_notes"], "purpose": attempt["purpose"], "consent_reference": attempt["consent_reference"], "provider": attempt["provider"], "provider_response_reference": provider.get("response_reference") or provider.get("request_id"), "created_by": user["name"]}
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            result = await db.identity_verifications.update_one({"verification_id": payload.verification_id, "status": "OTP Sent"}, {"$set": {"status": final_status, "completed_at": stamp}}, session=session)
            if result.modified_count != 1: raise HTTPException(409, "Verification request was already completed")
            await db.verification_logs.insert_one(deepcopy(public_log), session=session)
            await db.customers.update_one(
                {"customer_id": attempt["customer_id"]},
                {"$set": {"status": "Verified", "aadhaar_verified_at": stamp, "aadhaar_verification_id": payload.verification_id, "aadhaar_verification_provider": attempt["provider"]}},
                session=session,
            )
            await db.verification_events.insert_one({"customer_id": attempt["customer_id"], "status": "Verified", "reason": "Automatic Aadhaar OTP verification", "verification_id": payload.verification_id, "provider": attempt["provider"], "timestamp": stamp, "updated_by": user["name"]}, session=session)
            await audit(user, "aadhaar_otp_verification_completed", "identity_verification", payload.verification_id, public_log, request, session=session)
    return public_log


@app.post("/api/aadhaar/otp/resend")
async def resend_aadhaar_otp(payload: AadhaarOtpResendIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    attempt = await find_one("identity_verifications", {"verification_id": payload.verification_id})
    if not attempt: raise HTTPException(404, "Verification request not found")
    if attempt.get("status") not in {"OTP Sent", "Expired"}: raise HTTPException(409, "This verification cannot be resent. Start a new verification.")
    if int(attempt.get("resend_count", 0)) >= int(attempt.get("max_resends", 3)): raise HTTPException(429, "Maximum OTP resends reached. Start a new verification.")
    available_at = parse_date(attempt.get("resend_available_at"))
    if available_at > now():
        wait_seconds = max(int((available_at - now()).total_seconds()) + 1, 1)
        raise HTTPException(429, f"Please wait {wait_seconds} seconds before resending OTP.")
    provider = await aadhaar_provider_call("/otp/resend", {"transaction_id": attempt["provider_transaction_id"]})
    stamp = now(); expires_in = max(60, min(int(provider.get("expires_in_seconds", 180)), 600))
    next_transaction_id = provider.get("transaction_id") or provider.get("txn_id") or attempt["provider_transaction_id"]
    next_resend_count = int(attempt.get("resend_count", 0)) + 1
    await db.identity_verifications.update_one({"verification_id": payload.verification_id}, {"$set": {"provider_transaction_id": next_transaction_id, "status": "OTP Sent", "expires_at": iso(stamp + timedelta(seconds=expires_in)), "resend_available_at": iso(stamp + timedelta(seconds=30)), "attempt_count": 0}, "$inc": {"resend_count": 1}})
    event = {"verification_id": payload.verification_id, "event": "OTP resent", "resend_number": next_resend_count, "timestamp": iso(stamp), "actor_id": user["id"]}
    await insert_one("identity_verification_events", event)
    await audit(user, "aadhaar_otp_resent", "identity_verification", payload.verification_id, event, request)
    return {"verification_id": payload.verification_id, "status": "OTP Sent", "expires_in_seconds": expires_in, "expires_at": iso(stamp + timedelta(seconds=expires_in)), "attempts_remaining": int(attempt.get("max_attempts", 3)), "resends_remaining": int(attempt.get("max_resends", 3)) - next_resend_count, "resend_available_at": iso(stamp + timedelta(seconds=30))}


@app.get("/api/identity-verifications")
async def identity_verification_logs(customer_id: str = "", user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> list[dict[str, Any]]:
    query = {"client_id": customer_id} if customer_id else {}
    return sorted(await find_many("verification_logs", query), key=lambda x: x["attempted_at"], reverse=True)


@app.get("/api/aadhaar/access-requests")
async def aadhaar_access_requests(user: dict[str, Any] = Depends(require("owner", "manager"))) -> list[dict[str, Any]]:
    return sorted(await find_many("aadhaar_access_requests"), key=lambda x: x["requested_at"], reverse=True)


@app.post("/api/aadhaar/access-requests/{access_request_id}/decision")
async def decide_aadhaar_access(access_request_id: str, payload: AadhaarAccessDecisionIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    record = await find_one("aadhaar_access_requests", {"request_id": access_request_id})
    if not record: raise HTTPException(404, "Access request not found")
    if record["status"] != "Pending": raise HTTPException(409, "Access request was already decided")
    if record["requested_by_id"] == user["id"]: raise HTTPException(403, "Requester cannot approve their own Aadhaar access")
    status_value = "Approved" if payload.decision.strip().title() == "Approve" else "Rejected"
    updates = {"status": status_value, "decided_at": iso(now()), "decided_by": user["name"], "decided_by_id": user["id"], "checker_comments": payload.comments}
    if status_value == "Approved": updates["expires_at"] = iso(now() + timedelta(minutes=5)); updates["remaining_views"] = 1
    if USE_MEMORY:
        record.update(updates); await replace_one("aadhaar_access_requests", {"request_id": access_request_id}, record)
    else:
        result = await db.aadhaar_access_requests.update_one({"request_id": access_request_id, "status": "Pending"}, {"$set": updates})
        if result.modified_count != 1: raise HTTPException(409, "Access request was already decided")
    await audit(user, f"aadhaar_access_{status_value.lower()}", "aadhaar_access_request", access_request_id, {"customer_id": record["customer_id"], "purpose": record["purpose"], "comments": payload.comments}, request)
    return {**record, **updates}


@app.get("/api/customers/{customer_id}/aadhaar")
async def unmask_aadhaar(customer_id: str, access_request_id: str, request: Request, response: Response, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, str]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer or not customer.get("aadhaar_encrypted"): raise HTTPException(404, "Aadhaar not found")
    if customer.get("aadhaar_consent_status") != "Active": raise HTTPException(409, "Customer consent is not active")
    access = await find_one("aadhaar_access_requests", {"request_id": access_request_id, "customer_id": customer_id})
    if not access or access.get("status") != "Approved" or access.get("requested_by_id") != user["id"]: raise HTTPException(403, "Approved purpose-bound access request is required")
    if parse_date(access["expires_at"]) <= now() or int(access.get("remaining_views", 0)) < 1: raise HTTPException(410, "Aadhaar access approval expired or was already used")
    if USE_MEMORY:
        access["remaining_views"] = 0; access["used_at"] = iso(now()); await replace_one("aadhaar_access_requests", {"request_id": access_request_id}, access)
    else:
        result = await db.aadhaar_access_requests.update_one({"request_id": access_request_id, "remaining_views": {"$gt": 0}}, {"$inc": {"remaining_views": -1}, "$set": {"used_at": iso(now())}})
        if result.modified_count != 1: raise HTTPException(410, "Aadhaar access was already consumed")
    response.headers["Content-Disposition"] = "inline"
    response.headers["X-Download-Options"] = "noopen"
    response.headers["Cache-Control"] = "no-store, private, max-age=0"
    await audit(user, "aadhaar_viewed", "aadhaar_access_request", access_request_id, {"customer_id": customer_id, "purpose": access["purpose"], "case_reference": access["case_reference"]}, request)
    return {"aadhaar": decrypt_aadhaar(customer["aadhaar_encrypted"]), "purpose": access["purpose"]}


@app.post("/api/customers/{customer_id}/aadhaar-consent/withdraw")
async def withdraw_aadhaar_consent(customer_id: str, payload: ConsentWithdrawalIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer or not customer.get("aadhaar_encrypted"): raise HTTPException(404, "Aadhaar record not found")
    stamp = iso(now()); updates = {"aadhaar_consent_status": "Withdrawn", "aadhaar_consent_withdrawn_at": stamp, "aadhaar_consent_withdrawal_reference": payload.customer_request_reference}
    if USE_MEMORY:
        customer.update(updates); await replace_one("customers", {"customer_id": customer_id}, customer)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.customers.update_one({"customer_id": customer_id}, {"$set": updates}, session=session)
                await db.aadhaar_consents.update_many({"customer_id": customer_id, "status": "Active"}, {"$set": {"status": "Withdrawn", "withdrawn_at": stamp, "withdrawal_reason": payload.reason, "customer_request_reference": payload.customer_request_reference}}, session=session)
                await db.aadhaar_access_requests.update_many({"customer_id": customer_id, "status": "Approved"}, {"$set": {"status": "Revoked", "revoked_at": stamp}}, session=session)
                await audit(user, "aadhaar_consent_withdrawn", "customer", customer_id, {"reason": payload.reason, "customer_request_reference": payload.customer_request_reference}, request, session=session)
    return {"customer_id": customer_id, "consent_status": "Withdrawn", "access_revoked": True}


@app.post("/api/customers/{customer_id}/aadhaar-deletion-requests")
async def request_aadhaar_deletion(customer_id: str, payload: AadhaarDeletionRequestIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer or not customer.get("aadhaar_encrypted"): raise HTTPException(404, "Aadhaar record not found")
    seq = await next_sequence("ADR", "request_id", "aadhaar_deletion_requests")
    record = {"request_id": f"ADR-{seq:09d}", "customer_id": customer_id, **payload.model_dump(), "status": "Pending Approval", "requested_at": iso(now()), "requested_by": user["name"], "requested_by_id": user["id"]}
    await insert_one("aadhaar_deletion_requests", record); await audit(user, "aadhaar_deletion_requested", "aadhaar_deletion_request", record["request_id"], {"customer_id": customer_id, "reason": payload.reason}, request)
    return record


@app.post("/api/aadhaar/deletion-requests/{deletion_request_id}/approve")
async def approve_aadhaar_deletion(deletion_request_id: str, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    record = await find_one("aadhaar_deletion_requests", {"request_id": deletion_request_id})
    if not record: raise HTTPException(404, "Deletion request not found")
    if record["status"] != "Pending Approval": raise HTTPException(409, "Deletion request was already processed")
    if record["requested_by_id"] == user["id"]: raise HTTPException(403, "Requester cannot approve Aadhaar deletion")
    stamp = iso(now()); customer_id = record["customer_id"]
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            await db.customers.update_one({"customer_id": customer_id}, {"$unset": {"aadhaar_encrypted": "", "aadhaar_hash": "", "aadhaar_key_version": "", "aadhaar_last4": ""}, "$set": {"aadhaar_consent_status": "Deleted", "aadhaar_deleted_at": stamp}}, session=session)
            await db.aadhaar_deletion_requests.update_one({"request_id": deletion_request_id, "status": "Pending Approval"}, {"$set": {"status": "Completed", "approved_at": stamp, "approved_by": user["name"], "approved_by_id": user["id"]}}, session=session)
            await db.aadhaar_access_requests.update_many({"customer_id": customer_id, "status": {"$in": ["Pending", "Approved"]}}, {"$set": {"status": "Revoked", "revoked_at": stamp}}, session=session)
            await audit(user, "aadhaar_cryptographic_deletion", "aadhaar_deletion_request", deletion_request_id, {"customer_id": customer_id, "result": "Encrypted Aadhaar and lookup hash removed"}, request, session=session)
    return {"request_id": deletion_request_id, "status": "Completed", "customer_id": customer_id}


def risk_score(data: dict[str, Any]) -> int:
    score = 72
    score += 8 if len(data.get("mobile", "")) >= 10 else -8
    score += 6 if data.get("guarantor") else -12
    score += {"KUN": 2, "SLM": 5, "NMK": -2, "ERD": 1}.get(data.get("area"), 0)
    score += random.randint(-6, 10)
    return max(20, min(98, score))


@app.get("/api/loans")
async def loans(q: str = "", status_filter: str = "", loan_type: str = "", area: str = "", collector_id: str = "", user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    rows = [await enrich_loan(x) for x in await find_many("loans")]
    customers_map = {c["customer_id"]: await customer_view(c) for c in await find_many("customers")}
    out = []
    for loan in rows:
        c = customers_map.get(loan["customer_id"], {})
        item = {**loan, "customer_name": c.get("name", ""), "area": c.get("area", ""), "mobile": c.get("mobile", "")}
        out.append(item)
    if user["role"] == "collector":
        out = [x for x in out if x["collector_id"] == user["id"]]
    ql = q.lower().strip()
    if ql:
        out = [r for r in out if ql in " ".join([r["loan_id"], r["customer_id"], r["customer_name"], r["mobile"], r["area"]]).lower()]
    if status_filter:
        out = [r for r in out if r["status"] == status_filter]
    if loan_type:
        out = [r for r in out if r["loan_type"] == loan_type]
    if area:
        out = [r for r in out if r["area"] == area]
    if collector_id:
        out = [r for r in out if r["collector_id"] == collector_id]
    return out


@app.post("/api/loan-quotes")
async def loan_quote(payload: LoanIn, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    if abs(payload.interest_rate - 2.14) > 0.000001:
        raise HTTPException(422, "New loans must use the approved annual interest rate of 2.14%")
    borrow = parse_date(payload.borrow_date)
    schedule = build_amortization(payload, borrow)
    return {
        "quote_id": f"QTE-{uuid.uuid4().hex[:12].upper()}", "generated_at": iso(now()),
        "sanctioned_amount": payload.principal, "net_disbursed_amount": schedule["net_disbursed"],
        "annual_interest_rate": payload.interest_rate, "interest_method": payload.interest_method,
        "apr": schedule["apr"], "processing_fee": schedule["processing_fee"], "tax_on_fee": schedule["tax"],
        "periodic_instalment": schedule["emi"], "total_interest": schedule["interest_total"],
        "total_repayment": schedule["total_repayment"], "first_due_date": schedule["first_due_date"],
        "maturity_date": schedule["maturity_date"], "moratorium_periods": payload.moratorium_periods,
        "late_fee": payload.late_fee, "preclosure_charge_rate": payload.preclosure_charge_rate,
        "schedule": schedule["rows"], "requires_borrower_acknowledgement_before_disbursement": True,
    }


@app.get("/api/loans/{loan_id}/schedule")
async def get_loan_schedule(loan_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    if user["role"] == "collector" and loan.get("collector_id") != user["id"]:
        raise HTTPException(403, "Collector can only view assigned loans")
    version = int(loan.get("schedule_version", 1))
    schedule = await find_one("loan_schedules", {"loan_id": loan_id, "version": version})
    if not schedule:
        raise HTTPException(404, "This legacy loan has no immutable amortization schedule")
    return schedule


@app.get("/api/loans/{loan_id}/kfs")
async def loan_kfs(loan_id: str, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    customer = await customer_view(await find_one("customers", {"customer_id": loan["customer_id"]}))
    schedule = await find_one("loan_schedules", {"loan_id": loan_id, "version": int(loan.get("schedule_version", 1))})
    if not schedule:
        raise HTTPException(409, "Generate and approve a schedule before issuing a KFS")
    return {
        "document": "Key Facts Statement", "loan_id": loan_id, "borrower": {"customer_id": customer["customer_id"], "name": customer["name"]},
        "sanctioned_amount": loan["principal"], "net_disbursed_amount": loan["net_disbursed"],
        "annual_interest_rate": loan["interest_rate"], "interest_method": loan["interest_method"],
        "apr": loan["apr"], "tenor_periods": loan["repayment_period"], "repayment_frequency": "Daily" if loan["loan_type"] == "Daily 100-Day" else "Weekly" if loan["loan_type"] == "Weekly" else "Monthly",
        "periodic_instalment": loan["emi"], "total_interest": loan["contract_interest"], "total_repayment": loan["total_repayment"],
        "processing_fee": loan["processing_fee"], "tax_on_fee": loan["tax_amount"],
        "moratorium_periods": loan["moratorium_periods"], "moratorium_interest_capitalized": loan["moratorium_interest_capitalized"],
        "late_fee": loan["late_fee"], "preclosure_charge_rate": loan["preclosure_charge_rate"],
        "first_due_date": loan["first_due_date"], "maturity_date": loan["maturity_date"],
        "schedule_version": loan["schedule_version"], "schedule": schedule["rows"],
        "generated_at": iso(now()), "disclaimer": "Charges not disclosed in this KFS must not be collected from the borrower.",
    }


@app.get("/api/loans/{loan_id}/preclosure-quote")
async def preclosure_quote(loan_id: str, quote_date: Optional[str] = None, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    quote_at = parse_date(quote_date)
    schedule = await find_one("loan_schedules", {"loan_id": loan_id, "version": int(loan.get("schedule_version", 1))})
    if not schedule:
        raise HTTPException(409, "Legacy loan requires schedule migration")
    payments = [p for p in await find_many("payments", {"loan_id": loan_id}) if p.get("status", "Posted") != "Reversed"]
    principal_paid = sum(int(p.get("allocation", {}).get("principal_paise", 0)) for p in payments)
    interest_paid = sum(int(p.get("allocation", {}).get("interest_paise", 0)) for p in payments)
    principal_due = max(to_paise(loan["principal"]) - principal_paid, 0)
    accrued_interest = sum(to_paise(row["interest"]) for row in schedule["rows"] if parse_date(row["due_date"]) <= quote_at)
    interest_due = max(accrued_interest - interest_paid, 0)
    penalty_due = (await loan_component_balances(loan))["penalty_balance_paise"]
    charge = to_paise(Decimal(principal_due) / 100 * Decimal(str(loan.get("preclosure_charge_rate", 0))) / 100)
    total = principal_due + interest_due + penalty_due + charge
    return {"loan_id": loan_id, "quote_date": quote_at.date().isoformat(), "principal": from_paise(principal_due), "accrued_interest": from_paise(interest_due), "penal_charges": from_paise(penalty_due), "preclosure_charge": from_paise(charge), "total": from_paise(total), "valid_for_date_only": True}


def revised_schedule_input(loan: dict[str, Any], principal: float, annual_rate: float, periods: int, effective: datetime, moratorium: int = 0) -> LoanIn:
    first_due = effective + timedelta(days=1) if loan["loan_type"] == "Daily 100-Day" else effective + timedelta(days=7) if loan["loan_type"] == "Weekly" else add_months(effective, 1)
    return LoanIn(
        customer_id=loan["customer_id"], principal=principal, interest_rate=annual_rate,
        loan_type=loan["loan_type"], repayment_period=periods, collector_id=loan["collector_id"],
        borrow_date=iso(effective), disbursement_mode=loan.get("disbursement_mode", "Cash"),
        interest_method=loan.get("interest_method", "Reducing"), processing_fee=0, tax_rate=0,
        first_due_date=iso(first_due), moratorium_periods=moratorium,
        moratorium_interest_capitalized=loan.get("moratorium_interest_capitalized", True),
        preclosure_charge_rate=loan.get("preclosure_charge_rate", 0), late_fee=loan.get("late_fee", 0),
        kfs_acknowledgement_reference="REVISED-CONTRACT",
    )


@app.post("/api/loans/{loan_id}/part-payment")
async def part_payment(loan_id: str, payload: PartPaymentIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan or loan.get("contract_version", 1) < 2:
        raise HTTPException(409, "Part-payment recalculation requires a versioned amortization contract")
    effective = parse_date(payload.effective_date)
    balances = await loan_component_balances(loan)
    amount = to_paise(payload.amount)
    if amount > balances["principal_balance_paise"]:
        raise HTTPException(409, "Part-payment exceeds outstanding principal")
    old_schedule = await find_one("loan_schedules", {"loan_id": loan_id, "version": int(loan["schedule_version"])})
    remaining_periods = max(sum(1 for row in old_schedule["rows"] if parse_date(row["due_date"]) > effective), 1)
    new_principal = from_paise(balances["principal_balance_paise"] - amount)
    if new_principal <= 0:
        raise HTTPException(409, "Use the pre-closure workflow when paying all remaining principal")
    schedule_input = revised_schedule_input(loan, new_principal, loan["interest_rate"], remaining_periods, effective)
    if payload.strategy == "Reduce Tenor":
        target_emi = Decimal(str(loan["emi"]))
        for candidate in range(1, remaining_periods + 1):
            candidate_input = revised_schedule_input(loan, new_principal, loan["interest_rate"], candidate, effective)
            candidate_schedule = build_amortization(candidate_input, effective)
            if Decimal(str(candidate_schedule["emi"])) <= target_emi:
                schedule_input = candidate_input
                break
    schedule = build_amortization(schedule_input, effective)
    version = int(loan["schedule_version"]) + 1
    part_id = f"PPT-{await next_sequence('PPT', 'part_payment_id', 'part_payments'):08d}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    record = {"part_payment_id": part_id, "loan_id": loan_id, **payload.model_dump(), "amount": from_paise(amount), "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "schedule_version": version, "posted_by": user["name"]}
    lines = [ledger_line(cash_account(payload.mode), debit_paise=amount, loan_id=loan_id), ledger_line("1100", credit_paise=amount, loan_id=loan_id)]
    interest_paid = sum(int(p.get("allocation", {}).get("interest_paise", 0)) for p in await find_many("payments", {"loan_id": loan_id}) if p.get("status", "Posted") != "Reversed")
    new_interest_paise = to_paise(schedule["interest_total"])
    interest_difference = new_interest_paise - balances["interest_balance_paise"]
    if interest_difference > 0:
        lines.extend([ledger_line("1200", debit_paise=interest_difference, loan_id=loan_id), ledger_line("4000", credit_paise=interest_difference, loan_id=loan_id)])
    elif interest_difference < 0:
        lines.extend([ledger_line("4000", debit_paise=-interest_difference, loan_id=loan_id), ledger_line("1200", credit_paise=-interest_difference, loan_id=loan_id)])
    loan_updates = {"schedule_version": version, "emi": schedule["emi"], "maturity_date": schedule["maturity_date"], "contract_interest": from_paise(interest_paid + new_interest_paise), "total_repayment": schedule["total_repayment"]}
    schedule_doc = {"loan_id": loan_id, "version": version, "reason": payload.strategy, "consent_reference": payload.borrower_consent_reference, "created_at": iso(now()), **schedule}
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            await db.part_payments.insert_one(deepcopy(record), session=session)
            await db.loan_schedules.insert_one(deepcopy(schedule_doc), session=session)
            await db.loans.update_one({"loan_id": loan_id}, {"$set": loan_updates, "$inc": {"ledger_version": 1}}, session=session)
            await post_journal(entry_id, "part_payment", part_id, f"Part-payment: {payload.strategy}", lines, user, session=session)
    await audit(user, "part_payment_recalculation", "loan", loan_id, record, request)
    return {"part_payment": record, "schedule": schedule_doc, "loan": await enrich_loan(await find_one("loans", {"loan_id": loan_id}))}


@app.post("/api/loans/{loan_id}/restructure")
async def restructure_loan(loan_id: str, payload: RestructureIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan or loan.get("contract_version", 1) < 2:
        raise HTTPException(409, "Restructuring requires a versioned loan contract")
    effective = parse_date(payload.effective_date)
    balances = await loan_component_balances(loan)
    principal = from_paise(balances["principal_balance_paise"])
    schedule_input = revised_schedule_input(loan, principal, payload.annual_rate, payload.remaining_periods, effective, payload.moratorium_periods)
    schedule = build_amortization(schedule_input, effective)
    version = int(loan["schedule_version"]) + 1
    event_id = f"LEV-{await next_sequence('LEV', 'event_id', 'loan_events'):08d}"
    old_interest_remaining = balances["interest_balance_paise"]
    new_interest = to_paise(schedule["interest_total"])
    interest_paid = sum(int(p.get("allocation", {}).get("interest_paise", 0)) for p in await find_many("payments", {"loan_id": loan_id}) if p.get("status", "Posted") != "Reversed")
    journal_id = None
    lines: list[dict[str, Any]] = []
    difference = new_interest - old_interest_remaining
    if difference > 0:
        lines = [ledger_line("1200", debit_paise=difference, loan_id=loan_id), ledger_line("4000", credit_paise=difference, loan_id=loan_id)]
    elif difference < 0:
        lines = [ledger_line("4000", debit_paise=-difference, loan_id=loan_id), ledger_line("1200", credit_paise=-difference, loan_id=loan_id)]
    if lines:
        journal_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    event = {"event_id": event_id, "loan_id": loan_id, "type": "Restructure", **payload.model_dump(), "old_rate": loan["interest_rate"], "old_schedule_version": loan["schedule_version"], "new_schedule_version": version, "timestamp": iso(now()), "approved_by": user["name"], "journal_entry_id": journal_id}
    schedule_doc = {"loan_id": loan_id, "version": version, "reason": "Restructure", "approval_reference": payload.approval_reference, "consent_reference": payload.borrower_consent_reference, "created_at": iso(now()), **schedule}
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            await db.loan_events.insert_one(deepcopy(event), session=session)
            await db.loan_schedules.insert_one(deepcopy(schedule_doc), session=session)
            await db.loans.update_one({"loan_id": loan_id}, {"$set": {"interest_rate": payload.annual_rate, "repayment_period": payload.remaining_periods, "moratorium_periods": payload.moratorium_periods, "schedule_version": version, "emi": schedule["emi"], "maturity_date": schedule["maturity_date"], "contract_interest": from_paise(interest_paid + new_interest), "total_repayment": schedule["total_repayment"], "status": "Restructured"}}, session=session)
            if lines:
                await post_journal(journal_id, "loan_restructure", event_id, f"Restructure {payload.approval_reference}", lines, user, session=session)
    await audit(user, "loan_restructure", "loan", loan_id, event, request)
    return {"event": event, "schedule": schedule_doc, "loan": await enrich_loan(await find_one("loans", {"loan_id": loan_id}))}


@app.post("/api/loans/{loan_id}/write-off")
async def write_off_loan(loan_id: str, payload: WriteOffIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    balances = await loan_component_balances(loan)
    amount = to_paise(payload.amount)
    if amount > balances["balance_paise"]:
        raise HTTPException(409, "Write-off exceeds outstanding balance")
    remaining = amount
    penalty = min(remaining, balances["penalty_balance_paise"]); remaining -= penalty
    interest = min(remaining, balances["interest_balance_paise"]); remaining -= interest
    principal = remaining
    writeoff_id = f"WOF-{await next_sequence('WOF', 'writeoff_id', 'writeoffs'):08d}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    record = {"writeoff_id": writeoff_id, "loan_id": loan_id, **payload.model_dump(), "amount": from_paise(amount), "allocation": {"penalty_paise": penalty, "interest_paise": interest, "principal_paise": principal}, "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "approved_by": user["name"]}
    lines = [ledger_line("5200", debit_paise=amount, loan_id=loan_id)]
    if penalty: lines.append(ledger_line("1300", credit_paise=penalty, loan_id=loan_id))
    if interest: lines.append(ledger_line("1200", credit_paise=interest, loan_id=loan_id))
    if principal: lines.append(ledger_line("1100", credit_paise=principal, loan_id=loan_id))
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            await db.writeoffs.insert_one(deepcopy(record), session=session)
            await db.loans.update_one({"loan_id": loan_id}, {"$set": {"status": "Written Off" if amount == balances["balance_paise"] else loan.get("status", "Active")}}, session=session)
            await post_journal(entry_id, "loan_writeoff", writeoff_id, f"Write-off {payload.approval_reference}", lines, user, session=session)
    await audit(user, "loan_writeoff", "loan", loan_id, record, request)
    return {"writeoff": record, "loan": await enrich_loan(await find_one("loans", {"loan_id": loan_id}))}


@app.post("/api/loans")
async def create_loan(payload: LoanIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": payload.customer_id})
    if not customer:
        raise HTTPException(404, "Customer not found")
    if customer.get("status") not in {"Verified", "Manual Verification Approved"}:
        raise HTTPException(409, "Customer verification must be approved before disbursement")
    identity_verification = await find_one("verification_logs", {"verification_id": payload.identity_verification_id, "client_id": payload.customer_id, "otp_status": "Verified"}) if payload.identity_verification_id else None
    if REQUIRE_VERIFIED_DISBURSAL and not identity_verification:
        raise HTTPException(409, "A successful automatic Aadhaar verification reference is required before disbursal")
    if identity_verification and float(identity_verification.get("disbursed_amount", 0)) != float(payload.principal):
        raise HTTPException(409, "Verified handover amount does not match the loan principal")
    if payload.loan_type not in LOAN_TYPES:
        raise HTTPException(422, "Invalid loan type")
    if abs(payload.interest_rate - 2.14) > 0.000001:
        raise HTTPException(422, "New loans must use the approved annual interest rate of 2.14%")
    collector = await find_one("users", {"id": payload.collector_id})
    if not collector or collector.get("role") not in {"collector", "owner", "manager"} or not collector.get("active", True):
        raise HTTPException(422, "Select an active collector or the self-managed owner")
    borrow = parse_date(payload.borrow_date)
    schedule = build_amortization(payload, borrow)
    loan_seq = await next_sequence("LN", "loan_id", "loans")
    loan_id = f"LN-{loan_seq:09d}"
    loan = {
        "loan_id": loan_id,
        "customer_id": payload.customer_id,
        "principal": payload.principal,
        "interest_rate": payload.interest_rate,
        "loan_type": payload.loan_type,
        "repayment_period": payload.repayment_period,
        "collector_id": payload.collector_id,
        "borrow_date": iso(borrow),
        "status": "Active",
        "created_at": iso(now()),
        "disbursement_mode": payload.disbursement_mode,
        "contract_version": 2,
        "interest_method": payload.interest_method,
        "processing_fee": schedule["processing_fee"], "tax_rate": payload.tax_rate, "tax_amount": schedule["tax"],
        "net_disbursed": schedule["net_disbursed"], "apr": schedule["apr"],
        "first_due_date": schedule["first_due_date"], "maturity_date": schedule["maturity_date"],
        "moratorium_periods": payload.moratorium_periods, "moratorium_interest_capitalized": payload.moratorium_interest_capitalized,
        "preclosure_charge_rate": payload.preclosure_charge_rate, "late_fee": payload.late_fee,
        "emi": schedule["emi"], "contract_interest": schedule["interest_total"],
        "total_repayment": schedule["total_repayment"], "schedule_version": 1,
        "kfs_acknowledgement_reference": payload.kfs_acknowledgement_reference,
        "identity_verification_id": payload.identity_verification_id,
    }
    journal_seq = await next_sequence("JRN", "entry_id", "journal_entries")
    entry_id = f"JRN-{journal_seq:09d}"
    principal_paise = to_paise(payload.principal)
    interest_paise = to_paise(schedule["interest_total"])
    fee_paise = to_paise(schedule["processing_fee"])
    tax_paise = to_paise(schedule["tax"])
    net_paise = to_paise(schedule["net_disbursed"])
    lines = [
        ledger_line("1100", debit_paise=principal_paise, loan_id=loan_id, customer_id=payload.customer_id),
        ledger_line(cash_account(payload.disbursement_mode), credit_paise=net_paise, loan_id=loan_id),
    ]
    if fee_paise:
        lines.append(ledger_line("4200", credit_paise=fee_paise, loan_id=loan_id))
    if tax_paise:
        lines.append(ledger_line("2100", credit_paise=tax_paise, loan_id=loan_id))
    if interest_paise:
        lines.extend([
            ledger_line("1200", debit_paise=interest_paise, loan_id=loan_id, customer_id=payload.customer_id),
            ledger_line("4000", credit_paise=interest_paise, loan_id=loan_id),
        ])
    if USE_MEMORY:
        await insert_one("loans", loan)
        await insert_one("loan_schedules", {"loan_id": loan_id, "version": 1, "reason": "Origination", "created_at": iso(now()), **schedule})
        await post_journal(entry_id, "loan_disbursement", loan_id, f"Loan disbursed to {payload.customer_id}", lines, user)
        await audit(user, "loan_disbursement", "loan", loan_id, loan, request)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.loans.insert_one(deepcopy(loan), session=session)
                await db.loan_schedules.insert_one(deepcopy({"loan_id": loan_id, "version": 1, "reason": "Origination", "created_at": iso(now()), **schedule}), session=session)
                await post_journal(entry_id, "loan_disbursement", loan_id, f"Loan disbursed to {payload.customer_id}", lines, user, session=session)
                await audit(user, "loan_disbursement", "loan", loan_id, loan, request, session=session)
    return await enrich_loan(loan)


@app.post("/api/payments")
async def create_payment(payload: PaymentIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager", "collector"))) -> dict[str, Any]:
    request_id = payload.request_id or request.headers.get("Idempotency-Key")
    if request_id:
        existing_payment = await find_one("payments", {"request_id": request_id})
        if existing_payment:
            return {"payment": existing_payment, "loan": await enrich_loan(await find_one("loans", {"loan_id": existing_payment["loan_id"]})), "receipt": await receipt_payload(existing_payment), "duplicate": True}
    stamp = now()
    receipt_seq = await next_sequence(f"RCP-{stamp.strftime('%Y%m%d')}", "receipt_no", "payments")
    receipt_no = f"RCP-{stamp.strftime('%Y%m%d')}-{receipt_seq:06d}"
    journal_seq = await next_sequence("JRN", "entry_id", "journal_entries")
    entry_id = f"JRN-{journal_seq:09d}"

    async def build_and_post(session: Any = None) -> dict[str, Any]:
        if request_id and not USE_MEMORY:
            duplicate = await db.payments.find_one({"request_id": request_id}, session=session)
            if duplicate:
                return duplicate
        loan = await (find_one("loans", {"loan_id": payload.loan_id}) if USE_MEMORY else db.loans.find_one({"loan_id": payload.loan_id}, session=session))
        if not loan:
            raise HTTPException(404, "Loan not found")
        if user["role"] == "collector" and loan["collector_id"] != user["id"]:
            raise HTTPException(403, "Collector can only collect assigned loans")
        balances = await loan_component_balances(loan, session=session)
        amount_paise = to_paise(payload.amount)
        if amount_paise <= 0 or amount_paise > balances["balance_paise"]:
            raise HTTPException(422, "Payment must not exceed the principal, interest, and penalty outstanding")
        remaining = amount_paise
        penalty_part = min(remaining, balances["penalty_balance_paise"]); remaining -= penalty_part
        interest_part = min(remaining, balances["interest_balance_paise"]); remaining -= interest_part
        principal_part = remaining
        collector_id = payload.collector_id or user["id"]
        collector = await (find_one("users", {"id": collector_id}) if USE_MEMORY else db.users.find_one({"id": collector_id}, session=session))
        debit_account = cash_account(payload.mode)
        if payload.mode == "Cash" and collector and collector.get("role") == "collector":
            debit_account = "1030"
        payment = {
            "receipt_no": receipt_no, "loan_id": payload.loan_id, "customer_id": loan["customer_id"],
            "amount": from_paise(amount_paise), "mode": payload.mode, "collector_id": collector_id,
            "timestamp": iso(stamp), "status": "Posted", "journal_entry_id": entry_id,
            "allocation": {"penalty_paise": penalty_part, "interest_paise": interest_part, "principal_paise": principal_part},
            "identity_verified_at_disbursal": bool(loan.get("identity_verification_id")),
            "identity_verification_id": loan.get("identity_verification_id"),
        }
        if request_id:
            payment["request_id"] = request_id
        lines = [ledger_line(debit_account, debit_paise=amount_paise, loan_id=payload.loan_id, collector_id=collector_id)]
        if penalty_part:
            lines.append(ledger_line("1300", credit_paise=penalty_part, loan_id=payload.loan_id))
        if interest_part:
            lines.append(ledger_line("1200", credit_paise=interest_part, loan_id=payload.loan_id))
        if principal_part:
            lines.append(ledger_line("1100", credit_paise=principal_part, loan_id=payload.loan_id))
        if USE_MEMORY:
            await insert_one("payments", payment)
            await post_journal(entry_id, "payment", receipt_no, f"Receipt {receipt_no}", lines, user)
            await audit(user, "payment_entry", "payment", receipt_no, {"payment": payment, "balance_after_paise": balances["balance_paise"] - amount_paise}, request)
        else:
            await db.loans.update_one({"_id": loan["_id"]}, {"$inc": {"ledger_version": 1}}, session=session)
            await db.payments.insert_one(deepcopy(payment), session=session)
            await post_journal(entry_id, "payment", receipt_no, f"Receipt {receipt_no}", lines, user, session=session)
            await audit(user, "payment_entry", "payment", receipt_no, {"payment": payment, "balance_after_paise": balances["balance_paise"] - amount_paise}, request, session=session)
        return payment

    if USE_MEMORY:
        payment = await build_and_post()
    else:
        async with await mongo_client.start_session() as session:
            try:
                payment = await session.with_transaction(build_and_post)
            except DuplicateKeyError:
                if request_id:
                    payment = await db.payments.find_one({"request_id": request_id})
                    if payment:
                        return {"payment": payment, "loan": await enrich_loan(await find_one("loans", {"loan_id": payment["loan_id"]})), "receipt": await receipt_payload(payment), "duplicate": True}
                raise HTTPException(409, "This payment was already posted")
    loan = await find_one("loans", {"loan_id": payment["loan_id"]})
    after = await enrich_loan(loan)
    return {"payment": payment, "loan": after, "receipt": await receipt_payload(payment)}


async def receipt_payload(payment: dict[str, Any]) -> dict[str, Any]:
    customer = await customer_view(await find_one("customers", {"customer_id": payment["customer_id"]}))
    loan = await enrich_loan(await find_one("loans", {"loan_id": payment["loan_id"]}))
    collector = await find_one("users", {"id": payment["collector_id"]})
    return {
        "receipt_no": payment["receipt_no"],
        "customer": customer,
        "loan": loan,
        "collector": collector["name"] if collector else "Collector",
        "amount": payment["amount"],
        "mode": payment["mode"],
        "timestamp": payment["timestamp"],
        "balance_after": loan["balance"],
        "allocation": payment.get("allocation", {}),
    }


async def account_balance_paise(account_code: str, session: Any = None, dimensions: Optional[dict[str, Any]] = None) -> int:
    query: dict[str, Any] = {"status": "Posted", "lines.account_code": account_code}
    if USE_MEMORY:
        entries = await find_many("journal_entries")
    else:
        entries = await db.journal_entries.find(query, session=session).to_list(length=None)
    balance = 0
    for entry in entries:
        for line in entry.get("lines", []):
            if line.get("account_code") != account_code:
                continue
            if dimensions and any(line.get("dimensions", {}).get(key) != value for key, value in dimensions.items()):
                continue
            balance += int(line.get("debit_paise", 0)) - int(line.get("credit_paise", 0))
    return balance


@app.get("/api/accounting/summary")
async def accounting_summary(user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    balances = {code: await account_balance_paise(code) for code in ACCOUNT_MAP}
    journals = await find_many("journal_entries", {"status": "Posted"})
    opening_balances = await find_many("opening_balances")
    total_debits = sum(int(entry.get("debit_paise", 0)) for entry in journals)
    total_credits = sum(int(entry.get("credit_paise", 0)) for entry in journals)
    return {
        "accounts": [
            {"code": code, "name": ACCOUNT_MAP[code][0], "type": ACCOUNT_MAP[code][1], "balance": from_paise(value if ACCOUNT_MAP[code][1] in {"Asset", "Expense"} else -value)}
            for code, value in balances.items()
        ],
        "cash_on_hand": from_paise(balances["1000"]),
        "cash_with_collectors": from_paise(balances["1030"]),
        "upi_unsettled": from_paise(balances["1010"]),
        "bank_balance": from_paise(balances["1020"]),
        "receivables": from_paise(balances["1100"] + balances["1200"] + balances["1300"]),
        "balanced": total_debits == total_credits and all(int(entry.get("debit_paise", 0)) == int(entry.get("credit_paise", 0)) for entry in journals),
        "journal_count": len(journals),
        "total_debits": from_paise(total_debits),
        "total_credits": from_paise(total_credits),
        "locked_opening_accounts": sorted({row.get("account") for row in opening_balances if row.get("account")}),
        "generated_at": iso(now()),
    }


@app.get("/api/accounting/journals")
async def journal_entries(limit: int = 100, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> list[dict[str, Any]]:
    safe_limit = min(max(limit, 1), 500)
    if USE_MEMORY:
        rows = sorted(await find_many("journal_entries"), key=lambda row: row["timestamp"], reverse=True)
        return rows[:safe_limit]
    return await db.journal_entries.find({}, {"_id": 0}).sort("timestamp", -1).limit(safe_limit).to_list(length=safe_limit)


@app.post("/api/accounting/opening-balances")
async def opening_balance(payload: OpeningBalanceIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    account = cash_account(payload.account)
    if await find_one("opening_balances", {"account_code": account}):
        raise HTTPException(409, "Opening balance for this account is already locked")
    try:
        datetime.strptime(payload.as_of_date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(422, "Opening balance date must use YYYY-MM-DD") from exc
    amount = to_paise(payload.amount)
    opening_id = f"OPN-{account}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    record = {"opening_id": opening_id, "account_code": account, **payload.model_dump(), "amount": from_paise(amount), "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "posted_by": user["name"]}
    lines = [ledger_line(account, debit_paise=amount), ledger_line("3000", credit_paise=amount)]
    if USE_MEMORY:
        await insert_one("opening_balances", record); await post_journal(entry_id, "opening_balance", opening_id, payload.reference, lines, user)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.opening_balances.insert_one(deepcopy(record), session=session)
                await post_journal(entry_id, "opening_balance", opening_id, payload.reference, lines, user, session=session)
    await audit(user, "opening_balance", "account", account, record, request)
    return record


@app.post("/api/accounting/expenses")
async def create_expense(payload: ExpenseIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    account = cash_account(payload.paid_from)
    amount = to_paise(payload.amount)
    if await account_balance_paise(account) < amount:
        raise HTTPException(409, "Expense exceeds the recorded balance of the selected account")
    expense_id = f"EXP-{await next_sequence('EXP', 'expense_id', 'expenses'):08d}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    expense = {"expense_id": expense_id, **payload.model_dump(), "amount": from_paise(amount), "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "created_by": user["name"]}
    lines = [ledger_line("5000", debit_paise=amount, category=payload.expense_category), ledger_line(account, credit_paise=amount)]
    if USE_MEMORY:
        await insert_one("expenses", expense); await post_journal(entry_id, "expense", expense_id, payload.description, lines, user)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.expenses.insert_one(deepcopy(expense), session=session)
                await post_journal(entry_id, "expense", expense_id, payload.description, lines, user, session=session)
    await audit(user, "expense_posted", "expense", expense_id, expense, request)
    return expense


@app.post("/api/accounting/collector-deposits")
async def collector_deposit(payload: CollectorDepositIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    collector = await find_one("users", {"id": payload.collector_id, "role": "collector", "active": True})
    if not collector:
        raise HTTPException(422, "Select an active collector")
    amount = to_paise(payload.amount)
    available = await account_balance_paise("1030", dimensions={"collector_id": payload.collector_id})
    if amount > available:
        raise HTTPException(409, "Deposit exceeds cash currently recorded with this collector")
    destination = cash_account(payload.destination)
    deposit_id = f"DEP-{await next_sequence('DEP', 'deposit_id', 'collector_deposits'):08d}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    deposit = {"deposit_id": deposit_id, **payload.model_dump(), "amount": from_paise(amount), "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "received_by": user["name"]}
    lines = [ledger_line(destination, debit_paise=amount), ledger_line("1030", credit_paise=amount, collector_id=payload.collector_id)]
    if USE_MEMORY:
        await insert_one("collector_deposits", deposit); await post_journal(entry_id, "collector_deposit", deposit_id, payload.reference, lines, user)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.collector_deposits.insert_one(deepcopy(deposit), session=session)
                await post_journal(entry_id, "collector_deposit", deposit_id, payload.reference, lines, user, session=session)
    await audit(user, "collector_cash_deposited", "collector_deposit", deposit_id, deposit, request)
    return deposit


@app.post("/api/accounting/upi-settlements")
async def upi_settlement(payload: SettlementIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    amount = to_paise(payload.amount)
    if amount > await account_balance_paise("1010"):
        raise HTTPException(409, "Settlement exceeds the UPI clearing balance")
    settlement_id = f"SET-{await next_sequence('SET', 'settlement_id', 'settlements'):08d}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    settlement = {"settlement_id": settlement_id, **payload.model_dump(), "amount": from_paise(amount), "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "posted_by": user["name"]}
    lines = [ledger_line("1020", debit_paise=amount), ledger_line("1010", credit_paise=amount)]
    if USE_MEMORY:
        await insert_one("settlements", settlement); await post_journal(entry_id, "upi_settlement", settlement_id, payload.reference, lines, user)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.settlements.insert_one(deepcopy(settlement), session=session)
                await post_journal(entry_id, "upi_settlement", settlement_id, payload.reference, lines, user, session=session)
    await audit(user, "upi_settled", "settlement", settlement_id, settlement, request)
    return settlement


@app.post("/api/loans/{loan_id}/adjustments")
async def loan_adjustment(loan_id: str, payload: LoanAdjustmentIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    balances = await loan_component_balances(loan)
    amount = to_paise(payload.amount)
    if payload.kind == "Interest Waiver" and amount > balances["interest_balance_paise"]:
        raise HTTPException(409, "Waiver exceeds outstanding interest")
    if payload.kind == "Penalty Waiver" and amount > balances["penalty_balance_paise"]:
        raise HTTPException(409, "Waiver exceeds outstanding penalty")
    adjustment_id = f"ADJ-{await next_sequence('ADJ', 'adjustment_id', 'loan_adjustments'):08d}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    adjustment = {"adjustment_id": adjustment_id, "loan_id": loan_id, **payload.model_dump(), "amount": from_paise(amount), "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "posted_by": user["name"]}
    if payload.kind == "Penalty":
        lines = [ledger_line("1300", debit_paise=amount, loan_id=loan_id), ledger_line("4100", credit_paise=amount, loan_id=loan_id)]
    else:
        receivable = "1200" if payload.kind == "Interest Waiver" else "1300"
        lines = [ledger_line("5100", debit_paise=amount, loan_id=loan_id), ledger_line(receivable, credit_paise=amount, loan_id=loan_id)]
    if USE_MEMORY:
        await insert_one("loan_adjustments", adjustment); await post_journal(entry_id, "loan_adjustment", adjustment_id, f"{payload.kind}: {payload.reason}", lines, user)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.loan_adjustments.insert_one(deepcopy(adjustment), session=session)
                await post_journal(entry_id, "loan_adjustment", adjustment_id, f"{payload.kind}: {payload.reason}", lines, user, session=session)
    await audit(user, "loan_adjustment", "loan", loan_id, adjustment, request)
    return {"adjustment": adjustment, "loan": await enrich_loan(loan)}


@app.post("/api/loans/{loan_id}/late-fees/{installment_number}")
async def assess_late_fee(loan_id: str, installment_number: int, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan or loan.get("contract_version", 1) < 2:
        raise HTTPException(409, "Late charge assessment requires a versioned contract")
    late_fee = float(loan.get("late_fee", 0))
    if late_fee <= 0:
        raise HTTPException(409, "No late charge was disclosed in this loan's KFS")
    schedule = await find_one("loan_schedules", {"loan_id": loan_id, "version": int(loan["schedule_version"])})
    row = next((item for item in schedule["rows"] if int(item["number"]) == installment_number), None)
    if not row:
        raise HTTPException(404, "Installment not found")
    if parse_date(row["due_date"]) >= now():
        raise HTTPException(409, "Installment is not overdue")
    request_id = f"LATE-{loan_id}-{loan['schedule_version']}-{installment_number}"
    existing = await find_one("loan_adjustments", {"request_id": request_id})
    if existing:
        return {"adjustment": existing, "loan": await enrich_loan(loan), "duplicate": True}
    cumulative_due = to_paise(sum(Decimal(str(item["payment"])) for item in schedule["rows"] if int(item["number"]) <= installment_number))
    paid = sum(to_paise(p["amount"]) for p in await find_many("payments", {"loan_id": loan_id}) if p.get("status", "Posted") != "Reversed")
    if paid >= cumulative_due:
        raise HTTPException(409, "Installment is already fully paid")
    return await loan_adjustment(loan_id, LoanAdjustmentIn(kind="Penalty", amount=late_fee, reason=f"Contractual late charge for installment {installment_number}", request_id=request_id), request, user)


@app.post("/api/accounting/daily-close")
async def daily_close(payload: DailyCloseIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    try:
        business_date = datetime.strptime(payload.business_date, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise HTTPException(422, "Business date must use YYYY-MM-DD") from exc
    area = "ALL"
    existing = await find_one("daily_closings", {"business_date": business_date, "area": area})
    if existing:
        raise HTTPException(409, "This business day is already closed")
    expected = await account_balance_paise("1000")
    actual = to_paise(payload.actual_cash)
    closing_id = f"CLS-{business_date.replace('-', '')}-{area}"
    closing = {
        "closing_id": closing_id, "business_date": business_date, "area": area,
        "expected_cash": from_paise(expected), "actual_cash": from_paise(actual),
        "variance": from_paise(actual - expected), "notes": payload.notes,
        "status": "Closed", "closed_at": iso(now()), "closed_by": user["name"],
        "cash_with_collectors": from_paise(await account_balance_paise("1030")),
        "upi_unsettled": from_paise(await account_balance_paise("1010")),
        "bank_balance": from_paise(await account_balance_paise("1020")),
    }
    await insert_one("daily_closings", closing)
    await audit(user, "daily_close", "daily_closing", closing_id, closing, request)
    return closing


async def create_reversal_request(original: dict[str, Any], reason: str, user: dict[str, Any], request: Request) -> dict[str, Any]:
    if await find_one("journal_entries", {"reversal_of": original["entry_id"]}):
        raise HTTPException(409, "Journal entry is already reversed")
    pending = await find_one("reversal_requests", {"original_entry_id": original["entry_id"], "status": "Pending"})
    if pending:
        raise HTTPException(409, f"Pending reversal request already exists: {pending['request_id']}")
    request_id = f"RVR-{await next_sequence('RVR', 'request_id', 'reversal_requests'):09d}"
    record = {
        "request_id": request_id, "original_entry_id": original["entry_id"],
        "original_source_type": original["source_type"], "original_source_id": original["source_id"],
        "reason": reason, "status": "Pending", "requested_at": iso(now()),
        "requested_by": user["name"], "requested_by_id": user["id"], "requested_by_role": user["role"],
        "original_snapshot": deepcopy(original),
    }
    await insert_one("reversal_requests", record)
    await audit(user, "reversal_requested", "reversal_request", request_id, {
        "reason": reason, "original_transaction_reference": original["entry_id"],
        "before": deepcopy(original), "after": {"reversal_status": "Pending"},
    }, request)
    return record


@app.post("/api/payments/{receipt_no}/reversal-requests")
async def request_payment_reversal(receipt_no: str, payload: ReversalIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    payment = await find_one("payments", {"receipt_no": receipt_no})
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.get("status") == "Reversed":
        raise HTTPException(409, "Payment is already reversed")
    original = await find_one("journal_entries", {"entry_id": payment.get("journal_entry_id")})
    if not original:
        raise HTTPException(409, "This legacy receipt has no journal entry; migrate it before reversal")
    return await create_reversal_request(original, payload.reason, user, request)


@app.post("/api/accounting/journals/{entry_id}/reversal-requests")
async def request_journal_reversal(entry_id: str, payload: ReversalIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    original = await find_one("journal_entries", {"entry_id": entry_id})
    if not original:
        raise HTTPException(404, "Journal entry not found")
    if original.get("source_type") in {"payment", "loan_disbursement"}:
        raise HTTPException(409, "Use the receipt correction workflow for payments; loan disbursement cancellation requires a dedicated approval workflow")
    return await create_reversal_request(original, payload.reason, user, request)


@app.get("/api/accounting/reversal-requests")
async def list_reversal_requests(status_filter: str = "", user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> list[dict[str, Any]]:
    rows = await find_many("reversal_requests")
    if status_filter:
        rows = [row for row in rows if row.get("status", "").lower() == status_filter.lower()]
    return sorted(rows, key=lambda row: row["requested_at"], reverse=True)


@app.post("/api/accounting/reversal-requests/{request_id}/decision")
async def decide_reversal(request_id: str, payload: ReversalDecisionIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    reversal_request = await find_one("reversal_requests", {"request_id": request_id})
    if not reversal_request:
        raise HTTPException(404, "Reversal request not found")
    if reversal_request["status"] != "Pending":
        raise HTTPException(409, "Reversal request has already been decided")
    if reversal_request["requested_by_id"] == user["id"]:
        raise HTTPException(403, "Maker-checker violation: requester cannot approve or reject their own request")
    decision = payload.decision.strip().title()
    stamp = iso(now())
    decision_fields = {
        "status": "Approved" if decision == "Approve" else "Rejected",
        "decision": decision, "approval_reference": payload.approval_reference,
        "checker_comments": payload.comments, "decided_at": stamp,
        "decided_by": user["name"], "decided_by_id": user["id"], "decided_by_role": user["role"],
    }
    original = await find_one("journal_entries", {"entry_id": reversal_request["original_entry_id"]})
    if not original:
        raise HTTPException(409, "Original immutable journal entry is missing")
    if decision == "Reject":
        if USE_MEMORY:
            reversal_request.update(decision_fields); await replace_one("reversal_requests", {"request_id": request_id}, reversal_request)
        else:
            result = await db.reversal_requests.update_one({"request_id": request_id, "status": "Pending"}, {"$set": decision_fields})
            if result.modified_count != 1: raise HTTPException(409, "Reversal request has already been decided")
        await audit(user, "reversal_rejected", "reversal_request", request_id, {"before": {"status": "Pending"}, "after": decision_fields, "original_transaction_reference": original["entry_id"]}, request)
        return {**reversal_request, **decision_fields}
    if await find_one("journal_entries", {"reversal_of": original["entry_id"]}):
        raise HTTPException(409, "Journal entry is already reversed")
    for line in original["lines"]:
        if line.get("account_type") == "Asset" and int(line.get("debit_paise", 0)):
            dimensions = {"collector_id": line.get("dimensions", {}).get("collector_id")} if line["account_code"] == "1030" else None
            available = await account_balance_paise(line["account_code"], dimensions=dimensions)
            if available < int(line["debit_paise"]):
                raise HTTPException(409, f"Insufficient {line['account_name']} balance; reverse later dependent entries first")
    reversal_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    lines = [ledger_line(line["account_code"], debit_paise=int(line.get("credit_paise", 0)), credit_paise=int(line.get("debit_paise", 0)), **line.get("dimensions", {})) for line in original["lines"]]
    source_collections = {"expense": ("expenses", "expense_id"), "collector_deposit": ("collector_deposits", "deposit_id"), "upi_settlement": ("settlements", "settlement_id"), "loan_adjustment": ("loan_adjustments", "adjustment_id"), "opening_balance": ("opening_balances", "opening_id")}
    source_mapping = source_collections.get(original["source_type"])
    source_before = await find_one(source_mapping[0], {source_mapping[1]: original["source_id"]}) if source_mapping else None
    source_after = deepcopy(source_before) if source_before else None
    if source_after:
        source_after.update({"status": "Reversed", "reversal_entry_id": reversal_id, "reversal_reason": reversal_request["reason"]})
    if original["source_type"] == "payment":
        source_mapping = ("payments", "receipt_no")
        source_before = await find_one("payments", {"receipt_no": original["source_id"]})
        source_after = deepcopy(source_before)
        if source_after:
            source_after.update({"status": "Reversed", "reversed_at": stamp, "reversed_by": user["name"], "reversal_reason": reversal_request["reason"], "reversal_entry_id": reversal_id})
    decision_fields["reversal_entry_id"] = reversal_id
    if USE_MEMORY:
        reversal = await post_journal(reversal_id, "journal_reversal", original["entry_id"], f"Approved reversal {request_id}: {reversal_request['reason']}", lines, user, reversal_of=original["entry_id"])
        if source_mapping and source_after: await replace_one(source_mapping[0], {source_mapping[1]: original["source_id"]}, source_after)
        reversal_request.update(decision_fields); await replace_one("reversal_requests", {"request_id": request_id}, reversal_request)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                result = await db.reversal_requests.update_one({"request_id": request_id, "status": "Pending"}, {"$set": decision_fields}, session=session)
                if result.modified_count != 1: raise HTTPException(409, "Reversal request has already been decided")
                reversal = await post_journal(reversal_id, "journal_reversal", original["entry_id"], f"Approved reversal {request_id}: {reversal_request['reason']}", lines, user, session=session, reversal_of=original["entry_id"])
                if source_mapping and source_after:
                    await db[source_mapping[0]].replace_one({source_mapping[1]: original["source_id"]}, source_after, session=session)
    await audit(user, "reversal_approved_and_posted", "reversal_request", request_id, {
        "original_transaction_reference": original["entry_id"], "reason": reversal_request["reason"],
        "manager_approval": {"checker": user["name"], "checker_id": user["id"], "reference": payload.approval_reference, "comments": payload.comments},
        "before": {"journal": deepcopy(original), "source_record": source_before, "request_status": "Pending"},
        "after": {"reversal_journal": deepcopy(reversal), "source_record": source_after, "request": decision_fields},
    }, request)
    return {**reversal_request, **decision_fields, "reversal": reversal}


@app.get("/api/payments")
async def payments(loan_id: str = "", customer_id: str = "", user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    rows = await find_many("payments")
    if loan_id:
        rows = [r for r in rows if r["loan_id"] == loan_id]
    if customer_id:
        rows = [r for r in rows if r["customer_id"] == customer_id]
    return sorted(rows, key=lambda x: x["timestamp"], reverse=True)


@app.get("/api/verification-events")
async def verification_events(customer_id: str = "", user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    rows = await find_many("verification_events")
    if customer_id:
        rows = [r for r in rows if r["customer_id"] == customer_id]
    return sorted(rows, key=lambda x: x["timestamp"], reverse=True)


@app.get("/api/search")
async def search(q: str = "", status_filter: str = "", scheme: str = "", area: str = "", collector_id: str = "", user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "customers": await customers(q=q, area=area, user=user),
        "loans": await loans(q=q, status_filter=status_filter, loan_type=scheme, area=area, collector_id=collector_id, user=user),
    }


@app.post("/api/reports")
async def reports(payload: ReportRequest, request: Request, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    data = await build_report(payload)
    await audit(user, "report_generation", "report", payload.report_type, payload.model_dump(), request)
    return data


async def build_report(payload: ReportRequest) -> dict[str, Any]:
    loans_rows = [await enrich_loan(x) for x in await find_many("loans")]
    payment_rows = await find_many("payments")
    customers_rows = [await customer_view(x) for x in await find_many("customers")]
    if payload.report_type == "customer-ledger":
        cid = payload.customer_id or (customers_rows[0]["customer_id"] if customers_rows else "")
        return {
            "title": "Customer Ledger",
            "customer": next((c for c in customers_rows if c["customer_id"] == cid), {}),
            "loans": [l for l in loans_rows if l["customer_id"] == cid],
            "payments": [p for p in payment_rows if p["customer_id"] == cid],
        }
    if payload.report_type == "daily-collection":
        day = payload.date or now().date().isoformat()
        daily = [p for p in payment_rows if p["timestamp"][:10] == day]
        return {"title": "Daily Collection Report", "date": day, "payments": daily, "total": round(sum(p["amount"] for p in daily), 2)}
    if payload.report_type == "monthly-cashflow":
        month = payload.month or now().strftime("%Y-%m")
        monthly = [p for p in payment_rows if p["timestamp"][:7] == month]
        disbursed = [l for l in loans_rows if l["borrow_date"][:7] == month]
        return {
            "title": "Monthly Cash Flow",
            "month": month,
            "collections": round(sum(p["amount"] for p in monthly), 2),
            "disbursements": round(sum(l["principal"] for l in disbursed), 2),
            "interest_earned": round(sum(float(l.get("contract_interest", 0)) for l in disbursed), 2),
            "new_customers": len([c for c in customers_rows if c["created_at"][:7] == month]),
            "loans_closed": len([l for l in loans_rows if l["status"] == "Closed"]),
            "new_overdue": len([l for l in loans_rows if l["status"] == "Overdue"]),
        }
    if payload.report_type == "loan-summary":
        return {"title": "Loan Summary", "generated_at": iso(now()), "loans": loans_rows,
                "totals": {"principal": round(sum(l["principal"] for l in loans_rows), 2), "paid": round(sum(l["paid"] for l in loans_rows), 2), "outstanding": round(sum(l["balance"] for l in loans_rows), 2)}}
    if payload.report_type == "defaulters":
        overdue = [l for l in loans_rows if l["status"] == "Overdue"]
        return {"title": "Defaulters Report", "count": len(overdue), "total_overdue": round(sum(l["balance"] for l in overdue), 2), "loans": overdue}
    if payload.report_type == "area-report":
        summary = (await dashboard(await find_one("users", {"role": "owner"})))["area_summary"]
        return {"title": "Area Performance Report", "areas": summary}
    if payload.report_type == "collector-report":
        summary = (await dashboard(await find_one("users", {"role": "owner"})))["collector_breakdown"]
        return {"title": "Collector Performance Report", "collectors": summary}
    if payload.report_type == "profit-report":
        interest = round(sum(max(l["paid"] - l["principal"], 0) for l in loans_rows), 2)
        projected = round(sum(float(l.get("contract_interest", 0)) for l in loans_rows), 2)
        return {"title": "Profit & Interest Report", "realised_interest": interest, "projected_interest": projected, "active_loans": len([l for l in loans_rows if l["status"] == "Active"])}
    if payload.report_type == "recovery-rate":
        due = sum(l["paid"] + l["balance"] for l in loans_rows)
        paid = sum(l["paid"] for l in loans_rows)
        return {"title": "Recovery Rate Report", "recovery_rate_percent": round(paid / due * 100, 2) if due else 0, "collected": round(paid, 2), "portfolio_value": round(due, 2)}
    if payload.report_type == "business-growth":
        return {"title": "Business Growth Report", "cashflow": build_cashflow(payment_rows), "customers": len(customers_rows), "loans": len(loans_rows), "total_disbursed": round(sum(l["principal"] for l in loans_rows), 2)}
    year = str(payload.year or now().year)
    year_payments = [p for p in payment_rows if p["timestamp"][:4] == year]
    year_loans = [l for l in loans_rows if l["borrow_date"][:4] == year]
    return {
        "title": "Annual Report",
        "year": year,
        "collected": round(sum(p["amount"] for p in year_payments), 2),
        "disbursed": round(sum(l["principal"] for l in year_loans), 2),
        "bad_debts": round(sum(l["balance"] for l in loans_rows if l["status"] == "Overdue"), 2),
        "area_contribution": await dashboard(await find_one("users", {"role": "owner"})),
    }


@app.get("/api/audit")
async def audit_log(user: dict[str, Any] = Depends(require("owner"))) -> list[dict[str, Any]]:
    return sorted(await find_many("audit_logs"), key=lambda x: x["timestamp"], reverse=True)


@app.get("/api/audit/integrity")
async def audit_integrity(user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    rows = sorted([row for row in await find_many("audit_logs") if row.get("chain_sequence")], key=lambda x: x["chain_sequence"])
    state = await find_one("audit_chain_state", {"_id": "primary"}) if not USE_MEMORY else None
    current_epoch = int(state.get("epoch", 1)) if state else 1
    previous_by_epoch: dict[int, str] = {}; errors = []; current_errors = []
    for row in rows:
        epoch = int(row.get("chain_epoch", 1)); previous = previous_by_epoch.get(epoch, "GENESIS")
        stored = row.get("entry_hash", ""); unsigned = {k: v for k, v in row.items() if k != "entry_hash"}
        expected = hmac.new(AUDIT_HMAC_KEY, json.dumps(unsigned, sort_keys=True, separators=(",", ":"), default=str).encode(), hashlib.sha256).hexdigest()
        if row.get("previous_hash") != previous or not hmac.compare_digest(stored, expected):
            errors.append(row["id"])
            if epoch == current_epoch: current_errors.append(row["id"])
        previous_by_epoch[epoch] = stored
    if state and previous_by_epoch.get(current_epoch, "GENESIS") != state.get("head_hash"): current_errors.append("CHAIN_HEAD"); errors.append("CHAIN_HEAD")
    return {"valid": not errors, "current_epoch_valid": not current_errors, "current_epoch": current_epoch, "verified_entries": len(rows), "first_sequence": rows[0]["chain_sequence"] if rows else None, "last_sequence": rows[-1]["chain_sequence"] if rows else None, "errors": errors, "historical_integrity_incident": bool(errors and not current_errors), "external_archive_configured": AUDIT_ARCHIVE_DIR is not None}


@app.post("/api/audit/reseal")
async def reseal_audit_chain(payload: AuditResealIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    if USE_MEMORY: raise HTTPException(503, "Audit resealing requires persistent MongoDB")
    before = await db.audit_chain_state.find_one({"_id": "primary"})
    result = await db.audit_chain_state.update_one({"_id": "primary", "epoch": int(before.get("epoch", 1)), "sequence": before["sequence"], "head_hash": before["head_hash"]}, {"$inc": {"epoch": 1}, "$set": {"head_hash": "GENESIS", "resealed_at": iso(now()), "reseal_incident_reference": payload.incident_reference, "prior_head_hash": before["head_hash"]}})
    if result.modified_count != 1: raise HTTPException(409, "Audit chain changed concurrently; retry")
    await audit(user, "audit_chain_resealed", "audit_chain", payload.incident_reference, {"reason": payload.reason, "prior_epoch": before.get("epoch", 1), "prior_head_hash": before["head_hash"]}, request)
    return {"status": "Resealed without altering historical entries", "new_epoch": int(before.get("epoch", 1)) + 1, "incident_reference": payload.incident_reference}


@app.post("/api/audit/archive")
async def archive_audit_log(request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    if not AUDIT_ARCHIVE_DIR: raise HTTPException(503, "Configure AUDIT_ARCHIVE_DIR on separate append-only/WORM storage")
    integrity = await audit_integrity(user)
    if not integrity["valid"]: raise HTTPException(409, "Audit chain integrity verification failed; archive was blocked")
    rows = sorted(await find_many("audit_logs"), key=lambda x: x.get("chain_sequence", 0))
    AUDIT_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_id = f"AUDIT-{now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    body = "\n".join(json.dumps(row, sort_keys=True, default=str) for row in rows).encode()
    signature = hmac.new(AUDIT_HMAC_KEY, body, hashlib.sha256).hexdigest()
    target = AUDIT_ARCHIVE_DIR / f"{archive_id}.jsonl"
    target.write_bytes(body)
    (AUDIT_ARCHIVE_DIR / f"{archive_id}.sha256").write_text(signature, encoding="ascii")
    await audit(user, "audit_archive_created", "audit_archive", archive_id, {"entries": len(rows), "signature": signature, "storage": str(AUDIT_ARCHIVE_DIR)}, request)
    return {"archive_id": archive_id, "entries": len(rows), "signature": signature}


@app.post("/api/aadhaar/rotate-encryption")
async def rotate_aadhaar_encryption(request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    if len(AADHAAR_KEYRING) < 2: raise HTTPException(409, "Load the old and new HSM/KMS key versions before rotation")
    rotated = 0
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            cursor = db.customers.find({"aadhaar_encrypted": {"$exists": True}, "aadhaar_encrypted.key_version": {"$ne": AADHAAR_KEY_VERSION}}, session=session)
            async for customer in cursor:
                plaintext = decrypt_aadhaar(customer["aadhaar_encrypted"])
                await db.customers.update_one({"_id": customer["_id"]}, {"$set": {"aadhaar_encrypted": encrypt_aadhaar(plaintext), "aadhaar_key_version": AADHAAR_KEY_VERSION}}, session=session)
                rotated += 1
            await audit(user, "aadhaar_key_rotation", "key_version", AADHAAR_KEY_VERSION, {"records_rotated": rotated, "key_provider": AADHAAR_KEY_PROVIDER}, request, session=session)
    return {"active_key_version": AADHAAR_KEY_VERSION, "records_rotated": rotated, "key_provider": AADHAAR_KEY_PROVIDER}


@app.get("/api/alerts")
async def alerts(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return await find_many("overdue_alerts")


@app.get("/api/notifications")
async def notifications(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return await find_many("notifications")


@app.post("/api/areas")
async def create_area(payload: AreaIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    code = payload.code.upper()[:3]
    if await find_one("areas", {"code": code}):
        raise HTTPException(409, "Area code already exists")
    area = {"code": code, "name": payload.name, "counter": 0, "active": True}
    await insert_one("areas", area)
    await audit(user, "area_create", "area", code, area, request)
    return area


@app.post("/api/backups/manual")
async def manual_backup(request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    backup_seq = await next_sequence("BKP", "id", "backups")
    backup_id = f"BKP-{backup_seq:06d}"
    if USE_MEMORY:
        raise HTTPException(503, "Real backups require the persistent MongoDB database")
    if len(BACKUP_ENCRYPTION_KEY) != 32:
        raise HTTPException(503, "Backup encryption is not configured")
    collections = [
        "users", "areas", "customers", "loans", "payments", "audit_logs",
        "overdue_alerts", "notifications", "verification_events", "verification_logs", "identity_verifications", "backups", "counters", "audit_chain_state", "aadhaar_consents", "aadhaar_access_requests", "aadhaar_deletion_requests",
        "journal_entries", "reversal_requests", "expenses", "collector_deposits", "settlements", "loan_adjustments", "daily_closings", "opening_balances", "loan_schedules", "loan_events", "part_payments", "writeoffs",
    ]
    snapshot = {
        "format": "stf-encrypted-json-v1",
        "backup_id": backup_id,
        "database": MONGO_DB,
        "created_at": iso(now()),
        "collections": {name: await db[name].find({}).to_list(length=None) for name in collections},
    }
    compressed = gzip.compress(json_util.dumps(snapshot).encode("utf-8"), compresslevel=9)
    nonce = secrets.token_bytes(12)
    encrypted = AESGCM(BACKUP_ENCRYPTION_KEY).encrypt(nonce, compressed, backup_id.encode())
    payload = b"STFBKP1" + nonce + backup_id.encode().ljust(16, b" ") + encrypted
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{backup_id}-{now().strftime('%Y%m%dT%H%M%SZ')}.stfbak"
    final_path = BACKUP_DIR / filename
    temporary_path = BACKUP_DIR / f".{filename}.tmp"
    temporary_path.write_bytes(payload)
    os.replace(temporary_path, final_path)
    offsite_copied = False
    if OFFSITE_BACKUP_DIR is not None:
        OFFSITE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        offsite_path = OFFSITE_BACKUP_DIR / filename
        offsite_temporary = OFFSITE_BACKUP_DIR / f".{filename}.tmp"
        shutil.copyfile(final_path, offsite_temporary)
        os.replace(offsite_temporary, offsite_path)
        offsite_copied = True
    backup = {
        "id": backup_id,
        "timestamp": snapshot["created_at"],
        "status": "Completed",
        "encrypted": True,
        "filename": filename,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "retention_days": 90,
        "offsite_copied": offsite_copied,
    }
    await insert_one("backups", backup)
    await audit(user, "manual_backup", "backup", backup["id"], backup, request)
    return backup


@app.get("/api/backups")
async def backups(user: dict[str, Any] = Depends(require("owner"))) -> list[dict[str, Any]]:
    return await find_many("backups")


@app.get("/api/export/{kind}.csv")
async def export_csv(kind: str, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> StreamingResponse:
    rows = await find_many(kind)
    if not rows:
        rows = []
    headers = sorted({k for row in rows for k in row if not k.startswith("_") and k not in {"aadhaar_encrypted", "password_hash"}})
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(h, "")).replace(",", " ") for h in headers))
    return StreamingResponse(iter(["\n".join(lines)]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={kind}.csv"})
