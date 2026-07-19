# Message ready to send to Mistral

**Subject:** Leanstral 1.5 official chat template breaks tool-result turns under llama.cpp

Hello Mistral team,

I tested `mistralai/Leanstral-1.5-119B-A6B` as the third-party
`Frosty40/Leanstral-1.5-119B-A6B-GGUF-NVFP4` quant under llama.cpp b9294 on a
DGX Spark. The GGUF did not contain `tokenizer.chat_template`, so llama.cpp initially selected an
incompatible ChatML-style fallback and returned textual pseudo-calls instead of structured
`message.tool_calls`.

Loading Mistral's official `chat_template.jinja` fixed the first turn: the local endpoint returned
native tool calls in 10/10 identical requests. However, every tool-result follow-up then failed with
HTTP 500:

```text
Error: Not enough arguments provided to macro 'render_content'
```

The official template defines:

```jinja
macro render_content(content, context_name, supported_types_desc, support_thinking, support_images)
```

but its `role == 'tool'` branch calls the macro without `support_thinking`. Adding
`support_thinking=false` to that call fixes the second and subsequent agent turns.

After that one-line correction and removal of legacy ChatML stops for Leanstral 1.5:

| Check | Result |
|---|---:|
| Externally exposed route, HTTP 200 | 10/10 |
| Native `message.tool_calls` | 10/10 |
| Textual pseudo-calls | 0/10 |
| Direct llama.cpp tool-result follow-ups | 3/3 HTTP 200 |
| Router tool-result follow-ups | 3/3 HTTP 200 |
| Stock Vibe benchmark canary | 22 native calls and 22 executed results over 12 turns |

The canary reached the public verifier correctly but scored 0/1 because the model never edited the
proof placeholder. That is a model/agent outcome, not a transport failure. The earlier hosted panel
also scored 0/3 despite 60 native Vibe calls; its concrete ERC-4626 and Uniswap proof attempts did
not compile. I am treating proof quality separately from this deterministic template defect.

The full reproduction, exact request shape, scripts, prompts, tool counts, verifier errors, model provenance, and sanitized evidence are here:

- Repository: https://github.com/Th0rgal/mistral-vibe-leanstral-repro
- Comparison: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/blob/main/COMPARISON.md
- Evidence: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/tree/evidence/2026-07-19/artifacts

Could you please:

1. correct the missing `support_thinking` argument in the official template's tool-result branch;
2. publish the supported llama.cpp template/parser configuration alongside the existing vLLM recommendation;
3. make Vibe report raw tool sentinels as a template/parser mismatch instead of silently ending the turn; and
4. confirm whether the observed 300k–440k cumulative tokens per 12-turn built-in Vibe task is expected?

Separately, two replacement API keys became persistently unauthorized while the Admin key list still identified the tested replacement as type **Studio**, expiration **Never**, with the default **Shared connectors only** scope. Both failures were reproduced with fixed in-memory credentials on two execution paths plus fresh secret-manager reads, ruling out local secret rollback, client headers, and network path differences.

For the latest key, I first reproduced the documented rate limit: a controlled 320-request Leanstral burst produced 298 HTTP 200 responses and 22 explicit `429 rate_limited` responses at the advertised 300 requests/minute limit, then recovered to HTTP 200 after 70 seconds. The key later changed from 200 at `13:05:19.689901Z` to persistent 401 at `13:05:24.738584Z`, 36 minutes 35.478 seconds after the secret-manager revision. The benchmark namespace changed within 0.253 seconds and a fresh secret read also returned 401 for both `/models` and chat. Before invalidation, our controlled ledger recorded 7,986 API-reported tokens and 1,107 successful requests. The failure returned no rate-limit headers or `Retry-After`, only `401 {"detail":"Unauthorized"}`.

This falsifies a fixed one-hour TTL and distinguishes the persistent 401 from ordinary rate limiting. Please investigate the exact server-side revocation event at `13:05:24Z`: did an anti-abuse system react asynchronously to the earlier 300 RPM event, is there an undocumented per-key/Labs evaluation request limit, or is Workspace/Organization state inconsistent between the Admin control plane and API auth data plane? Please confirm the key's internal issue/expiry/revocation state and correlate the supplied CF-Ray IDs. My account ID is `76a1b995-3912-40f0-8ab5-a25ce3341e1f` and organization ID is `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`.

No credential value, prefix, hash, length, authorization header, private endpoint, or local filesystem identity is included in the repository.

Thanks,
Thomas