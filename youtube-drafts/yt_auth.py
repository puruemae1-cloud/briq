#!/usr/bin/env python3
"""OAuth for Briq YouTube uploads (@briq_kr).

Local: browser login once → youtube-drafts/token.json
Cloud Automations: set Runtime Secrets
  YOUTUBE_CLIENT_SECRET_JSON  (full client_secret.json text)
  YOUTUBE_TOKEN_JSON          (full token.json text)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN = ROOT / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def _materialize_from_env() -> None:
    """Write secret files from env when running in Cloud Agents."""
    secret = os.environ.get("YOUTUBE_CLIENT_SECRET_JSON", "").strip()
    token = os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
    if secret and not CLIENT_SECRET.exists():
        CLIENT_SECRET.write_text(secret if secret.lstrip().startswith("{") else secret)
        CLIENT_SECRET.chmod(0o600)
        # validate JSON
        json.loads(CLIENT_SECRET.read_text())
    if token and not TOKEN.exists():
        TOKEN.write_text(token if token.lstrip().startswith("{") else token)
        TOKEN.chmod(0o600)
        json.loads(TOKEN.read_text())


def get_credentials() -> Credentials:
    _materialize_from_env()
    if not CLIENT_SECRET.exists():
        raise SystemExit(
            f"Missing {CLIENT_SECRET} (local file or YOUTUBE_CLIENT_SECRET_JSON secret)"
        )

    creds: Credentials | None = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())
        TOKEN.chmod(0o600)
        return creds

    # Interactive local login only — cloud must supply a valid YOUTUBE_TOKEN_JSON
    if os.environ.get("CI") or os.environ.get("CURSOR_AGENT") or os.environ.get("YOUTUBE_TOKEN_JSON"):
        raise SystemExit(
            "YouTube token missing/expired. Refresh locally (python3 yt_auth.py), "
            "then update Cloud Agent Runtime Secret YOUTUBE_TOKEN_JSON."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    TOKEN.write_text(creds.to_json())
    TOKEN.chmod(0o600)
    return creds


def main() -> None:
    creds = get_credentials()
    print("OK: authorized")
    print(f"token: {TOKEN}")
    print(f"scopes: {sorted(creds.scopes or [])}")


if __name__ == "__main__":
    main()
