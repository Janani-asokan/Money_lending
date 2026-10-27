from __future__ import annotations

import base64
import asyncio
import gzip
import hashlib
import hmac
import ipaddress
import json
import os
import random
import secrets
import shutil
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request as UrlRequest, urlopen
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from contextvars import ContextVar
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
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
# Customer mobile OTP over SMS. "android_gateway" sends through the free, open-source
# SMS Gateway for Android app (https://sms-gate.app) using the SIM in your own phone, so
# each OTP costs nothing beyond your normal mobile plan. "console" prints the OTP in the
# server log (development only). "disabled" turns the feature off.
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "disabled" if APP_ENV == "production" else "console").strip().lower()

def normalized_sms_provider() -> str:
    p = SMS_PROVIDER.strip().lower()
    if p in {"smsgate", "sms_gate", "android", "android_gateway"}:
        return "android_gateway"
    if p in {"console", "demo", "mock"}:
        return "console"
    if p in {"disabled", "none", "off", "false", ""}:
        return "disabled"
    return p

SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "https://api.sms-gate.app/3rdparty/v1/message").strip()
SMS_GATEWAY_USERNAME = os.getenv("SMS_GATEWAY_USERNAME", "")
SMS_GATEWAY_PASSWORD = os.getenv("SMS_GATEWAY_PASSWORD", "")
SMS_SENDER_NAME = os.getenv("SMS_SENDER_NAME", "Sri Sakthi Thirumurugan Finance")
# When no SMS gateway is connected, show the OTP on screen instead of sending it. Handy on a
# laptop; on the live (production) server it is off unless explicitly enabled, because an OTP
# shown on screen proves nothing about the customer's phone.
SMS_ALLOW_DEMO_OTP = os.getenv("SMS_ALLOW_DEMO_OTP", "false" if APP_ENV == "production" else "true").strip().lower() == "true"
MOBILE_OTP_TTL_SECONDS = max(60, min(int(os.getenv("MOBILE_OTP_TTL_SECONDS", "300")), 900))
MOBILE_OTP_MAX_ATTEMPTS = 3
MOBILE_OTP_RESEND_SECONDS = 30
MOBILE_OTP_DAILY_LIMIT = int(os.getenv("MOBILE_OTP_DAILY_LIMIT", "10"))
REQUIRE_MOBILE_VERIFIED_DISBURSAL = os.getenv("REQUIRE_MOBILE_VERIFIED_DISBURSAL", "false").lower() == "true"
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()]
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(Path(__file__).resolve().parent.parent / "backups"))).resolve()
BACKUP_KEY_RAW = os.getenv("BACKUP_ENCRYPTION_KEY", "")
BACKUP_ENCRYPTION_KEY = BACKUP_KEY_RAW.encode()
OFFSITE_BACKUP_DIR_RAW = os.getenv("OFFSITE_BACKUP_DIR", "").strip()
OFFSITE_BACKUP_DIR = Path(OFFSITE_BACKUP_DIR_RAW).resolve() if OFFSITE_BACKUP_DIR_RAW else None
LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
PASSWORD_RESET_REQUESTS: dict[str, deque[float]] = defaultdict(deque)
PASSWORD_RESET_TTL_SECONDS = 600
PASSWORD_RESET_MAX_ATTEMPTS = 5
PASSWORD_RESET_RESEND_SECONDS = 60
PASSWORD_RESET_DAILY_LIMIT = 5
# Fallback recovery mobile for the owner account, used until a recovery mobile is saved in Settings.
OWNER_RECOVERY_MOBILE = "".join(ch for ch in os.getenv("OWNER_RECOVERY_MOBILE", "") if ch.isdigit())[-10:]

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
# Monthly interest rate (%) for NEW loans. Editable at loan creation within this range.
# Change the limits here (or via environment variables) - this is the only place.
DEFAULT_MONTHLY_INTEREST_RATE = float(os.getenv("DEFAULT_MONTHLY_INTEREST_RATE", "2.14"))
MIN_MONTHLY_INTEREST_RATE = float(os.getenv("MIN_MONTHLY_INTEREST_RATE", "0.01"))
MAX_MONTHLY_INTEREST_RATE = float(os.getenv("MAX_MONTHLY_INTEREST_RATE", "10"))
# Cash handed to the borrower may be rounded by hand (e.g. 46,433.33 -> 46,430) by up to
# this many rupees either way. The difference is absorbed in the upfront interest.
MAX_CASH_ROUNDING_RUPEES = float(os.getenv("MAX_CASH_ROUNDING_RUPEES", "100"))
# Loan date rules. A new loan may be entered a few days late; anything older must be
# entered as an "existing loan" (money given before this system, no cash moved today).
NEW_LOAN_BACKDATE_DAYS = int(os.getenv("NEW_LOAN_BACKDATE_DAYS", "7"))
EXISTING_LOAN_MAX_AGE_DAYS = int(os.getenv("EXISTING_LOAN_MAX_AGE_DAYS", "1830"))
# Borrower acknowledgement by OTP to the customer's registered mobile:
#   auto     - required whenever this server can send OTPs (default)
#   required - always required (loan creation is blocked if SMS is not working)
#   off      - not used; a typed acknowledgement reference is accepted instead
LOAN_ACK_OTP = os.getenv("LOAN_ACK_OTP", "auto").strip().lower()
LOAN_ACK_OTP_TTL_SECONDS = 600
LOAN_ACK_VALID_MINUTES = 60


# Late charge rule - the ONLY place that decides who is a "defaulter".
# A loan is a defaulter when its oldest unpaid instalment is at least this many days past its due date.
# Change the number here (or set the LATE_CHARGE_DEFAULTER_DAYS environment variable).
LATE_CHARGE_DEFAULTER_DAYS = int(os.getenv("LATE_CHARGE_DEFAULTER_DAYS", "30"))


def apply_cash_rounding(schedule: dict[str, Any], cash_handover: Optional[float]) -> dict[str, Any]:
    """Use the cash amount the owner rounded by hand; the difference adjusts the upfront interest."""
    calculated = Decimal(str(schedule["net_disbursed"]))
    schedule = {**schedule, "calculated_net_disbursed": float(calculated), "cash_rounding_adjustment": 0.0}
    if cash_handover is None:
        return schedule
    cash = Decimal(str(cash_handover)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    difference = cash - calculated
    if abs(difference) > Decimal(str(MAX_CASH_ROUNDING_RUPEES)):
        raise HTTPException(422, f"Cash handed over can be rounded by at most ₹{MAX_CASH_ROUNDING_RUPEES:g} from the calculated ₹{calculated:,.2f}")
    interest = Decimal(str(schedule["interest_total"])) - difference
    if interest < 0:
        raise HTTPException(422, "Rounded cash cannot be more than the sanctioned amount minus charges")
    cashflows = [-cash] + [Decimal(str(row["payment"])) for row in schedule["rows"] if float(row["payment"]) > 0]
    periods_per_year = Decimal(365 if schedule.get("loan_type") == "Daily 100-Day" else 52 if schedule.get("loan_type") == "Weekly" else 12)
    apr = ((Decimal(1) + periodic_irr(cashflows)) ** int(periods_per_year) - 1) * 100
    schedule.update({"net_disbursed": float(cash), "interest_total": float(interest), "cash_rounding_adjustment": float(difference), "apr": float(apr.quantize(Decimal("0.0001")))})
    return schedule


def validate_new_loan_rate(rate: float) -> None:
    if not (MIN_MONTHLY_INTEREST_RATE <= rate <= MAX_MONTHLY_INTEREST_RATE):
        raise HTTPException(422, f"Monthly interest rate must be between {MIN_MONTHLY_INTEREST_RATE:g}% and {MAX_MONTHLY_INTEREST_RATE:g}%")
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
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path not in {"/api/auth/login", "/api/auth/refresh", "/api/auth/forgot-password/send", "/api/auth/forgot-password/reset"}:
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
    # SMS problems never stop the site from starting; they are reported in the log and in
    # Settings -> SMS OTP setup, and OTP sending explains what is missing.
    if not sms_gateway_ready():
        print("[sms] Real SMS is not set up: " + " ".join(sms_setup_problems()), flush=True)
    if problems:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))


class LoginIn(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=6, max_length=200)


def check_strong_password(value: str) -> str:
    if not all((any(c.islower() for c in value), any(c.isupper() for c in value), any(c.isdigit() for c in value), any(not c.isalnum() for c in value))):
        raise ValueError("New password must include uppercase, lowercase, number, and symbol")
    return value


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=6, max_length=200)
    new_password: str = Field(min_length=12, max_length=200)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return check_strong_password(value)


class PasswordResetSendIn(BaseModel):
    username: str = Field(min_length=2, max_length=80)


class PasswordResetIn(BaseModel):
    reset_id: str = Field(min_length=8, max_length=60)
    otp: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=12, max_length=200)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return check_strong_password(value)


class RecoveryMobileIn(BaseModel):
    mobile: str = Field(pattern=r"^[6-9]\d{9}$")
    otp_id: str = Field(min_length=3, max_length=40)


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
    mobile_otp_id: str = Field(default="", max_length=50)

    def model_post_init(self, __context: Any) -> None:
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError("Invalid verification status")

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


class CustomerUpdateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    father_name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(min_length=10, max_length=15)
    address: str = Field(min_length=5, max_length=500)
    area: str = Field(min_length=2, max_length=3)
    guarantor: str = Field(default="", max_length=120)

    @field_validator("name", "father_name", "address", "guarantor")
    @classmethod
    def strip_update_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("mobile")
    @classmethod
    def valid_update_mobile(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 10 or digits[0] not in "6789":
            raise ValueError("Mobile must be a valid 10-digit Indian number")
        return digits

    @field_validator("area")
    @classmethod
    def uppercase_update_area(cls, value: str) -> str:
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
    interest_method: str = "Upfront Monthly Flat"
    processing_fee: float = Field(default=0, ge=0, le=10000000)
    tax_rate: float = Field(default=0, ge=0, le=100)
    first_due_date: Optional[str] = None
    moratorium_periods: int = Field(default=0, ge=0, le=24)
    moratorium_interest_capitalized: bool = True
    preclosure_charge_rate: float = Field(default=0, ge=0, le=10)
    late_fee: float = Field(default=0, ge=0, le=1000000)
    kfs_acknowledgement_reference: str = Field(default="", max_length=120)
    identity_verification_id: Optional[str] = Field(default=None, max_length=120)
    cash_handover: Optional[float] = Field(default=None, gt=0, le=100000000)
    acknowledgement_no: Optional[str] = Field(default=None, max_length=40)
    existing_loan: bool = False
    already_repaid: float = Field(default=0, ge=0, le=100000000)
    repaid_up_to: Optional[str] = None

    @field_validator("disbursement_mode")
    @classmethod
    def valid_disbursement_mode(cls, value: str) -> str:
        if value not in PAYMENT_MODES:
            raise ValueError("Invalid disbursement mode")
        return value

    @field_validator("interest_method")
    @classmethod
    def valid_interest_method(cls, value: str) -> str:
        if value not in {"Upfront Monthly Flat", "Reducing", "Flat"}:
            raise ValueError("Invalid interest method")
        return value


class LoanAckVerifyIn(BaseModel):
    ack_request_id: str = Field(min_length=3, max_length=40)
    otp: str = Field(pattern=r"^\d{6}$")


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
    payment_reference: Optional[str] = Field(default=None, max_length=120)
    payment_type: str = "Collection"

    @field_validator("payment_type")
    @classmethod
    def valid_payment_type(cls, value: str) -> str:
        if value not in {"Collection", "Prepayment"}:
            raise ValueError("Payment type must be Collection or Prepayment")
        return value

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, value: str) -> str:
        if value not in PAYMENT_MODES:
            raise ValueError("Invalid payment mode")
        return value

    def model_post_init(self, __context: Any) -> None:
        if self.mode == "UPI" and len((self.payment_reference or "").strip()) < 3:
            raise ValueError("UPI transaction/reference ID is required")


class LoanClosureIn(BaseModel):
    mode: str
    payment_reference: Optional[str] = Field(default=None, max_length=120)
    reason: str = Field(min_length=5, max_length=300)
    confirmation: str = Field(min_length=3, max_length=40)
    confirmed: bool = False
    request_id: str = Field(min_length=8, max_length=100)
    approval_reference: str = Field(default="", max_length=120)

    @field_validator("mode")
    @classmethod
    def valid_closure_mode(cls, value: str) -> str:
        if value not in PAYMENT_MODES:
            raise ValueError("Invalid closure payment mode")
        return value

    def model_post_init(self, __context: Any) -> None:
        if self.mode != "Cash" and len((self.payment_reference or "").strip()) < 3:
            raise ValueError("UPI or bank reference is required")


class LegacyLoanMigrationIn(BaseModel):
    confirmation: str = Field(min_length=3, max_length=40)
    reason: str = Field(min_length=5, max_length=300)
    approval_reference: str = Field(min_length=3, max_length=120)
    borrower_acknowledgement_reference: str = Field(min_length=3, max_length=120)


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


class MobileOtpVerifyIn(BaseModel):
    otp_id: str = Field(min_length=3, max_length=40)
    otp: str = Field(pattern=r"^\d{6}$")


