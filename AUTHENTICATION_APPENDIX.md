# Historical authentication appendix

> This is preserved as supporting context, not the repository's primary report. For the reproducible Leanstral tool-calling and hosted-vs-NVFP4 comparison, start with [`COMPARISON.md`](COMPARISON.md). Authentication-lifecycle details are summarized only in the direct support message.

## Instrumented approximately one-hour transition

A later replacement key was monitored using two long-lived processes that retained the exact credential in memory, plus a third path that re-read Bitwarden on every tick:

| Path | Last 200 | First 401 | CF-Ray transition |
|---|---|---|---|
| Host, fixed in-memory credential | `12:09:48.407374Z` | `12:10:14.172365Z` | `a1d99e8aacc85288-HEL` → `a1d99f2e586a8dab-HEL` |
| Benchmark namespace, same fixed credential | `12:09:49.156194Z` | `12:10:15.210414Z` | `a1d99e8f2c3c1579-HEL` → `a1d99f34debf15dc-HEL` |
| Fresh Bitwarden read | `12:09:40.320332Z` | `12:10:44.047700Z` | `a1d99e581ed85894-HEL` → `a1d99fe91e3e15dc-HEL` |

The Bitwarden secret revision was recorded at `11:10:21.332866Z`. The first fixed-key 401 followed 3,592.839499 seconds later—59 minutes 52.84 seconds. The last fixed-key 200 and first 401 are separated by only 25.764991 seconds. The host and benchmark namespace had identical public egress, and exact-value scans found no copy of the current key in 515,262 inspected workspace/log files.

Immediately before invalidation, `labs-leanstral-1-5` returned 200 with rate-limit headers showing 30,000,000 tokens/minute and 300 requests/minute, nearly all remaining. `mistral-small-latest` showed 500,000 tokens/minute and 1,000 requests/minute; an eight-request concurrent burst returned 8/8 HTTP 200 and consumed 160 tokens. The subsequent failure returned generic 401 for both `/models` and chat, without `Retry-After` or rate-limit headers.

This evidence rules out ordinary API rate limiting and strongly indicates a credential-lifecycle event close to a one-hour TTL. Mistral Admin confirms that the replacement key is type **Studio**, expiration **Never**, with the default **Shared connectors only** scope. Per Mistral's documentation, that scope controls Connector access only and does not restrict ordinary model/chat API calls. The Vibe-plan-key explanation therefore does not apply: the leading diagnosis is an auth control-plane/data-plane inconsistency, erroneous internal expiry, or hourly Workspace/Organization entitlement revalidation. Only Mistral can inspect the key's internal issue/expiry state and explicit revocation reason.

## Second Studio/Never key: controlled 429 followed by persistent 401

A subsequent Studio/Never key falsified a fixed one-hour TTL. A controlled 320-request Leanstral burst hit the advertised 300 RPM boundary: 298 requests returned 200, 22 returned explicit `429 rate_limited`, and a request after 70 seconds recovered to 200. This demonstrates the ordinary rate-limit response and recovery path.

The same key later returned its last 200 at `13:05:19.689901Z` and first persistent 401 at `13:05:24.738584Z`, only 2,195.477975 seconds (36 minutes 35.478 seconds) after the secret-manager revision. The benchmark namespace changed within 0.253 seconds; a fresh secret-manager read returned 401 for both `/models` and chat. Controlled usage before invalidation totaled 7,986 API-reported tokens and 1,107 successful requests.

This later result rules out both ordinary rate limiting and a deterministic one-hour expiration. Plausible server-side causes now include delayed anti-abuse revocation after the RPM burst, an undocumented per-key/Labs evaluation request threshold, or Workspace/Organization entitlement state inconsistent between the Admin control plane and API auth data plane.

## Customer identity

- Account ID: `76a1b995-3912-40f0-8ab5-a25ce3341e1f`
- Organization ID: `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`

## Summary

I have used both a Mistral API key and a credential associated with my former Vibe subscription. My Vibe subscription has ended. In practice, credentials repeatedly end up returning HTTP 401 until I create a new API key. This makes Vibe and the direct API unreliable enough that I moved my Lean workload to a self-hosted Leanstral model on a DGX Spark.

The self-hosted model must be a 4-bit NVFP4 quant because the DGX Spark has 128 GB of unified memory. I would prefer to use the hosted Mistral endpoint, but the recurring authentication failure blocks it.

The repository now captures both the original simultaneous 401 snapshot and a stronger reproduction of the lifecycle problem: after I rotated `MISTRAL_API_KEY`, the new key returned 200 and reached the hosted Leanstral endpoint, then returned the same 401 less than 19 minutes later.

## Reproduction environment

- UTC timestamp, direct API probes: `2026-07-19T07:43:50Z`–`07:43:51Z`
- UTC timestamp, Vibe probes: `2026-07-19T07:45:44Z`–`07:45:47Z`
- UTC timestamp, rotated-key success: `2026-07-19T08:09:12Z`–`08:22:28Z`
- UTC timestamp, rotated-key 401 recheck: `2026-07-19T08:28:09Z`–`08:28:17Z`
- Mistral Vibe: `2.21.0`
- API base: `https://api.mistral.ai/v1`
- User-Agent: `th0rgal-mistral-auth-repro/1.0`
- Authentication: `Authorization: Bearer [REDACTED]`
- Redirects: none
- Egress reached Cloudflare POP `HEL`

## Rotated-key valid-to-invalid transition

