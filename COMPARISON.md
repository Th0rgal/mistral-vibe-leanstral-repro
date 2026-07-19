# Leanstral 1.5: hosted API vs local NVFP4 tool behavior

## Executive finding

The hosted Mistral endpoint and the local NVFP4 llama.cpp endpoint do not expose the same tool protocol.

Using the same non-streaming request, tool schema, prompt, sampling, and `tool_choice: auto`:

| Endpoint | HTTP 200 | Native `tool_calls` | Textual pseudo-calls | Empty/plain responses |
|---|---:|---:|---:|---:|
| Mistral API, `labs-leanstral-1-5` | 10/10 | **10/10** | 0/10 | 0/10 |
| Local NVFP4 through llama.cpp | 10/10 | **0/10** | 2/10 | 8/10 |

One local pseudo-call was returned as assistant text rather than structured `tool_calls`:

```text
<|tool_call_begin|>preflight_echo
<|tool_call_argument_begin|>value: ok
<|tool_call_end|>
```

Stock Vibe does not execute that text as a tool call. This explains the one-turn/no-tool behavior observed with the local quant. It does **not** show that hosted Leanstral lacks native tool support: the API result is consistently structured and works through Vibe.

## Minimal protocol reproduction

The probe uses Python's standard library and never records the credential or endpoint secret.

### Hosted Mistral API

```bash
export MISTRAL_API_KEY='set locally; never commit'
python3 scripts/probe_tool_calling.py \
  --base-url https://api.mistral.ai/v1 \
  --endpoint-label mistral-api \
  --api-key-env MISTRAL_API_KEY \
  --model labs-leanstral-1-5 \
  --attempts 10 \
  --output /tmp/tool-probe-hosted.json
```

Expected observed summary:

```json
{
  "attempts": 10,
  "http_200": 10,
  "attempts_with_native_tool_calls": 10,
  "attempts_with_textual_pseudo_calls": 0
}
```

### Local OpenAI-compatible endpoint

```bash
export LEANSTRAL_LOCAL_BASE_URL='http://localhost:PORT/v1'
export LEANSTRAL_LOCAL_API_KEY='set locally if required'
python3 scripts/probe_tool_calling.py \
  --base-url-env LEANSTRAL_LOCAL_BASE_URL \
  --endpoint-label local-nvfp4-llamacpp \
  --api-key-env LEANSTRAL_LOCAL_API_KEY \
  --model leanstral-1.5 \
  --attempts 10 \
  --output /tmp/tool-probe-local.json
```

The captured local deployment used route `spark/leanstral-1.5-119b-a6b`; replace the model ID with the one exposed by the local server.

## Three-task agent comparison

All tasks, prompts, starters, benchmark SHA, tool budget, turn budget, and private verifier were held constant. The benchmark checkout was:

```text
lfglabs-dev/ethereum-verification-benchmark
2b27270b66a1fc248e4ff594ba323698648ef02c
Lean 4.24.0
lean-lsp-mcp 0.28.0
```

Tasks:

1. `1inch/xycswap_curve_safety/quote_exact_in_curve_safety`
2. `openzeppelin/erc4626_virtual_offset_deposit/deposit_redeem_round_trip_bound`
3. `uniswap_v2/pair_fee_adjusted_swap/swap_enforces_fee_adjusted_invariant`

### Vibe 2.21.0

| Runtime | Score | Native calls executed | Tool successes/failures | Files changed | Tokens |
|---|---:|---:|---:|---:|---:|
| Hosted `labs-leanstral-1-5` | 0/3 | **60** | 58 / 2 | 1/3 | 1,201,624 |
| Local NVFP4 llama.cpp | 0/3 | **0** | 0 / 0 | 0/3 | 9,586 |

Hosted per-task behavior:

| Task | Native calls | Main tools | Edit | Verifier |
|---|---:|---|---:|---|
| 1inch | 21 | `read_file`, `bash`, Lean goal/search/build | no | `forbidden_placeholder` |
| ERC-4626 | 20 | `read_file`, `bash`, Lean goal/build | no | `lean_check_failed` |
| Uniswap v2 | 19 | `read_file`, `bash`, `edit`, Lean goal/diagnostics/build | yes | `lean_check_failed` |

Every hosted run reached the 12-turn benchmark limit. The Uniswap attempt changed the proof to:

```lean
by
  simp only [grind_norm]
  exact hK
```

Lean rejected it with `maximum recursion depth has been reached`.

The local NVFP4 sessions ended after one assistant turn because Vibe received no native calls. They emitted zero edits and only four textual pseudo-calls across all three tasks.

### Standalone benchmark harness

| Runtime | Score | Requests | Lean MCP calls | Files submitted | Tokens |
|---|---:|---:|---:|---:|---:|
| Hosted, native tools | 0/3 | 29 | **13** | 1/3 | 196,415 |
| Local NVFP4, JSON-text fallback | 0/3 | 27 | **6** | 0/3 | 74,748 |

All three final hosted artifacts passed `scripts/check_run_artifacts.py` and were classified `GENUINE_FAIL`, not infrastructure failures.

The hosted ERC-4626 run submitted:

```lean
by
  unfold deposit_redeem_round_trip_bound_spec
  grind
```

Lean rejected it because `grind` left the core arithmetic goal. The 1inch and Uniswap hosted runs ended in repetition loops without a gradeable submission.

## Interpretation

### Established

1. Hosted Leanstral emits valid native Mistral tool calls.
2. Stock Vibe executes those calls and sustains multi-turn tool loops.
3. The tested local NVFP4/llama.cpp stack does not convert Leanstral's textual tool sentinels into OpenAI `tool_calls`.
4. Hosted Leanstral makes more operational progress than the local quant: 60 Vibe calls, 13 Lean MCP calls, and two concrete proof edits/submissions.
5. Neither runtime solved any of the three tasks.

### Not established

1. The experiment does not isolate quantization from serving/parser differences.
2. It does not show that the unquantized weights fail tool calling; the hosted API demonstrates the opposite.
3. The panel is behavioral evidence on a frozen diagnostic benchmark commit, not a published current-main benchmark score.
4. Large hosted Vibe usage reflects cumulative multi-turn session accounting and is not a measure of proof efficiency by itself.

## Questions for Mistral

1. Which exact local serving configuration reproduces the hosted parser and chat template for Leanstral 1.5?
2. Are vLLM's `--tool-call-parser mistral`, `--enable-auto-tool-choice`, and `--reasoning-parser mistral` required for correct behavior, and is there an equivalent supported llama.cpp configuration?
3. Should Vibe detect raw `<|tool_call_begin|>` sentinels and report a parser mismatch instead of silently ending the agent turn?
4. Is `labs-leanstral-1-5` the intended stable API model ID for external evaluation?
5. Is the 300k–440k cumulative-token range per 12-turn Vibe task expected for the built-in Lean agent, or should the session be compacted earlier?
6. Can Mistral provide a temporary Leanstral-specific evaluation key with at least 1M tokens/minute, 60 requests/minute, stable Labs entitlement, and several days of validity? The observed concurrent peak exceeded 500k tokens/minute, and repeated seeded panels will require materially more than the single-run 1.4M-token final comparison.

## Evidence

Sanitized machine-readable probe outputs and comparison summaries are on branch `evidence/2026-07-19`. No credential value, prefix, hash, length, authorization header, private endpoint, or local filesystem identity is included.
