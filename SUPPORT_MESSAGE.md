# Message ready to send to Mistral

**Subject:** Leanstral 1.5 tool-calling comparison, local parser mismatch, and request for an evaluation key

Hello Mistral team,

I ran a controlled comparison between:

- hosted `labs-leanstral-1-5` through the Mistral API;
- the same model family self-hosted as `Frosty40/Leanstral-1.5-119B-A6B-GGUF-NVFP4` through llama.cpp on a DGX Spark;
- Mistral Vibe 2.21.0 and a separate Lean MCP benchmark harness;
- three identical public Lean tasks at benchmark commit `2b27270b66a1fc248e4ff594ba323698648ef02c`.

The minimal direct protocol test is particularly clear. I sent the same non-streaming request ten times to each endpoint, with the same prompt, tool schema, `tool_choice: auto`, temperature 1, and top-p 1:

| Endpoint | HTTP 200 | Native `tool_calls` | Textual pseudo-calls | Empty/plain responses |
|---|---:|---:|---:|---:|
| Mistral API | 10/10 | **10/10** | 0/10 | 0/10 |
| Local NVFP4 llama.cpp | 10/10 | **0/10** | 2/10 | 8/10 |

The local endpoint sometimes returned raw sentinel text in assistant `content`:

```text
<|tool_call_begin|>preflight_echo
<|tool_call_argument_begin|>value: ok
<|tool_call_end|>
```

Stock Vibe does not execute this as a tool call. The hosted API consistently returns structured `tool_calls`, so I do not think this is a general inability of the Leanstral weights to call tools. It looks like a local chat-template/parser interoperability problem.

On the three Lean tasks:

| Lane | Score | Tool behavior | Code progress | Tokens |
|---|---:|---|---|---:|
| Hosted + Vibe 2.21.0 | 0/3 | 60 native calls executed | one edit | 1,201,624 |
| NVFP4 llama.cpp + Vibe | 0/3 | zero native calls; four textual pseudo-calls | no edits | 9,586 |
| Hosted standalone | 0/3 | 13 Lean MCP calls | one submitted proof | 196,415 |
| NVFP4 standalone fallback | 0/3 | six Lean MCP calls | no submissions | 74,748 |

The hosted model therefore made much more operational progress, but it did not solve the panel. Its two concrete proof attempts failed:

- ERC-4626: `unfold deposit_redeem_round_trip_bound_spec; grind`; `grind` left the arithmetic goal.
- Uniswap: `simp only [grind_norm]; exact hK`; Lean hit the maximum recursion depth.

The full reproduction, exact request shape, scripts, prompts, tool counts, verifier errors, model provenance, and sanitized evidence are here:

- Repository: https://github.com/Th0rgal/mistral-vibe-leanstral-repro
- Comparison: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/blob/main/COMPARISON.md
- Evidence: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/tree/evidence/2026-07-19/artifacts

Could you help clarify:

1. Which exact local serving configuration reproduces the hosted Leanstral parser and chat template?
2. Are vLLM's `--tool-call-parser mistral`, `--enable-auto-tool-choice`, and `--reasoning-parser mistral` required? Is there a supported llama.cpp equivalent?
3. Should Vibe detect raw `<|tool_call_begin|>` sentinels and report a parser mismatch rather than ending the turn without executing anything?
4. Is `labs-leanstral-1-5` the intended stable API model ID for evaluation?
5. Is 300k–440k cumulative tokens per 12-turn Vibe task expected for the built-in Lean agent, or should it compact earlier?

I would also like to run repeated seeded panels rather than a single three-task sample. The observed concurrent peak exceeded 500k tokens/minute, and the final comparison alone used about 1.4 million hosted tokens. Could you provide a temporary Leanstral-specific evaluation key with approximately:

- at least 1 million tokens/minute;
- at least 60 requests/minute;
- stable access to `labs-leanstral-1-5` for several days;
- enough total quota for repeated 3-task and larger benchmark panels?

Separately, two replacement API keys became persistently unauthorized while the Admin key list still identified the tested replacement as type **Studio**, expiration **Never**, with the default **Shared connectors only** scope. Both failures were reproduced with fixed in-memory credentials on two execution paths plus fresh secret-manager reads, ruling out local secret rollback, client headers, and network path differences.

For the latest key, I first reproduced the documented rate limit: a controlled 320-request Leanstral burst produced 298 HTTP 200 responses and 22 explicit `429 rate_limited` responses at the advertised 300 requests/minute limit, then recovered to HTTP 200 after 70 seconds. The key later changed from 200 at `13:05:19.689901Z` to persistent 401 at `13:05:24.738584Z`, 36 minutes 35.478 seconds after the secret-manager revision. The benchmark namespace changed within 0.253 seconds and a fresh secret read also returned 401 for both `/models` and chat. Before invalidation, our controlled ledger recorded 7,986 API-reported tokens and 1,107 successful requests. The failure returned no rate-limit headers or `Retry-After`, only `401 {"detail":"Unauthorized"}`.

This falsifies a fixed one-hour TTL and distinguishes the persistent 401 from ordinary rate limiting. Please investigate the exact server-side revocation event at `13:05:24Z`: did an anti-abuse system react asynchronously to the earlier 300 RPM event, is there an undocumented per-key/Labs evaluation request limit, or is Workspace/Organization state inconsistent between the Admin control plane and API auth data plane? Please confirm the key's internal issue/expiry/revocation state and correlate the supplied CF-Ray IDs. My account ID is `76a1b995-3912-40f0-8ab5-a25ce3341e1f` and organization ID is `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`.

No credential value, prefix, hash, length, authorization header, private endpoint, or local filesystem identity is included in the repository.

Thanks,
Thomas