After replacing `MISTRAL_API_KEY` in the secret manager, the following requests succeeded or reached normal model validation:

| UTC | Request | Result | CF-Ray |
|---|---|---|---|
| `08:09:12` | `GET /v1/models` | 200; model catalog returned | `a1d83e1c7adff78c-HEL` |
| `08:09:12` | `mistral-small-latest` completion | 200; assistant returned `OK` | `a1d83e1f7ea6e9e8-HEL` |
| `08:09:13` | `leanstral-1-5` completion | 400 `invalid_model` | `a1d83e213af9554a-HEL` |
| `08:09:13` | `labs-leanstral-1-5`, greedy shape | 400 `invalid_request_greedy_sampling`; the model was resolved | `a1d83e21bfccb8cb-HEL` |

The returned catalog listed:

```text
labs-leanstral-1-5
labs-leanstral-1-5-1
```

Each is an alias of the other, with `function_calling: true`, `reasoning: true`, and a 262,144-token context. The unprefixed `leanstral-1-5` ID was not valid for this account.

Two hosted benchmark canaries then authenticated:

- Vibe 2.21.0 ran from `08:22:01.124462Z` to `08:22:13.813777Z`. Its provider accounting recorded 52,214 prompt tokens and 1,062 completion tokens, totaling 53,276. The experiment had an incorrect 50,000-token client cap, so it stopped before tool execution. This attempt is `INFRA_INVALID`, not a hosted-model score.
- The standalone harness then completed five authenticated requests and accounted for another 696 tokens: 328 prompt and 368 completion. Chat completion, model selection, and usage checks passed. Its streaming protocol probe did not observe a native tool call, so the harness correctly stopped before scoring. A separate correctly shaped direct request had observed a native tool call earlier in the valid window.

These two durable canaries account for 53,972 LLM tokens before failure, excluding earlier successful direct probes whose usage counters were not retained. This is a lower bound on observed consumption, not evidence of a token quota.

The first 401 has a server timestamp of `08:28:08Z`. This places the transition within 354.186 seconds—5 minutes 54.186 seconds—after the last precisely timestamped successful Vibe session. The standalone preflight made five successful requests later in the same period and ended at approximately `08:22:27.890Z`, but it did not persist per-request timestamps; it likely narrows the gap to about 5 minutes 40 seconds, but that is not a hard bound.

At `08:28:09Z`, all three correctly shaped hosted Leanstral probes had returned 401. At `08:28:17Z`, a full recheck returned the same response for `/models`, `mistral-small-latest`, `leanstral-1-5`, and `labs-leanstral-1-5`:

```text
HTTP 401
{"detail":"Unauthorized"}
```

The `/models` recheck CF-Ray was `a1d85a0ef8cdf78c-HEL`; the three completion CF-Rays were `a1d85a0f3eec2945-HEL`, `a1d85a0f9f51e39a-HEL`, and `a1d85a0fe891a0a8-HEL`.

No local credential configuration changed between the successful and rejected windows. The corrected retries—a 200,000-token Vibe budget and non-streaming standalone transport—are prepared but cannot run while the key is rejected.

The evidence does not identify a token-triggered cutoff. A token threshold near 54k is only one hypothesis; there was no request exactly at the transition, earlier direct-probe usage is missing, and a quota would normally be expected to produce a quota/rate-limit response rather than a generic 401. Mistral's internal key event logs are required to distinguish revocation, expiry, organization state, policy, or another authentication-layer cause.

## Original direct API reproduction

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

The general model `mistral-small-latest` failed identically in this original snapshot, so that snapshot was not a Leanstral entitlement/model-name failure. Authentication was rejected before model resolution.

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

1. Can you inspect key creation, revocation, expiry, and organization-membership events for the account and organization above, specifically between `08:09:12Z` and `08:28:09Z` on 2026-07-19?
2. Why did a newly rotated key successfully list models and complete authenticated requests, then begin returning 401 less than 19 minutes later?
3. Can ending a Vibe subscription invalidate API keys, organization membership, or credentials used by the API platform?
4. What is the intended credential mechanism for a Vibe subscription? Vibe 2.21.0 reads only `MISTRAL_API_KEY`; should a subscription credential ever be used there?
5. Is `labs-leanstral-1-5` the intended current API ID? It was listed and resolved successfully, while `leanstral-1-5` returned `invalid_model`.
6. Can you correlate the CF-Ray identifiers above with an internal auth rejection reason or request ID?

## Secondary local-Vibe observation

After the hosted API became unusable, I self-hosted Leanstral 1.5 as an NVFP4 GGUF through llama.cpp. On three public Lean tasks the model returned textual pseudo-calls such as `read_file{"path": ...}` but an empty native `tool_calls` field. Stock Vibe executed nothing and ended after one turn.

This is intentionally reported as an interoperability observation, not as evidence against the hosted model. The runtime differs from Mistral's recommended vLLM setup and uses a 4-bit quant. The three sanitized traces are included so the expected parser/tool-protocol behavior can be discussed precisely.

## Comparison status

The local NVFP4 lanes have verifier-backed results: stock Vibe scored 0/3 with no native tool calls or edits, and the standalone fallback lane scored 0/3 after tool loops with no edits. The hosted canaries above are both `INFRA_INVALID`, so no hosted score is reported and no score comparison is claimed. Completing the same three tasks requires a hosted credential that remains valid through the run.

## Security

No credential value, prefix, suffix, hash, or length appears in this repository. Logs were allow-list reduced and scanned before publication. Account and organization IDs are included intentionally for support correlation.
