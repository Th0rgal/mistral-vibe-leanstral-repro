# Focused Mistral authentication bug report

**Subject:** Studio / Never-expiring API keys become permanently unauthorized after initially working

Hello Mistral team,

Two newly created API keys became permanently unauthorized after initially working normally. The Admin control plane identifies the tested key as:

- type: **Studio**;
- expiration: **Never**;
- connector scope: **Shared connectors only**.

The failure is a generic persistent response on both `/v1/models` and `/v1/chat/completions`:

```text
HTTP 401
{"detail":"Unauthorized"}
```

This is distinct from ordinary rate limiting. In a controlled test against `labs-leanstral-1-5`, the advertised 300 requests/minute limit produced explicit `429 rate_limited` responses and recovered to HTTP 200 after 70 seconds. The same key later changed from 200 to persistent 401:

- last HTTP 200: `2026-07-19T13:05:19.689901Z`;
- first host HTTP 401: `2026-07-19T13:05:24.738584Z`;
- first benchmark-namespace HTTP 401: `2026-07-19T13:05:24.485833Z`;
- fresh secret-manager read also returned 401 for models and chat at `13:05:38.655797Z`;
- elapsed from secret-manager revision: 2,195.477975 seconds (36 minutes 35.478 seconds);
- controlled usage before invalidation: 7,986 API-reported tokens and 1,107 successful requests.

A previous replacement key showed the same persistent 401 behavior after a different lifetime, so this is not a deterministic one-hour TTL. Fixed in-memory credentials, a separate benchmark namespace, and fresh secret-manager reads all failed together, ruling out local credential rollback, client headers, or network-path differences.

Please investigate:

1. What exact server-side revocation/authentication event invalidated this Studio/Never key at `13:05:24Z`?
2. Did an anti-abuse system react asynchronously to the earlier controlled 300 RPM event?
3. Is there an undocumented per-key request limit or Labs evaluation limit?
4. Why did the key become persistently unauthorized instead of receiving a documented 429 quota response?
5. Did the API auth data plane disagree with the Admin control plane about the key's active/expiry state?

Sanitized evidence with exact timestamps, CF-Ray IDs, request counts, usage and rate-limit recovery:

- Repository: https://github.com/Th0rgal/mistral-vibe-leanstral-repro
- Authentication appendix: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/blob/main/AUTHENTICATION_APPENDIX.md
- Machine-readable incident: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/blob/evidence/2026-07-19/artifacts/api/studio-key-rate-limit-and-401-20260719.json

Account ID: `76a1b995-3912-40f0-8ab5-a25ce3341e1f`  
Organization ID: `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`

No credential value, prefix, suffix, hash, length, or authorization header is included.

Thanks,  
Thomas