class RegistrationOtpSendIn(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)

    @field_validator("mobile")
    @classmethod
    def valid_mobile(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 10 or digits[0] not in "6789":
            raise ValueError("Mobile must be a valid 10-digit Indian number")
        return digits


class RegistrationOtpVerifyIn(BaseModel):
    otp_id: str = Field(min_length=3, max_length=40)
    mobile: str = Field(min_length=10, max_length=15)
    otp: str = Field(pattern=r"^\d{6}$")

    @field_validator("mobile")
    @classmethod
    def valid_mobile(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 10 or digits[0] not in "6789":
            raise ValueError("Mobile must be a valid 10-digit Indian number")
        return digits


class LoanAdjustmentIn(BaseModel):
    kind: str
    amount: float = Field(gt=0, le=100000000)
    reason: str = Field(min_length=5, max_length=300)
    request_id: str = Field(min_length=8, max_length=100)
    borrower_acknowledgement_reference: str = Field(default="", max_length=120)
    approval_reference: str = Field(default="", max_length=120)
    confirmed: bool = False

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, value: str) -> str:
        allowed = {"Penalty", "Interest Waiver", "Interest Rebate", "Penalty Waiver"}
        if value not in allowed:
            raise ValueError("Invalid adjustment type")
        return value

    def model_post_init(self, __context: Any) -> None:
        if self.kind == "Interest Rebate":
            if len(self.borrower_acknowledgement_reference.strip()) < 3:
                raise ValueError("Borrower acknowledgement reference is required for an interest rebate")
            if len(self.approval_reference.strip()) < 3:
                raise ValueError("Manager approval reference is required for an interest rebate")
            if not self.confirmed:
                raise ValueError("Confirm the before-and-after balance before posting")


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


class AreaUpdateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: Optional[str] = Field(default=None, pattern=r"^[A-Za-z]{3}$")

    @field_validator("code")
    @classmethod
    def normalize_area_code(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().upper() if value else None


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
    if payload.interest_method == "Upfront Monthly Flat":
        periods = payload.repayment_period
        monthly_rate = Decimal(str(payload.interest_rate)) / 100
        tenure_months = (
            Decimal(periods) / Decimal(30)
            if payload.loan_type == "Daily 100-Day"
            else Decimal(periods) * Decimal(7) / Decimal(30)
            if payload.loan_type == "Weekly"
            else Decimal(periods)
        )
        upfront_interest = (principal * monthly_rate * tenure_months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee = Decimal(str(payload.processing_fee)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax = (fee * Decimal(str(payload.tax_rate)) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net_disbursed = principal - upfront_interest - fee - tax
        if net_disbursed <= 0:
            raise HTTPException(422, "Upfront interest, fee and tax cannot equal or exceed the sanctioned amount")
        first_due = parse_date(payload.first_due_date) if payload.first_due_date else (borrow + timedelta(days=1) if payload.loan_type == "Daily 100-Day" else borrow + timedelta(days=7) if payload.loan_type == "Weekly" else add_months(borrow, 1))
        def due_for(number: int) -> datetime:
            if payload.loan_type == "Daily 100-Day": return first_due + timedelta(days=number - 1)
            if payload.loan_type == "Weekly": return first_due + timedelta(days=7 * (number - 1))
            return add_months(first_due, number - 1)
        base_payment = (principal / periods).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        balance = principal
        rows: list[dict[str, Any]] = []
        for number in range(1, periods + 1):
            opening = balance
            payment = balance if number == periods else min(base_payment, balance)
            balance = (balance - payment).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            rows.append({"number": number, "due_date": iso(due_for(number)), "opening": float(opening), "payment": float(payment), "principal": float(payment), "interest": 0.0, "closing": float(balance), "moratorium": False})
        cashflows = [-net_disbursed] + [Decimal(str(row["payment"])) for row in rows]
        irr = periodic_irr(cashflows)
        periods_per_year = Decimal(365 if payload.loan_type == "Daily 100-Day" else 52 if payload.loan_type == "Weekly" else 12)
        annual_apr = ((Decimal(1) + irr) ** int(periods_per_year) - 1) * 100
        return {
            "rows": rows, "emi": float(base_payment), "principal": float(principal),
            "interest_total": float(upfront_interest), "processing_fee": float(fee), "tax": float(tax),
            "net_disbursed": float(net_disbursed), "apr": float(annual_apr.quantize(Decimal("0.0001"))),
            "first_due_date": iso(first_due), "maturity_date": rows[-1]["due_date"],
            "total_repayment": float(principal), "monthly_interest_rate": float(payload.interest_rate),
            "tenure_months": float(tenure_months.quantize(Decimal("0.0001"))),
            "interest_deduction_basis": "Deducted upfront from sanctioned principal",
            "loan_type": payload.loan_type,
        }
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
    await db.mobile_otps.create_index("otp_id", name="idx_mobile_otps_otp_id", unique=True)
    await db.loan_acknowledgements.create_index("ack_request_id", name="idx_loan_ack_request_id", unique=True)
    await db.loan_acknowledgements.create_index("ack_no", name="idx_loan_ack_no", unique=True, partialFilterExpression={"ack_no": {"$type": "string"}})
    await db.mobile_otps.create_index([("customer_id", 1), ("created_at", -1)], name="idx_mobile_otps_customer_created")
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


def sms_gateway_ready() -> bool:
    return normalized_sms_provider() == "android_gateway" and bool(SMS_GATEWAY_URL and SMS_GATEWAY_USERNAME and SMS_GATEWAY_PASSWORD)


def sms_demo_mode() -> bool:
    """True when OTPs are shown on screen instead of being sent by SMS."""
    return normalized_sms_provider() == "console" or (not sms_gateway_ready() and SMS_ALLOW_DEMO_OTP)


def sms_configured() -> bool:
    return sms_gateway_ready() or sms_demo_mode()


def sms_gateway_base() -> str:
    url = SMS_GATEWAY_URL.rstrip("/")
    return url[: -len("/message")] if url.endswith("/message") else url


def sms_gateway_url_kind() -> str:
    host = (urlparse(SMS_GATEWAY_URL).hostname or "").lower()
    if not host:
        return "missing"
    if host.endswith("sms-gate.app"):
        return "cloud"
    if host == "localhost":
        return "local-network"
    try:
        address = ipaddress.ip_address(host)
        return "local-network" if (address.is_private or address.is_loopback or address.is_link_local) else "custom"
    except ValueError:
        return "custom"


def sms_setup_problems() -> list[str]:
    """Plain-language reasons why real SMS cannot be sent from this server."""
    provider = normalized_sms_provider()
    problems = []
    if provider == "console":
        problems.append("SMS_PROVIDER is set to console/demo, so OTPs are only shown on screen. Set SMS_PROVIDER=android_gateway on this server.")
        return problems
    if provider != "android_gateway":
        problems.append(f"SMS_PROVIDER is '{SMS_PROVIDER or 'not set'}' on this server. Set SMS_PROVIDER=android_gateway.")
    if not SMS_GATEWAY_USERNAME:
        problems.append("SMS_GATEWAY_USERNAME is not set on this server (it is only in your local server/.env, which is never uploaded).")
    if not SMS_GATEWAY_PASSWORD:
        problems.append("SMS_GATEWAY_PASSWORD is not set on this server.")
    if sms_gateway_url_kind() == "local-network":
        problems.append(f"SMS_GATEWAY_URL points to a home/office network address ({urlparse(SMS_GATEWAY_URL).hostname}). An online server cannot reach your phone there. Use https://api.sms-gate.app/3rdparty/v1/message with the app's Cloud server username and password.")
    return problems


def gateway_request(method: str, path: str, body: Optional[dict[str, Any]] = None, timeout: int = 20) -> tuple[int, Any]:
    """Call the SMS Gateway API. Returns (status, parsed JSON or text). Network errors raise URLError/TimeoutError."""
    credentials = base64.b64encode(f"{SMS_GATEWAY_USERNAME}:{SMS_GATEWAY_PASSWORD}".encode()).decode()
    request = UrlRequest(
        f"{sms_gateway_base()}{path}", data=json.dumps(body).encode() if body is not None else None, method=method,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {credentials}", "User-Agent": "MoneyLendingSMS/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except HTTPError as exc:
        raw, status = exc.read(), exc.code
    try:
        return status, json.loads(raw) if raw else {}
    except ValueError:
        return status, raw.decode(errors="replace")[:300]


def gateway_error_message(status: int) -> str:
    if status == 401:
        return "SMS gateway rejected the username/password (401). Use the Cloud server username and password shown in the SMS Gateway app, and update them on this server."
    if status == 403:
        return "SMS gateway refused the request (403). Check the account in the SMS Gateway app is active."
    if status == 404:
        return "SMS gateway address not found (404). SMS_GATEWAY_URL should be https://api.sms-gate.app/3rdparty/v1/message."
    if status == 429:
        return "SMS gateway is rate-limiting this account (429). Wait a minute and try again."
    return f"SMS gateway returned an error ({status}). Try again, or run the SMS check in Settings."


async def send_sms(mobile: str, text: str) -> dict[str, Any]:
    """Send one SMS. Returns {"demo": bool, "gateway_message_id", "gateway_state"}; raises a clear HTTP error otherwise."""
    if sms_gateway_ready():
        def send() -> dict[str, Any]:
            try:
                status, reply = gateway_request("POST", "/message", {"textMessage": {"text": text}, "phoneNumbers": [f"+91{mobile}"]})
            except (URLError, TimeoutError, OSError) as exc:
                if sms_gateway_url_kind() == "local-network":
                    raise HTTPException(424, "This server cannot reach the phone's local network address. Use the cloud gateway URL https://api.sms-gate.app/3rdparty/v1/message.") from exc
                raise HTTPException(424, "SMS gateway could not be reached from this server. Check its internet access, or run the SMS check in Settings.") from exc
            if status >= 400:
                raise HTTPException(424, gateway_error_message(status))
            reply = reply if isinstance(reply, dict) else {}
            return {"demo": False, "gateway_message_id": reply.get("id"), "gateway_state": reply.get("state", "Pending")}
        return await asyncio.to_thread(send)
    if sms_demo_mode():
        print(f"[SMS demo] to +91{mobile}: {text}", flush=True)
        return {"demo": True, "gateway_message_id": None, "gateway_state": "Demo"}
    raise HTTPException(409, "SMS is not set up on this server: " + " ".join(sms_setup_problems()))


def mask_mobile(mobile: str) -> str:
    return f"+91 XXXXXX{mobile[-4:]}" if len(mobile) >= 4 else "registered mobile"


def mobile_otp_hash(otp_id: str, otp: str) -> str:
    return hmac.new(APP_SECRET_KEY.encode(), f"mobile-otp:{otp_id}:{otp}".encode(), hashlib.sha256).hexdigest()


@asynccontextmanager
async def atomic():
    """MongoDB transaction in production; plain sequential writes in demo (in-memory) mode."""
    if USE_MEMORY:
        yield None
        return
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            yield session


async def tx_insert(collection: str, doc: dict[str, Any], session: Any) -> None:
    if USE_MEMORY:
        await insert_one(collection, doc)
    else:
        await db[collection].insert_one(deepcopy(doc), session=session)


async def tx_set(collection: str, query: dict[str, Any], fields: dict[str, Any], session: Any) -> None:
    if USE_MEMORY:
        await update_where(collection, query, fields)
    else:
        await db[collection].update_one(query, {"$set": fields}, session=session)


async def update_where(collection: str, query: dict[str, Any], fields: dict[str, Any], inc: Optional[dict[str, int]] = None) -> bool:
    """Conditionally update one document; returns False when nothing matched (state changed)."""
    if USE_MEMORY:
        for row in STORE.get(collection, []):
            if matches(row, query):
                row.update(deepcopy(fields))
                for key, amount in (inc or {}).items(): row[key] = int(row.get(key, 0)) + amount
                return True
        return False
    update: dict[str, Any] = {"$set": fields}
    if inc: update["$inc"] = inc
    result = await db[collection].update_one(query, update)
    return result.modified_count == 1


def mobile_verified(customer: dict[str, Any]) -> bool:
    return bool(customer.get("mobile_verified_at")) and customer.get("mobile_verified_number") == customer.get("mobile")


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


# Bulk-read cache used while enriching many loans/customers in one request, so list
# screens make a handful of database queries instead of several per loan.
_PREFETCH: ContextVar[Optional[dict[str, Any]]] = ContextVar("_prefetch", default=None)
LOAN_CHILD_COLLECTIONS = ("payments", "loan_adjustments", "part_payments", "writeoffs")


def prefetched_rows(collection: str, loan_id: str) -> Optional[list[dict[str, Any]]]:
    cache = _PREFETCH.get()
    if cache is None or collection not in cache:
        return None
    return cache[collection].get(loan_id, [])


async def area_lookup(code: str) -> Optional[dict[str, Any]]:
    cache = _PREFETCH.get()
    if cache is not None and "areas" in cache:
        return cache["areas"].get(code)
    return await find_one("areas", {"code": code})


async def schedule_lookup(loan: dict[str, Any]) -> Optional[dict[str, Any]]:
    key = (loan["loan_id"], int(loan.get("schedule_version", 1)))
    cache = _PREFETCH.get()
    if cache is not None and "loan_schedules" in cache:
        return cache["loan_schedules"].get(key)
    return await find_one("loan_schedules", {"loan_id": key[0], "version": key[1]})


async def build_prefetch() -> dict[str, Any]:
    cache: dict[str, Any] = {}
    for collection in LOAN_CHILD_COLLECTIONS:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        rows = await find_many(collection)
        rows.sort(key=lambda row: str(row.get("timestamp", "")))
        for row in rows:
            grouped[row.get("loan_id")].append(row)
        cache[collection] = grouped
    cache["loan_schedules"] = {(row.get("loan_id"), int(row.get("version", 1))): row for row in await find_many("loan_schedules")}
    cache["areas"] = {row.get("code"): row for row in await find_many("areas")}
    return cache


async def enrich_loans(loans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    token = _PREFETCH.set(await build_prefetch()) if _PREFETCH.get() is None else None
    try:
        return [await enrich_loan(loan) for loan in loans]
    finally:
        if token is not None:
            _PREFETCH.reset(token)


async def customer_views(customers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    token = _PREFETCH.set({"areas": {row.get("code"): row for row in await find_many("areas")}}) if _PREFETCH.get() is None else None
    try:
        return [await customer_view(customer) for customer in customers]
    finally:
        if token is not None:
            _PREFETCH.reset(token)


def repayment_rows(loan: dict[str, Any], schedule_doc: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    """Instalment rows for a loan. Older (pre-versioned) loans have no stored schedule,
    so one is derived from their contract terms instead of showing 0 instalments."""
    if schedule_doc:
        return [row for row in schedule_doc.get("rows", []) if not row.get("moratorium") and float(row.get("payment", 0)) > 0]
    terms = loan_schedule(loan)
    count = 100 if loan["loan_type"] == "Daily 100-Day" else max(int(loan.get("repayment_period") or (52 if loan["loan_type"] == "Weekly" else 12)), 1)
    remaining = to_paise(terms["total_payable"])
    step = to_paise(terms["installment"])
    borrow = parse_date(loan["borrow_date"])
    rows = []
    for number in range(1, count + 1):
        if remaining <= 0:
            break
        payment = remaining if number == count else min(step, remaining)
        remaining -= payment
        due = borrow + timedelta(days=number) if loan["loan_type"] == "Daily 100-Day" else borrow + timedelta(days=7 * number) if loan["loan_type"] == "Weekly" else add_months(borrow, number)
        rows.append({"number": number, "due_date": iso(due), "payment": from_paise(payment)})
    return rows


async def enrich_loan(loan: dict[str, Any]) -> dict[str, Any]:
    balances = await loan_component_balances(loan)
    paid = from_paise(balances["paid_paise"])
    total_payable = from_paise(balances["total_payable_paise"])
    balance = from_paise(balances["balance_paise"])
    borrow = parse_date(loan["borrow_date"])
    elapsed = max((now() - borrow).days, 0)
    schedule = loan_schedule(loan)
    rows = repayment_rows(loan, await schedule_lookup(loan))
    paid_remaining = Decimal(str(paid))
    installments_paid = 0
    next_due_date = None
    for row in rows:
        due = Decimal(str(row.get("payment", 0)))
        if paid_remaining >= due:
            installments_paid += 1; paid_remaining -= due
        elif next_due_date is None:
            next_due_date = row.get("due_date")
    remaining_installments = max(len(rows) - installments_paid, 0)
    if balance <= 0:
        remaining_installments, next_due_date = 0, None
    elif remaining_installments == 0:
        # Every instalment is paid but charges (e.g. a penalty) are still outstanding.
        remaining_installments = 1
        next_due_date = rows[-1]["due_date"] if rows else iso(now())
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
    def live(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [row for row in rows if row.get("status", "Posted") != "Reversed"]
    if session is None and prefetched_rows("payments", loan["loan_id"]) is not None:
        payments, adjustments, part_payments, writeoffs = (live(prefetched_rows(name, loan["loan_id"])) for name in LOAN_CHILD_COLLECTIONS)
    elif USE_MEMORY:
        payments, adjustments, part_payments, writeoffs = [live(await find_many(name, {"loan_id": loan["loan_id"]})) for name in LOAN_CHILD_COLLECTIONS]
        payments.sort(key=lambda row: str(row.get("timestamp", "")))
    else:
        payments = await db.payments.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).sort("timestamp", 1).to_list(length=None)
        adjustments = await db.loan_adjustments.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).to_list(length=None)
        part_payments = await db.part_payments.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).to_list(length=None)
        writeoffs = await db.writeoffs.find({"loan_id": loan["loan_id"], "status": {"$ne": "Reversed"}}, session=session).to_list(length=None)
    principal = to_paise(loan["principal"])
    upfront_interest = loan.get("interest_collection_basis") == "Upfront Discount"
    interest = 0 if upfront_interest else to_paise(loan.get("contract_interest", Decimal(str(loan["principal"])) * Decimal(str(loan.get("interest_rate", 0))) / 100))
    penalty = sum(to_paise(a["amount"]) for a in adjustments if a["kind"] == "Penalty")
    interest = max(interest - sum(to_paise(a["amount"]) for a in adjustments if a["kind"] == "Interest Waiver"), 0)
    penalty = max(penalty - sum(to_paise(a["amount"]) for a in adjustments if a["kind"] == "Penalty Waiver"), 0)
    principal = max(principal - sum(to_paise(a["amount"]) for a in adjustments if a["kind"] == "Interest Rebate"), 0)
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
    visible["mobile_verified"] = mobile_verified(customer)
    area = await area_lookup(customer.get("area"))
    visible["area_code"] = customer.get("area", "")
    visible["area_name"] = area.get("name", customer.get("area", "")) if area else customer.get("area", "")
    visible["area"] = visible["area_name"]
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
        terms = loan_schedule(loan)
        installment = terms["installment"]
        # Demo payments: never dated in the future and never more than the amount payable.
        remaining = to_paise(terms["total_payable"])
        step_days = 1 if loan_type == "Daily 100-Day" else 30
        due_so_far = max((now() - borrow).days // step_days, 0)
        for p in range(1, due_so_far + 1):
            if remaining <= 0:
                break
            if random.random() < 0.18:
                continue
            pay_dt = borrow + timedelta(days=p * step_days, hours=random.randint(9, 18))
            if pay_dt >= now():
                break
            amount_paise = min(to_paise(installment), remaining)
            remaining -= amount_paise
            await insert_one("payments", {
                "receipt_no": f"RCP-{pay_dt.strftime('%Y%m%d')}-{i:02d}{p:04d}",
                "loan_id": loan_id,
                "customer_id": customer["customer_id"],
                "amount": from_paise(amount_paise),
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
    loans = await enrich_loans(await find_many("loans"))
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


async def late_charge_status(loan: dict[str, Any]) -> dict[str, Any]:
    """Defaulter check for the late-charge rule (see LATE_CHARGE_DEFAULTER_DAYS)."""
    late_fee = float(loan.get("late_fee", 0) or 0)
    info: dict[str, Any] = {
        "is_defaulter": False, "overdue_days": 0, "threshold_days": LATE_CHARGE_DEFAULTER_DAYS,
        "late_fee": late_fee, "next_installment": None, "can_apply": False, "message": "",
    }
    if loan.get("status") in {"Closed", "Written Off"}:
        info["message"] = "Loan is closed."
        return info
    if loan.get("contract_version", 1) < 2:
        info["message"] = "Late charges need a versioned contract."
        return info
    schedule = await find_one("loan_schedules", {"loan_id": loan["loan_id"], "version": int(loan.get("schedule_version", 1))})
    if not schedule:
        info["message"] = "No schedule found."
        return info
    paid = await instalment_paid_paise(loan["loan_id"])
    stamp = now()
    cumulative = 0
    unpaid_overdue: list[dict[str, Any]] = []
    for row in sorted(schedule["rows"], key=lambda item: int(item["number"])):
        cumulative += to_paise(row["payment"])
        if cumulative > paid and parse_date(row["due_date"]) < stamp:
            unpaid_overdue.append(row)
    if unpaid_overdue:
        info["overdue_days"] = max((stamp - parse_date(unpaid_overdue[0]["due_date"])).days, 0)
    info["is_defaulter"] = bool(unpaid_overdue) and info["overdue_days"] >= LATE_CHARGE_DEFAULTER_DAYS
    if not info["is_defaulter"]:
        info["message"] = f"Late charge applies only to defaulters (oldest unpaid instalment at least {LATE_CHARGE_DEFAULTER_DAYS} days overdue). This loan is {info['overdue_days']} day(s) overdue."
        return info
    if late_fee <= 0:
        info["message"] = "No late charge was disclosed in this loan's KFS."
        return info
    for row in unpaid_overdue:
        request_id = f"LATE-{loan['loan_id']}-{loan['schedule_version']}-{int(row['number'])}"
        if not await find_one("loan_adjustments", {"request_id": request_id}):
            info["next_installment"] = int(row["number"])
            info["can_apply"] = True
            return info
    info["message"] = "Late charge is already applied to every overdue instalment."
    return info


async def instalment_paid_paise(loan_id: str) -> int:
    total = 0
    for payment in await find_many("payments", {"loan_id": loan_id}):
        if payment.get("status", "Posted") == "Reversed":
            continue
        allocation = payment.get("allocation")
        if allocation:
            total += int(allocation.get("principal_paise", 0)) + int(allocation.get("interest_paise", 0))
        else:
            total += to_paise(payment["amount"])
    return total


AUTO_CLOSE_REASON = "Balance reached zero - closed automatically"


async def sync_loan_status(loan_id: str, allow_reopen: bool = False) -> Optional[str]:
    """Keep the stored loan status in line with the real balance.

    - balance 0 and loan not Closed / Written Off  -> status becomes "Closed"
    - allow_reopen (used only after an approved reversal): a Closed loan whose
      balance is outstanding again goes back to "Active"
    No payment, ledger or schedule data is touched; only the status fields plus an
    event and an audit entry are written. Safe to call repeatedly.
    """
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        return None
    current = loan.get("status", "Active")
    if current == "Written Off":
        return None
    balances = await loan_component_balances(loan)
    stamp = iso(now())
    if balances["balance_paise"] <= 0 and current != "Closed":
        fields = {"status": "Closed", "closed_at": stamp, "closed_by": "System", "closure_reason": AUTO_CLOSE_REASON}
        event_type, reason, outcome = "Loan Closed", AUTO_CLOSE_REASON, "Closed"
        guard = {"loan_id": loan_id, "status": {"$nin": ["Closed", "Written Off"]}}
    elif allow_reopen and balances["balance_paise"] > 0 and current == "Closed":
        fields = {"status": "Active", "reopened_at": stamp, "reopened_reason": "A reversal made the balance outstanding again"}
        event_type, reason, outcome = "Loan Reopened", fields["reopened_reason"], "Reopened"
        guard = {"loan_id": loan_id, "status": "Closed"}
    else:
        return None
    if USE_MEMORY:
        await replace_one("loans", {"loan_id": loan_id}, {**loan, **fields})
    else:
        result = await db.loans.update_one(guard, {"$set": fields, "$inc": {"ledger_version": 1}})
        if result.modified_count != 1:
            return None
    event_id = f"LEV-{await next_sequence('LEV', 'event_id', 'loan_events'):08d}"
    event = {"event_id": event_id, "loan_id": loan_id, "event_type": event_type, "reason": reason, "approval_reference": "AUTOMATIC", "timestamp": stamp, "posted_by": "System", "previous_status": current}
    await insert_one("loan_events", event)
    await audit(None, "loan_auto_closed" if outcome == "Closed" else "loan_reopened", "loan", loan_id, {"event": event, "balance_paise": balances["balance_paise"]})
    return outcome


async def auto_close_zero_balance_loans() -> int:
    """One-time/idempotent sweep: closes every existing loan whose balance is already 0."""
    closed = 0
    try:
        for row in await find_many("loans"):
            if row.get("status", "Active") in {"Closed", "Written Off"}:
                continue
            if await sync_loan_status(row["loan_id"]) == "Closed":
                closed += 1
        if closed:
            print(f"[auto-close] {closed} loan(s) with zero balance were marked Closed")
    except Exception as exc:  # never block application startup
        print(f"[auto-close] sweep skipped: {exc}")
    return closed


_background_tasks: set = set()


def schedule_auto_close_sweep() -> None:
    """Run the zero-balance sweep in the background so a slow or failing sweep can never delay or break server start-up."""
    task = asyncio.create_task(auto_close_zero_balance_loans())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@app.on_event("startup")
async def startup() -> None:
    global mongo_client, db, USE_MEMORY
    validate_production_config()
    if not MONGO_ENABLED:
        USE_MEMORY = True
        await seed_data()
        schedule_auto_close_sweep()
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
    schedule_auto_close_sweep()


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


def recovery_mobile_for(user: dict[str, Any]) -> str:
    return user.get("recovery_mobile") or (OWNER_RECOVERY_MOBILE if user.get("role") == "owner" and len(OWNER_RECOVERY_MOBILE) == 10 else "")


@app.post("/api/auth/forgot-password/send")
async def send_password_reset_otp(payload: PasswordResetSendIn, request: Request) -> dict[str, Any]:
    client_key = request.client.host if request.client else "unknown"
    requests_log = PASSWORD_RESET_REQUESTS[client_key]
    while requests_log and requests_log[0] < time.time() - 900:
        requests_log.popleft()
    if len(requests_log) >= 5:
        raise HTTPException(429, "Too many reset requests. Try again in 15 minutes.", headers={"Retry-After": "900"})
    requests_log.append(time.time())
    stamp = now()
    # The reply looks the same whether or not the username exists, so it cannot be used to discover accounts.
    reset_id = f"PWR-{secrets.token_urlsafe(18)}"
    result: dict[str, Any] = {
        "reset_id": reset_id, "expires_in_seconds": PASSWORD_RESET_TTL_SECONDS, "resend_in_seconds": PASSWORD_RESET_RESEND_SECONDS,
        "message": "If this username has a recovery mobile number, a 6-digit OTP has been sent to it.",
    }
    user = await find_one("users", {"username": payload.username.strip()})
    mobile = recovery_mobile_for(user) if user and user.get("active", True) else ""
    if not mobile:
        return result
    history = await find_many("password_resets", {"user_id": user["id"]})
    if sum(1 for row in history if parse_date(row["created_at"]) > stamp - timedelta(days=1)) >= PASSWORD_RESET_DAILY_LIMIT:
        raise HTTPException(429, "Daily reset limit reached for this account. Try again tomorrow.")
    latest = max(history, key=lambda row: row["created_at"], default=None)
    if latest and latest.get("status") == "Sent":
        available_at = parse_date(latest["created_at"]) + timedelta(seconds=PASSWORD_RESET_RESEND_SECONDS)
        if available_at > stamp:
            raise HTTPException(429, f"Please wait {int((available_at - stamp).total_seconds()) + 1} seconds before requesting another OTP.")
    otp = f"{secrets.randbelow(1_000_000):06d}"
    delivery = await send_sms(mobile, f"{otp} is your OTP to reset your {SMS_SENDER_NAME} login password. Valid for {PASSWORD_RESET_TTL_SECONDS // 60} minutes. Do not share it with anyone.")
    for row in history:
        if row.get("status") == "Sent":
            await update_where("password_resets", {"reset_id": row["reset_id"], "status": "Sent"}, {"status": "Superseded", "completed_at": iso(stamp)})
    await insert_one("password_resets", {
        "reset_id": reset_id, "user_id": user["id"], "mobile": mobile, "otp_hash": mobile_otp_hash(reset_id, otp),
        "status": "Sent", "created_at": iso(stamp), "expires_at": iso(stamp + timedelta(seconds=PASSWORD_RESET_TTL_SECONDS)),
        "attempt_count": 0, "max_attempts": PASSWORD_RESET_MAX_ATTEMPTS, "gateway_message_id": delivery["gateway_message_id"],
        "ip": client_key,
    })
    await audit(user, "password_reset_otp_sent", "user", user["id"], {"reset_id": reset_id, "mobile": mask_mobile(mobile)}, request)
    if delivery["demo"] or APP_ENV != "production":
        result["dev_otp"] = otp
    return result


@app.post("/api/auth/forgot-password/reset")
async def reset_password_with_otp(payload: PasswordResetIn, request: Request) -> dict[str, str]:
    invalid = HTTPException(422, "Incorrect or expired OTP. Request a new OTP and try again.")
    record = await find_one("password_resets", {"reset_id": payload.reset_id})
    if not record or record["status"] != "Sent":
        raise invalid
    stamp = now()
    if parse_date(record["expires_at"]) <= stamp:
        await update_where("password_resets", {"reset_id": payload.reset_id, "status": "Sent"}, {"status": "Expired", "completed_at": iso(stamp)})
        raise HTTPException(410, "OTP expired. Request a new OTP.")
    if not hmac.compare_digest(record["otp_hash"], mobile_otp_hash(payload.reset_id, payload.otp)):
        attempts = int(record.get("attempt_count", 0))
        remaining = max(int(record.get("max_attempts", PASSWORD_RESET_MAX_ATTEMPTS)) - attempts - 1, 0)
        await update_where("password_resets", {"reset_id": payload.reset_id, "status": "Sent", "attempt_count": attempts}, {"status": "Locked" if remaining == 0 else "Sent", "last_failed_at": iso(stamp)}, {"attempt_count": 1})
        if remaining == 0:
            raise HTTPException(423, "Too many incorrect attempts. Request a new OTP.")
        raise HTTPException(422, f"Incorrect OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
    user = await find_one("users", {"id": record["user_id"]})
    if not user or not user.get("active", True):
        raise invalid
    if pwd_context.verify(payload.new_password, user["password_hash"]):
        raise HTTPException(422, "New password must be different from the old password.")
    if not await update_where("password_resets", {"reset_id": payload.reset_id, "status": "Sent"}, {"status": "Used", "completed_at": iso(stamp)}):
        raise invalid
    updates = {"password_hash": pwd_context.hash(payload.new_password), "must_change_password": False, "password_changed_at": iso(stamp), "initial_password_fingerprint": "user-managed"}
    await update_where("users", {"id": user["id"]}, updates)
    for session in await find_many("auth_sessions", {"user_id": user["id"]}):
        if not session.get("revoked_at"):
            await update_where("auth_sessions", {"session_id": session["session_id"]}, {"revoked_at": iso(stamp)})
    LOGIN_ATTEMPTS.pop(request.client.host if request.client else "unknown", None)
    await audit(user, "password_reset_by_otp", "user", user["id"], {"reset_id": payload.reset_id, "mobile": mask_mobile(record["mobile"]), "all_sessions_revoked": True}, request)
    return {"status": "Password reset. Sign in with your new password."}


@app.get("/api/auth/recovery-mobile")
async def get_recovery_mobile(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    mobile = recovery_mobile_for(user)
    return {"configured": bool(mobile), "masked": mask_mobile(mobile) if mobile else None,
            "source": "settings" if user.get("recovery_mobile") else ("server" if mobile else None)}


@app.post("/api/auth/recovery-mobile")
async def save_recovery_mobile(payload: RecoveryMobileIn, request: Request, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    # The number must have been proved by an SMS OTP sent by this same user in the last 15 minutes.
    record = await find_one("mobile_otps", {"otp_id": payload.otp_id, "mobile": payload.mobile})
    if (not record or record.get("status") != "Verified" or record.get("requested_by_id") != user["id"]
            or parse_date(record.get("completed_at") or record["created_at"]) < now() - timedelta(minutes=15)):
        raise HTTPException(422, "Verify this mobile number with an OTP first.")
    if not await update_where("mobile_otps", {"otp_id": payload.otp_id, "status": "Verified"}, {"status": "Consumed"}):
        raise HTTPException(409, "This OTP was already used. Verify the number again.")
    await update_where("users", {"id": user["id"]}, {"recovery_mobile": payload.mobile, "recovery_mobile_verified_at": iso(now())})
    await audit(user, "recovery_mobile_set", "user", user["id"], {"mobile": mask_mobile(payload.mobile)}, request)
    return {"configured": True, "masked": mask_mobile(payload.mobile), "source": "settings"}


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
        "interest_rate": {"default": DEFAULT_MONTHLY_INTEREST_RATE, "min": MIN_MONTHLY_INTEREST_RATE, "max": MAX_MONTHLY_INTEREST_RATE},
        "max_cash_rounding": MAX_CASH_ROUNDING_RUPEES,
        "loan_ack_required": loan_ack_required(),
        "new_loan_backdate_days": NEW_LOAN_BACKDATE_DAYS,
        "existing_loan_max_age_days": EXISTING_LOAN_MAX_AGE_DAYS,
    }


@app.get("/api/dashboard")
async def dashboard(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    token = _PREFETCH.set(await build_prefetch())
    try:
        return await build_dashboard()
    finally:
        _PREFETCH.reset(token)


async def build_dashboard() -> dict[str, Any]:
    customers = await customer_views([x for x in await find_many("customers") if not x.get("profile_deleted_at")])
    loans = await enrich_loans(await find_many("loans"))
    payments = [p for p in await find_many("payments") if p.get("status", "Posted") != "Reversed" and p.get("payment_type") != "Opening balance"]
    today_key = business_now().date().isoformat()
    month_key = business_now().strftime("%Y-%m")
    today_payments = [p for p in payments if business_date_key(p["timestamp"]) == today_key]
    month_payments = [p for p in payments if business_month_key(p["timestamp"]) == month_key]
    area_summary = []
    for area in await find_many("areas"):
        code = area["code"]
        area_customers = [c for c in customers if c.get("area_code") == code]
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
        paid_remaining = Decimal(str(loan.get("paid", 0)))
        next_row = None
        for installment_row in repayment_rows(loan, await schedule_lookup(loan)):
            installment_due = Decimal(str(installment_row.get("payment", 0)))
            applied = min(paid_remaining, installment_due); paid_remaining -= applied
            remaining_due = installment_due - applied
            if remaining_due > 0 and not installment_row.get("moratorium"):
                next_row = {**installment_row, "remaining_due": float(remaining_due)}; break
        if not next_row: continue
        due_at = parse_date(next_row["due_date"]); client = customer_by_id.get(loan["customer_id"], {})
        pending_dues.append({
            "loan_id": loan["loan_id"], "customer_id": loan["customer_id"], "customer_name": client.get("name", loan["customer_id"]),
            "mobile": client.get("mobile", ""), "area": client.get("area_code", ""),
            "frequency": "Daily" if loan["loan_type"] == "Daily 100-Day" else "Weekly" if loan["loan_type"] == "Weekly" else "Monthly",
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
            "outstanding": round(sum(l["balance"] for l in loans if l["status"] not in {"Closed", "Written Off"}), 2),
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


def collection_period(plan: str, day: date) -> tuple[date, date, str]:
    """The collection cycle a plan is judged on: the day, the Monday-Sunday week, or the calendar month."""
    if plan == "Daily":
        return day, day, "day"
    if plan == "Weekly":
        start = day - timedelta(days=day.weekday())
        return start, start + timedelta(days=6), "week"
    start = day.replace(day=1)
    return start, (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1), "month"


@app.get("/api/dashboard/payment-status")
async def payment_status(on: Optional[str] = None, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    """Per loan, on its own collection cycle (daily loans: that day, weekly: that week, monthly: that month):
    the instalment due versus what was paid, marked Paid / Less paid / Not paid / Upcoming."""
    today = business_now().date()
    try:
        selected = date.fromisoformat(on) if on else today
    except ValueError:
        raise HTTPException(422, "Date must look like 2026-10-27")
    zero = Decimal("0")
    to_day = lambda value: parse_date(value).astimezone(BUSINESS_TIMEZONE).date()
    token = _PREFETCH.set(await build_prefetch())
    try:
        customers = {c["customer_id"]: c for c in await customer_views(await find_many("customers"))}
        area_names = {a["code"]: a["name"] for a in await find_many("areas")}
        loans = await enrich_loans(await find_many("loans"))
        payments_by_loan: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for payment in await find_many("payments"):
            if payment.get("status", "Posted") != "Reversed":
                payments_by_loan[payment["loan_id"]].append(payment)
        rows = []
        for loan in loans:
            if loan.get("status") == "Written Off":
                continue
            plan = "Daily" if loan["loan_type"] == "Daily 100-Day" else "Weekly" if loan["loan_type"] == "Weekly" else "Monthly"
            start, end, period = collection_period(plan, selected)
            schedule = [(to_day(r["due_date"]), Decimal(str(r["payment"]))) for r in repayment_rows(loan, await schedule_lookup(loan))]
            loan_payments = payments_by_loan.get(loan["loan_id"], [])
            opening = sum((Decimal(str(p["amount"])) for p in loan_payments if p.get("payment_type") == "Opening balance"), zero)
            collections = [(to_day(p["timestamp"]), Decimal(str(p["amount"]))) for p in loan_payments if p.get("payment_type") != "Opening balance"]
            # An existing loan is only tracked from the day it was entered; the amount already repaid counts as paid in advance.
            carry = zero
            entered = to_day(loan["entered_at"]) if loan.get("existing_loan") and loan.get("entered_at") else None
            if entered:
                if end < entered:
                    continue
                carry = max(opening - sum((amount for day, amount in schedule if day < entered), zero), zero)
                schedule = [(day, amount) for day, amount in schedule if day >= entered]
            period_rows = [(day, amount) for day, amount in schedule if start <= day <= end]
            due = sum((amount for _, amount in period_rows), zero)
            paid = sum((amount for day, amount in collections if start <= day <= end), zero)
            if due <= 0 and paid <= 0:
                continue
            prior_due = sum((amount for day, amount in schedule if day < start), zero)
            advance = max(sum((amount for day, amount in collections if day < start), zero) + carry - prior_due, zero)
            covered = min(paid + advance, due)
            if covered >= due:
                status = "Paid"
            elif covered > 0:
                status = "Less paid"
            elif any(day <= min(selected, today) for day, _ in period_rows) and not (entered and start <= entered <= end):
                status = "Not paid"
            else:
                status = "Upcoming"  # nothing due yet in this cycle, or an existing loan entered during this cycle
            left, next_due = covered, None
            for day, amount in period_rows:
                if left >= amount:
                    left -= amount
                else:
                    next_due = day
                    break
            client = customers.get(loan["customer_id"], {})
            rows.append({
                "loan_id": loan["loan_id"], "customer_id": loan["customer_id"], "customer_name": client.get("name", loan["customer_id"]),
                "mobile": client.get("mobile", ""), "area": client.get("area_code", ""), "area_name": area_names.get(client.get("area_code", ""), client.get("area_code", "")),
                "frequency": plan, "period": period, "period_start": start.isoformat(), "period_end": end.isoformat(),
                "instalments_due": len(period_rows), "scheduled": float(due), "paid": float(paid),
                "paid_in_advance": float(min(advance, due)), "covered": float(covered), "short": float(max(due - covered, zero)), "status": status,
                "next_due_date": next_due.isoformat() if next_due else None,
                "days_overdue": max((today - next_due).days, 0) if next_due else 0,
                "existing_loan": bool(loan.get("existing_loan")), "loan_status": loan.get("status"),
            })
    finally:
        _PREFETCH.reset(token)
    order = {"Not paid": 0, "Less paid": 1, "Upcoming": 2, "Paid": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["next_due_date"] or "9999", -r["short"], r["customer_name"]))
    return {
        "date": selected.isoformat(), "rows": rows,
        "counts": {name: sum(1 for r in rows if r["status"] == name) for name in order},
        "scheduled": round(sum(r["scheduled"] for r in rows), 2), "paid": round(sum(r["paid"] for r in rows), 2),
        "short": round(sum(r["short"] for r in rows), 2),
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
    rows = await customer_views(customer_records)
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
        rows = [r for r in rows if r.get("area_code") == area]
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


@app.patch("/api/customers/{customer_id}")
async def update_customer(customer_id: str, payload: CustomerUpdateIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer or customer.get("profile_deleted_at"):
        raise HTTPException(404, "Active customer profile not found")
    area = await find_one("areas", {"code": payload.area})
    if not area or not area.get("active", True):
        raise HTTPException(422, "Select an active operating area")
    duplicate = await find_one("customers", {"mobile": payload.mobile})
    if duplicate and duplicate.get("customer_id") != customer_id and not duplicate.get("profile_deleted_at"):
        raise HTTPException(409, f"Mobile already belongs to {duplicate['customer_id']}")
    before = {key: customer.get(key, "") for key in payload.model_fields}
    updated = deepcopy(customer)
    updated.update(payload.model_dump())
    updated.update({"updated_at": iso(now()), "updated_by": user["name"]})
    if payload.mobile != customer.get("mobile"):
        for key in ("mobile_verified_at", "mobile_verified_by", "mobile_verified_number", "mobile_otp_id"):
            updated.pop(key, None)
    details = {"before": before, "after": payload.model_dump(), "customer_id_unchanged": True}
    if USE_MEMORY:
        await replace_one("customers", {"customer_id": customer_id}, updated)
        await audit(user, "customer_details_updated", "customer", customer_id, details, request)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                result = await db.customers.replace_one({"customer_id": customer_id, "profile_deleted_at": {"$exists": False}}, updated, session=session)
                if result.modified_count != 1:
                    raise HTTPException(409, "Customer changed concurrently; reload and retry")
                await audit(user, "customer_details_updated", "customer", customer_id, details, request, session=session)
    return await customer_view(updated)


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
        consent = {"consent_id": f"CNS-{consent_seq:09d}", "customer_id": customer_id, "status": "Active", "purpose_disclosed": payload.aadhaar_consent_purpose.strip() or "Identity verification for loan application", "customer_consent_reference": payload.aadhaar_consent_reference.strip() or f"Recorded at registration by {user['name']}", "captured_at": iso(now()), "captured_by": user["name"], "captured_by_id": user["id"]}
    mobile_event = None
    if payload.mobile_otp_id:
        otp_rec = await find_one("mobile_otps", {"otp_id": payload.mobile_otp_id, "mobile": payload.mobile, "status": "Verified"})
        if otp_rec:
            customer["mobile_verified_at"] = otp_rec.get("completed_at", iso(now()))
            customer["mobile_verified_by"] = user["name"]
            customer["mobile_verified_number"] = payload.mobile
            customer["mobile_otp_id"] = payload.mobile_otp_id
            m_seq = await next_sequence("VEF", "id", "verification_events")
            mobile_event = {
                "id": f"VEF-{m_seq:08d}", "customer_id": customer_id,
                "from_status": None, "to_status": "Pending Verification",
                "reason": f"Mobile {mask_mobile(payload.mobile)} verified by SMS OTP during registration",
                "verification_id": payload.mobile_otp_id, "provider": "SMS OTP",
                "timestamp": iso(now()), "updated_by": user["name"]
            }
    audit_details = {"masked_aadhaar": mask_aadhaar(payload.aadhaar) if payload.aadhaar else "Not provided", "method": "aadhaar" if payload.aadhaar else "manual", "status": "Pending Verification", "mobile_verified": bool(customer.get("mobile_verified_at"))}
    try:
        if USE_MEMORY:
            await insert_one("customers", customer)
            await insert_one("verification_events", verification_event)
            if mobile_event: await insert_one("verification_events", mobile_event)
            if payload.mobile_otp_id: await update_where("mobile_otps", {"otp_id": payload.mobile_otp_id}, {"customer_id": customer_id})
            if consent: await insert_one("aadhaar_consents", consent)
            await audit(user, "customer_registration", "customer", customer_id, audit_details, request)
        else:
            async with await mongo_client.start_session() as session:
                async with session.start_transaction():
                    await db.customers.insert_one(deepcopy(customer), session=session)
                    await db.verification_events.insert_one(deepcopy(verification_event), session=session)
                    if mobile_event: await db.verification_events.insert_one(deepcopy(mobile_event), session=session)
                    if payload.mobile_otp_id: await db.mobile_otps.update_one({"otp_id": payload.mobile_otp_id}, {"$set": {"customer_id": customer_id}}, session=session)
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


@app.get("/api/sms/status")
async def sms_status(user: dict[str, Any] = Depends(require("owner", "manager", "accountant", "collector"))) -> dict[str, Any]:
    configured = sms_gateway_ready()
    return {
        "configured": configured,
        "provider": normalized_sms_provider(),
        "raw_provider": SMS_PROVIDER,
        "otp_ttl_seconds": MOBILE_OTP_TTL_SECONDS,
        "mobile_verified_disbursal_required": REQUIRE_MOBILE_VERIFIED_DISBURSAL,
        "demo_mode": sms_demo_mode(),
        "available": configured or sms_demo_mode(),
        "has_credentials": bool(SMS_GATEWAY_USERNAME and SMS_GATEWAY_PASSWORD),
        "problems": [] if configured else sms_setup_problems(),
    }


class SmsTestIn(BaseModel):
    mobile: str = Field(min_length=10, max_length=15)

    @field_validator("mobile")
    @classmethod
    def valid_mobile(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())[-10:]
        if len(digits) != 10 or digits[0] not in "6789":
            raise ValueError("Mobile must be a valid 10-digit Indian number")
        return digits


def _mask_secret(value: str) -> str:
    if not value:
        return "not set"
    return value[:2] + "•" * max(len(value) - 4, 2) + value[-2:] if len(value) > 4 else "•" * len(value)


@app.get("/api/sms/diagnostics")
async def sms_diagnostics(user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    """Step-by-step check of the SMS setup on THIS server, in plain language."""
    checks: list[dict[str, Any]] = []
    provider = normalized_sms_provider()
    checks.append({"name": "SMS provider", "ok": provider == "android_gateway", "detail": f"SMS_PROVIDER = '{SMS_PROVIDER or 'not set'}'" + ("" if provider == "android_gateway" else " — set it to android_gateway")})
    checks.append({"name": "Gateway username", "ok": bool(SMS_GATEWAY_USERNAME), "detail": f"SMS_GATEWAY_USERNAME = {_mask_secret(SMS_GATEWAY_USERNAME)}"})
    checks.append({"name": "Gateway password", "ok": bool(SMS_GATEWAY_PASSWORD), "detail": "SMS_GATEWAY_PASSWORD is set" if SMS_GATEWAY_PASSWORD else "SMS_GATEWAY_PASSWORD is not set"})
    kind = sms_gateway_url_kind()
    checks.append({"name": "Gateway address", "ok": kind in {"cloud", "custom"}, "detail": f"{SMS_GATEWAY_URL or 'not set'}" + (" — a local network address cannot be reached from an online server" if kind == "local-network" else "")})
    devices: list[dict[str, Any]] = []
    if SMS_GATEWAY_USERNAME and SMS_GATEWAY_PASSWORD and kind != "missing":
        def probe() -> dict[str, Any]:
            try:
                status, reply = gateway_request("GET", "/devices" if kind == "cloud" else "/health", timeout=10)
                return {"status": status, "reply": reply}
            except (URLError, TimeoutError, OSError) as exc:
                return {"status": 0, "reply": str(getattr(exc, "reason", exc))[:200]}
        result = await asyncio.to_thread(probe)
        if result["status"] == 0:
            checks.append({"name": "Reach the gateway", "ok": False, "detail": f"This server could not connect: {result['reply']}"})
        elif result["status"] >= 400:
            checks.append({"name": "Gateway login", "ok": False, "detail": gateway_error_message(result["status"])})
        else:
            checks.append({"name": "Gateway login", "ok": True, "detail": "Username and password accepted"})
            if kind == "cloud":
                for device in result["reply"] if isinstance(result["reply"], list) else []:
                    last_seen = device.get("lastSeen")
                    minutes = None
                    if last_seen:
                        try: minutes = int((now() - parse_date(last_seen)).total_seconds() // 60)
                        except Exception: minutes = None
                    devices.append({"name": device.get("name") or device.get("id"), "last_seen": last_seen, "minutes_ago": minutes})
                recent = [d for d in devices if d["minutes_ago"] is not None and d["minutes_ago"] <= 30]
                checks.append({"name": "Gateway phone", "ok": bool(recent), "detail": (f"{len(devices)} phone(s) registered; last seen {min(d['minutes_ago'] for d in devices if d['minutes_ago'] is not None)} min ago" if any(d["minutes_ago"] is not None for d in devices) else "No phone is registered to this account — open the app, enable Cloud server and tap Online") if devices else "No phone is registered to this account — open the SMS Gateway app, enable Cloud server and tap Online"})
    ready = all(check["ok"] for check in checks)
    return {
        "environment": APP_ENV, "ready": ready, "demo_mode": sms_demo_mode(), "checks": checks, "devices": devices,
        "problems": sms_setup_problems(),
        "summary": "Real SMS can be sent from this server." if ready else ("OTPs are shown on screen (demo mode) because real SMS is not set up on this server." if sms_demo_mode() else "OTP sending is blocked until the problems below are fixed."),
    }


@app.post("/api/sms/test")
async def sms_test(payload: SmsTestIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    if not sms_gateway_ready():
        raise HTTPException(409, "Real SMS is not set up on this server: " + " ".join(sms_setup_problems()))
    delivery = await send_sms(payload.mobile, f"Test message from {SMS_SENDER_NAME}: SMS OTP is working on the live server ({business_now().strftime('%d %b %Y %I:%M %p')}).")
    await audit(user, "sms_test_sent", "mobile", mask_mobile(payload.mobile), {"gateway_message_id": delivery["gateway_message_id"]}, request)
    return {"sent": True, "mobile": mask_mobile(payload.mobile), "message_id": delivery["gateway_message_id"], "state": delivery["gateway_state"]}


@app.get("/api/sms/test/{message_id}")
async def sms_test_status(message_id: str, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    if not sms_gateway_ready():
        raise HTTPException(409, "Real SMS is not set up on this server.")
    safe_id = "".join(ch for ch in message_id if ch.isalnum() or ch in "-_")[:80]
    try:
        status, reply = await asyncio.to_thread(gateway_request, "GET", f"/message/{safe_id}", None, 10)
    except (URLError, TimeoutError, OSError) as exc:
        raise HTTPException(424, "SMS gateway could not be reached from this server.") from exc
    if status >= 400:
        raise HTTPException(424, gateway_error_message(status))
    reply = reply if isinstance(reply, dict) else {}
    recipients = reply.get("recipients") or []
    error = next((r.get("error") for r in recipients if isinstance(r, dict) and r.get("error")), None)
    return {"message_id": safe_id, "state": reply.get("state", "Unknown"), "error": error}


@app.post("/api/registration/mobile-otp/send")
async def send_registration_mobile_otp(payload: RegistrationOtpSendIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager", "accountant", "collector"))) -> dict[str, Any]:
    mobile = payload.mobile
    stamp = now()
    history = await find_many("mobile_otps", {"mobile": mobile})
    if sum(1 for row in history if parse_date(row["created_at"]) > stamp - timedelta(days=1)) >= MOBILE_OTP_DAILY_LIMIT:
        raise HTTPException(429, "Daily OTP limit reached for this mobile number. Try again tomorrow.")
    latest = max(history, key=lambda row: row["created_at"], default=None)
    if latest and latest.get("status") == "Sent":
        available_at = parse_date(latest["created_at"]) + timedelta(seconds=MOBILE_OTP_RESEND_SECONDS)
        if available_at > stamp:
            raise HTTPException(429, f"Please wait {int((available_at - stamp).total_seconds()) + 1} seconds before resending OTP.")
    seq = await next_sequence("MOTP", "otp_id", "mobile_otps")
    otp_id = f"MOTP-{seq:09d}"
    otp = f"{secrets.randbelow(1_000_000):06d}"
    minutes = MOBILE_OTP_TTL_SECONDS // 60
    delivery = await send_sms(mobile, f"{otp} is your OTP to verify your mobile number with {SMS_SENDER_NAME}. Valid for {minutes} minutes. Do not share it with anyone.")
    for row in history:
        if row.get("status") == "Sent":
            await update_where("mobile_otps", {"otp_id": row["otp_id"], "status": "Sent"}, {"status": "Superseded", "completed_at": iso(stamp)})
    norm_provider = "demo" if delivery["demo"] else normalized_sms_provider()
    gateway_ready = not delivery["demo"]
    record = {
        "otp_id": otp_id, "customer_id": None, "mobile": mobile, "gateway_message_id": delivery["gateway_message_id"],
        "otp_hash": mobile_otp_hash(otp_id, otp), "provider": norm_provider,
        "status": "Sent", "created_at": iso(stamp),
        "expires_at": iso(stamp + timedelta(seconds=MOBILE_OTP_TTL_SECONDS)),
        "attempt_count": 0, "max_attempts": MOBILE_OTP_MAX_ATTEMPTS,
        "requested_by": user["name"], "requested_by_id": user["id"]
    }
    await insert_one("mobile_otps", record)
    await audit(user, "registration_mobile_otp_sent", "mobile", mobile, {"otp_id": otp_id, "mobile": mask_mobile(mobile), "provider": norm_provider}, request)
    result = {
        "otp_id": otp_id, "status": "Sent", "masked_destination": mask_mobile(mobile),
        "expires_at": record["expires_at"], "expires_in_seconds": MOBILE_OTP_TTL_SECONDS,
        "attempts_remaining": MOBILE_OTP_MAX_ATTEMPTS,
        "resend_available_at": iso(stamp + timedelta(seconds=MOBILE_OTP_RESEND_SECONDS)),
        "sms_provider": norm_provider,
        "sms_gateway_configured": gateway_ready,
    }
    if delivery["demo"] or APP_ENV != "production":
        result["dev_otp"] = otp
    return result


@app.post("/api/registration/mobile-otp/verify")
async def verify_registration_mobile_otp(payload: RegistrationOtpVerifyIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager", "accountant", "collector"))) -> dict[str, Any]:
    record = await find_one("mobile_otps", {"otp_id": payload.otp_id, "mobile": payload.mobile})
    if not record:
        raise HTTPException(404, "OTP request not found")
    if record["status"] != "Sent":
        raise HTTPException(409, "This OTP is no longer valid. Send a new OTP.")
    stamp = now()
    if parse_date(record["expires_at"]) <= stamp:
        await update_where("mobile_otps", {"otp_id": payload.otp_id, "status": "Sent"}, {"status": "Expired", "completed_at": iso(stamp)})
        raise HTTPException(410, "OTP expired. Send a new OTP.")
    if not hmac.compare_digest(record["otp_hash"], mobile_otp_hash(payload.otp_id, payload.otp)):
        attempts = int(record.get("attempt_count", 0))
        remaining = max(int(record.get("max_attempts", MOBILE_OTP_MAX_ATTEMPTS)) - attempts - 1, 0)
        changed = await update_where("mobile_otps", {"otp_id": payload.otp_id, "status": "Sent", "attempt_count": attempts}, {"status": "Locked" if remaining == 0 else "Sent", "last_failed_at": iso(stamp)}, {"attempt_count": 1})
        if not changed:
            raise HTTPException(409, "OTP state changed. Please try again.")
        await audit(user, "registration_mobile_otp_failed", "mobile", payload.mobile, {"otp_id": payload.otp_id, "attempts_remaining": remaining}, request)
        if remaining == 0:
            raise HTTPException(423, "OTP locked after 3 incorrect attempts. Send a new OTP.")
        raise HTTPException(422, f"Incorrect OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
    if not await update_where("mobile_otps", {"otp_id": payload.otp_id, "status": "Sent"}, {"status": "Verified", "completed_at": iso(stamp)}):
        raise HTTPException(409, "This OTP was already used")
    await audit(user, "registration_mobile_otp_verified", "mobile", payload.mobile, {"otp_id": payload.otp_id, "mobile": mask_mobile(payload.mobile)}, request)
    return {"verified": True, "otp_id": payload.otp_id, "mobile": payload.mobile, "verified_at": iso(stamp)}


@app.post("/api/customers/{customer_id}/mobile-otp/send")
async def send_mobile_otp(customer_id: str, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer or customer.get("profile_deleted_at"):
        raise HTTPException(404, "Active customer profile not found")
    if mobile_verified(customer):
        raise HTTPException(409, "This mobile number is already verified")
    stamp = now()
    history = await find_many("mobile_otps", {"customer_id": customer_id})
    if sum(1 for row in history if parse_date(row["created_at"]) > stamp - timedelta(days=1)) >= MOBILE_OTP_DAILY_LIMIT:
        raise HTTPException(429, "Daily OTP limit reached for this customer. Try again tomorrow.")
    latest = max(history, key=lambda row: row["created_at"], default=None)
    if latest and latest.get("status") == "Sent":
        available_at = parse_date(latest["created_at"]) + timedelta(seconds=MOBILE_OTP_RESEND_SECONDS)
        if available_at > stamp:
            raise HTTPException(429, f"Please wait {int((available_at - stamp).total_seconds()) + 1} seconds before resending OTP.")
    seq = await next_sequence("MOTP", "otp_id", "mobile_otps")
    otp_id = f"MOTP-{seq:09d}"
    otp = f"{secrets.randbelow(1_000_000):06d}"
    minutes = MOBILE_OTP_TTL_SECONDS // 60
    delivery = await send_sms(customer["mobile"], f"{otp} is your OTP to verify your mobile number with {SMS_SENDER_NAME}. Valid for {minutes} minutes. Do not share it with anyone.")
    for row in history:
        if row.get("status") == "Sent":
            await update_where("mobile_otps", {"otp_id": row["otp_id"], "status": "Sent"}, {"status": "Superseded", "completed_at": iso(stamp)})
    norm_provider = "demo" if delivery["demo"] else normalized_sms_provider()
    gateway_ready = not delivery["demo"]
    record = {"otp_id": otp_id, "customer_id": customer_id, "mobile": customer["mobile"], "gateway_message_id": delivery["gateway_message_id"], "otp_hash": mobile_otp_hash(otp_id, otp), "provider": norm_provider, "status": "Sent", "created_at": iso(stamp), "expires_at": iso(stamp + timedelta(seconds=MOBILE_OTP_TTL_SECONDS)), "attempt_count": 0, "max_attempts": MOBILE_OTP_MAX_ATTEMPTS, "requested_by": user["name"], "requested_by_id": user["id"]}
    await insert_one("mobile_otps", record)
    await audit(user, "mobile_otp_sent", "customer", customer_id, {"otp_id": otp_id, "mobile": mask_mobile(customer["mobile"]), "provider": norm_provider}, request)
    result = {"otp_id": otp_id, "status": "Sent", "masked_destination": mask_mobile(customer["mobile"]), "expires_at": record["expires_at"], "expires_in_seconds": MOBILE_OTP_TTL_SECONDS, "attempts_remaining": MOBILE_OTP_MAX_ATTEMPTS, "resend_available_at": iso(stamp + timedelta(seconds=MOBILE_OTP_RESEND_SECONDS)), "sms_provider": norm_provider, "sms_gateway_configured": gateway_ready}
    if delivery["demo"] or APP_ENV != "production":
        result["dev_otp"] = otp
    return result


@app.post("/api/customers/{customer_id}/mobile-otp/verify")
async def verify_mobile_otp(customer_id: str, payload: MobileOtpVerifyIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    record = await find_one("mobile_otps", {"otp_id": payload.otp_id, "customer_id": customer_id})
    if not record: raise HTTPException(404, "OTP request not found")
    if record["status"] != "Sent": raise HTTPException(409, "This OTP is no longer valid. Send a new OTP.")
    stamp = now()
    if parse_date(record["expires_at"]) <= stamp:
        await update_where("mobile_otps", {"otp_id": payload.otp_id, "status": "Sent"}, {"status": "Expired", "completed_at": iso(stamp)})
        raise HTTPException(410, "OTP expired. Send a new OTP.")
    if not hmac.compare_digest(record["otp_hash"], mobile_otp_hash(payload.otp_id, payload.otp)):
        attempts = int(record.get("attempt_count", 0))
        remaining = max(int(record.get("max_attempts", MOBILE_OTP_MAX_ATTEMPTS)) - attempts - 1, 0)
        changed = await update_where("mobile_otps", {"otp_id": payload.otp_id, "status": "Sent", "attempt_count": attempts}, {"status": "Locked" if remaining == 0 else "Sent", "last_failed_at": iso(stamp)}, {"attempt_count": 1})
        if not changed: raise HTTPException(409, "OTP state changed. Please try again.")
        await audit(user, "mobile_otp_failed", "customer", customer_id, {"otp_id": payload.otp_id, "attempts_remaining": remaining}, request)
        if remaining == 0: raise HTTPException(423, "OTP locked after 3 incorrect attempts. Send a new OTP.")
        raise HTTPException(422, f"Incorrect OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
    if not await update_where("mobile_otps", {"otp_id": payload.otp_id, "status": "Sent"}, {"status": "Verified", "completed_at": iso(stamp)}):
        raise HTTPException(409, "This OTP was already used")
    customer = await find_one("customers", {"customer_id": customer_id})
    if not customer or customer.get("mobile") != record["mobile"]:
        raise HTTPException(409, "The customer's mobile number changed after the OTP was sent. Send a new OTP.")
    verified = {"mobile_verified_at": iso(stamp), "mobile_verified_by": user["name"], "mobile_verified_number": record["mobile"], "mobile_otp_id": payload.otp_id}
    await update_where("customers", {"customer_id": customer_id, "mobile": record["mobile"]}, verified)
    customer.update(verified)
    verification_seq = await next_sequence("VEF", "id", "verification_events")
    await insert_one("verification_events", {"id": f"VEF-{verification_seq:08d}", "customer_id": customer_id, "status": customer.get("status"), "reason": f"Mobile {mask_mobile(record['mobile'])} verified by SMS OTP", "verification_id": payload.otp_id, "provider": "SMS OTP", "timestamp": iso(stamp), "updated_by": user["name"]})
    await audit(user, "mobile_otp_verified", "customer", customer_id, {"otp_id": payload.otp_id, "mobile": mask_mobile(record["mobile"])}, request)
    return {"verified": True, "otp_id": payload.otp_id, "verified_at": iso(stamp), "customer": await customer_view(customer)}


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
    rows = await enrich_loans(await find_many("loans"))
    customers_map = {c["customer_id"]: c for c in await customer_views(await find_many("customers"))}
    out = []
    for loan in rows:
        c = customers_map.get(loan["customer_id"], {})
        item = {
            **loan,
            "customer_name": c.get("name", ""),
            "area": c.get("area_code", c.get("area", "")),
            "area_code": c.get("area_code", c.get("area", "")),
            "area_name": c.get("area_name", c.get("area", "")),
            "mobile": c.get("mobile", ""),
        }
        out.append(item)
    if user["role"] == "collector":
        out = [x for x in out if x["collector_id"] == user["id"]]
    ql = q.lower().strip()
    if ql:
        out = [r for r in out if ql in " ".join([r["loan_id"], r["customer_id"], r["customer_name"], r["mobile"], r["area"], r.get("area_name", "")]).lower()]
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
    payload, borrow, _, schedule = prepare_loan_terms(payload)
    return {
        "acknowledgement_required": not payload.existing_loan and loan_ack_required(),
        "calculated_net_disbursed": schedule["calculated_net_disbursed"], "cash_rounding_adjustment": schedule["cash_rounding_adjustment"],
        "quote_id": f"QTE-{uuid.uuid4().hex[:12].upper()}", "generated_at": iso(now()),
        "sanctioned_amount": payload.principal, "net_disbursed_amount": schedule["net_disbursed"],
        "monthly_interest_rate": payload.interest_rate, "interest_method": payload.interest_method,
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


@app.get("/api/loans/{loan_id}/details")
async def loan_details(loan_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    loan_record = await find_one("loans", {"loan_id": loan_id})
    if not loan_record:
        raise HTTPException(404, "Loan not found")
    if user["role"] == "collector" and loan_record.get("collector_id") != user["id"]:
        raise HTTPException(403, "Collector can only view assigned loans")
    loan = await enrich_loan(loan_record)
    customer_record = await find_one("customers", {"customer_id": loan_record["customer_id"]})
    customer = await customer_view(customer_record) if customer_record else {"customer_id": loan_record["customer_id"], "name": "Customer record unavailable"}
    schedule = await find_one("loan_schedules", {"loan_id": loan_id, "version": int(loan_record.get("schedule_version", 1))})
    payments = sorted(
        await find_many("payments", {"loan_id": loan_id}),
        key=lambda row: row.get("timestamp", ""), reverse=True,
    )
    running_balance = to_paise(loan.get("balance", 0))
    payment_history = []
    for row in payments:
        item = deepcopy(row)
        allocation = item.get("allocation", {})
        # Older receipts have no allocation; the whole amount reduced the balance.
        applied = sum(int(allocation.get(key, 0)) for key in ("principal_paise", "interest_paise", "penalty_paise")) if allocation else to_paise(item.get("amount", 0))
        item["principal_paid"] = from_paise(int(allocation.get("principal_paise", 0)))
        item["interest_paid"] = from_paise(int(allocation.get("interest_paise", 0)))
        item["penalty_paid"] = from_paise(int(allocation.get("penalty_paise", 0)))
        item["closure_charge_paid"] = from_paise(int(allocation.get("preclosure_charge_paise", 0)))
        item["payment_type"] = "Closure" if item.get("closure_payment") else item.get("payment_type", "Collection")
        item["balance_after"] = item.get("balance_after", from_paise(running_balance))
        if item.get("status", "Posted") != "Reversed":
            running_balance += applied
        item["balance_before"] = item.get("balance_before", from_paise(running_balance))
        payment_history.append(item)
    adjustments = sorted(
        await find_many("loan_adjustments", {"loan_id": loan_id}),
        key=lambda row: row.get("timestamp", ""), reverse=True,
    )
    events = sorted(
        await find_many("loan_events", {"loan_id": loan_id}),
        key=lambda row: row.get("timestamp", row.get("created_at", "")), reverse=True,
    )
    part_payments = sorted(
        await find_many("part_payments", {"loan_id": loan_id}),
        key=lambda row: row.get("timestamp", ""), reverse=True,
    )
    writeoffs = sorted(
        await find_many("writeoffs", {"loan_id": loan_id}),
        key=lambda row: row.get("timestamp", ""), reverse=True,
    )
    verification_id = loan_record.get("identity_verification_id")
    verification = await find_one("verification_logs", {"verification_id": verification_id}) if verification_id else None
    closure_payment = next((row for row in payments if loan.get("status") == "Closed" and row.get("status", "Posted") != "Reversed"), None)
    return {
        "loan": loan,
        "customer": customer,
        "schedule": (schedule or {}).get("rows", []),
        "schedule_version": int(loan_record.get("schedule_version", 1)),
        "payments": payment_history,
        "repayment_summary": {
            "receipt_count": len([row for row in payment_history if row.get("status", "Posted") != "Reversed"]),
            "total_received": round(sum(float(row.get("amount", 0)) for row in payment_history if row.get("status", "Posted") != "Reversed"), 2),
            "principal_received": from_paise(sum(int(row.get("allocation", {}).get("principal_paise", 0)) for row in payment_history if row.get("status", "Posted") != "Reversed")),
            "interest_received": from_paise(sum(int(row.get("allocation", {}).get("interest_paise", 0)) for row in payment_history if row.get("status", "Posted") != "Reversed")),
            "penalty_received": from_paise(sum(int(row.get("allocation", {}).get("penalty_paise", 0)) for row in payment_history if row.get("status", "Posted") != "Reversed")),
            "outstanding": loan.get("balance", 0),
            "remaining_installments": loan.get("remaining_installments", 0),
            "next_due_date": loan.get("next_due_date"),
        },
        "adjustments": adjustments,
        "events": events,
        "part_payments": part_payments,
        "writeoffs": writeoffs,
        "identity_verification": verification,
        "late_charge": await late_charge_status(loan_record),
        "closure": {
            "closed": loan.get("status") == "Closed",
            "closed_at": closure_payment.get("timestamp") if closure_payment else None,
            "final_receipt": closure_payment.get("receipt_no") if closure_payment else None,
        },
    }


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
        "monthly_interest_rate": loan["interest_rate"], "interest_method": loan["interest_method"],
        "apr": loan["apr"], "tenor_periods": loan["repayment_period"], "repayment_frequency": "Daily" if loan["loan_type"] == "Daily 100-Day" else "Weekly" if loan["loan_type"] == "Weekly" else "Monthly",
        "periodic_instalment": loan["emi"], "total_interest": loan["contract_interest"], "total_repayment": loan["total_repayment"],
        "processing_fee": loan["processing_fee"], "tax_on_fee": loan["tax_amount"],
        "moratorium_periods": loan["moratorium_periods"], "moratorium_interest_capitalized": loan["moratorium_interest_capitalized"],
        "late_fee": loan["late_fee"], "preclosure_charge_rate": loan["preclosure_charge_rate"],
        "first_due_date": loan["first_due_date"], "maturity_date": loan["maturity_date"],
        "schedule_version": loan["schedule_version"], "schedule": schedule["rows"],
        "borrower_acknowledgement": {"reference": loan.get("kfs_acknowledgement_reference"), "acknowledgement_no": loan.get("acknowledgement_no"), "method": loan.get("acknowledgement_method"), "mobile": loan.get("acknowledgement_mobile"), "verified_at": loan.get("acknowledgement_verified_at")},
        "generated_at": iso(now()), "disclaimer": "Charges not disclosed in this KFS must not be collected from the borrower.",
    }


def migration_schedule_input(loan: dict[str, Any]) -> LoanIn:
    return LoanIn(
        customer_id=loan["customer_id"], principal=float(loan["principal"]), interest_rate=2.14,
        loan_type=loan["loan_type"], repayment_period=int(loan.get("repayment_period", 100)),
        collector_id=loan["collector_id"], borrow_date=loan.get("borrow_date"),
        disbursement_mode=loan.get("disbursement_mode", "Cash"), interest_method="Upfront Monthly Flat",
        processing_fee=float(loan.get("processing_fee", 0)), tax_rate=float(loan.get("tax_rate", 18)),
        first_due_date=loan.get("first_due_date"), moratorium_periods=int(loan.get("moratorium_periods", 0)),
        moratorium_interest_capitalized=bool(loan.get("moratorium_interest_capitalized", True)),
        preclosure_charge_rate=float(loan.get("preclosure_charge_rate", 0)), late_fee=float(loan.get("late_fee", 0)),
        kfs_acknowledgement_reference="LEGACY-MIGRATION-PREVIEW",
    )


@app.get("/api/loans/{loan_id}/migration-preview")
async def legacy_loan_migration_preview(loan_id: str, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    if int(loan.get("contract_version", 1)) >= 2:
        raise HTTPException(409, "This loan already uses the current contract model")
    before = await loan_component_balances(loan)
    schedule = build_amortization(migration_schedule_input(loan), parse_date(loan["borrow_date"]))
    paid = before["paid_paise"]
    after_balance = max(to_paise(loan["principal"]) - paid, 0)
    return {
        "loan_id": loan_id, "contract_version_before": int(loan.get("contract_version", 1)),
        "contract_version_after": 2, "old_outstanding": from_paise(before["balance_paise"]),
        "new_outstanding": from_paise(after_balance), "difference": from_paise(after_balance - before["balance_paise"]),
        "paid_preserved": from_paise(paid), "monthly_interest_rate": 2.14,
        "interest_deducted": schedule["interest_total"], "net_disbursed_original_contract_basis": schedule["net_disbursed"],
        "installment": schedule["emi"], "maturity_date": schedule["maturity_date"],
        "requires_owner_confirmation_and_borrower_acknowledgement": True,
    }


@app.post("/api/loans/{loan_id}/migrate-contract")
async def migrate_legacy_loan(loan_id: str, payload: LegacyLoanMigrationIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    if payload.confirmation.strip().upper() != loan_id.upper():
        raise HTTPException(422, f"Type loan ID {loan_id} to confirm migration")
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    if int(loan.get("contract_version", 1)) >= 2:
        raise HTTPException(409, "This loan has already been migrated")
    schedule = build_amortization(migration_schedule_input(loan), parse_date(loan["borrow_date"]))
    event_id = f"LEV-{await next_sequence('LEV', 'event_id', 'loan_events'):08d}"
    before = deepcopy(loan)
    updates = {
        "contract_version": 2, "interest_rate": 2.14, "interest_rate_period": "Monthly",
        "interest_method": "Upfront Monthly Flat", "interest_collection_basis": "Upfront Discount",
        "processing_fee": schedule["processing_fee"], "tax_amount": schedule["tax"],
        "net_disbursed": schedule["net_disbursed"], "apr": schedule["apr"],
        "first_due_date": schedule["first_due_date"], "maturity_date": schedule["maturity_date"],
        "emi": schedule["emi"], "contract_interest": schedule["interest_total"],
        "total_repayment": schedule["total_repayment"], "schedule_version": 1,
        "kfs_acknowledgement_reference": payload.borrower_acknowledgement_reference,
        "migration_approval_reference": payload.approval_reference, "migrated_at": iso(now()), "migrated_by": user["name"],
    }
    event = {"event_id": event_id, "loan_id": loan_id, "event_type": "Legacy Contract Migrated", **payload.model_dump(exclude={"confirmation"}), "timestamp": iso(now()), "before_contract_version": int(loan.get("contract_version", 1)), "after_contract_version": 2, "posted_by": user["name"]}
    schedule_doc = {"loan_id": loan_id, "version": 1, "reason": "Controlled legacy migration", "approval_reference": payload.approval_reference, "consent_reference": payload.borrower_acknowledgement_reference, "created_at": iso(now()), **schedule}
    if USE_MEMORY:
        await insert_one("loan_schedules", schedule_doc); await insert_one("loan_events", event)
        await replace_one("loans", {"loan_id": loan_id}, {**loan, **updates})
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                await db.loan_schedules.insert_one(deepcopy(schedule_doc), session=session)
                await db.loan_events.insert_one(deepcopy(event), session=session)
                result = await db.loans.update_one({"loan_id": loan_id, "$or": [{"contract_version": {"$lt": 2}}, {"contract_version": {"$exists": False}}]}, {"$set": updates, "$inc": {"ledger_version": 1}}, session=session)
                if result.modified_count != 1: raise HTTPException(409, "Loan changed concurrently; reload and retry")
    await audit(user, "legacy_contract_migrated", "loan", loan_id, {"before": before, "after": {**before, **updates}, "approval_reference": payload.approval_reference, "reason": payload.reason}, request)
    return {"loan": await enrich_loan(await find_one("loans", {"loan_id": loan_id})), "event": event}


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
    async with atomic() as session:
        await tx_insert("part_payments", record, session)
        await tx_insert("loan_schedules", schedule_doc, session)
        await tx_set("loans", {"loan_id": loan_id}, loan_updates, session)
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
    async with atomic() as session:
        await tx_insert("loan_events", event, session)
        await tx_insert("loan_schedules", schedule_doc, session)
        await tx_set("loans", {"loan_id": loan_id}, {"interest_rate": payload.annual_rate, "repayment_period": payload.remaining_periods, "moratorium_periods": payload.moratorium_periods, "schedule_version": version, "emi": schedule["emi"], "maturity_date": schedule["maturity_date"], "contract_interest": from_paise(interest_paid + new_interest), "total_repayment": schedule["total_repayment"], "status": "Restructured"}, session)
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
    async with atomic() as session:
        await tx_insert("writeoffs", record, session)
        await tx_set("loans", {"loan_id": loan_id}, {"status": "Written Off" if amount == balances["balance_paise"] else loan.get("status", "Active")}, session)
        await post_journal(entry_id, "loan_writeoff", writeoff_id, f"Write-off {payload.approval_reference}", lines, user, session=session)
    await audit(user, "loan_writeoff", "loan", loan_id, record, request)
    return {"writeoff": record, "loan": await enrich_loan(await find_one("loans", {"loan_id": loan_id}))}


def parse_business_date(value: Optional[str], field: str) -> datetime:
    """A calendar date chosen in the UI (YYYY-MM-DD) is taken as 10:00 India time that day."""
    if not value:
        return now()
    text = str(value).strip()
    try:
        if len(text) == 10:
            day = datetime.strptime(text, "%Y-%m-%d").date()
            return datetime(day.year, day.month, day.day, 10, 0, tzinfo=BUSINESS_TIMEZONE).astimezone(timezone.utc)
        return parse_date(text)
    except ValueError as exc:
        raise HTTPException(422, f"{field} is not a valid date") from exc


def validate_loan_dates(payload: LoanIn) -> tuple[datetime, Optional[datetime]]:
    today = business_now().date()
    borrow = parse_business_date(payload.borrow_date, "Loan date")
    borrow_day = borrow.astimezone(BUSINESS_TIMEZONE).date()
    if borrow_day > today:
        raise HTTPException(422, "Loan date cannot be in the future")
    age = (today - borrow_day).days
    if payload.existing_loan:
        if age > EXISTING_LOAN_MAX_AGE_DAYS:
            raise HTTPException(422, f"Existing loans can be entered up to {EXISTING_LOAN_MAX_AGE_DAYS // 365} years back")
    elif age > NEW_LOAN_BACKDATE_DAYS:
        raise HTTPException(422, f"A new loan can be dated at most {NEW_LOAN_BACKDATE_DAYS} days back. For an older loan, tick 'Existing loan'.")
    repaid_on = None
    if payload.existing_loan and payload.already_repaid > 0:
        repaid_on = parse_business_date(payload.repaid_up_to, "Repaid up to date") if payload.repaid_up_to else min(now(), borrow + timedelta(days=1))
        repaid_day = repaid_on.astimezone(BUSINESS_TIMEZONE).date()
        if repaid_day < borrow_day or repaid_day > today:
            raise HTTPException(422, "'Repaid up to' must be between the loan date and today")
    return borrow, repaid_on


def prepare_loan_terms(payload: LoanIn) -> tuple[LoanIn, datetime, Optional[datetime], dict[str, Any]]:
    if payload.loan_type not in LOAN_TYPES:
        raise HTTPException(422, "Invalid loan type")
    validate_new_loan_rate(payload.interest_rate)
    # Tax on fee, moratorium and pre-closure charge were removed from disbursement: new loans always carry 0 for them.
    payload = payload.model_copy(update={"interest_method": "Upfront Monthly Flat", "tax_rate": 0, "moratorium_periods": 0, "preclosure_charge_rate": 0})
    borrow, repaid_on = validate_loan_dates(payload)
    schedule = apply_cash_rounding(build_amortization(payload, borrow), payload.cash_handover)
    if payload.existing_loan and payload.already_repaid > schedule["total_repayment"]:
        raise HTTPException(422, f"Amount already repaid cannot be more than the total repayment of ₹{schedule['total_repayment']:,.2f}")
    return payload, borrow, repaid_on, schedule


def loan_ack_required() -> bool:
    if LOAN_ACK_OTP == "off":
        return False
    if LOAN_ACK_OTP == "required":
        return True
    return sms_configured()


def ack_terms(payload: LoanIn, schedule: dict[str, Any]) -> dict[str, Any]:
    return {
        "principal": round(float(payload.principal), 2), "cash_handover": round(float(schedule["net_disbursed"]), 2),
        "interest_rate": round(float(payload.interest_rate), 4), "loan_type": payload.loan_type,
        "repayment_period": int(payload.repayment_period), "instalment": round(float(schedule["emi"]), 2),
        "processing_fee": round(float(schedule["processing_fee"]), 2),
    }


def rupees(value: float) -> str:
    return f"Rs {value:,.2f}".replace(".00", "")


@app.post("/api/loan-acknowledgements/send")
async def send_loan_acknowledgement(payload: LoanIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    """SMS the loan's key facts and an OTP to the customer's registered mobile."""
    if payload.existing_loan:
        raise HTTPException(409, "Existing loans entered from old records do not need an OTP acknowledgement")
    customer = await find_one("customers", {"customer_id": payload.customer_id})
    if not customer or customer.get("profile_deleted_at"):
        raise HTTPException(404, "Customer not found")
    payload, borrow, _, schedule = prepare_loan_terms(payload)
    stamp = now()
    recent = [row for row in await find_many("loan_acknowledgements", {"customer_id": payload.customer_id}) if parse_date(row["created_at"]) > stamp - timedelta(days=1)]
    if len(recent) >= MOBILE_OTP_DAILY_LIMIT:
        raise HTTPException(429, "Daily OTP limit reached for this customer. Try again tomorrow.")
    latest = max(recent, key=lambda row: row["created_at"], default=None)
    if latest and latest.get("status") == "Sent" and parse_date(latest["created_at"]) + timedelta(seconds=MOBILE_OTP_RESEND_SECONDS) > stamp:
        wait = int((parse_date(latest["created_at"]) + timedelta(seconds=MOBILE_OTP_RESEND_SECONDS) - stamp).total_seconds()) + 1
        raise HTTPException(429, f"Please wait {wait} seconds before resending the OTP.")
    terms = ack_terms(payload, schedule)
    request_id = f"LAK-{await next_sequence('LAK', 'ack_request_id', 'loan_acknowledgements'):09d}"
    otp = f"{secrets.randbelow(1_000_000):06d}"
    # Kept short at the client's request: loan amount and OTP only. The full terms
    # (cash given, instalments) are still bound to this acknowledgement on the server.
    text = (f"{SMS_SENDER_NAME}: You are taking a loan of {rupees(terms['principal'])}. "
            f"OTP {otp}. Share this OTP with our staff ONLY if you agree and have received the cash.")
    delivery = await send_sms(customer["mobile"], text)
    for row in recent:
        if row.get("status") == "Sent":
            await update_where("loan_acknowledgements", {"ack_request_id": row["ack_request_id"], "status": "Sent"}, {"status": "Superseded"})
    record = {
        "ack_request_id": request_id, "customer_id": payload.customer_id, "mobile": customer["mobile"], "terms": terms,
        "sms_text_sha256": hashlib.sha256(text.replace(otp, "******").encode()).hexdigest(), "sms_text_masked": text.replace(otp, "******"),
        "otp_hash": mobile_otp_hash(request_id, otp), "status": "Sent", "created_at": iso(stamp),
        "expires_at": iso(stamp + timedelta(seconds=LOAN_ACK_OTP_TTL_SECONDS)), "attempt_count": 0, "max_attempts": MOBILE_OTP_MAX_ATTEMPTS,
        "provider": "demo" if delivery["demo"] else normalized_sms_provider(), "gateway_message_id": delivery["gateway_message_id"],
        "requested_by": user["name"], "requested_by_id": user["id"],
    }
    await insert_one("loan_acknowledgements", record)
    await audit(user, "loan_acknowledgement_otp_sent", "customer", payload.customer_id, {"ack_request_id": request_id, "mobile": mask_mobile(customer["mobile"]), "terms": terms}, request)
    result = {"ack_request_id": request_id, "status": "Sent", "masked_destination": mask_mobile(customer["mobile"]), "terms": terms,
              "expires_at": record["expires_at"], "resend_available_at": iso(stamp + timedelta(seconds=MOBILE_OTP_RESEND_SECONDS)),
              "attempts_remaining": MOBILE_OTP_MAX_ATTEMPTS, "sms_preview": record["sms_text_masked"]}
    if delivery["demo"]:
        result["dev_otp"] = otp
    return result


@app.post("/api/loan-acknowledgements/verify")
async def verify_loan_acknowledgement(payload: LoanAckVerifyIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    record = await find_one("loan_acknowledgements", {"ack_request_id": payload.ack_request_id})
    if not record:
        raise HTTPException(404, "Acknowledgement request not found")
    if record["status"] != "Sent":
        raise HTTPException(409, "This OTP is no longer valid. Send a new OTP.")
    stamp = now()
    if parse_date(record["expires_at"]) <= stamp:
        await update_where("loan_acknowledgements", {"ack_request_id": payload.ack_request_id, "status": "Sent"}, {"status": "Expired"})
        raise HTTPException(410, "OTP expired. Send a new OTP.")
    if not hmac.compare_digest(record["otp_hash"], mobile_otp_hash(payload.ack_request_id, payload.otp)):
        attempts = int(record.get("attempt_count", 0))
        remaining = max(int(record.get("max_attempts", MOBILE_OTP_MAX_ATTEMPTS)) - attempts - 1, 0)
        if not await update_where("loan_acknowledgements", {"ack_request_id": payload.ack_request_id, "status": "Sent", "attempt_count": attempts}, {"status": "Locked" if remaining == 0 else "Sent", "last_failed_at": iso(stamp)}, {"attempt_count": 1}):
            raise HTTPException(409, "OTP state changed. Please try again.")
        await audit(user, "loan_acknowledgement_otp_failed", "customer", record["customer_id"], {"ack_request_id": payload.ack_request_id, "attempts_remaining": remaining}, request)
        if remaining == 0:
            raise HTTPException(423, "OTP locked after 3 incorrect attempts. Send a new OTP.")
        raise HTTPException(422, f"Incorrect OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.")
    ack_no = f"ACK-{business_now().strftime('%Y%m%d')}-{await next_sequence('ACKN', 'ack_seq', 'loan_acknowledgements'):06d}"
    fields = {"status": "Verified", "ack_no": ack_no, "ack_seq": f"ACKN{ack_no[-6:]}", "verified_at": iso(stamp), "verified_by": user["name"],
              "valid_until": iso(stamp + timedelta(minutes=LOAN_ACK_VALID_MINUTES)), "ip": request.client.host if request.client else "local"}
    if not await update_where("loan_acknowledgements", {"ack_request_id": payload.ack_request_id, "status": "Sent"}, fields):
        raise HTTPException(409, "This OTP was already used")
    await audit(user, "loan_acknowledgement_verified", "customer", record["customer_id"], {"ack_no": ack_no, "ack_request_id": payload.ack_request_id, "mobile": mask_mobile(record["mobile"]), "terms": record["terms"]}, request)
    return {"ack_no": ack_no, "verified_at": fields["verified_at"], "valid_until": fields["valid_until"], "masked_destination": mask_mobile(record["mobile"]), "terms": record["terms"]}


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
    if REQUIRE_MOBILE_VERIFIED_DISBURSAL and not mobile_verified(customer):
        raise HTTPException(409, "Verify the customer's mobile number by SMS OTP before disbursal")
    if identity_verification and float(identity_verification.get("disbursed_amount", 0)) != float(payload.principal):
        raise HTTPException(409, "Verified handover amount does not match the loan principal")
    payload, borrow, repaid_on, schedule = prepare_loan_terms(payload)
    collector = await find_one("users", {"id": payload.collector_id})
    if not collector or collector.get("role") not in {"collector", "owner", "manager"} or not collector.get("active", True):
        raise HTTPException(422, "Select an active collector or the self-managed owner")
    acknowledgement = None
    if payload.existing_loan:
        reference = payload.kfs_acknowledgement_reference.strip() or f"Existing loan entered on {business_now().strftime('%d-%m-%Y')}"
        payload = payload.model_copy(update={"kfs_acknowledgement_reference": reference, "acknowledgement_no": None})
    else:
        ack_no = (payload.acknowledgement_no or "").strip().upper()
        if ack_no:
            acknowledgement = await find_one("loan_acknowledgements", {"ack_no": ack_no})
            if not acknowledgement or acknowledgement.get("status") != "Verified":
                raise HTTPException(409, "Acknowledgement number not found or already used. Send a new OTP to the customer.")
            if acknowledgement["customer_id"] != payload.customer_id:
                raise HTTPException(409, "This acknowledgement belongs to a different customer")
            if parse_date(acknowledgement["valid_until"]) < now():
                raise HTTPException(409, f"Acknowledgement expired ({LOAN_ACK_VALID_MINUTES} minutes after OTP). Send a new OTP.")
            if acknowledgement["terms"] != ack_terms(payload, schedule):
                raise HTTPException(409, "Loan details changed after the customer acknowledged them. Send a new OTP so the customer confirms the final amount.")
            payload = payload.model_copy(update={"kfs_acknowledgement_reference": ack_no, "acknowledgement_no": ack_no})
        elif loan_ack_required():
            raise HTTPException(409, "The customer must acknowledge this loan by OTP on their registered mobile before it can be created.")
        elif len(payload.kfs_acknowledgement_reference.strip()) < 3:
            raise HTTPException(422, "Enter the borrower acknowledgement reference (at least 3 characters).")
    loan_seq = await next_sequence("LN", "loan_id", "loans")
    loan_id = f"LN-{loan_seq:09d}"
    loan = {
        "loan_id": loan_id,
        "customer_id": payload.customer_id,
        "principal": payload.principal,
        "interest_rate": payload.interest_rate,
        "interest_rate_period": "Monthly",
        "interest_collection_basis": "Upfront Discount",
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
        "calculated_net_disbursed": schedule["calculated_net_disbursed"], "cash_rounding_adjustment": schedule["cash_rounding_adjustment"],
        "first_due_date": schedule["first_due_date"], "maturity_date": schedule["maturity_date"],
        "moratorium_periods": payload.moratorium_periods, "moratorium_interest_capitalized": payload.moratorium_interest_capitalized,
        "preclosure_charge_rate": payload.preclosure_charge_rate, "late_fee": payload.late_fee,
        "emi": schedule["emi"], "contract_interest": schedule["interest_total"],
        "total_repayment": schedule["total_repayment"], "schedule_version": 1,
        "kfs_acknowledgement_reference": payload.kfs_acknowledgement_reference,
        "identity_verification_id": payload.identity_verification_id,
        "existing_loan": payload.existing_loan, "entered_at": iso(now()),
    }
    if acknowledgement:
        loan.update({"acknowledgement_no": acknowledgement["ack_no"], "acknowledgement_method": "OTP to registered mobile",
                     "acknowledgement_mobile": mask_mobile(acknowledgement["mobile"]), "acknowledgement_verified_at": acknowledgement["verified_at"],
                     "acknowledgement_sms": acknowledgement.get("sms_text_masked")})
    journal_seq = await next_sequence("JRN", "entry_id", "journal_entries")
    entry_id = f"JRN-{journal_seq:09d}"
    principal_paise = to_paise(payload.principal)
    interest_paise = to_paise(schedule["interest_total"])
    fee_paise = to_paise(schedule["processing_fee"])
    tax_paise = to_paise(schedule["tax"])
    net_paise = to_paise(schedule["net_disbursed"])
    opening_payment = None
    if payload.existing_loan:
        # Money was lent before this system: no cash moves today. The amount still owed is
        # recorded as an opening receivable against Opening Balance Equity.
        repaid_paise = to_paise(payload.already_repaid)
        outstanding_paise = principal_paise - repaid_paise
        lines = [ledger_line("1100", debit_paise=outstanding_paise, loan_id=loan_id, customer_id=payload.customer_id), ledger_line("3000", credit_paise=outstanding_paise, loan_id=loan_id)] if outstanding_paise > 0 else []
        if repaid_paise > 0:
            opening_payment = {
                "receipt_no": f"OPN-{loan_id}", "loan_id": loan_id, "customer_id": payload.customer_id, "amount": from_paise(repaid_paise),
                "mode": "Opening balance", "collector_id": payload.collector_id, "timestamp": iso(repaid_on), "status": "Posted",
                "payment_type": "Opening balance", "journal_entry_id": None, "payment_reference": "Repaid before this system",
                "allocation": {"penalty_paise": 0, "interest_paise": 0, "principal_paise": repaid_paise},
                "balance_before": from_paise(principal_paise), "balance_after": from_paise(outstanding_paise), "recorded_at": iso(now()), "recorded_by": user["name"],
            }
        description = f"Existing loan brought in for {payload.customer_id}"
    else:
        lines = [
            ledger_line("1100", debit_paise=principal_paise, loan_id=loan_id, customer_id=payload.customer_id),
            ledger_line(cash_account(payload.disbursement_mode), credit_paise=net_paise, loan_id=loan_id),
        ]
        if fee_paise:
            lines.append(ledger_line("4200", credit_paise=fee_paise, loan_id=loan_id))
        if tax_paise:
            lines.append(ledger_line("2100", credit_paise=tax_paise, loan_id=loan_id))
        if interest_paise:
            lines.append(ledger_line("4000", credit_paise=interest_paise, loan_id=loan_id))
        description = f"Loan disbursed to {payload.customer_id}"
    if not lines:
        loan["journal_entry_id"] = None
    async with atomic() as session:
        if acknowledgement:
            used = {"status": "Used", "loan_id": loan_id, "used_at": iso(now())}
            if USE_MEMORY:
                if not await update_where("loan_acknowledgements", {"ack_no": acknowledgement["ack_no"], "status": "Verified"}, used):
                    raise HTTPException(409, "This acknowledgement was already used for another loan")
            else:
                result = await db.loan_acknowledgements.update_one({"ack_no": acknowledgement["ack_no"], "status": "Verified"}, {"$set": used}, session=session)
                if result.modified_count != 1:
                    raise HTTPException(409, "This acknowledgement was already used for another loan")
        await tx_insert("loans", loan, session)
        await tx_insert("loan_schedules", {"loan_id": loan_id, "version": 1, "reason": "Existing loan" if payload.existing_loan else "Origination", "created_at": iso(now()), **schedule}, session)
        if opening_payment:
            await tx_insert("payments", opening_payment, session)
        if lines:
            await post_journal(entry_id, "existing_loan" if payload.existing_loan else "loan_disbursement", loan_id, description, lines, user, session=session)
        await audit(user, "existing_loan_entered" if payload.existing_loan else "loan_disbursement", "loan", loan_id, loan, request, session=session)
    if payload.existing_loan:
        await sync_loan_status(loan_id)
        loan = await find_one("loans", {"loan_id": loan_id}) or loan
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
        if payload.payment_type == "Prepayment" and amount_paise >= balances["balance_paise"]:
            raise HTTPException(422, "A prepayment must be less than the outstanding balance. Use Close account to settle the full balance.")
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
            "payment_reference": (payload.payment_reference or "").strip() or None,
            "payment_type": payload.payment_type,
            "allocation": {"penalty_paise": penalty_part, "interest_paise": interest_part, "principal_paise": principal_part},
            "balance_before": from_paise(balances["balance_paise"]),
            "balance_after": from_paise(balances["balance_paise"] - amount_paise),
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
    await sync_loan_status(payment["loan_id"])
    loan = await find_one("loans", {"loan_id": payment["loan_id"]})
    after = await enrich_loan(loan)
    return {"payment": payment, "loan": after, "receipt": await receipt_payload(payment)}


@app.post("/api/loans/{loan_id}/close")
async def close_loan(loan_id: str, payload: LoanClosureIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    if not payload.confirmed or payload.confirmation.strip().upper() != loan_id.upper():
        raise HTTPException(422, f"Type loan ID {loan_id} and confirm the permanent closure")
    if user["role"] == "manager" and len(payload.approval_reference.strip()) < 3:
        raise HTTPException(422, "Owner approval reference is required when a manager closes a loan")
    existing = await find_one("payments", {"request_id": payload.request_id})
    if existing:
        loan = await enrich_loan(await find_one("loans", {"loan_id": loan_id}))
        return {"loan": loan, "receipt": await receipt_payload(existing), "duplicate": True}
    stamp = now()
    receipt_seq = await next_sequence(f"RCP-{stamp.strftime('%Y%m%d')}", "receipt_no", "payments")
    receipt_no = f"RCP-{stamp.strftime('%Y%m%d')}-{receipt_seq:06d}"
    journal_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    event_id = f"LEV-{await next_sequence('LEV', 'event_id', 'loan_events'):08d}"

    async def post_closure(session: Any = None) -> dict[str, Any]:
        loan = await (find_one("loans", {"loan_id": loan_id}) if USE_MEMORY else db.loans.find_one({"loan_id": loan_id}, session=session))
        if not loan:
            raise HTTPException(404, "Loan not found")
        balances = await loan_component_balances(loan, session=session)
        if balances["balance_paise"] <= 0:
            raise HTTPException(409, "This loan is already completed")
        settlement = balances["balance_paise"]
        remaining = balances["balance_paise"]
        penalty_part = min(remaining, balances["penalty_balance_paise"]); remaining -= penalty_part
        interest_part = min(remaining, balances["interest_balance_paise"]); remaining -= interest_part
        principal_part = remaining
        payment = {
            "receipt_no": receipt_no, "loan_id": loan_id, "customer_id": loan["customer_id"],
            "amount": from_paise(settlement), "mode": payload.mode, "collector_id": user["id"],
            "timestamp": iso(stamp), "status": "Posted", "journal_entry_id": journal_id,
            "payment_reference": (payload.payment_reference or "").strip() or None,
            "request_id": payload.request_id, "closure_payment": True, "closure_reason": payload.reason.strip(),
            "closure_approval_reference": payload.approval_reference.strip() or f"OWNER-{user['id']}",
            "allocation": {"penalty_paise": penalty_part, "interest_paise": interest_part, "principal_paise": principal_part},
            "balance_before": from_paise(balances["balance_paise"]), "balance_after": 0.0,
        }
        lines = [ledger_line(cash_account(payload.mode), debit_paise=settlement, loan_id=loan_id)]
        if penalty_part: lines.append(ledger_line("1300", credit_paise=penalty_part, loan_id=loan_id))
        if interest_part: lines.append(ledger_line("1200", credit_paise=interest_part, loan_id=loan_id))
        if principal_part: lines.append(ledger_line("1100", credit_paise=principal_part, loan_id=loan_id))
        event = {"event_id": event_id, "loan_id": loan_id, "event_type": "Loan Closed", "reason": payload.reason.strip(), "approval_reference": payload.approval_reference.strip() or f"OWNER-{user['id']}", "receipt_no": receipt_no, "settlement_amount": from_paise(settlement), "timestamp": iso(stamp), "posted_by": user["name"]}
        loan_update = {"status": "Closed", "closed_at": iso(stamp), "closed_by": user["name"], "closure_reason": payload.reason.strip(), "closure_receipt_no": receipt_no}
        if USE_MEMORY:
            await insert_one("payments", payment)
            await insert_one("loan_events", event)
            await replace_one("loans", {"loan_id": loan_id}, {**loan, **loan_update})
            await post_journal(journal_id, "loan_closure", receipt_no, f"Full and final closure of {loan_id}", lines, user)
            await audit(user, "loan_closed", "loan", loan_id, {"payment": payment, "event": event}, request)
        else:
            await db.payments.insert_one(deepcopy(payment), session=session)
            await db.loan_events.insert_one(deepcopy(event), session=session)
            result = await db.loans.update_one({"_id": loan["_id"], "status": {"$ne": "Closed"}}, {"$set": loan_update, "$inc": {"ledger_version": 1}}, session=session)
            if result.modified_count != 1: raise HTTPException(409, "Loan changed concurrently; reload and retry")
            await post_journal(journal_id, "loan_closure", receipt_no, f"Full and final closure of {loan_id}", lines, user, session=session)
            await audit(user, "loan_closed", "loan", loan_id, {"payment": payment, "event": event}, request, session=session)
        return payment

    if USE_MEMORY:
        payment = await post_closure()
    else:
        async with await mongo_client.start_session() as session:
            try:
                payment = await session.with_transaction(post_closure)
            except DuplicateKeyError:
                payment = await db.payments.find_one({"request_id": payload.request_id})
                if not payment: raise HTTPException(409, "Closure was already submitted")
    loan = await enrich_loan(await find_one("loans", {"loan_id": loan_id}))
    return {"loan": loan, "receipt": await receipt_payload(payment), "closed_at": loan.get("closed_at"), "closure_reason": loan.get("closure_reason")}


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
        "payment_reference": payment.get("payment_reference"),
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


async def interest_rebate_limit(loan: dict[str, Any], balances: dict[str, int]) -> tuple[int, int, int]:
    original_interest = to_paise(loan.get("contract_interest", 0))
    adjustments = await find_many("loan_adjustments", {"loan_id": loan["loan_id"]})
    already_rebated = sum(
        to_paise(row.get("amount", 0)) for row in adjustments
        if row.get("kind") == "Interest Rebate" and row.get("status", "Posted") != "Reversed"
    )
    return original_interest, already_rebated, min(max(original_interest - already_rebated, 0), balances["principal_balance_paise"])


@app.get("/api/loans/{loan_id}/adjustment-preview")
async def adjustment_preview(loan_id: str, amount: float, user: dict[str, Any] = Depends(require("owner", "manager", "accountant"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.get("status") not in {"Active", "Overdue", "Restructured"}:
        raise HTTPException(409, "Interest can be adjusted only on an active loan")
    proposed = to_paise(amount)
    if proposed <= 0:
        raise HTTPException(422, "Adjustment amount must be greater than zero")
    balances = await loan_component_balances(loan)
    original_interest, already_rebated, maximum = await interest_rebate_limit(loan, balances)
    return {
        "loan_id": loan_id, "original_interest": from_paise(original_interest),
        "previous_rebates": from_paise(already_rebated),
        "maximum_rebate": from_paise(maximum), "proposed_rebate": from_paise(proposed),
        "balance_before": from_paise(balances["balance_paise"]),
        "balance_after": from_paise(max(balances["balance_paise"] - proposed, 0)),
        "permitted": proposed <= maximum,
        "message": "Adjustment is within the remaining contract interest" if proposed <= maximum else "Rebate exceeds the remaining adjustable contract interest",
    }


@app.post("/api/loans/{loan_id}/adjustments")
async def loan_adjustment(loan_id: str, payload: LoanAdjustmentIn, request: Request, user: dict[str, Any] = Depends(require("owner", "manager"))) -> dict[str, Any]:
    loan = await find_one("loans", {"loan_id": loan_id})
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.get("status") not in {"Active", "Overdue", "Restructured"}:
        raise HTTPException(409, "Adjustments can be posted only to an active loan")
    balances = await loan_component_balances(loan)
    amount = to_paise(payload.amount)
    if payload.kind == "Interest Waiver" and amount > balances["interest_balance_paise"]:
        raise HTTPException(409, "Waiver exceeds outstanding interest")
    if payload.kind == "Interest Rebate":
        _original_interest, _already_rebated, maximum_rebate = await interest_rebate_limit(loan, balances)
        if amount > maximum_rebate:
            raise HTTPException(409, "Interest rebate exceeds the remaining adjustable contract interest")
    if payload.kind == "Penalty Waiver" and amount > balances["penalty_balance_paise"]:
        raise HTTPException(409, "Waiver exceeds outstanding penalty")
    adjustment_id = f"ADJ-{await next_sequence('ADJ', 'adjustment_id', 'loan_adjustments'):08d}"
    entry_id = f"JRN-{await next_sequence('JRN', 'entry_id', 'journal_entries'):09d}"
    adjustment = {"adjustment_id": adjustment_id, "loan_id": loan_id, **payload.model_dump(), "amount": from_paise(amount), "balance_before": from_paise(balances["balance_paise"]), "balance_after": from_paise(max(balances["balance_paise"] - amount, 0)), "timestamp": iso(now()), "status": "Posted", "journal_entry_id": entry_id, "posted_by": user["name"]}
    if payload.kind == "Penalty":
        lines = [ledger_line("1300", debit_paise=amount, loan_id=loan_id), ledger_line("4100", credit_paise=amount, loan_id=loan_id)]
    elif payload.kind == "Interest Rebate":
        lines = [ledger_line("4000", debit_paise=amount, loan_id=loan_id), ledger_line("1100", credit_paise=amount, loan_id=loan_id)]
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
    await sync_loan_status(loan_id)
    loan = await find_one("loans", {"loan_id": loan_id}) or loan
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
    paid = await instalment_paid_paise(loan_id)
    if paid >= cumulative_due:
        raise HTTPException(409, "Installment is already fully paid")
    defaulter = await late_charge_status(loan)
    if not defaulter["is_defaulter"]:
        raise HTTPException(409, defaulter["message"] or "Late charge can be applied only to defaulters")
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
    if payment.get("payment_type") == "Opening balance":
        raise HTTPException(409, "This is the amount repaid before the system was used. If it is wrong, ask the owner to correct the existing loan entry.")
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
    affected_loan_id = (source_before or {}).get("loan_id")
    if affected_loan_id:
        await sync_loan_status(affected_loan_id, allow_reopen=True)
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
    loans_rows = await enrich_loans(await find_many("loans"))
    payment_rows = await find_many("payments")
    # Money actually collected through the system (not reversed, not amounts repaid before the system).
    collected_rows = [p for p in payment_rows if p.get("status", "Posted") != "Reversed" and p.get("payment_type") != "Opening balance"]
    customers_rows = await customer_views(await find_many("customers"))
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
        daily = [p for p in collected_rows if business_date_key(p["timestamp"]) == day]
        return {"title": "Daily Collection Report", "date": day, "payments": daily, "total": round(sum(p["amount"] for p in daily), 2)}
    if payload.report_type == "monthly-cashflow":
        month = payload.month or now().strftime("%Y-%m")
        monthly = [p for p in collected_rows if business_month_key(p["timestamp"]) == month]
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
        return {"title": "Business Growth Report", "cashflow": build_cashflow(collected_rows), "customers": len(customers_rows), "loans": len(loans_rows), "total_disbursed": round(sum(l["principal"] for l in loans_rows), 2)}
    year = str(payload.year or now().year)
    year_payments = [p for p in collected_rows if p["timestamp"][:4] == year]
    year_loans = [l for l in loans_rows if l["borrow_date"][:4] == year]
    return {
        "title": "Annual Report",
        "year": year,
        "collected": round(sum(p["amount"] for p in year_payments), 2),
        "disbursed": round(sum(l["principal"] for l in year_loans), 2),
        "bad_debts": round(sum(l["balance"] for l in loans_rows if l["status"] == "Overdue"), 2),
        "area_contribution": [
            {"name": area["name"], "customers": area["customers"], "active_loans": area["active_loans"], "total_disbursed": area["total_disbursed"], "outstanding": area["outstanding"]}
            for area in (await dashboard(await find_one("users", {"role": "owner"})))["area_summary"]
        ],
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


@app.patch("/api/areas/{code}")
async def update_area(code: str, payload: AreaUpdateIn, request: Request, user: dict[str, Any] = Depends(require("owner"))) -> dict[str, Any]:
    old_code = code.strip().upper()
    new_code = payload.code or old_code
    area = await find_one("areas", {"code": old_code})
    if not area:
        raise HTTPException(404, "Area not found")
    if new_code != old_code and await find_one("areas", {"code": new_code}):
        raise HTTPException(409, f"Area code {new_code} already exists")
    updated = {
        **area, "code": new_code, "name": " ".join(payload.name.split()),
        "updated_at": iso(now()), "updated_by": user["name"],
    }
    details = {
        "old_code": old_code, "new_code": new_code,
        "old_name": area.get("name"), "new_name": updated["name"],
        "customer_ids_unchanged": True,
    }
    if USE_MEMORY:
        affected = await find_many("customers", {"area": old_code})
        await replace_one("areas", {"code": old_code}, updated)
        for customer in affected:
            migrated = {**customer, "area": new_code, "area_updated_at": updated["updated_at"]}
            await replace_one("customers", {"customer_id": customer["customer_id"]}, migrated)
        details["customers_migrated"] = len(affected)
        await audit(user, "area_updated", "area", new_code, details, request)
    else:
        async with await mongo_client.start_session() as session:
            async with session.start_transaction():
                result = await db.areas.replace_one({"code": old_code}, deepcopy(updated), session=session)
                if result.modified_count != 1:
                    raise HTTPException(409, "Area changed concurrently; reload and retry")
                customer_result = await db.customers.update_many(
                    {"area": old_code},
                    {"$set": {"area": new_code, "area_updated_at": updated["updated_at"]}},
                    session=session,
                )
                details["customers_migrated"] = customer_result.modified_count
                await audit(user, "area_updated", "area", new_code, details, request, session=session)
    return {**updated, "customers_migrated": details["customers_migrated"]}


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
