#!/usr/bin/env python3
"""Secret-safe Mistral API probe using only Python's standard library."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = "https://api.mistral.ai/v1"
USER_AGENT = "th0rgal-mistral-auth-repro/1.0"
MODELS = ("mistral-small-latest", "leanstral-1-5", "labs-leanstral-1-5")
SAFE_HEADERS = ("date", "content-type", "x-request-id", "request-id", "mistral-request-id", "cf-ray")


def sanitize(value: Any, secret: str) -> Any:
    if isinstance(value, dict):
        return {
            str(k): "[REDACTED]" if any(x in str(k).lower() for x in ("authorization", "api_key", "token", "secret", "password")) else sanitize(v, secret)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [sanitize(v, secret) for v in value]
    if isinstance(value, str):
        text = value.replace(secret, "[REDACTED]") if secret else value
        return re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", text)
    return value


def request(secret: str, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    url = BASE + path
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw, status, final_url, headers = response.read(100_000), response.status, response.geturl(), response.headers
            error_class = None
    except urllib.error.HTTPError as exc:
        raw, status, final_url, headers = exc.read(100_000), exc.code, exc.geturl(), exc.headers
        error_class = "http_error"
    except Exception as exc:
        return {"method": method, "path": path, "status": None, "error_class": type(exc).__name__, "error_message": sanitize(str(exc), secret), "started_at": started}
    text = raw.decode(errors="replace")
    try:
        body: Any = json.loads(text)
    except json.JSONDecodeError:
        body = {"raw_text": text[:4000]}
    return {
        "method": method,
        "path": path,
        "final_url": final_url,
        "redirected": final_url != url,
        "status": status,
        "error_class": error_class,
        "response_headers": {k: headers.get(k) for k in SAFE_HEADERS if headers.get(k) is not None},
        "response_body": sanitize(body, secret),
        "started_at": started,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--credential-env", default="MISTRAL_API_KEY")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    secret = os.environ.get(args.credential_env, "")
    if not secret:
        raise SystemExit(f"{args.credential_env} is not set")
    probes = [request(secret, "GET", "/models", None)]
    for model in MODELS:
        is_leanstral = "leanstral" in model
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Reply exactly OK."}],
            "max_tokens": 64 if is_leanstral else 4,
            "temperature": 1.0 if is_leanstral else 0.0,
            "top_p": 1.0,
        }
        if is_leanstral:
            payload["reasoning_effort"] = "high"
        item = request(secret, "POST", "/chat/completions", payload)
        item["requested_model"] = model
        probes.append(item)
    artifact = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "credential_source": args.credential_env,
        "credential_present": True,
        "base_url": BASE,
        "user_agent": USER_AGENT,
        "auth_scheme": "Authorization: Bearer <credential>",
        "probes": probes,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"artifact": str(output), "statuses": [p.get("status") for p in probes]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
