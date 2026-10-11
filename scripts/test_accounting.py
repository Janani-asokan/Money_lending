"""End-to-end accounting regression against the configured local production stack."""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "server" / ".env")
BASE = "http://127.0.0.1:8000"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["MONGO_DB"]]


def call(path: str, method: str = "GET", body: dict | None = None, token: str = ""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(BASE + path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read())


def cleanup() -> None:
    loan_ids = [row["loan_id"] for row in db.loans.find({"customer_id": "QAT001"}, {"loan_id": 1})]
    receipt_ids = [row["receipt_no"] for row in db.payments.find({"customer_id": "QAT001"}, {"receipt_no": 1})]
    expense_ids = [row["expense_id"] for row in db.expenses.find({"description": "QA ledger expense"}, {"expense_id": 1})]
    deposit_ids = [row["deposit_id"] for row in db.collector_deposits.find({"collector_id": "USR-QA"}, {"deposit_id": 1})]
    opening_ids = [row["opening_id"] for row in db.opening_balances.find({"reference": "QA opening"}, {"opening_id": 1})]
    part_ids = [row["part_payment_id"] for row in db.part_payments.find({"loan_id": {"$in": loan_ids}}, {"part_payment_id": 1})]
    writeoff_ids = [row["writeoff_id"] for row in db.writeoffs.find({"loan_id": {"$in": loan_ids}}, {"writeoff_id": 1})]
    event_ids = [row["event_id"] for row in db.loan_events.find({"loan_id": {"$in": loan_ids}}, {"event_id": 1})]
    adjustment_ids = [row["adjustment_id"] for row in db.loan_adjustments.find({"loan_id": {"$in": loan_ids}}, {"adjustment_id": 1})]
    source_ids = loan_ids + receipt_ids + expense_ids + deposit_ids + opening_ids + part_ids + writeoff_ids + event_ids + adjustment_ids
    entry_ids = [row["entry_id"] for row in db.journal_entries.find({"$or": [{"source_id": {"$in": source_ids}}, {"posted_by_id": "USR-QA"}]}, {"entry_id": 1})]
    reversal_request_ids = [row["request_id"] for row in db.reversal_requests.find({"original_entry_id": {"$in": entry_ids}}, {"request_id": 1})]
    db.journal_entries.delete_many({"$or": [{"entry_id": {"$in": entry_ids}}, {"reversal_of": {"$in": entry_ids}}]})
    db.payments.delete_many({"customer_id": "QAT001"})
    db.loans.delete_many({"customer_id": "QAT001"})
    db.loan_schedules.delete_many({"loan_id": {"$in": loan_ids}})
    db.part_payments.delete_many({"loan_id": {"$in": loan_ids}})
    db.writeoffs.delete_many({"loan_id": {"$in": loan_ids}})
    db.loan_events.delete_many({"loan_id": {"$in": loan_ids}})
    db.loan_adjustments.delete_many({"loan_id": {"$in": loan_ids}})
    db.customers.delete_many({"customer_id": "QAT001"})
    db.users.delete_many({"id": "USR-QA"})
    db.users.delete_many({"id": "USR-QA-CHECKER"})
    db.auth_sessions.delete_many({"user_id": {"$in": ["USR-QA", "USR-QA-CHECKER"]}})
    db.reversal_requests.delete_many({"$or": [{"original_entry_id": {"$in": entry_ids}}, {"requested_by_id": {"$in": ["USR-QA", "USR-QA-CHECKER"]}}]})
    db.expenses.delete_many({"description": "QA ledger expense"})
    db.collector_deposits.delete_many({"collector_id": "USR-QA"})
    db.daily_closings.delete_many({"notes": "QA accounting close"})
    db.opening_balances.delete_many({"reference": "QA opening"})
    # Audit logs are intentionally append-only. QA cleanup must never erase history.


def main() -> None:
    cleanup()
    try:
        db.users.insert_one({"id": "USR-QA", "username": "qa-collector", "name": "QA Collector", "role": "collector", "area": "KUN", "active": True, "password_hash": "not-used"})
        db.customers.insert_one({"id": "QAT001", "customer_id": "QAT001", "_customer_seq": "QAT1", "name": "QA Ledger Customer", "father_name": "QA", "mobile": "9000099999", "address": "QA only", "area": "KUN", "guarantor": "", "status": "Manual Verification Approved", "created_at": "2026-01-01T00:00:00+00:00", "risk_score": 70})
        login = call("/api/auth/login", "POST", {"username": os.environ["INITIAL_ADMIN_USERNAME"], "password": os.environ["INITIAL_ADMIN_PASSWORD"]})
        token = login["token"]
        owner = db.users.find_one({"username": os.environ["INITIAL_ADMIN_USERNAME"]})
        db.users.insert_one({"id": "USR-QA-CHECKER", "username": "qa-checker", "name": "QA Manager Checker", "role": "manager", "area": "ALL", "active": True, "password_hash": owner["password_hash"]})
        checker_token = call("/api/auth/login", "POST", {"username": "qa-checker", "password": os.environ["INITIAL_ADMIN_PASSWORD"]})["token"]

        def reverse(path: str, reason: str):
            made = call(path, "POST", {"reason": reason}, token)
            assert made["status"] == "Pending" and made["requested_by_id"] != "USR-QA-CHECKER"
            try:
                call(f"/api/accounting/reversal-requests/{made['request_id']}/decision", "POST", {"decision": "Approve", "approval_reference": "QA-SELF-APPROVAL", "comments": "Must be blocked"}, token)
                raise AssertionError("Maker was incorrectly allowed to approve their own reversal")
            except HTTPError as exc:
                assert exc.code == 403
            decided = call(f"/api/accounting/reversal-requests/{made['request_id']}/decision", "POST", {"decision": "Approve", "approval_reference": "QA-MANAGER-APPROVAL", "comments": "Verified against QA source record"}, checker_token)
            assert decided["status"] == "Approved" and decided["reversal"]["reversal_of"] == made["original_entry_id"]
            return decided
        opening = call("/api/accounting/opening-balances", "POST", {"account": "UPI", "amount": 100, "as_of_date": "2099-12-29", "reference": "QA opening", "request_id": str(uuid.uuid4())}, token)
        loan = call("/api/loans", "POST", {"customer_id": "QAT001", "principal": 1000, "interest_rate": 10, "loan_type": "Monthly EMI", "repayment_period": 10, "collector_id": "USR-QA", "borrow_date": "2026-01-01T00:00:00+00:00", "disbursement_mode": "Bank Transfer", "interest_method": "Reducing", "processing_fee": 10, "tax_rate": 18, "late_fee": 5, "kfs_acknowledgement_reference": "QA-KFS-ACK"}, token)
        schedule = call(f"/api/loans/{loan['loan_id']}/schedule", token=token)
        kfs = call(f"/api/loans/{loan['loan_id']}/kfs", token=token)
        assert round(sum(row["principal"] for row in schedule["rows"]), 2) == 1000.00
        assert round(sum(row["payment"] for row in schedule["rows"]), 2) == round(schedule["total_repayment"], 2)
        assert kfs["apr"] > kfs["annual_interest_rate"] and kfs["net_disbursed_amount"] == 988.20
        late = call(f"/api/loans/{loan['loan_id']}/late-fees/1", "POST", {}, token)
        assert late["adjustment"]["amount"] == 5
        part = call(f"/api/loans/{loan['loan_id']}/part-payment", "POST", {"amount": 100, "strategy": "Reduce EMI", "effective_date": "2026-02-01", "borrower_consent_reference": "QA-PART-CONSENT", "mode": "Bank Transfer"}, token)
        assert part["schedule"]["version"] == 2
        restructured = call(f"/api/loans/{loan['loan_id']}/restructure", "POST", {"annual_rate": 9, "remaining_periods": 8, "moratorium_periods": 1, "effective_date": "2026-03-01", "approval_reference": "QA-BOARD-APPROVAL", "borrower_consent_reference": "QA-RESTRUCTURE-CONSENT"}, token)
        assert restructured["schedule"]["version"] == 3
        payment = call("/api/payments", "POST", {"loan_id": loan["loan_id"], "amount": 200, "mode": "Cash", "collector_id": "USR-QA", "request_id": str(uuid.uuid4())}, token)
        allocation = payment["payment"]["allocation"]
        assert allocation["interest_paise"] > 0 and allocation["penalty_paise"] + allocation["interest_paise"] + allocation["principal_paise"] == 20000
        written = call(f"/api/loans/{loan['loan_id']}/write-off", "POST", {"amount": 50, "reason": "QA approved partial write-off", "approval_reference": "QA-WRITEOFF-APPROVAL"}, token)
        assert written["writeoff"]["allocation"]["principal_paise"] + written["writeoff"]["allocation"]["interest_paise"] + written["writeoff"]["allocation"]["penalty_paise"] == 5000
        deposit = call("/api/accounting/collector-deposits", "POST", {"collector_id": "USR-QA", "amount": 200, "destination": "Cash", "reference": "QA deposit", "request_id": str(uuid.uuid4())}, token)
        expense = call("/api/accounting/expenses", "POST", {"amount": 50, "description": "QA ledger expense", "paid_from": "Cash", "expense_category": "QA", "request_id": str(uuid.uuid4())}, token)
        close = call("/api/accounting/daily-close", "POST", {"business_date": "2099-12-30", "actual_cash": 150, "notes": "QA accounting close"}, token)
        assert close["variance"] == 0
        reverse(f"/api/accounting/journals/{expense['journal_entry_id']}/reversal-requests", "QA reverse expense")
        reverse(f"/api/accounting/journals/{deposit['journal_entry_id']}/reversal-requests", "QA reverse deposit")
        reverse(f"/api/payments/{payment['payment']['receipt_no']}/reversal-requests", "QA reverse receipt")
        reverse(f"/api/accounting/journals/{opening['journal_entry_id']}/reversal-requests", "QA reverse opening")
        journals = call("/api/accounting/journals?limit=500", token=token)
        assert journals and all(row["debit_paise"] == row["credit_paise"] for row in journals)
        print("ACCOUNTING TEST PASSED: allocation, deposits, expenses, closing, maker-checker reversals, and audit balance")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
