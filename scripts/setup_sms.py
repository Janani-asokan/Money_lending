"""Connect the app to SMS Gateway for Android and send a test OTP.

Run from the project folder:  python scripts/setup_sms.py
(or double-click setup-sms.bat on Windows)

It checks your gateway login, confirms the phone is online, sends a real test
OTP to a mobile number you choose, and saves the settings into server/.env.
The password is stored only in server/.env, which git ignores.
"""
from __future__ import annotations

import base64
import getpass
import json
import secrets
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "server" / ".env"
ENV_EXAMPLE = ROOT / "server" / ".env.example"
CLOUD_API = "https://api.sms-gate.app/3rdparty/v1"


def call(method: str, url: str, username: str, password: str, body: dict | None = None) -> tuple[int, object]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    request = Request(url, data=data, method=method, headers={"Authorization": f"Basic {token}", "Content-Type": "application/json", "User-Agent": "MoneyLendingSMS/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def save_env(values: dict[str, str]) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    remaining = dict(values)
    out = []
    for line in lines:
        key = line.split("=", 1)[0].lstrip("# ").strip()
        if key in remaining and ("=" in line):
            out.append(f"{key}={remaining.pop(key)}")
        else:
            out.append(line)
    out.extend(f"{key}={value}" for key, value in remaining.items())
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    print("=== Free SMS OTP setup (SMS Gateway for Android) ===\n")
    print("On the gateway phone: open the SMS Gateway app, turn on 'Cloud server' and tap 'Online'.\n")
    username = input("Gateway username (exactly as shown in the app): ").strip()
    password = getpass.getpass("Gateway password (hidden while typing): ").strip()
    if not username or not password:
        print("Username and password are required.")
        return 1

    print("\n[1/3] Checking login and phone status...")
    try:
        status, devices = call("GET", f"{CLOUD_API}/devices", username, password)
    except (URLError, TimeoutError) as exc:
        print(f"  Cannot reach api.sms-gate.app ({exc}). Check this computer's internet connection.")
        return 1
    if status == 401:
        print("  Login rejected. Re-check the username/password in the app (they are case-sensitive).")
        return 1
    if status != 200:
        print(f"  Unexpected reply {status}: {devices}")
        return 1
    if not devices:
        print("  Login OK, but no phone is registered. Open the app, enable Cloud server and tap Online.")
        return 1
    for device in devices:
        print(f"  Phone: {device.get('name', 'device')}  last seen: {device.get('lastSeen', 'unknown')}")
    print("  Login OK.")

    print("\n[2/3] Sending a test OTP...")
    mobile = "".join(ch for ch in input("Mobile number to receive the test OTP (10 digits): ") if ch.isdigit())[-10:]
    if len(mobile) != 10 or mobile[0] not in "6789":
        print("  Enter a valid 10-digit Indian mobile number.")
        return 1
    otp = f"{secrets.randbelow(1_000_000):06d}"
    status, sent = call("POST", f"{CLOUD_API}/message", username, password,
                        {"textMessage": {"text": f"{otp} is your test OTP from Sri Sakthi Thirumurugan Finance. SMS setup is working."}, "phoneNumbers": [f"+91{mobile}"]})
    if status not in (200, 201, 202):
        print(f"  Gateway refused the message ({status}): {sent}")
        return 1
    message_id = sent.get("id") if isinstance(sent, dict) else None
    state = sent.get("state", "Pending") if isinstance(sent, dict) else "Pending"
    print(f"  Queued (id {message_id}). Waiting for the phone to send it...")
    for _ in range(12):
        if not message_id or state in {"Sent", "Delivered", "Failed"}:
            break
        time.sleep(5)
        status, info = call("GET", f"{CLOUD_API}/message/{message_id}", username, password)
        if status == 200 and isinstance(info, dict):
            state = info.get("state", state)
            print(f"  Status: {state}")
    if state == "Failed":
        print("  The phone could not send the SMS. Check its SIM balance/SMS pack and that the app has SMS permission.")
        return 1
    if state in {"Pending", "Processed"}:
        print("  Still waiting on the phone. Make sure it is Online, unlocked once, and has battery saver off for the app.")

    typed = input(f"\nType the OTP you received on {mobile} (or press Enter to skip): ").strip()
    if typed and typed != otp:
        print("  That code does not match. The settings will still be saved; try again from the app.")
    elif typed:
        print("  OTP matched - SMS delivery works!")

    print("\n[3/3] Saving settings to server/.env ...")
    save_env({
        "SMS_PROVIDER": "android_gateway",
        "SMS_GATEWAY_URL": f"{CLOUD_API}/message",
        "SMS_GATEWAY_USERNAME": username,
        "SMS_GATEWAY_PASSWORD": password,
    })
    print(f"  Saved {ENV_FILE}")
    print("\nDone. Start the app (start-app.bat), log in as owner, open Customer 360 and click 'Send OTP by SMS'.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
