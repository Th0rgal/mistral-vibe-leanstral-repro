#!/usr/bin/env python3
"""Run the same native-tool probe against any OpenAI/Mistral-compatible endpoint."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "leanstral-tool-protocol-repro/1.0"
TOOL = {
    "type": "function",
    "function": {
        "name": "preflight_echo",
        "description": "Echo a short string.",
        "parameters": {
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
            "additionalProperties": False,
        },
    },
}


def post(url: str, key: str, payload: dict) -> tuple[int, dict, dict]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            status, raw, headers = response.status, response.read(1_000_000), response.headers
    except urllib.error.HTTPError as exc:
        status, raw, headers = exc.code, exc.read(1_000_000), exc.headers
    try:
        body = json.loads(raw)
    except Exception:
        body = {"raw_text": raw.decode(errors="replace")[:20_000]}
    serialized = json.dumps(body)
    if key in serialized:
        body = json.loads(serialized.replace(key, "[REDACTED]"))
    safe_headers = {
        name: headers.get(name)
        for name in ("date", "content-type", "x-request-id", "request-id", "mistral-request-id", "cf-ray")
        if headers.get(name)
    }
    return status, body, safe_headers


def summarize(status: int, body: dict, headers: dict) -> dict:
    raw_choice = ((body.get("choices") or [{}])[0] or {}) if isinstance(body, dict) else {}
    choice: dict = raw_choice if isinstance(raw_choice, dict) else {}
    raw_message = choice.get("message")
    message: dict = raw_message if isinstance(raw_message, dict) else {}
    content = message.get("content") or ""
    raw_native = message.get("tool_calls")
    native: list = raw_native if isinstance(raw_native, list) else []
    pseudo = bool(
        not native
        and content
        and (
            "<|tool_call_begin|>" in str(content)
            or re.search(r"(?i)preflight_echo\s*(?:\{|\(|\n)", str(content))
        )
    )
    return {
        "status": status,
        "returned_model": body.get("model") if isinstance(body, dict) else None,
        "finish_reason": choice.get("finish_reason"),
        "native_tool_call_count": len(native),
        "native_tool_calls": native,
        "assistant_content": content,
        "textual_pseudo_tool_call": pseudo,
        "usage": body.get("usage") if isinstance(body, dict) else None,
        "error": {
            key: body.get(key)
            for key in ("detail", "code", "type", "message")
            if isinstance(body, dict) and body.get(key) is not None
        },
        "response_headers": headers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--base-url")
    source.add_argument("--base-url-env")
    parser.add_argument("--endpoint-label", required=True)
    parser.add_argument("--api-key-env", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base_url = args.base_url or os.environ.get(args.base_url_env or "", "")
    key = os.environ.get(args.api_key_env, "")
    if not base_url:
        raise SystemExit("base URL is missing")
    if not key:
        raise SystemExit(f"{args.api_key_env} is missing")

    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": "Call preflight_echo exactly once with value ok. Do not answer in prose.",
            }
        ],
        "tools": [TOOL],
        "tool_choice": "auto",
        "temperature": 1.0,
        "top_p": 1.0,
        "max_tokens": 256,
        "stream": False,
    }
    results = []
    endpoint = base_url.rstrip("/") + "/chat/completions"
    for attempt in range(1, args.attempts + 1):
        status, body, headers = post(endpoint, key, payload)
        item = summarize(status, body, headers)
        item["attempt"] = attempt
        results.append(item)

    artifact = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "endpoint_label": args.endpoint_label,
        "model": args.model,
        "request_shape": {
            "messages": payload["messages"],
            "tools": payload["tools"],
            "tool_choice": payload["tool_choice"],
            "temperature": payload["temperature"],
            "top_p": payload["top_p"],
            "max_tokens": payload["max_tokens"],
            "stream": payload["stream"],
        },
        "results": results,
        "summary": {
            "attempts": len(results),
            "http_200": sum(item["status"] == 200 for item in results),
            "attempts_with_native_tool_calls": sum(item["native_tool_call_count"] > 0 for item in results),
            "attempts_with_textual_pseudo_calls": sum(item["textual_pseudo_tool_call"] for item in results),
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({"artifact": str(output), **artifact["summary"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
