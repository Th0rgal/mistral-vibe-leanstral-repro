# Support report: recurring Mistral API 401 and Vibe failure

## Customer identity

- Account ID: `76a1b995-3912-40f0-8ab5-a25ce3341e1f`
- Organization ID: `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`

## Summary

I have used both a Mistral API key and a credential associated with my former Vibe subscription. My Vibe subscription has ended. In practice, credentials repeatedly end up returning HTTP 401 until I create a new API key. This makes Vibe and the direct API unreliable enough that I moved my Lean workload to a self-hosted Leanstral model on a DGX Spark.

The self-hosted model must be a 4-bit NVFP4 quant because the DGX Spark has 128 GB of unified memory. I would prefer to use the hosted Mistral endpoint, but the recurring authentication failure blocks it.

The repeated historical invalidation is customer-reported behavior. This repository captures one precise, simultaneous snapshot with both currently provisioned credentials.

## Reproduction environment

- UTC timestamp, direct API probes: `2026-07-19T07:43:50Z`–`07:43:51Z`
- UTC timestamp, Vibe probes: `2026-07-19T07:45:44Z`–`07:45:47Z`
- Mistral Vibe: `2.21.0`
- API base: `https://api.mistral.ai/v1`
- User-Agent: `th0rgal-mistral-auth-repro/1.0`
- Authentication: `Authorization: Bearer <credential>`
- Redirects: none
- Egress reached Cloudflare POP `HEL`

## Direct API reproduction

The same request shape was issued separately with each credential. Credentials were held only in process memory.

### Credential A: `MISTRAL_API_KEY`

| Request | Status | Body | CF-Ray |
|---|---:|---|---|
| `GET /v1/models` | 401 | `{"detail":"Unauthorized"}` | `a1d818f6ae96cc81-HEL` |
| `POST /v1/chat/completions`, `mistral-small-latest` | 401 | same | `a1d818f6f934b69e-HEL` |
| `POST /v1/chat/completions`, `leanstral-1-5` | 401 | same | `a1d818f74d668dda-HEL` |
| `POST /v1/chat/completions`, `labs-leanstral-1-5` | 401 | same | `a1d818f7b9c6b141-HEL` |

### Credential B: `MISTRAL_VIBE_SECRET`

For this comparison, the value was intentionally tested as the Bearer credential. This does **not** assume that a subscription credential is contractually interchangeable with an API key; clarification on the intended credential flow is part of the support request.

| Request | Status | Body | CF-Ray |
|---|---:|---|---|
| `GET /v1/models` | 401 | `{"detail":"Unauthorized"}` | `a1d818f7f8dde756-HEL` |
| `POST /v1/chat/completions`, `mistral-small-latest` | 401 | same | `a1d818f858c48d75-HEL` |
| `POST /v1/chat/completions`, `leanstral-1-5` | 401 | same | `a1d818f8ac589a02-HEL` |
| `POST /v1/chat/completions`, `labs-leanstral-1-5` | 401 | same | `a1d818f8fd3f8d81-HEL` |

The general model `mistral-small-latest` fails identically, so this snapshot is not a Leanstral entitlement/model-name failure. Authentication is rejected before model resolution.

## Vibe reproduction

Vibe 2.21.0's built-in Lean profile uses:

```text
provider: https://api.mistral.ai/v1
credential env: MISTRAL_API_KEY
model: labs-leanstral-1-5
```

Each credential was separately assigned to `MISTRAL_API_KEY` in the child process. Both runs exited 1 in under three seconds and printed exactly:

```text
Error: API error from mistral-testing (model: labs-leanstral-1-5): Invalid API key. Please check your API key and try again.
```

The detailed Vibe log also records:

```text
401 Unauthorized
https://api.mistral.ai/v1/connectors/bootstrap?include_auth_actionable_connectors=true
```

No model output or tool call occurred.

## Questions for Mistral

1. Can you inspect key creation, revocation, expiry, and organization-membership events for the account and organization above?
2. Why do API keys for this account repeatedly begin returning 401 until a new key is created?
3. Can ending a Vibe subscription invalidate API keys, organization membership, or credentials used by the API platform?
4. What is the intended credential mechanism for a Vibe subscription? Vibe 2.21.0 reads only `MISTRAL_API_KEY`; should a subscription credential ever be used there?
5. Is `labs-leanstral-1-5`, hardcoded by Vibe 2.21.0, still a supported alias? The current public model card refers to `leanstral-1-5`.
6. Can you correlate the CF-Ray identifiers above with an internal auth rejection reason or request ID?

## Secondary local-Vibe observation

After the hosted API became unusable, I self-hosted Leanstral 1.5 as an NVFP4 GGUF through llama.cpp. On three public Lean tasks the model returned textual pseudo-calls such as `read_file{"path": ...}` but an empty native `tool_calls` field. Stock Vibe executed nothing and ended after one turn.

This is intentionally reported as an interoperability observation, not as evidence against the hosted model. The runtime differs from Mistral's recommended vLLM setup and uses a 4-bit quant. The three sanitized traces are included so the expected parser/tool-protocol behavior can be discussed precisely.

## Security

No credential value, prefix, suffix, hash, or length appears in this repository. Logs were allow-list reduced and scanned before publication. Account and organization IDs are included intentionally for support correlation.
